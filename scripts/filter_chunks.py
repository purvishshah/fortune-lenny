import json
from pathlib import Path
from collections import Counter

# --------------------------------------------------
# Paths
# --------------------------------------------------
BASE_DIR = Path(__file__).parent.parent
INPUT_FILE = BASE_DIR / "output" / "chunks" / "chunks.json"
OUTPUT_FILE = BASE_DIR / "output" / "chunks" / "chunks_filtered.json"

# --------------------------------------------------
# Config (balanced, not aggressive)
# --------------------------------------------------
MIN_CHAR_LENGTH = 200
MIN_SENTENCES = 2
MAX_SENTENCES = 8

BLOCKLIST_PHRASES = [
    "this episode is brought to you by",
    "thanks to our sponsor",
    "sponsored by",
    "subscribe to the podcast",
    "welcome to",
    "today's episode",
    "sign up at",
]

GLUE_PHRASES = [
    "you know",
    "i think",
    "i guess",
    "kind of",
    "sort of",
    "yeah",
    "totally",
    "i mean",
    "right?",
]

# --------------------------------------------------
# Load chunks
# --------------------------------------------------
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    payload = json.load(f)

chunks = payload["chunks"]
original_count = len(chunks)

stats = Counter()
filtered = []

# --------------------------------------------------
# Filtering logic
# --------------------------------------------------
for c in chunks:
    text = c["text"].lower()

    # 1. Length filter
    if len(text) < MIN_CHAR_LENGTH:
        stats["too_short"] += 1
        continue

    # 2. Sponsor / intro phrases
    if any(phrase in text for phrase in BLOCKLIST_PHRASES):
        stats["sponsor_or_intro"] += 1
        continue

    # 3. Speaker-based heuristic
    # Hosts ask more questions; guests deliver insight
    if c["speaker"].lower() == "lenny" and len(text) < 350:
        stats["short_host_chunk"] += 1
        continue


    # 4. Question-heavy chunks
    if text.count("?") >= 2:
        stats["question_heavy"] += 1
        continue

    # 5. Sentence count heuristic
    sentence_count = len([s for s in text.split(".") if s.strip()])
    if sentence_count < MIN_SENTENCES or sentence_count > MAX_SENTENCES:
        stats["sentence_count_out_of_range"] += 1
        continue

    # 6. Glue phrase density (light touch)
    glue_hits = sum(text.count(p) for p in GLUE_PHRASES)
    if glue_hits >= 3:
        stats["too_much_glue"] += 1
        continue

    # Passed all filters
    filtered.append(c)

# --------------------------------------------------
# Output
# --------------------------------------------------
output = {
    "schema_version": "1.2",
    "total_chunks": len(filtered),
    "chunks": filtered,
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

# --------------------------------------------------
# Report
# --------------------------------------------------
print("\nFiltering complete\n")
print(f"Original chunks : {original_count}")
print(f"Filtered chunks : {len(filtered)}")
print(f"Reduction       : {original_count - len(filtered)} ({(original_count - len(filtered)) / original_count:.1%})\n")

print("Breakdown by rule:")
for k, v in stats.most_common():
    print(f"  {k:30s} {v}")
