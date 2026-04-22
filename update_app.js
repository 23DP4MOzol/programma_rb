const fs = require('fs');
const path = 'android/app/src/main/java/com/rimi/inventory/MainActivity.java';
let text = fs.readFileSync(path, 'utf8');

// Back handler
let startStr = `        getOnBackPressedDispatcher().addCallback(this, new androidx.activity.OnBackPressedCallback(true) {`;
let endStr = `        loadRemoteWebApp();`;
let iStart = text.indexOf(startStr);
let iEnd = text.indexOf(endStr, iStart);

if (iStart !== -1 && iEnd !== -1) {
  let rep = `        getOnBackPressedDispatcher().addCallback(this, new androidx.activity.OnBackPressedCallback(true) {
            @Override
            public void handleOnBackPressed() {
                if (appWebView != null) {
                    String currentUrl = appWebView.getUrl();
                    boolean isLocal = currentUrl != null && (currentUrl.contains("23dp4mozol.github.io") || currentUrl.contains("file:///android_asset/web/"));
                    if (!isLocal) {
                        appWebView.stopLoading();
                        appWebView.evaluateJavascript("window.onbeforeunload = null; window.onunload = null;", null);
                        appWebView.clearHistory();
                        appWebView.loadUrl(LOCAL_WEB_URL);
                        return;
                    } else if (appWebView.canGoBack()) {
                        appWebView.goBack();
                        return;
                    }
                }
                setEnabled(false);
                getOnBackPressedDispatcher().onBackPressed();
            }
        });\n\n`;
  text = text.substring(0, iStart) + rep + text.substring(iEnd);
  console.log('Fixed back handler.');
}

// Samsung
let samOld = `"    if (currUrl.indexOf('samsung') > -1) {" +
                                "      input = document.querySelector('input[name=\\"serialNumber\\"], input#serialNumber, input[type=\\"text\\"]');" +
                                "      btn = document.querySelector('button[type=\\"submit\\"], .check-warranty-btn, #submit');" +`;

let samNew = `"    if (currUrl.indexOf('samsung') > -1) {" +
                                "      input = deepQuery('input[name=\\"serialNumber\\"], input#serialNumber, input#imei, input[placeholder*=\\"IMEI\\"], input[placeholder*=\\"Serial\\"], input[placeholder*=\\"serial\\"], input[type=\\"text\\"]');" +
                                "      btn = deepQuery('button[type=\\"submit\\"], button.check-warranty-btn, button#submit, button.warranty-check-submit, button.sn-submit');" +
                                "      if (!btn) { var allBtns = document.querySelectorAll('button'); for(var i=0;i<allBtns.length;i++){ var t=allBtns[i].innerText?allBtns[i].innerText.toLowerCase():''; if(t.indexOf('check')>-1||t.indexOf('submit')>-1||t.indexOf('continue')>-1){ btn=allBtns[i]; break; } } }" +`;
if (text.includes(samOld)) {
    text = text.replace(samOld, samNew);
    console.log('Fixed Samsung JS.');
}

// Lenovo
let lenOld = `"    } else if (currUrl.indexOf('lenovo') > -1) {" +
                                "      input = document.querySelector('input[name=\\"search-text\\"], .search-input, input[type=\\"text\\"]');" +
                                "      btn = document.querySelector('button[aria-label*=\\"Search\\"], .search-button');" +`;

let lenNew = `"    } else if (currUrl.indexOf('lenovo') > -1) {" +
                                "      input = deepQuery('input[name=\\"search-text\\"], input#input-search, input.search-input, input.sn-search, input[placeholder*=\\"Serial\\"], input[placeholder*=\\"serial\\"], input[placeholder*=\\"SN\\"], input[type=\\"text\\"]');" +
                                "      btn = deepQuery('button[aria-label*=\\"Search\\"], button.search-button, button#search-btn, button[type=\\"submit\\"]');" +
                                "      if (!btn) { var allBtns = document.querySelectorAll('button'); for(var i=0;i<allBtns.length;i++){ var t=allBtns[i].innerText?allBtns[i].innerText.toLowerCase():''; if(t.indexOf('search')>-1||t.indexOf('submit')>-1||t.indexOf('check')>-1){ btn=allBtns[i]; break; } } }" +`;

if (text.includes(lenOld)) {
    text = text.replace(lenOld, lenNew);
    console.log('Fixed Lenovo JS.');
}

fs.writeFileSync(path, text, 'utf8');
console.log('Done writing files.');
