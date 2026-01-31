from pathlib import Path
BASE_DIR = Path(__file__).parent.parent
EPISODES_DIR = BASE_DIR / "episodes"

episodes_data = [] # List to hold data for all episodes. Empty list created.

for episode_folder in EPISODES_DIR.iterdir():
    transcript_file = episode_folder / "transcript.md"

    if not transcript_file.exists():
        continue  # skip folders without transcripts

    text = transcript_file.read_text(encoding="utf-8", errors="ignore")

    episode_info = {
        "episode": episode_folder.name,
        "word_count": len(text.split()),
        "line_count": len(text.splitlines())
    }

    episodes_data.append(episode_info)

# Print summary
print("Total episodes processed:", len(episodes_data))

# Print first 3 as a sample
for ep in episodes_data[:3]:
    print(ep)