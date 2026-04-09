package com.rimi.inventory;

import android.annotation.SuppressLint;
import android.Manifest;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothSocket;
import android.content.pm.ActivityInfo;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;

import java.io.IOException;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.Set;
import java.util.UUID;

public class MainActivity extends AppCompatActivity {
    private static final int REQ_BT_PERMISSION = 7001;
    private static final UUID SPP_UUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB");

    private BluetoothAdapter bluetoothAdapter;
    private BluetoothSocket printerSocket;
    private BluetoothDevice connectedPrinter;
    private final Object printerLock = new Object();

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_PORTRAIT);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        setContentView(R.layout.activity_main);

        bluetoothAdapter = BluetoothAdapter.getDefaultAdapter();

        WebView webView = findViewById(R.id.webview);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);
        settings.setCacheMode(WebSettings.LOAD_NO_CACHE);

        webView.setWebViewClient(new WebViewClient());
        webView.addJavascriptInterface(new AndroidPrinterBridge(), "AndroidPrinter");
        webView.clearCache(true);
        webView.clearHistory();
        String cacheBust = String.valueOf(System.currentTimeMillis());
        webView.loadUrl(getString(R.string.web_app_url) + "?v=" + cacheBust);
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

    private boolean hasBluetoothConnectPermission() {
        if (android.os.Build.VERSION.SDK_INT < android.os.Build.VERSION_CODES.S) {
            return true;
        }
        return ActivityCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_CONNECT) == PackageManager.PERMISSION_GRANTED;
    }

    private boolean ensureBluetoothPermission() {
        if (hasBluetoothConnectPermission()) {
            return true;
        }
        ActivityCompat.requestPermissions(
                this,
                new String[]{Manifest.permission.BLUETOOTH_CONNECT},
                REQ_BT_PERMISSION
        );
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

        BluetoothDevice fallback = null;
        for (BluetoothDevice device : bonded) {
            String name = device.getName() == null ? "" : device.getName();
            String upper = name.toUpperCase();
            if (upper.contains("ZQ620")) {
                return device;
            }
            if (fallback == null && (upper.contains("ZQ6") || upper.contains("ZEBRA"))) {
                fallback = device;
            }
        }
        return fallback;
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
            return new PrinterResult(false, "Bluetooth permission requested. Tap connect again.", "");
        }

        BluetoothDevice target;
        try {
            target = findBondedZq620();
        } catch (SecurityException se) {
            return new PrinterResult(false, "Bluetooth permission missing", "");
        }

        if (target == null) {
            return new PrinterResult(false, "No bonded ZQ620 printer found", "");
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
                return new PrinterResult(false, "Bluetooth permission missing", "");
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

        if (!hasBluetoothConnectPermission()) {
            if (!ensureBluetoothPermission()) {
                return new PrinterResult(false, "Bluetooth permission requested. Try print again.", "");
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
                return new PrinterResult(false, "Bluetooth permission missing", "");
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
