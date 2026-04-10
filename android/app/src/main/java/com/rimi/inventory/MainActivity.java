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
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
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
    private static final UUID SPP_UUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB");
    private static final String LOCAL_WEB_URL = "file:///android_asset/web/index.html";
    private static final long DISCOVERY_TIMEOUT_MS = 9000;
    private static final long BOND_TIMEOUT_MS = 9000;

    private BluetoothAdapter bluetoothAdapter;
    private BluetoothSocket printerSocket;
    private BluetoothDevice connectedPrinter;
    private final Object printerLock = new Object();
    private WebView appWebView;
    private boolean localWebFallbackLoaded = false;

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

        appWebView.setWebViewClient(new InventoryWebViewClient());
        appWebView.addJavascriptInterface(new AndroidPrinterBridge(), "AndroidPrinter");
        appWebView.clearCache(true);
        appWebView.clearHistory();
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

    @Override
    protected void onDestroy() {
        super.onDestroy();
        synchronized (printerLock) {
            closeSocketLocked();
        }
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

    private PrinterResult getPrinterStatusInternal() {
        synchronized (printerLock) {
            if (printerSocket != null && printerSocket.isConnected()) {
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
            if (printerSocket == null || !printerSocket.isConnected()) {
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
        public String getPrinterStatus() {
            return toJson(getPrinterStatusInternal());
        }

        @JavascriptInterface
        public String printZpl(String zpl) {
            return toJson(printZplInternal(zpl));
        }
    }
}
