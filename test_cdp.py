import os
import subprocess
import time
from playwright.sync_api import sync_playwright

def test():
    edge_cmd = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "--remote-debugging-port=9222",
        "--user-data-dir=" + os.path.join(os.environ['LOCALAPPDATA'], 'pw_edge_test'),
        "https://example.com"
    ]
    print("Launching Edge...", edge_cmd)
    proc = subprocess.Popen(edge_cmd)
    time.sleep(3)
    
    print("Connecting via CDP...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            print("Connected!", browser.contexts[0].pages[0].title())
            browser.close()
    except Exception as e:
        print("Error:", e)
    
    proc.terminate()

if __name__ == '__main__':
    test()