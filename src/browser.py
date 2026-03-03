"""
CCNA Netacad Auto-Solver — Browser Controller
Controls Chrome browser using Playwright for test automation.
"""

import time
from playwright.sync_api import sync_playwright


class BrowserController:
    """Controls the browser for Netacad test automation."""
    
    def __init__(self, headless=False, slow_mo=500):
        """
        Initialize browser controller.
        
        Args:
            headless: Run browser without GUI (not recommended)
            slow_mo: Delay between actions in ms (helps avoid detection)
        """
        self.headless = headless
        self.slow_mo = slow_mo
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
    
    def start(self):
        """Launch the browser."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo,
            args=[
                '--start-maximized',
                '--disable-blink-features=AutomationControlled',
            ]
        )
        self.context = self.browser.new_context(
            viewport={'width': 1280, 'height': 900},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        self.page = self.context.new_page()
        
        # Remove automation detection
        self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)
        
        return self.page
    
    def navigate(self, url):
        """Navigate to a URL and wait for load."""
        self.page.goto(url, wait_until='domcontentloaded', timeout=60000)
        time.sleep(2)
    
    def wait_for_user_login(self):
        """Wait for the user to log in manually."""
        print("\n" + "="*60)
        print("🔐 PLEASE LOG IN TO NETACAD IN THE BROWSER")
        print("="*60)
        print("\n  1. Log in with your Netacad credentials")
        print("  2. Navigate to your test/exam page")
        print("  3. Start the exam so the first question is visible")
        print()
        input("  Press ENTER when the first question is visible... ")
        print()
        time.sleep(2)
    
    def get_page_text(self):
        """Get all visible text on the page."""
        try:
            return self.page.evaluate("() => document.body.innerText")
        except Exception:
            return ""
    
    def scroll_down(self, pixels=300):
        """Scroll down the page."""
        try:
            self.page.evaluate(f"window.scrollBy(0, {pixels})")
            time.sleep(0.5)
        except Exception:
            pass
    
    def scroll_to_top(self):
        """Scroll to top of page."""
        try:
            self.page.evaluate("window.scrollTo(0, 0)")
            time.sleep(0.5)
        except Exception:
            pass
    
    def click_at(self, x, y):
        """Click at specific coordinates."""
        try:
            self.page.mouse.click(x, y)
            time.sleep(0.3)
        except Exception:
            pass
    
    def find_and_click_text(self, text):
        """Find an element containing the text and click it."""
        try:
            # Try multiple strategies
            locator = self.page.get_by_text(text, exact=False).first
            if locator:
                locator.click()
                return True
        except Exception:
            pass
        
        try:
            # JavaScript-based click
            clicked = self.page.evaluate(f"""(searchText) => {{
                const elements = document.querySelectorAll('*');
                for (const el of elements) {{
                    if (el.children.length === 0 && el.innerText && 
                        el.innerText.trim().includes(searchText)) {{
                        el.click();
                        return true;
                    }}
                }}
                return false;
            }}""", text[:50])
            return clicked
        except Exception:
            return False
    
    def find_and_click_radio(self, answer_text):
        """Find a radio button/checkbox whose label matches the answer text and click it."""
        try:
            result = self.page.evaluate("""(answerText) => {
                const searchText = answerText.toLowerCase().trim();
                
                // Search in radio buttons and checkboxes
                const inputs = document.querySelectorAll('input[type="radio"], input[type="checkbox"]');
                
                for (const input of inputs) {
                    const label = input.closest('label') || 
                                  document.querySelector('label[for="' + input.id + '"]') ||
                                  input.parentElement;
                    
                    if (label) {
                        const labelText = label.innerText.toLowerCase().trim();
                        // Check for match
                        if (labelText.includes(searchText.substring(0, 40)) || 
                            searchText.includes(labelText.substring(0, 40))) {
                            input.click();
                            return { success: true, text: label.innerText.trim() };
                        }
                    }
                }
                
                return { success: false, text: '' };
            }""", answer_text)
            return result.get('success', False)
        except Exception:
            return False
    
    def click_submit_button(self):
        """Find and click the Submit/Next button."""
        try:
            # Try various approaches
            result = self.page.evaluate("""() => {
                // Look for buttons with submit-like text
                const allButtons = document.querySelectorAll('button, input[type="submit"], input[type="button"], a.btn, .btn');
                
                for (const btn of allButtons) {
                    const text = (btn.innerText || btn.value || '').toLowerCase();
                    if (text.includes('submit') || text.includes('next') || 
                        text.includes('check') || text.includes('enviar') ||
                        text.includes('siguiente')) {
                        btn.click();
                        return true;
                    }
                }
                
                return false;
            }""")
            
            if result:
                time.sleep(2)
                return True
            
            return False
        except Exception:
            return False
    
    def is_test_complete(self):
        """Check if the test has been completed (results page visible)."""
        try:
            text = self.get_page_text().lower()
            completion_indicators = [
                'your score', 'quiz results', 'exam results', 
                'test complete', 'assessment complete',
                'you scored', 'final score', 'grade:',
                'results for', 'attempt'
            ]
            return any(indicator in text for indicator in completion_indicators)
        except Exception:
            return False
    
    def get_current_question_number(self):
        """Try to determine the current question number."""
        try:
            result = self.page.evaluate("""() => {
                const text = document.body.innerText;
                const match = text.match(/(\\d+)\\s*(?:of|de|/)\\s*(\\d+)/i);
                if (match) {
                    return { current: parseInt(match[1]), total: parseInt(match[2]) };
                }
                return { current: -1, total: -1 };
            }""")
            return result
        except Exception:
            return {'current': -1, 'total': -1}
    
    def take_screenshot(self, path):
        """Save a screenshot of the current page."""
        try:
            self.page.screenshot(path=path)
        except Exception:
            pass
    
    def close(self):
        """Clean up browser resources."""
        try:
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception:
            pass
