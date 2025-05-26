import docker

SOURCE_USER = "alfin06"
DEST_USER = "llmagents"

IMAGE_TAGS = [
    "agentissue-bench:autogen_4733",
    "agentissue-bench:autogen_3361",
    "agentissue-bench:autogen_4197",
    "agentissue-bench:autogen_5124",
    "agentissue-bench:autogen_1174",
    "agentissue-bench:autogen_1844",
    "agentissue-bench:autogen_4382",
    "agentissue-bench:autogen_4785",
    "agentissue-bench:autogen_5012",
    "agentissue-bench:autogen_5007",
    "agentissue-bench:agixt_1371",
    "agentissue-bench:agixt_1369",
    "agentissue-bench:agixt_1256",
    "agentissue-bench:agixt_1026",
    "agentissue-bench:agixt_1030",
    "agentissue-bench:agixt_1253",
    "agentissue-bench:camel_1145",
    "agentissue-bench:camel_1309",
    "agentissue-bench:camel_1273",
    "agentissue-bench:camel_88",
    "agentissue-bench:camel_1614",
    "agentissue-bench:chatdev_318",
    "agentissue-bench:chatdev_413",
    "agentissue-bench:chatdev_465",
    "agentissue-bench:crewai_1934",
    "agentissue-bench:crewai_1824",
    "agentissue-bench:crewai_1753",
    "agentissue-bench:crewai_1723",
    "agentissue-bench:crewai_1270",
    "agentissue-bench:crewai_1323",
    "agentissue-bench:crewai_1370",
    "agentissue-bench:crewai_1463",
    "agentissue-bench:crewai_1532",
    "agentissue-bench:evoninja_445",
    "agentissue-bench:evoninja_504",
    "agentissue-bench:evoninja_515",
    "agentissue-bench:evoninja_525",
    "agentissue-bench:evoninja_594",
    "agentissue-bench:evoninja_652",
    "agentissue-bench:lagent_244",
    "agentissue-bench:lagent_239",
    "agentissue-bench:lagent_279",
    "agentissue-bench:metagpt_1313",
    "agentissue-bench:superagent_953",
    "agentissue-bench:gpt-researcher_1027",
    "agentissue-bench:gpt-engineer_1197",
    "agentissue-bench:pythagora_55",
    "agentissue-bench:swe_agent_741",
    "agentissue-bench:swe_agent_333",
    "agentissue-bench:swe_agent_362",
]

def transfer_images():
    client = docker.from_env()

    for tag in IMAGE_TAGS:
        source_image = f"{SOURCE_USER}/{tag}"
        dest_image = f"{DEST_USER}/{tag}"

        print(f"\n⏬ Pulling {source_image}...")
        try:
            client.images.pull(source_image)
            print(f"✅ Pulled {source_image}")
        except Exception as e:
            print(f"❌ Failed to pull {source_image}: {e}")
            continue

        print(f"🔁 Tagging {source_image} as {dest_image}")
        try:
            image = client.images.get(source_image)
            image.tag(dest_image)
            print(f"✅ Tagged as {dest_image}")
        except Exception as e:
            print(f"❌ Failed to tag image: {e}")
            continue

        print(f"⏫ Pushing {dest_image}...")
        try:
            for line in client.images.push(dest_image, stream=True, decode=True):
                print(line.get("status") or line.get("error"))
            print(f"✅ Pushed {dest_image}")
        except Exception as e:
            print(f"❌ Failed to push {dest_image}: {e}")
            continue

        print(f"🗑️ Removing local images for {tag}...")
        try:
            client.images.remove(image=source_image, force=True)
            client.images.remove(image=dest_image, force=True)
            print(f"✅ Deleted {source_image} and {dest_image} from local Docker")
        except Exception as e:
            print(f"❌ Failed to delete local images: {e}")

if __name__ == "__main__":
    transfer_images()
