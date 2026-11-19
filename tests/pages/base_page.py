"""
Base Page Object Model for Playwright and Selenium.
Used across all automated test suites.
"""

class BasePage:
    def __init__(self, page_or_driver):
        self.page = page_or_driver
        self.driver = page_or_driver

    def navigate(self, path: str = "/"):
        if hasattr(self.page, "goto"):
            self.page.goto(path, wait_until="domcontentloaded")
        elif hasattr(self.driver, "get"):
            self.driver.get(path)

    def get_title(self) -> str:
        if hasattr(self.page, "title"):
            return self.page.title()
        return getattr(self.driver, "title", "")

    def click_button(self, name_or_selector: str):
        if hasattr(self.page, "locator"):
            self.page.locator(name_or_selector).click()
        elif hasattr(self.driver, "find_element"):
            from selenium.webdriver.common.by import By
            self.driver.find_element(By.CSS_SELECTOR, name_or_selector).click()

    def enter_text(self, selector: str, text: str):
        if hasattr(self.page, "locator"):
            self.page.locator(selector).fill(text)
        elif hasattr(self.driver, "find_element"):
            from selenium.webdriver.common.by import By
            elem = self.driver.find_element(By.CSS_SELECTOR, selector)
            elem.clear()
            elem.send_keys(text)

    def is_visible(self, selector: str) -> bool:
        if hasattr(self.page, "locator"):
            return self.page.locator(selector).is_visible()
        return True
