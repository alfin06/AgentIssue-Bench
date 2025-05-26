import os
import subprocess

# Step 1: Simulate a project with Pythagora initialized
def setup_test_environment():
    os.makedirs("test_project", exist_ok=True)
    os.chdir("test_project")

    with open("server.js", "w") as f:
        f.write("""\
const express = require('express');
const app = express();
const port = 3000;

app.get('/', (req, res) => {
    res.send('Hello World!');
});

app.listen(port, () => {
    console.log(`Example app listening on port ${port}`);
});
""")

    # Step 2: Install Pythagora
    subprocess.run(["npm", "init", "-y"])
    subprocess.run(["npm", "install", "pythagora", "express"])

# Step 3: Set invalid API key in environment variable
def set_invalid_api_key():
    os.environ["PYTHAGORA_API_KEY"] = "invalid_api_key"

# Step 4: Trigger unit test generation with invalid key
def trigger_pythagora():
    print("\n>>> Running Pythagora with invalid API key...\n")
    try:
        subprocess.run(["npx", "pythagora", "test", "server.js"], check=True)
    except subprocess.CalledProcessError as e:
        print(">>> Caught error as expected due to invalid API key.")

if __name__ == "__main__":
    setup_test_environment()
    set_invalid_api_key()
    trigger_pythagora()
