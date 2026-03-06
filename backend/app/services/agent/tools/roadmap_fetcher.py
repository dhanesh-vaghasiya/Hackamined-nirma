import requests


def fetch_available_roadmaps():

    url = "https://roadmap.sh/api/v1-list-official-roadmaps"

    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
    except requests.RequestException:
        return []
    
    data = response.json()

    if not isinstance(data, list):
        return []

    return sorted(
        [item.get("slug") for item in data if isinstance(item, dict) and item.get("slug")]
    )


def fetch_roadmap(roadmap_name):

    url = f"https://roadmap.sh/api/v1-official-roadmap/{roadmap_name}"

    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"Request failed: {exc}")
        return []

    data = response.json()

    if data.get("error"):
        print("Roadmap not found")
        return []

    nodes = data.get("nodes", [])

    roadmap_topics = []

    for node in nodes:
        if node.get("type") not in {"topic", "subtopic"}:
            continue

        title = node.get("data", {}).get("label")

        if title:
            roadmap_topics.append(title)

    return roadmap_topics


def main():

    available_roadmaps = fetch_available_roadmaps()

    if available_roadmaps:
        print(f"Available official roadmaps: {len(available_roadmaps)}")
        print("Type 'list' to view all slugs.")

    roadmap = input("Enter roadmap slug: ").strip().lower()

    if roadmap == "list":
        if not available_roadmaps:
            print("Could not load roadmap list right now.")
            return

        print("\nAvailable roadmap slugs:\n")
        for slug in available_roadmaps:
            print(f"- {slug}")
        return

    if available_roadmaps and roadmap not in available_roadmaps:
        print("Unknown roadmap slug.")
        print("Use 'list' to see all available slugs.")
        return

    topics = fetch_roadmap(roadmap)

    if not topics:
        return

    print("\nFull Roadmap:\n")

    for i, topic in enumerate(topics, 1):
        print(f"{i}. {topic}")


if __name__ == "__main__":
    main()