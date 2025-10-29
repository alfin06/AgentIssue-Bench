import subprocess
import os
import time
import re

# List of tags to process
TAGS = [
    "agixt_1026", "crewai_1370",
    "agixt_1030", "crewai_1463",
    "agixt_1253", "crewai_1532",
    "agixt_1256", "crewai_1723",
    "agixt_1369", "crewai_1753",
    "agixt_1371", "crewai_1824",
    "ai_5628", "crewai_1934",
    "haystack_9523", "evoninja_504",
    "ai_4619", "evoninja_515",
    "haystack_8912", "evoninja_525",
    "evoninja_594", "evoninja_652",
    "autogen_4733", "autogen_4382",
    "autogen_4785", "autogen_4197",
    "autogen_5007", "lagent_239",
    "ai_4411", "lagent_244",
    "ai_6510", "lagent_279",
    "camel_1145", "autogen_3361",
    "camel_1273", "metagpt_1313",
    "camel_1614", "autogen_1844",
    "camel_88", "autogen_1174",
    "chatdev_318", "pythagora_55",
    "chatdev_413", "superagent_953",
    "chatdev_465", "crewai_1270",
    "crewai_1323", "sweagent_741",
    "gpt-engineer_1197", "gpt-researcher_1027"
]

# ADDITIONAL_TAGS = [
#     "ai_3953", "crewai_2237",
#     "ai_5365", "crewai_2127",
#     "ai_4412", "crewai_2150",
#     "ai_4446", "haystack_9313",
#     "crewai_2708", "haystack_9487",
#     "crewai_1495", "haystack_9193",
#     "langgraphjs_1217", "mle_agent_173",
#     "mastra_4331", "sweagent_333",
#     "ai_5380", "openmanus_1143",
#     "ai_4761", "ai_2705"    
# ]

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def clean_ansi(text):
    return ANSI_ESCAPE.sub('', text)

def run_command(command, logfile, timeout=None, skip_on_fail=False):
    print(f"\n>>> Running: {command}\n")
    logfile.write(f"\n>>> Running: {command}\n")
    try:
        process = subprocess.Popen(
            command, shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True,
            stdin=subprocess.DEVNULL
        )
        for line in process.stdout:
            print(line, end="")
            logfile.write(clean_ansi(line))
        process.wait(timeout=timeout)
        logfile.write(f"\n--- Exit code: {process.returncode} ---\n")
    except subprocess.TimeoutExpired:
        print(f"\n⚠️ Timeout! Skipping command: {command}\n")
        logfile.write(f"\n⚠️ Timeout! Skipped command: {command}\n")
        process.kill()
    except subprocess.CalledProcessError:
        if skip_on_fail:
            print(f"\n⚠️ Error! Skipping command: {command}\n")
            logfile.write(f"\n⚠️ Error! Skipped command: {command}\n")
        else:
            raise

if __name__ == "__main__":
    # Prompt user for API keys and URLs
    OPENAI_API_KEY = input("Enter your OPENAI_API_KEY: ").strip()
    OPENAI_API_BASE = input("Enter your OPENAI_API_BASE: ").strip()
    BASE_URL = OPENAI_API_BASE
    SERPERDEV_API_KEY = input("Enter your SERPERDEV_API_KEY: ").strip()
    GOOGLE_API_KEY = input("Enter your GOOGLE_API_KEY: ").strip()

    print(">>> Removing all existing Docker images...\n")
    subprocess.run("sudo docker rmi -f $(sudo docker images -q) || true", shell=True)
    print("\n>>> All existing images removed.\n")
    time.sleep(2)

    env_vars = (
        f"-e OPENAI_API_KEY={OPENAI_API_KEY} "
        f"-e OPENAI_API_BASE={OPENAI_API_BASE} "
        f"-e BASE_URL={BASE_URL} "
        f"-e SERPERDEV_API_KEY={SERPERDEV_API_KEY} "
        f"-e GOOGLE_GENERATIVE_AI_API_KEY={GOOGLE_API_KEY} "
    )

    for idx, tag in enumerate(TAGS, start=1):
        print(f"\n===== [{idx}/{len(TAGS)}] Processing {tag} =====\n")
        log_path = os.path.join(LOG_DIR, f"{tag}.log")
        with open(log_path, "w", encoding="utf-8") as logfile:
            image = f"alfin06/agentissue-bench:{tag}"
            run_command(f"sudo docker pull {image}", logfile, timeout=600, skip_on_fail=True)
            run_command(f"sudo docker run --rm {env_vars}\"{image}\" test_buggy", logfile, timeout=600, skip_on_fail=True)
            run_command(f"sudo docker run --rm {env_vars}\"{image}\" test_fixed", logfile, timeout=600, skip_on_fail=True)

        print(f"\n>>> Finished {tag}. Log saved to: {log_path}\n")
        time.sleep(1)

    print("\n✅ All tasks completed. Check logs/ folder for clean outputs.")