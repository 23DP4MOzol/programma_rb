const fs = require('fs');
let mainActivityPath = 'android/app/src/main/java/com/rimi/inventory/MainActivity.java';
let java = fs.readFileSync(mainActivityPath, 'utf-8');
// I am matching the whole line that starts with `    } else if (currUrl.indexOf('lenovo') > -1)`...
// Because it currently has unescaped quotes!
// Let me just replace the entire JS block with a clean new one.
let newJs = `try { (function() {
  var getSn = function(u) { try { var p = u.split('?')[1]; if(!p) return null; var vars = p.split('&'); for(var i=0;i<vars.length;i++){var pair = vars[i].split('='); if(pair[0].toLowerCase().indexOf('serial') > -1) return decodeURIComponent(pair[1]); } return null; } catch(e){return null;} };
  var sn = getSn(window.location.href) || getSn('" + safeUrl + "');
  if (!sn) return;
  var deepQuery = function(s, r) { root = r || document; var n = root.querySelector(s); if (n) return n; var els = root.querySelectorAll('*'); for (var i=0; i<els.length; i++) { if (els[i].shadowRoot) { var deep = deepQuery(s, els[i].shadowRoot); if (deep) return deep; } } return null; };
  var attempt = 0;
  var poll = setInterval(function() {
    attempt++;
    if (attempt > 60) { clearInterval(poll); return; }
    var input = null; var btn = null;
    var currUrl = window.location.href + '" + safeUrl + "';
    if (currUrl.indexOf('samsung') > -1) {
      input = deepQuery('input[name="serialNumber"], input#serialNumber, input#imei, input[placeholder*="IMEI"], input[placeholder*="Serial"], input[placeholder*="serial"], input[type="text"]');
      btn = deepQuery('button[type="submit"], button.check-warranty-btn, button#submit, button.warranty-check-submit, button.sn-submit');
      if (!btn) { var allBtns = document.querySelectorAll('button'); for(var i=0;i<allBtns.length;i++){ var t=allBtns[i].innerText?allBtns[i].innerText.toLowerCase():''; if(t.indexOf('check')>-1||t.indexOf('submit')>-1||t.indexOf('continue')>-1){ btn=allBtns[i]; break; } } }
    } else if (currUrl.indexOf('zebra') > -1) {
      input = deepQuery('input.slds-input[placeholder="Serial Number"], input.slds-input, input[name="serial"]');
      var btns = document.querySelectorAll('button.slds-button_brand, button.slds-button');
      if (!btns || btns.length === 0) { btn = deepQuery('button.slds-button_brand, button.slds-button'); }
      if (!btn && btns) { for (var i = 0; i < btns.length; i++) { if (btns[i].innerText && btns[i].innerText.toLowerCase().indexOf('search') > -1) { btn = btns[i]; break; } } }
      if (!btn && btns && btns.length > 0) btn = btns[0];
    } else if (currUrl.indexOf('lenovo') > -1) {
      input = deepQuery('input.button-placeholder__input, input[name="search-text"], input#input-search, input.search-input, input.sn-search, input[placeholder*="Serial"], input[type="text"]');
      btn = deepQuery('button.basic-search__suffix-btn, button[aria-label*="Search"], button.search-button, button#search-btn, button[type="submit"]');
      if (!btn) { var allBtns = document.querySelectorAll('button'); for(var i=0;i<allBtns.length;i++){ var t=allBtns[i].innerText?allBtns[i].innerText.toLowerCase():''; if(t.indexOf('search')>-1||t.indexOf('submit')>-1||t.indexOf('check')>-1){ btn=allBtns[i]; break; } } }
    } else if (currUrl.indexOf('apple.com') > -1) {
      input = deepQuery('input[id*="serial"], input[name*="serial"], input[placeholder*="Serial"], input[type="text"]');
      btn = deepQuery('button[id*="submit"], button[type="submit"], button');
    } else if (currUrl.indexOf('asus.com') > -1) {
      input = deepQuery('input[name="serialNumber"], input[id*="serial"], input[placeholder*="Serial"], input[type="text"]');
      btn = deepQuery('button[type="submit"], button[class*="search"], button[class*="submit"], button');
    } else if (currUrl.indexOf('dell.com') > -1) {
      input = deepQuery('input[id*="ServiceTag"], input[id*="serial"], input[name*="serial"], input[placeholder*="Service Tag"], input[placeholder*="Serial"], input[type="text"]');
      btn = deepQuery('button[id*="submit"], button[id*="search"], button[class*="submit"], button[class*="search"], button');
    } else if (currUrl.indexOf('hp.com') > -1) {
      input = document.querySelector('input#inputtextpfinder, input[formcontrolname="serialNumber"], input.hp-text-input');
      btn = document.querySelector('button#FindMyProduct, button.submitBtn');
    }
    if (input) {
      var isSet = false;
      if (input.value !== sn) {
        try { input.focus(); } catch(e){}
        try {
          var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value');
          if (nativeSetter && nativeSetter.set) { nativeSetter.set.call(input, sn); } else { input.value = sn; }
        } catch(e) { input.value = sn; }
        try { input.dispatchEvent(new Event('input', {bubbles: true})); } catch(e){}
        try { input.dispatchEvent(new Event('change', {bubbles: true})); } catch(e){}
      }
      try { isSet = (input.value === sn); } catch(e){}
      if (isSet && btn) {
        try { btn.disabled = false; btn.removeAttribute('disabled'); } catch(e){}
        setTimeout(function(){ try { btn.click(); } catch(e){} }, 800);
        clearInterval(poll);
      }
    }
  }, 500);
})(); } catch(e) {}`;
// Escape standard quotes (to `\"`)
newJs = newJs.replace(/"/g, '\\"');
// Restore the `\" + safeUrl + \"` trick:
newJs = newJs.replace(/\\"\s*\+\s*safeUrl\s*\+\s*\\"/g, '" + safeUrl + "');
// Let's format it as a valid Java string concatenation
let javaStrSegments = newJs.split('\n');
let javaStr = 'String js = ';
for(let i=0; i<javaStrSegments.length; i++) {
    javaStr += `"${javaStrSegments[i]}\\n"`;
    if(i < javaStrSegments.length - 1) {
        javaStr += ' +\n                                  ';
    } else {
        javaStr += ';';
    }
}
// Find existing `String js = ...` and replace
let fixedCode = java.replace(/String js = "try \{ \(function.*?view\.evaluateJavascript\(js, null\);/s, javaStr + '\n                          view.evaluateJavascript(js, null);');
fs.writeFileSync(mainActivityPath, fixedCode);
console.log("Rewrote js perfectly.");
