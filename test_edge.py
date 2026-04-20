import os
from playwright.sync_api import sync_playwright

def test():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                channel='msedge',
                headless=True
            )
            print('Edge Success!')
            browser.close()
    except Exception as e:
        print('Error:', type(e).__name__, str(e))

if __name__ == '__main__':
    test()