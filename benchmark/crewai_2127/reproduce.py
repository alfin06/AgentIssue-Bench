import os
from unittest.mock import patch

from crewai_tools import SeleniumScrapingTool

class FakeWebDriver:
    """A dummy WebDriver that can be instantiated but not called."""
    def __init__(self, options=None):
        pass

    def get(self, url):
        pass

print("--- Attempting to reproduce TypeError: 'WebDriver' object is not callable ---")

PATCH_TARGET = 'selenium.webdriver.Chrome'

try:
    with patch(PATCH_TARGET, FakeWebDriver):
        print("Initializing SeleniumScrapingTool with a mocked browser...")
        
        # Now, `SeleniumScrapingTool()` will instantiate `FakeWebDriver`.
        # `self.driver` will become an *instance* of FakeWebDriver.
        # Pydantic has no issue with this, so initialization succeeds.
        scraping_tool = SeleniumScrapingTool(
            website_url='https://www.trendyol.com/16-gb-laptop-x-c103108-a232-v4012?utm_source=chatgpt.com'
        )

    print("Calling scraping_tool._run(). This is expected to fail with a TypeError...")
    
    scraping_tool._run()

    print("\n--- SCRIPT FINISHED UNEXPECTEDLY ---")
    print("FAILURE: The bug was NOT reproduced. No TypeError was raised.")
    exit(0)

except TypeError as e:
    print(f"\nSUCCESS: The script failed with a TypeError as expected.")
    print(f"Error Message: {e}")

    expected_error_substring = "is not callable"
    if expected_error_substring in str(e):
        print(f"Verification successful: The error message contains '{expected_error_substring}', as expected.")
        exit(1)
    else:
        print(f"Verification failed: The TypeError did not contain the expected message '{expected_error_substring}'.")
        exit(0)
except Exception as e:
    print(f"\n--- SCRIPT FAILED WITH AN UNEXPECTED ERROR ---")
    print(f"FAILURE: An unexpected error occurred: {type(e).__name__}: {e}")
    exit(0)