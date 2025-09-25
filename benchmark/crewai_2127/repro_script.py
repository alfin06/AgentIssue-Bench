import os
from unittest.mock import patch

# crewAI and its tools have Pydantic as a dependency.
# We must let the tool initialize correctly before triggering the bug.
from crewai_tools import SeleniumScrapingTool

# --- Corrected Mocking Strategy ---
# The original bug is `TypeError: 'WebDriver' object is not callable`.
# This happens because `self.driver` is an INSTANCE of the driver, and the
# code incorrectly tries to call it as a function: `self.driver()`.
#
# Our goal is to replicate this state. We will create a dummy class that can be
# instantiated, and then attempting to call that instance will raise the correct TypeError.
# This avoids using MagicMock during initialization, which conflicts with Pydantic.

class FakeWebDriver:
    """A dummy WebDriver that can be instantiated but not called."""
    def __init__(self, options=None):
        # This __init__ allows `Chrome(options=...)` to run without error.
        pass

    def get(self, url):
        # This method needs to exist because the tool calls it after the buggy line.
        # We won't reach it, but it's good practice for a robust mock.
        pass

print("--- Attempting to reproduce TypeError: 'WebDriver' object is not callable ---")

# The path to the class that the tool imports and uses.
PATCH_TARGET = 'selenium.webdriver.Chrome'

try:
    # We patch `selenium.webdriver.Chrome` with our `FakeWebDriver`.
    with patch(PATCH_TARGET, FakeWebDriver):
        print("Initializing SeleniumScrapingTool with a mocked browser...")
        
        # Now, `SeleniumScrapingTool()` will instantiate our `FakeWebDriver`.
        # `self.driver` will become an *instance* of FakeWebDriver.
        # Pydantic has no issue with this, so initialization succeeds.
        scraping_tool = SeleniumScrapingTool(
            website_url='https://www.trendyol.com/16-gb-laptop-x-c103108-a232-v4012?utm_source=chatgpt.com'
        )

    # We call `_run()` to get to the tool's core logic.
    print("Calling scraping_tool._run(). This is expected to fail with a TypeError...")
    
    # Inside `_run()`, the code calls `_create_driver()`, which contains the buggy line:
    # `driver = self.driver(options=options)`.
    # This will attempt to call the `FakeWebDriver` instance, triggering the TypeError.
    scraping_tool._run()

    # If the script gets here, the bug was not reproduced.
    print("\n--- SCRIPT FINISHED UNEXPECTEDLY ---")
    print("FAILURE: The bug was NOT reproduced. No TypeError was raised.")
    exit(0)

except TypeError as e:
    print(f"\nSUCCESS: The script failed with a TypeError as expected.")
    print(f"Error Message: {e}")

    expected_error_substring = "is not callable"
    # The error will be something like "TypeError: 'FakeWebDriver' object is not callable"
    if expected_error_substring in str(e):
        print(f"Verification successful: The error message contains '{expected_error_substring}', as expected.")
        # Exit with 1 to signal that the bug was successfully found.
        exit(1)
    else:
        print(f"Verification failed: The TypeError did not contain the expected message '{expected_error_substring}'.")
        exit(0)
except Exception as e:
    # Catch any other unexpected errors.
    print(f"\n--- SCRIPT FAILED WITH AN UNEXPECTED ERROR ---")
    print(f"FAILURE: An unexpected error occurred: {type(e).__name__}: {e}")
    exit(0)