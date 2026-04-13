package com.rimi.inventory;

import android.annotation.SuppressLint;
import android.Manifest;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothClass;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothSocket;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.ActivityInfo;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.os.SystemClock;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;
import android.webkit.PermissionRequest;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;

import java.io.IOException;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.UUID;

public class MainActivity extends AppCompatActivity {
    private static final int REQ_BT_PERMISSION = 7001;
    private static final int REQ_CAMERA_PERMISSION = 7002;
    private static final UUID SPP_UUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB");
    private static final String LOCAL_WEB_URL = "file:///android_asset/web/index.html";
    private static final long DISCOVERY_TIMEOUT_MS = 9000;
    private static final long DISCOVERY_LIST_TIMEOUT_MS = 5500;
    private static final long BOND_TIMEOUT_MS = 9000;

    private BluetoothAdapter bluetoothAdapter;
    private BluetoothSocket printerSocket;
    private BluetoothDevice connectedPrinter;
    private final Object printerLock = new Object();
    private WebView appWebView;
    private boolean localWebFallbackLoaded = false;
    private boolean printerAclReceiverRegistered = false;
    private PermissionRequest pendingWebPermissionRequest;

    private final BroadcastReceiver printerAclReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            String action = intent != null ? intent.getAction() : null;
            if (!BluetoothDevice.ACTION_ACL_DISCONNECTED.equals(action)
                    && !BluetoothDevice.ACTION_ACL_DISCONNECT_REQUESTED.equals(action)) {
                return;
            }

            BluetoothDevice eventDevice = null;
            try {
                eventDevice = intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE);
            } catch (Exception ignored) {
                // Ignore malformed intent extras.
            }
            if (eventDevice == null) {
                return;
            }

            synchronized (printerLock) {
                if (connectedPrinter == null) {
                    return;
                }
                try {
                    String connectedAddress = connectedPrinter.getAddress();
                    String eventAddress = eventDevice.getAddress();
                    if (connectedAddress != null
                            && eventAddress != null
                            && connectedAddress.equalsIgnoreCase(eventAddress)) {
                        closeSocketLocked();
                    }
                } catch (SecurityException ignored) {
                    // Permission races should not crash the app.
                }
            }
        }
    };

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_PORTRAIT);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        setContentView(R.layout.activity_main);

        bluetoothAdapter = BluetoothAdapter.getDefaultAdapter();

        appWebView = findViewById(R.id.webview);
        WebSettings settings = appWebView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);
        settings.setCacheMode(WebSettings.LOAD_NO_CACHE);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);

        appWebView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onPermissionRequest(PermissionRequest request) {
                handleWebPermissionRequest(request);
            }

            @Override
            public void onPermissionRequestCanceled(PermissionRequest request) {
                if (pendingWebPermissionRequest == request) {
                    pendingWebPermissionRequest = null;
                }
            }
        });
        appWebView.setWebViewClient(new InventoryWebViewClient());
        appWebView.addJavascriptInterface(new AndroidPrinterBridge(), "AndroidPrinter");
        appWebView.clearCache(true);
        appWebView.clearHistory();
        registerPrinterAclReceiver();
        loadRemoteWebApp();
    }

    private void loadRemoteWebApp() {
        if (appWebView == null) {
            return;
        }
        String cacheBust = String.valueOf(System.currentTimeMillis());
        appWebView.loadUrl(getString(R.string.web_app_url) + "?v=" + cacheBust);
    }

    private void loadLocalWebFallback() {
        if (appWebView == null || localWebFallbackLoaded) {
            return;
        }
        localWebFallbackLoaded = true;
        String cacheBust = String.valueOf(System.currentTimeMillis());
        appWebView.loadUrl(LOCAL_WEB_URL + "?v=" + cacheBust);
    }

    private final class InventoryWebViewClient extends WebViewClient {
        @Override
        public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
            super.onReceivedError(view, request, error);
            if (request != null && request.isForMainFrame()) {
                loadLocalWebFallback();
            }
        }

        @Override
        public void onReceivedError(WebView view, int errorCode, String description, String failingUrl) {
            super.onReceivedError(view, errorCode, description, failingUrl);
            loadLocalWebFallback();
        }

        @Override
        public void onReceivedHttpError(WebView view, WebResourceRequest request, WebResourceResponse errorResponse) {
            super.onReceivedHttpError(view, request, errorResponse);
            if (request != null && request.isForMainFrame() && errorResponse != null && errorResponse.getStatusCode() >= 400) {
                loadLocalWebFallback();
            }
        }
    }

    private boolean hasCameraPermission() {
        return ActivityCompat.checkSelfPermission(this, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED;
    }

    private void handleWebPermissionRequest(PermissionRequest request) {
        if (request == null) {
            return;
        }

        boolean wantsCamera = false;
        String[] resources = request.getResources();
        if (resources != null) {
            for (String resource : resources) {
                if (PermissionRequest.RESOURCE_VIDEO_CAPTURE.equals(resource)) {
                    wantsCamera = true;
                    break;
                }
            }
        }

        if (!wantsCamera) {
            request.grant(resources);
            return;
        }

        runOnUiThread(() -> {
            if (hasCameraPermission()) {
                request.grant(request.getResources());
                return;
            }

            pendingWebPermissionRequest = request;
            ActivityCompat.requestPermissions(
                    MainActivity.this,
                    new String[]{Manifest.permission.CAMERA},
                    REQ_CAMERA_PERMISSION
            );
        });
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);

        if (requestCode != REQ_CAMERA_PERMISSION) {
            return;
        }

        PermissionRequest pending = pendingWebPermissionRequest;
        pendingWebPermissionRequest = null;
        if (pending == null) {
            return;
        }

        boolean granted = grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED;
        if (granted) {
            pending.grant(pending.getResources());
        } else {
            pending.deny();
        }
    }

    @Override
    protected void onDestroy() {
        if (pendingWebPermissionRequest != null) {
            pendingWebPermissionRequest.deny();
            pendingWebPermissionRequest = null;
        }
        unregisterPrinterAclReceiver();
        super.onDestroy();
        synchronized (printerLock) {
            closeSocketLocked();
        }
    }

    private void registerPrinterAclReceiver() {
        if (printerAclReceiverRegistered) {
            return;
        }
        try {
            IntentFilter filter = new IntentFilter();
            filter.addAction(BluetoothDevice.ACTION_ACL_DISCONNECTED);
            filter.addAction(BluetoothDevice.ACTION_ACL_DISCONNECT_REQUESTED);
            registerReceiver(printerAclReceiver, filter);
            printerAclReceiverRegistered = true;
        } catch (Exception ignored) {
            // Best effort only.
        }
    }

    private void unregisterPrinterAclReceiver() {
        if (!printerAclReceiverRegistered) {
            return;
        }
        try {
            unregisterReceiver(printerAclReceiver);
        } catch (Exception ignored) {
            // Ignore unregister failures.
        } finally {
            printerAclReceiverRegistered = false;
        }
    }

    @SuppressLint("MissingPermission")
    private boolean isAclConnected(BluetoothDevice device) {
        if (device == null) {
            return false;
        }
        try {
            java.lang.reflect.Method method = BluetoothDevice.class.getMethod("isConnected");
            Object result = method.invoke(device);
            if (result instanceof Boolean) {
                return (Boolean) result;
            }
        } catch (Exception ignored) {
            // Reflection may be unavailable on some OS variants.
        }
        return true;
    }

    @SuppressLint("MissingPermission")
    private boolean hasLivePrinterConnectionLocked() {
        if (bluetoothAdapter == null || !bluetoothAdapter.isEnabled()) {
            closeSocketLocked();
            return false;
        }
        if (printerSocket == null || connectedPrinter == null) {
            return false;
        }

        try {
            if (!printerSocket.isConnected()) {
                closeSocketLocked();
                return false;
            }
        } catch (Exception ignored) {
            closeSocketLocked();
            return false;
        }

        if (!isAclConnected(connectedPrinter)) {
            closeSocketLocked();
            return false;
        }

        return true;
    }

    private static final class PrinterResult {
        final boolean ok;
        final String message;
        final String printer;

        PrinterResult(boolean ok, String message, String printer) {
            this.ok = ok;
            this.message = message;
            this.printer = printer;
        }
    }

    private static final class PrinterCandidate {
        final String name;
        final String address;
        final boolean bonded;

        PrinterCandidate(String name, String address, boolean bonded) {
            this.name = name;
            this.address = address;
            this.bonded = bonded;
        }
    }

    private String toJson(PrinterResult result) {
        return "{"
                + "\"ok\":" + result.ok + ","
                + "\"message\":\"" + jsonEscape(result.message) + "\","
                + "\"printer\":\"" + jsonEscape(result.printer) + "\""
                + "}";
    }

    private String jsonEscape(String value) {
        if (value == null) return "";
        return value
                .replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\n", " ")
                .replace("\r", " ");
    }

    private String toJsonPrinters(boolean ok, String message, List<PrinterCandidate> printers) {
        StringBuilder sb = new StringBuilder();
        sb.append("{")
                .append("\"ok\":").append(ok).append(",")
                .append("\"message\":\"").append(jsonEscape(message)).append("\",")
                .append("\"printers\":[");

        for (int i = 0; i < printers.size(); i++) {
            PrinterCandidate p = printers.get(i);
            if (i > 0) {
                sb.append(",");
            }
            sb.append("{")
                    .append("\"name\":\"").append(jsonEscape(p.name)).append("\",")
                    .append("\"address\":\"").append(jsonEscape(p.address)).append("\",")
                    .append("\"bonded\":").append(p.bonded)
                    .append("}");
        }

        sb.append("]}");
        return sb.toString();
    }

    private String toJsonPrinterHealth(
            String message,
            boolean bluetoothAvailable,
            boolean bluetoothEnabled,
            boolean connectPermission,
            boolean scanPermission,
            boolean locationPermission,
            boolean connected,
            String printer,
            String address,
            int bondedCount
    ) {
        return "{"
                + "\"ok\":true,"
                + "\"message\":\"" + jsonEscape(message) + "\"," 
                + "\"bluetoothAvailable\":" + bluetoothAvailable + ","
                + "\"bluetoothEnabled\":" + bluetoothEnabled + ","
                + "\"connectPermission\":" + connectPermission + ","
                + "\"scanPermission\":" + scanPermission + ","
                + "\"locationPermission\":" + locationPermission + ","
                + "\"connected\":" + connected + ","
                + "\"printer\":\"" + jsonEscape(printer) + "\"," 
                + "\"address\":\"" + jsonEscape(address) + "\"," 
                + "\"bondedCount\":" + bondedCount
                + "}";
    }

    private boolean hasPermission(String permission) {
        return ActivityCompat.checkSelfPermission(this, permission) == PackageManager.PERMISSION_GRANTED;
    }

    private boolean hasBluetoothConnectPermission() {
        if (android.os.Build.VERSION.SDK_INT < android.os.Build.VERSION_CODES.S) {
            return true;
        }
        return hasPermission(Manifest.permission.BLUETOOTH_CONNECT);
    }

    private boolean hasBluetoothScanPermission() {
        if (android.os.Build.VERSION.SDK_INT < android.os.Build.VERSION_CODES.S) {
            return true;
        }
        return hasPermission(Manifest.permission.BLUETOOTH_SCAN);
    }

    private boolean hasLegacyLocationPermission() {
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.S) {
            return true;
        }
        return hasPermission(Manifest.permission.ACCESS_FINE_LOCATION)
                || hasPermission(Manifest.permission.ACCESS_COARSE_LOCATION);
    }

    private boolean ensureBluetoothPermission() {
        if (android.os.Build.VERSION.SDK_INT < android.os.Build.VERSION_CODES.S) {
            if (hasLegacyLocationPermission()) {
                return true;
            }
            runOnUiThread(() -> ActivityCompat.requestPermissions(
                    MainActivity.this,
                    new String[]{Manifest.permission.ACCESS_FINE_LOCATION},
                    REQ_BT_PERMISSION
            ));
            return false;
        }

        if (hasBluetoothConnectPermission() && hasBluetoothScanPermission()) {
            return true;
        }

        runOnUiThread(() -> ActivityCompat.requestPermissions(
                MainActivity.this,
                new String[]{
                        Manifest.permission.BLUETOOTH_CONNECT,
                        Manifest.permission.BLUETOOTH_SCAN
                },
                REQ_BT_PERMISSION
        ));
        return false;
    }

    @SuppressLint("MissingPermission")
    private BluetoothDevice findBondedZq620() {
        if (bluetoothAdapter == null) {
            return null;
        }
        Set<BluetoothDevice> bonded = bluetoothAdapter.getBondedDevices();
        if (bonded == null || bonded.isEmpty()) {
            return null;
        }

        BluetoothDevice zebraLike = null;
        BluetoothDevice imagingLike = null;
        BluetoothDevice namedFallback = null;
        List<BluetoothDevice> any = new ArrayList<>();

        for (BluetoothDevice device : bonded) {
            any.add(device);
            String name = device.getName() == null ? "" : device.getName();
            String upper = name.toUpperCase();

            if (upper.contains("ZQ620")) {
                return device;
            }

            // Some Zebra mobile printers expose a serial-like BT name (e.g. XXZKJ222903269).
            if (upper.matches("XX[A-Z0-9]{8,}")) {
                return device;
            }

            if (
                    zebraLike == null &&
                    (
                            upper.contains("ZQ6") ||
                            upper.contains("ZEBRA") ||
                            upper.contains("ZD") ||
                            upper.contains("ZT") ||
                            upper.contains("GK") ||
                            upper.contains("QL") ||
                            upper.contains("RW")
                    )
            ) {
                zebraLike = device;
            }

            BluetoothClass klass = device.getBluetoothClass();
            if (
                    imagingLike == null &&
                    klass != null &&
                    klass.getMajorDeviceClass() == BluetoothClass.Device.Major.IMAGING
            ) {
                imagingLike = device;
            }

            if (namedFallback == null && !name.trim().isEmpty()) {
                namedFallback = device;
            }
        }

        if (zebraLike != null) {
            return zebraLike;
        }
        if (imagingLike != null) {
            return imagingLike;
        }
        if (any.size() == 1) {
            return any.get(0);
        }
        if (namedFallback != null) {
            return namedFallback;
        }
        return any.get(0);
    }

    private boolean isLikelyPrinterName(String upperName) {
        if (upperName == null) return false;
        return upperName.contains("ZQ620")
                || upperName.matches("XX[A-Z0-9]{8,}")
                || upperName.contains("ZQ6")
                || upperName.contains("ZEBRA")
                || upperName.contains("ZD")
                || upperName.contains("ZT")
                || upperName.contains("GK")
                || upperName.contains("QL")
                || upperName.contains("RW");
    }

    @SuppressLint("MissingPermission")
    private boolean isLikelyPrinter(BluetoothDevice device) {
        if (device == null) return false;
        String name = device.getName() == null ? "" : device.getName().toUpperCase();
        if (isLikelyPrinterName(name)) {
            return true;
        }

        BluetoothClass klass = device.getBluetoothClass();
        return klass != null && klass.getMajorDeviceClass() == BluetoothClass.Device.Major.IMAGING;
    }

    @SuppressLint("MissingPermission")
    private boolean waitForBond(BluetoothDevice device, long timeoutMs) {
        if (device == null) return false;
        long deadline = SystemClock.elapsedRealtime() + timeoutMs;
        while (SystemClock.elapsedRealtime() < deadline) {
            if (device.getBondState() == BluetoothDevice.BOND_BONDED) {
                return true;
            }
            SystemClock.sleep(250);
        }
        return device.getBondState() == BluetoothDevice.BOND_BONDED;
    }

    @SuppressLint("MissingPermission")
    private boolean ensureBonded(BluetoothDevice device) {
        if (device == null) {
            return false;
        }
        if (device.getBondState() == BluetoothDevice.BOND_BONDED) {
            return true;
        }
        try {
            device.createBond();
            return waitForBond(device, BOND_TIMEOUT_MS);
        } catch (SecurityException ignored) {
            return false;
        }
    }

    @SuppressLint("MissingPermission")
    private BluetoothDevice discoverNearbyPrinter(long timeoutMs) {
        if (bluetoothAdapter == null) {
            return null;
        }

        final Object lock = new Object();
        final BluetoothDevice[] found = new BluetoothDevice[1];

        BroadcastReceiver receiver = new BroadcastReceiver() {
            @Override
            public void onReceive(Context context, Intent intent) {
                String action = intent != null ? intent.getAction() : null;
                if (!BluetoothDevice.ACTION_FOUND.equals(action)) {
                    return;
                }
                try {
                    BluetoothDevice device = intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE);
                    if (device != null && isLikelyPrinter(device) && found[0] == null) {
                        found[0] = device;
                        synchronized (lock) {
                            lock.notifyAll();
                        }
                    }
                } catch (SecurityException ignored) {
                    // Ignore permission race
                }
            }
        };

        boolean registered = false;
        try {
            registerReceiver(receiver, new IntentFilter(BluetoothDevice.ACTION_FOUND));
            registered = true;

            if (bluetoothAdapter.isDiscovering()) {
                bluetoothAdapter.cancelDiscovery();
            }
            bluetoothAdapter.startDiscovery();

            long deadline = SystemClock.elapsedRealtime() + timeoutMs;
            synchronized (lock) {
                while (found[0] == null && SystemClock.elapsedRealtime() < deadline) {
                    long remaining = deadline - SystemClock.elapsedRealtime();
                    if (remaining <= 0) {
                        break;
                    }
                    try {
                        lock.wait(Math.min(remaining, 500));
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        break;
                    }
                }
            }
        } catch (SecurityException ignored) {
            return null;
        } finally {
            try {
                if (bluetoothAdapter.isDiscovering()) {
                    bluetoothAdapter.cancelDiscovery();
                }
            } catch (SecurityException ignored) {
                // Ignore cleanup failures
            }

            if (registered) {
                try {
                    unregisterReceiver(receiver);
                } catch (Exception ignored) {
                    // Ignore unregister failures
                }
            }
        }

        if (found[0] != null && ensureBonded(found[0])) {
            return found[0];
        }
        return null;
    }

    @SuppressLint("MissingPermission")
    private void addPrinterCandidate(List<PrinterCandidate> out, BluetoothDevice device) {
        if (device == null || !isLikelyPrinter(device)) {
            return;
        }

        String address;
        try {
            address = device.getAddress();
        } catch (SecurityException se) {
            return;
        }
        if (address == null || address.trim().isEmpty()) {
            return;
        }

        for (PrinterCandidate c : out) {
            if (address.equalsIgnoreCase(c.address)) {
                return;
            }
        }

        String name;
        try {
            name = device.getName();
        } catch (SecurityException se) {
            name = "";
        }

        boolean bonded = false;
        try {
            bonded = device.getBondState() == BluetoothDevice.BOND_BONDED;
        } catch (SecurityException ignored) {
            // Keep default false when state is inaccessible.
        }

        out.add(new PrinterCandidate(
                (name == null || name.trim().isEmpty()) ? "(unnamed)" : name,
                address,
                bonded
        ));
    }

    @SuppressLint("MissingPermission")
    private List<BluetoothDevice> discoverNearbyPrinters(long timeoutMs) {
        List<BluetoothDevice> discovered = new ArrayList<>();
        if (bluetoothAdapter == null) {
            return discovered;
        }

        final Object lock = new Object();

        BroadcastReceiver receiver = new BroadcastReceiver() {
            @Override
            public void onReceive(Context context, Intent intent) {
                String action = intent != null ? intent.getAction() : null;
                if (!BluetoothDevice.ACTION_FOUND.equals(action)) {
                    return;
                }
                try {
                    BluetoothDevice device = intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE);
                    if (device != null && isLikelyPrinter(device)) {
                        String address = device.getAddress();
                        if (address != null && !address.trim().isEmpty()) {
                            boolean exists = false;
                            for (BluetoothDevice d : discovered) {
                                String dAddress = d.getAddress();
                                if (dAddress != null && address.equalsIgnoreCase(dAddress)) {
                                    exists = true;
                                    break;
                                }
                            }
                            if (!exists) {
                                discovered.add(device);
                            }
                        }
                    }
                    synchronized (lock) {
                        lock.notifyAll();
                    }
                } catch (SecurityException ignored) {
                    // Ignore permission races.
                }
            }
        };

        boolean registered = false;
        try {
            registerReceiver(receiver, new IntentFilter(BluetoothDevice.ACTION_FOUND));
            registered = true;

            if (bluetoothAdapter.isDiscovering()) {
                bluetoothAdapter.cancelDiscovery();
            }
            bluetoothAdapter.startDiscovery();

            long deadline = SystemClock.elapsedRealtime() + timeoutMs;
            synchronized (lock) {
                while (SystemClock.elapsedRealtime() < deadline) {
                    long remaining = deadline - SystemClock.elapsedRealtime();
                    if (remaining <= 0) {
                        break;
                    }
                    try {
                        lock.wait(Math.min(remaining, 500));
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        break;
                    }
                }
            }
        } catch (SecurityException ignored) {
            return discovered;
        } finally {
            try {
                if (bluetoothAdapter.isDiscovering()) {
                    bluetoothAdapter.cancelDiscovery();
                }
            } catch (SecurityException ignored) {
                // Ignore cleanup failures.
            }

            if (registered) {
                try {
                    unregisterReceiver(receiver);
                } catch (Exception ignored) {
                    // Ignore unregister failures.
                }
            }
        }

        return discovered;
    }

    @SuppressLint("MissingPermission")
    private String listLikelyPrintersInternal() {
        List<PrinterCandidate> candidates = new ArrayList<>();

        if (bluetoothAdapter == null) {
            return toJsonPrinters(false, "Bluetooth not available on this device", candidates);
        }
        if (!bluetoothAdapter.isEnabled()) {
            return toJsonPrinters(false, "Enable Bluetooth first", candidates);
        }
        if (!ensureBluetoothPermission()) {
            return toJsonPrinters(false, "Bluetooth permission requested. Allow Nearby devices, then tap Find printers again.", candidates);
        }

        try {
            Set<BluetoothDevice> bonded = bluetoothAdapter.getBondedDevices();
            if (bonded != null) {
                for (BluetoothDevice device : bonded) {
                    addPrinterCandidate(candidates, device);
                }
            }
        } catch (SecurityException ignored) {
            return toJsonPrinters(false, "Bluetooth permission missing. Allow Nearby devices in Android settings.", candidates);
        }

        for (BluetoothDevice device : discoverNearbyPrinters(DISCOVERY_LIST_TIMEOUT_MS)) {
            addPrinterCandidate(candidates, device);
        }

        if (candidates.isEmpty() && connectedPrinter != null) {
            addPrinterCandidate(candidates, connectedPrinter);
        }

        return toJsonPrinters(true, candidates.isEmpty() ? "No likely printers found" : "ok", candidates);
    }

    @SuppressLint("MissingPermission")
    private String describeBondedDevices() {
        if (bluetoothAdapter == null) {
            return "Bluetooth unavailable";
        }
        Set<BluetoothDevice> bonded = bluetoothAdapter.getBondedDevices();
        if (bonded == null || bonded.isEmpty()) {
            return "none";
        }

        StringBuilder sb = new StringBuilder();
        int i = 0;
        for (BluetoothDevice device : bonded) {
            if (i > 0) {
                sb.append(", ");
            }
            String name = device.getName();
            String address = device.getAddress();
            if (name == null || name.trim().isEmpty()) {
                name = "(unnamed)";
            }
            sb.append(name);
            if (address != null && !address.trim().isEmpty()) {
                sb.append(" [").append(address).append("]");
            }
            i++;
            if (i >= 6) {
                sb.append(" ...");
                break;
            }
        }
        return sb.toString();
    }

    @SuppressLint("MissingPermission")
    private BluetoothSocket openSocket(BluetoothDevice device) throws IOException {
        IOException lastError = null;

        try {
            BluetoothSocket socket = device.createRfcommSocketToServiceRecord(SPP_UUID);
            socket.connect();
            return socket;
        } catch (IOException err) {
            lastError = err;
        }

        BluetoothSocket insecure = device.createInsecureRfcommSocketToServiceRecord(SPP_UUID);
        try {
            insecure.connect();
            return insecure;
        } catch (IOException err) {
            try {
                insecure.close();
            } catch (IOException ignored) {
                // Ignore close failures
            }
            throw (lastError != null) ? lastError : err;
        }
    }

    private void closeSocketLocked() {
        if (printerSocket != null) {
            try {
                printerSocket.close();
            } catch (IOException ignored) {
                // Ignore close failures
            }
        }
        printerSocket = null;
        connectedPrinter = null;
    }

    private PrinterResult connectZq620Internal() {
        if (bluetoothAdapter == null) {
            return new PrinterResult(false, "Bluetooth not available on this device", "");
        }
        if (!bluetoothAdapter.isEnabled()) {
            return new PrinterResult(false, "Enable Bluetooth first", "");
        }
        if (!ensureBluetoothPermission()) {
            return new PrinterResult(false, "Bluetooth permission requested. Allow Nearby devices, then tap connect again.", "");
        }

        BluetoothDevice target;
        try {
            target = findBondedZq620();
            if (target == null) {
                target = discoverNearbyPrinter(DISCOVERY_TIMEOUT_MS);
            }
        } catch (SecurityException se) {
            return new PrinterResult(false, "Bluetooth permission missing. Allow Nearby devices in Android settings.", "");
        }

        if (target == null) {
            return new PrinterResult(false, "No suitable bonded printer found. Bonded devices: " + describeBondedDevices(), "");
        }

        synchronized (printerLock) {
            closeSocketLocked();
            try {
                bluetoothAdapter.cancelDiscovery();
                BluetoothSocket socket = openSocket(target);
                printerSocket = socket;
                connectedPrinter = target;
                String printerName = target.getName() == null ? "ZQ620" : target.getName();
                return new PrinterResult(true, "Connected", printerName);
            } catch (SecurityException se) {
                closeSocketLocked();
                return new PrinterResult(false, "Bluetooth permission missing. Allow Nearby devices in Android settings.", "");
            } catch (IOException io) {
                closeSocketLocked();
                return new PrinterResult(false, "Could not connect to printer", "");
            }
        }
    }

    private PrinterResult connectPrinterByAddressInternal(String address) {
        if (bluetoothAdapter == null) {
            return new PrinterResult(false, "Bluetooth not available on this device", "");
        }
        if (!bluetoothAdapter.isEnabled()) {
            return new PrinterResult(false, "Enable Bluetooth first", "");
        }
        if (!ensureBluetoothPermission()) {
            return new PrinterResult(false, "Bluetooth permission requested. Allow Nearby devices, then tap connect again.", "");
        }

        String targetAddress = address == null ? "" : address.trim();
        if (targetAddress.isEmpty()) {
            return new PrinterResult(false, "Select a printer first", "");
        }

        BluetoothDevice target = null;
        try {
            Set<BluetoothDevice> bonded = bluetoothAdapter.getBondedDevices();
            if (bonded != null) {
                for (BluetoothDevice device : bonded) {
                    String deviceAddress = device.getAddress();
                    if (deviceAddress != null && targetAddress.equalsIgnoreCase(deviceAddress)) {
                        target = device;
                        break;
                    }
                }
            }
        } catch (SecurityException ignored) {
            return new PrinterResult(false, "Bluetooth permission missing. Allow Nearby devices in Android settings.", "");
        }

        if (target == null) {
            try {
                target = bluetoothAdapter.getRemoteDevice(targetAddress);
            } catch (IllegalArgumentException iae) {
                return new PrinterResult(false, "Invalid printer address", "");
            }
        }

        if (!ensureBonded(target)) {
            return new PrinterResult(false, "Could not pair with selected printer", "");
        }

        synchronized (printerLock) {
            closeSocketLocked();
            try {
                bluetoothAdapter.cancelDiscovery();
                BluetoothSocket socket = openSocket(target);
                printerSocket = socket;
                connectedPrinter = target;
                String printerName = target.getName() == null ? "ZQ620" : target.getName();
                return new PrinterResult(true, "Connected", printerName);
            } catch (SecurityException se) {
                closeSocketLocked();
                return new PrinterResult(false, "Bluetooth permission missing. Allow Nearby devices in Android settings.", "");
            } catch (IOException io) {
                closeSocketLocked();
                return new PrinterResult(false, "Could not connect to selected printer", "");
            }
        }
    }

    @SuppressLint("MissingPermission")
    private String getPrinterHealthInternal() {
        boolean bluetoothAvailable = bluetoothAdapter != null;
        boolean bluetoothEnabled = bluetoothAvailable && bluetoothAdapter.isEnabled();
        boolean connectPermission = hasBluetoothConnectPermission();
        boolean scanPermission = hasBluetoothScanPermission();
        boolean locationPermission = hasLegacyLocationPermission();

        boolean connected = false;
        String printerName = "";
        String printerAddress = "";

        synchronized (printerLock) {
            if (hasLivePrinterConnectionLocked()) {
                connected = true;
                if (connectedPrinter != null) {
                    try {
                        if (connectedPrinter.getName() != null) {
                            printerName = connectedPrinter.getName();
                        }
                    } catch (SecurityException ignored) {
                        printerName = "";
                    }
                    try {
                        if (connectedPrinter.getAddress() != null) {
                            printerAddress = connectedPrinter.getAddress();
                        }
                    } catch (SecurityException ignored) {
                        printerAddress = "";
                    }
                }
            }
        }

        int bondedCount = 0;
        if (bluetoothAvailable) {
            try {
                Set<BluetoothDevice> bonded = bluetoothAdapter.getBondedDevices();
                bondedCount = bonded == null ? 0 : bonded.size();
            } catch (SecurityException ignored) {
                bondedCount = 0;
            }
        }

        String message;
        if (!bluetoothAvailable) {
            message = "Bluetooth unavailable";
        } else if (!bluetoothEnabled) {
            message = "Bluetooth disabled";
        } else if (!connectPermission || !scanPermission || !locationPermission) {
            message = "Permission missing";
        } else if (connected) {
            message = "Connected";
        } else {
            message = "Not connected";
        }

        return toJsonPrinterHealth(
                message,
                bluetoothAvailable,
                bluetoothEnabled,
                connectPermission,
                scanPermission,
                locationPermission,
                connected,
                printerName,
                printerAddress,
                bondedCount
        );
    }

    private PrinterResult getPrinterStatusInternal() {
        synchronized (printerLock) {
            if (hasLivePrinterConnectionLocked()) {
                String printerName = (connectedPrinter != null && connectedPrinter.getName() != null)
                        ? connectedPrinter.getName()
                        : "ZQ620";
                return new PrinterResult(true, "Connected", printerName);
            }
        }
        return new PrinterResult(false, "not connected", "");
    }

    private PrinterResult printZplInternal(String zpl) {
        if (zpl == null || zpl.trim().isEmpty()) {
            return new PrinterResult(false, "Empty print payload", "");
        }

        if (!hasBluetoothConnectPermission() || !hasBluetoothScanPermission()) {
            if (!ensureBluetoothPermission()) {
                return new PrinterResult(false, "Bluetooth permission requested. Allow Nearby devices, then try print again.", "");
            }
        }

        synchronized (printerLock) {
            if (!hasLivePrinterConnectionLocked()) {
                PrinterResult connectResult = connectZq620Internal();
                if (!connectResult.ok) {
                    return connectResult;
                }
            }

            try {
                OutputStream output = printerSocket.getOutputStream();
                output.write(zpl.getBytes(StandardCharsets.UTF_8));
                output.flush();
                String printerName = (connectedPrinter != null && connectedPrinter.getName() != null)
                        ? connectedPrinter.getName()
                        : "ZQ620";
                return new PrinterResult(true, "Printed", printerName);
            } catch (IOException io) {
                closeSocketLocked();
                return new PrinterResult(false, "Print failed. Reconnect printer.", "");
            } catch (SecurityException se) {
                return new PrinterResult(false, "Bluetooth permission missing. Allow Nearby devices in Android settings.", "");
            }
        }
    }

    private final class AndroidPrinterBridge {
        @JavascriptInterface
        public String connectZq620() {
            return toJson(connectZq620Internal());
        }

        @JavascriptInterface
        public String listLikelyPrinters() {
            return listLikelyPrintersInternal();
        }

        @JavascriptInterface
        public String connectPrinterByAddress(String address) {
            return toJson(connectPrinterByAddressInternal(address));
        }

        @JavascriptInterface
        public String getPrinterStatus() {
            return toJson(getPrinterStatusInternal());
        }

        @JavascriptInterface
        public String getPrinterHealth() {
            return getPrinterHealthInternal();
        }

        @JavascriptInterface
        public String printZpl(String zpl) {
            return toJson(printZplInternal(zpl));
        }
    }
}
