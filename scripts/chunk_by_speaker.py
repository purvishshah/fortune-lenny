from pathlib import Path
import json
import re
from datetime import datetime, timezone

# -----------------------------
# Paths
# -----------------------------
BASE_DIR = Path(__file__).parent.parent
CLEAN_DIR = BASE_DIR / "output" / "cleaned"
CHUNKS_DIR = BASE_DIR / "output" / "chunks"
CHUNKS_FILE = CHUNKS_DIR / "chunks.json"

CHUNKS_DIR.mkdir(exist_ok=True)

# -----------------------------
# Helpers
# -----------------------------
def hhmmss_to_seconds(time_str: str) -> int:
    h, m, s = time_str.split(":")
    return int(h) * 3600 + int(m) * 60 + int(s)

SPEAKER_RE = re.compile(r"\[SPEAKER=([^\]]+)\]")
TIME_RE = re.compile(r"\[TIME=(\d{2}:\d{2}:\d{2})\]")

# -----------------------------
# Main logic
# -----------------------------
all_chunks = []
global_order = 0

for file_path in sorted(CLEAN_DIR.glob("*.txt")):
    episode_slug = file_path.stem
    episode_id = f"ep_{episode_slug}"

    lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()

    current_speaker = None
    current_start_time = None
    buffer = []

    for line in lines:
        speaker_match = SPEAKER_RE.search(line)
        time_match = TIME_RE.search(line)

        # If we hit a new marker line
        if speaker_match or time_match:
            # Flush existing chunk
            if current_speaker and buffer:
                chunk_id = f"{episode_id}_{str(global_order).zfill(4)}"
                all_chunks.append({
                    "chunk_id": chunk_id,
                    "episode_id": episode_id,
                    "speaker": current_speaker,
                    "text": " ".join(buffer).strip(),
                    "order": global_order,
                    "start_time_raw": current_start_time,
                    "timestamp_seconds": hhmmss_to_seconds(current_start_time)
                })
                global_order += 1
                buffer = []

            # Update state
            if speaker_match:
                current_speaker = speaker_match.group(1).strip()
            if time_match:
                current_start_time = time_match.group(1).strip()

            continue  # marker lines never contain spoken text

        # Normal spoken text
        if current_speaker:
            stripped = line.strip()
            if stripped:
                buffer.append(stripped)

    # Flush last chunk in file
    if current_speaker and buffer:
        chunk_id = f"{episode_id}_{str(global_order).zfill(4)}"
        all_chunks.append({
            "chunk_id": chunk_id,
            "episode_id": episode_id,
            "speaker": current_speaker,
            "text": " ".join(buffer).strip(),
            "order": global_order,
            "start_time_raw": current_start_time,
            "timestamp_seconds": hhmmss_to_seconds(current_start_time)
        })
        global_order += 1

# -----------------------------
# Output
# -----------------------------
output_payload = {
    "schema_version": "1.0",
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "total_chunks": len(all_chunks),
    "chunks": all_chunks
}

with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
    json.dump(output_payload, f, indent=2)

print(f"Created {len(all_chunks)} chunks")
print(f"Saved to {CHUNKS_FILE}")
