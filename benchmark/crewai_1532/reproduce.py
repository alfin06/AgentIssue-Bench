#!/usr/bin/env python
import sys
from crew import crewaiCrew
import traceback
from dotenv import load_dotenv
import os
import logging
import io

os.environ["OTEL_SDK_DISABLED "] = "false"
load_dotenv(override=True)

# Capture logs in memory
log_stream = io.StringIO()
log_handler = logging.StreamHandler(log_stream)
log_handler.setLevel(logging.ERROR)

# Attach to OpenTelemetry logger
otel_logger = logging.getLogger("opentelemetry")
otel_logger.setLevel(logging.ERROR)
otel_logger.addHandler(log_handler)

def run():
    """
    Run the crew and check logs for OpenTelemetry exporter errors.
    """
    inputs = {'topic': "AI Agents"}
    try:
        print("[INFO] Running kickoff with inputs:", inputs)
        crewaiCrew().crew().kickoff(inputs=inputs)

        log_contents = log_stream.getvalue()
        if "Exception while exporting Span batch" in log_contents:
            print("❌ OpenTelemetry exporter error detected.")
            print(log_contents)
        else:
            print("✅ No error occurred — OpenTelemetry export succeeded.")
    except TimeoutError as e:
        print("❌ TimeoutError caught (OTel export failure).")
        print("Message:", str(e))
    except Exception as e:
        print("❌ An unexpected exception occurred.")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {e}")
        print("Full traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    run()
