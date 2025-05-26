# reproduce.py

# Simulating AGiXT's Websearch logic where websearch_depth is not cast to int
def websearch_agent(websearch_depth):
    # Simulate the behavior in agixt/Websearch.py
    if websearch_depth > 0:
        print(f"Performing web search with depth: {websearch_depth}")
    else:
        print("Web search depth must be greater than 0.")

if __name__ == "__main__":
    # Simulating the case where websearch_depth is passed as a string
    websearch_depth = "3"  # From config or user input, etc.

    try:
        websearch_agent(websearch_depth)
    except TypeError as e:
        print("Caught expected TypeError:", e)
