from pathlib import Path
import re

BASE_DIR = Path(__file__).parent.parent

TRANSCRIPTS_DIR = BASE_DIR / "lennys-podcast-transcripts" / "episodes"
CLEAN_DIR = BASE_DIR / "output" / "cleaned"

def remove_yaml_front_matter(text):
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            return parts[2].strip()
    return text.strip()

def normalize_speaker_and_time(text):
    """
    Handles both:
      'Ada Chen Rekhi (00:05:12): hello'
      '(00:05:54): continued thought'

    Carries forward the last known speaker.
    """
    lines = text.splitlines()
    normalized = []

    current_speaker = None

    full_pattern = re.compile(
        r"^(.+?)\s*\((\d{2}:\d{2}:\d{2})\)\s*:\s*(.*)"
    )
    time_only_pattern = re.compile(
        r"^\((\d{2}:\d{2}:\d{2})\)\s*:\s*(.*)"
    )

    for line in lines:
        full_match = full_pattern.match(line)
        time_only_match = time_only_pattern.match(line)

        if full_match:
            speaker = full_match.group(1).strip()
            timestamp = full_match.group(2)
            speech = full_match.group(3).strip()

            current_speaker = speaker

            normalized.append(
                f"[SPEAKER={current_speaker}][TIME={timestamp}] {speech}"
            )

        elif time_only_match and current_speaker:
            timestamp = time_only_match.group(1)
            speech = time_only_match.group(2).strip()

            normalized.append(
                f"[SPEAKER={current_speaker}][TIME={timestamp}] {speech}"
            )

        else:
            normalized.append(line)

    return "\n".join(normalized)

def normalize_whitespace(text):
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

CLEAN_DIR.mkdir(exist_ok=True)

processed = 0

for episode_folder in TRANSCRIPTS_DIR.iterdir():
    transcript_file = episode_folder / "transcript.md"

    if not transcript_file.exists():
        continue

    raw_text = transcript_file.read_text(encoding="utf-8", errors="ignore")

    text = remove_yaml_front_matter(raw_text)
    text = normalize_speaker_and_time(text)
    text = normalize_whitespace(text)

    output_file = CLEAN_DIR / f"{episode_folder.name}.txt"
    output_file.write_text(text, encoding="utf-8")

    processed += 1

print(f"Cleaned {processed} transcripts with speaker + time labels")
print(f"Output directory: {CLEAN_DIR}")
