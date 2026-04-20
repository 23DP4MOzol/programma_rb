import os
from playwright.sync_api import sync_playwright

def test():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                channel='msedge',
                headless=True
            )
            print("Edge Channel Success!")
            page = browser.new_page()
            page.goto("https://example.com")
            print("Page created:", page.title())
            browser.close()
    except Exception as e:
        print('Error:', type(e).__name__, str(e))

if __name__ == '__main__':
    test()