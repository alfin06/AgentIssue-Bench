import docker
import argparse

# Docker Hub user and repository
DOCKERHUB_USER = "llmagents"
REPO_NAME = "agentissue-bench"

# List of image tags
IMAGE_TAGS = [
    "autogen_4733",
    "autogen_3361",
    "autogen_4197",
    "autogen_5124",
    "autogen_1174",
    "autogen_1844",
    "autogen_4382",
    "autogen_4785",
    "autogen_5012",
    "autogen_5007",
    "agixt_1371",
    "agixt_1369",
    "agixt_1256",
    "agixt_1026",
    "agixt_1030",
    "agixt_1253",
    "camel_1145",
    "camel_1309",
    "camel_1273",
    "camel_88",
    "camel_1614",
    "chatdev_318",
    "chatdev_413",
    "chatdev_465",
    "crewai_1934",
    "crewai_1824",
    "crewai_1753",
    "crewai_1723",
    "crewai_1270",
    "crewai_1323",
    "crewai_1370",
    "crewai_1463",
    "crewai_1532",
    "evoninja_445",
    "evoninja_504",
    "evoninja_515",
    "evoninja_525",
    "evoninja_594",
    "evoninja_652",
    "lagent_244",
    "lagent_239",
    "lagent_279",
    "metagpt_1313",
    "superagent_953",
    "gpt-researcher_1027",
    "gpt-engineer_1197",
    "pythagora_55",
    "swe_agent_741",
    "swe_agent_333",
    "swe_agent_362",
]

def pull_and_run_image(tag: str):
    client = docker.from_env()
    full_image = f"{DOCKERHUB_USER}/{REPO_NAME}:{tag}"
    print(f"Pulling image {full_image}...")
    try:
        client.images.pull(full_image)
        print(f"Successfully pulled {full_image}")
    except Exception as e:
        print(f"Failed to pull {full_image}: {e}")
        return

    container_name = f"{REPO_NAME}_{tag}".replace(":", "_")
    print(f"Running container {container_name} and capturing output...")

    try:
        container = client.containers.run(
            full_image,
            name=container_name,
            remove=True,
            tty=True,
            stdin_open=True,
            stdout=True,
            stderr=True
        )
        print(container.decode() if isinstance(container, bytes) else container)
    except docker.errors.ContainerError as e:
        print(f"Container {container_name} exited with error:\n{e.stderr.decode()}")
    except docker.errors.APIError as e:
        print(f"Failed to run container {container_name}: {e.explanation}")

def main():
    parser = argparse.ArgumentParser(description="Pull and run Docker images.")
    parser.add_argument(
        "--tag", type=str, help="Specific image tag to pull and run (e.g., crewai_1532)"
    )
    args = parser.parse_args()

    if args.tag:
        if args.tag not in IMAGE_TAGS:
            print(f"Error: Tag '{args.tag}' not found in IMAGE_TAGS list.")
            return
        pull_and_run_image(args.tag)
    else:
        for tag in IMAGE_TAGS:
            pull_and_run_image(tag)

if __name__ == "__main__":
    main()
