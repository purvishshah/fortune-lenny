import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from anthropic import Anthropic
from tqdm import tqdm

START = 8500
END = 8600

# --------------------------------------------------
# Helpers
# --------------------------------------------------
def extract_json_object(text: str):
    """
    Extract the first valid JSON object from a string.
    Returns dict or None.
    """
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None

# --------------------------------------------------
# Environment & client setup
# --------------------------------------------------
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not API_KEY:
    raise RuntimeError("ANTHROPIC_API_KEY not found in .env")

print("DEBUG API KEY PRESENT:", bool(API_KEY))

client = Anthropic(api_key=API_KEY)

# --------------------------------------------------
# Paths
# --------------------------------------------------
CHUNKS_FILE = BASE_DIR / "output" / "chunks" / "chunks_filtered.json"
OUTPUT_DIR = BASE_DIR / "output" / "quotes"
OUTPUT_FILE = OUTPUT_DIR / "quotes_raw.json"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# Model & runtime config
# --------------------------------------------------
MODEL_NAME = "claude-sonnet-4-20250514"
MAX_TOKENS = 300
TEMPERATURE = 0.2
REQUEST_DELAY = 1.0  # seconds

# --------------------------------------------------
# Prompt template
# NOTE: {{ }} are REQUIRED to escape literal JSON braces
# --------------------------------------------------
PROMPT_TEMPLATE = """
You are an expert at extracting distilled wisdom from conversations.

Your goal is to identify high-quality, standalone quotes from a podcast transcript.

A good quote:
- Is self-contained and makes sense without surrounding context.
- Is insightful, profound, or counter-intuitive (not generic advice).
- Is short to medium length (1–2 sentences).
- Is spoken by the Guest (preferred) or the Host.
- Contains experiential insight or practical wisdom.


Identify AT MOST ONE quote from the transcript.

If no sentence meets a very high bar for standalone wisdom,
return an empty list.

Do NOT return multiple quotes under any circumstances.
Selection matters more than coverage.
Do not force quotes if the quality bar is not met.

Exclude quotes that:
- Are questions.
- Are generic, logistical, or filler.
- Depend on unresolved references (e.g. “this”, “that”, “it”).
- Exceed 280 characters.
- Are about personal or romantic relationships.
- Are purely negative narratives without insight.
- Are spoken by someone other than host or guest.
- Have a sentence that depends on prior context, starts mid-thought.

IMPORTANT:
- Use the exact words spoken in the transcript.
- Do NOT paraphrase.
- Output ONLY valid JSON. No prose, no markdown.

Return the result in this exact format:
{{
  "quotes": [
    {{
      "quote": "…",
      "speaker": "…",
      "timestamp": "HH:MM:SS",
      "tags": ["tag1", "tag2"]
    }}
  ]
}}

Transcript:
\"\"\"
{transcript}
\"\"\"
"""

# --------------------------------------------------
# Load chunks
# --------------------------------------------------
with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
    chunks = json.load(f)["chunks"]

# --------------------------------------------------
# Resume support
# --------------------------------------------------
existing_quotes = []
processed_chunk_ids = set()

if OUTPUT_FILE.exists():
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        existing_quotes = json.load(f)
        processed_chunk_ids = {q["chunk_id"] for q in existing_quotes}

all_quotes = existing_quotes[:]

# --------------------------------------------------
# Main loop
# --------------------------------------------------
for chunk in tqdm(chunks[START:END]): # Adjust range as needed
    if chunk["chunk_id"] in processed_chunk_ids:
        continue

    transcript_text = f'{chunk["speaker"]}: {chunk["text"]}'
    prompt = PROMPT_TEMPLATE.format(transcript=transcript_text)

    try:
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            system="You are a JSON generator. Output ONLY valid JSON.",
            messages=[
                {"role": "user", "content": prompt}
            ],
        )

        content = response.content[0].text.strip()
        parsed = extract_json_object(content)

        if not parsed:
            print(f"\n⚠️ Failed to extract JSON for {chunk['chunk_id']}")
            print(content[:300])
            continue

        quotes = parsed.get("quotes", [])
        if len(quotes) > 1:
         quotes = quotes[:1]
        print(f"Parsed {len(quotes)} quotes from {chunk['chunk_id']}")

        for quote in quotes:
            quote["chunk_id"] = chunk["chunk_id"]
            quote["episode_id"] = chunk["episode_id"]
            quote["timestamp_seconds"] = chunk["timestamp_seconds"]
            all_quotes.append(quote)

        # Incremental write (crash-safe)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(all_quotes, f, indent=2)

        time.sleep(REQUEST_DELAY)

    except Exception as e:
        print(f"\n❌ Error processing {chunk['chunk_id']}: {e}")
        time.sleep(REQUEST_DELAY * 2)

print(f"\n✅ Done. Extracted {len(all_quotes)} quotes.")
