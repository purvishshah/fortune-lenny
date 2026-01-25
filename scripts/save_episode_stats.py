from pathlib import Path
import json

# Base directory
BASE_DIR = Path(__file__).parent.parent

EPISODES_DIR = BASE_DIR / "episodes"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_FILE = OUTPUT_DIR / "episode_stats.json"

episodes_data = []

for episode_folder in EPISODES_DIR.iterdir():
    transcript_file = episode_folder / "transcript.md"

    if not transcript_file.exists():
        continue

    text = transcript_file.read_text(encoding="utf-8", errors="ignore")

    episode_info = {
        "episode": episode_folder.name,
        "word_count": len(text.split()),
        "line_count": len(text.splitlines())
    }

    episodes_data.append(episode_info)

    # Make sure output folder exists
OUTPUT_DIR.mkdir(exist_ok=True)

# Save to JSON
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(episodes_data, f, indent=2)

print(f"Saved stats for {len(episodes_data)} episodes")
print(f"File location: {OUTPUT_FILE}")

