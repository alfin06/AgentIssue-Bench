import docker
import argparse
import os

# Docker Hub user and repository
DOCKERHUB_USER = "alfin06"
REPO_NAME = "agentissue-bench"

# List of image tags
IMAGE_TAGS = [
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

def stop_and_remove(tag: str):
    client = docker.from_env()
    full_image = f"{DOCKERHUB_USER}/{REPO_NAME}:{tag}"
    container_name = f"{REPO_NAME}_{tag}".replace(":", "_")

    # Stop and remove container if it exists
    try:
        container = client.containers.get(container_name)
        print(f"Stopping container {container_name}...")
        container.stop()
        container.remove()
        print(f"Removed container {container_name}")
    except docker.errors.NotFound:
        print(f"Container {container_name} not found.")
    except docker.errors.APIError as e:
        print(f"Error removing container {container_name}: {e.explanation}")

    # Remove image if it exists
    try:
        print(f"Removing image {full_image}...")
        client.images.remove(full_image)
        print(f"Removed image {full_image}")
    except docker.errors.ImageNotFound:
        print(f"Image {full_image} not found.")
    except docker.errors.APIError as e:
        print(f"Error removing image {full_image}: {e.explanation}")

def main():
    parser = argparse.ArgumentParser(description="Stop containers and remove Docker images.")
    parser.add_argument(
        "--tag", type=str, help="Specific image tag to stop and remove (e.g., crewai_1532)"
    )
    args = parser.parse_args()

    if args.tag:
        if args.tag not in IMAGE_TAGS:
            print(f"Error: Tag '{args.tag}' not found in IMAGE_TAGS list.")
            return
        stop_and_remove(args.tag)
    else:
        for tag in IMAGE_TAGS:
            stop_and_remove(tag)

if __name__ == "__main__":
    main()
