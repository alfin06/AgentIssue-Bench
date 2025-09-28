import sys
from unittest.mock import patch

# This FakeWebDriver class allows us to replicate this state reliably.
# `SeleniumScrapingTool` will instantiate it, and any attempt to *call* that
# instance will correctly trigger a TypeError.

class FakeWebDriver:
    """A dummy WebDriver that can be instantiated but not called."""
    def __init__(self, options=None):
        pass

    def get(self, url):
        pass

    def quit(self):
        pass

    def close(self):
        pass

def test_selenium_type_error(version="buggy"):
    """
    Tests for the WebDriver TypeError.
    - The 'buggy' version is expected to raise the TypeError.
    - The 'fixed' version is expected to run without raising the TypeError.
    """
    from crewai_tools import SeleniumScrapingTool

    PATCH_TARGET = 'selenium.webdriver.Chrome'
    EXPECTED_ERROR_SUBSTRING = "is not callable"

    print(f"--- Running test for '{version}' version ---")
    
    try:
        # We patch `selenium.webdriver.Chrome` with our `FakeWebDriver`.
        with patch(PATCH_TARGET, FakeWebDriver):
            print("Initializing SeleniumScrapingTool with mocked WebDriver...")
            
            # During initialization, the tool creates an *instance* of our FakeWebDriver
            # and stores it as `self.driver`. This step should pass for both versions.
            tool = SeleniumScrapingTool(website_url='https://www.trendyol.com/16-gb-laptop-x-c103108-a232-v4012?utm_source=chatgpt.com')

            print("Calling tool's internal _run() method...")
            # The _run() method contains the buggy line: `driver = self.driver(options=options)`
            # This will attempt to call the FakeWebDriver instance, triggering the bug.
            tool._run()

        # --- Analysis for when NO error is raised ---
        if version == "buggy":
            print("\n❌ BUG NOT REPRODUCED: The tool ran successfully without the expected TypeError.")
            return 1
        else: # version == "fixed"
            print("\n✅ FIX CONFIRMED: The tool ran successfully without raising a TypeError.")
            return 0

    except TypeError as e:
        # --- Analysis for when a TypeError IS raised ---
        error_message = str(e)
        if version == "buggy":
            if EXPECTED_ERROR_SUBSTRING in error_message:
                print(f"\n✅ BUG REPRODUCED: Caught the expected TypeError.")
                print(f"   Error Message: {error_message}")
                return 0
            else:
                print(f"\n❌ BUG NOT REPRODUCED: A TypeError was caught, but it had an unexpected message: {error_message}")
                return 1
        else: # version == "fixed"
            print(f"\n❌ FIX NOT CONFIRMED: A TypeError was raised unexpectedly in the fixed version.")
            print(f"   Error Message: {error_message}")
            return 1

    except Exception as e:
        # --- Analysis for any other unexpected errors ---
        print(f"\n❌ TEST FAILED: An unexpected error occurred for '{version}' version: {type(e).__name__}: {e}")
        return 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reproduce.py [buggy|fixed]", file=sys.sys.stderr)
        sys.exit(1)
    
    version_arg = sys.argv[1]
    if version_arg not in ["buggy", "fixed"]:
        print(f"Invalid argument: '{version_arg}'. Please use 'buggy' or 'fixed'.", file=sys.stderr)
        sys.exit(1)

    # The exit code determines the success (0) or failure (1) of the test run.
    exit_code = test_selenium_type_error(version_arg)
    sys.exit(exit_code)