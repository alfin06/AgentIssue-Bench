import os
import sys
import subprocess
import yaml

def update_api_key(api_key, config_path):
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    config.setdefault("llm", {})
    config["llm"]["api_key"] = api_key
    with open(config_path, "w") as f:
        yaml.safe_dump(config, f)

def run_game(game_script):
    try:
        proc = subprocess.Popen(
            ["python", game_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        try:
            stdout, stderr = proc.communicate(timeout=20)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()

        if "pydantic_core._pydantic_core.ValidationError" in stdout or \
           "pydantic_core._pydantic_core.ValidationError" in stderr:
            return True
        return False
    except Exception as e:
        print(f"Error running game: {e}")
        return False

def run_test(version):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY is not set in environment")
        return 2

    root = f"/app/source_code_{version}"
    config_path = os.path.join(root, "config", "config2.yaml")
    game_script = os.path.join(root,  "examples", "werewolf_game", "start_game.py")

    if not os.path.exists(config_path):
        print(f"Config file not found: {config_path}")
        return 2
    if not os.path.exists(game_script):
        print(f"Game script not found: {game_script}")
        return 2

    update_api_key(api_key, config_path)
    success = run_game(game_script)

    if version == "buggy":
        return 0 if success else 1
    elif version in ["fixed", "patched"]:
        return 0 if not success else 1
    else:
        print(f"Invalid version: {version}")
        return 2

if __name__ == "__main__":
    import sys

    version = sys.argv[1] if len(sys.argv) > 1 else None
    if version not in ["buggy", "fixed", "patched"]:
        print("Usage: python reproduce.py [buggy|fixed|patched]")
        sys.exit(1)

    exit_code = run_test(version)
    if version == "buggy":
        final_code = 1 if exit_code == 0 else 0
    else:
        final_code = 0 if exit_code == 0 else 1

    sys.exit(final_code)