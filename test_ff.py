from playwright.sync_api import sync_playwright

def test_firefox():
    try:
        with sync_playwright() as p:
            print("1. Path to bundled Firefox:", p.firefox.executable_path)
            print("2. Trying to launch Playwright bundled Firefox...")
            browser = p.firefox.launch(headless=True)
            print("3. Firefox Launch Success!")
            page = browser.new_page()
            page.goto("https://example.com")
            print("4. Page loaded:", page.title())
            browser.close()
    except Exception as e:
        print("\n[!] FIREFOX LAUNCH ERROR:", type(e).__name__)
        print(str(e))

if __name__ == '__main__':
    test_firefox()