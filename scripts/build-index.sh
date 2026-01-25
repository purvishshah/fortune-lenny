#!/bin/bash

# Build index/ folder from podcast transcripts using Claude CLI
# Usage: ./scripts/build-index.sh
#
# Features:
# - Idempotent: skips episodes already indexed in keyword files
# - Incremental: appends to existing keyword files
# - Resume support: can be interrupted and restarted

set -e

EPISODES_DIR="${EPISODES_DIR:-episodes}"
OUTPUT_DIR="${OUTPUT_DIR:-index}"
TEMP_DIR="${TEMP_DIR:-$(mktemp -d)}"

# Track progress
TOTAL=$(ls -d "$EPISODES_DIR"/*/ 2>/dev/null | wc -l | tr -d ' ')
CURRENT=0
PROCESSED=0

echo "Building index for $TOTAL episodes..."
echo "Temp directory: $TEMP_DIR"

# Initialize output directory
mkdir -p "$OUTPUT_DIR"

# Process each episode
for dir in "$EPISODES_DIR"/*/; do
    slug=$(basename "$dir")
    transcript="$dir/transcript.md"

    ((CURRENT++)) || true

    # Check if episode already indexed in keyword files (idempotency)
    # Exclude README.md and episodes.md (legacy file)
    if ls "$OUTPUT_DIR"/*.md 2>/dev/null | grep -v README.md | grep -v episodes.md | xargs grep -lq "episodes/$slug/transcript.md" 2>/dev/null; then
        echo "[$CURRENT/$TOTAL] Skipping $slug (already indexed)"
        continue
    fi

    if [[ ! -f "$transcript" ]]; then
        echo "[$CURRENT/$TOTAL] Skipping $slug (no transcript.md)"
        continue
    fi

    echo "[$CURRENT/$TOTAL] Processing $slug..."

    # Extract guest name from YAML frontmatter
    frontmatter=$(sed -n '/^---$/,/^---$/p' "$transcript" | sed '1d;$d')
    guest=$(echo "$frontmatter" | grep '^guest:' | sed 's/^guest: *//' | sed 's/^"//' | sed 's/"$//')

    # Write transcript to temp file (skip frontmatter)
    transcript_temp="$TEMP_DIR/transcript_temp.txt"
    sed '1,/^---$/d' "$transcript" > "$transcript_temp"

    # Create prompt file
    prompt_file="$TEMP_DIR/prompt.txt"
    cat > "$prompt_file" << 'PROMPT_END'
Analyze this podcast transcript and provide 4-6 BROAD topic keywords.

Rules:
- Use general categories, not specific terms (e.g., "AI" not "ai-coding-agents", "leadership" not "servant-leadership")
- Prefer these existing topics when relevant: product management, leadership, growth strategy, product-led growth, product strategy, product development, career development, experimentation, hiring, entrepreneurship, startup growth, venture capital, team building, company culture, decision making, AI, machine learning, remote work, OKRs, mentorship, storytelling, innovation, feedback, retention, user experience, network effects
- Only include company names if they are a major focus (e.g., Airbnb, Google, Meta, Stripe, Uber, Slack, Facebook)

Output ONLY valid JSON: {"keywords": ["...", "..."]}

TRANSCRIPT:
PROMPT_END
    cat "$transcript_temp" >> "$prompt_file"

    # Call Claude for keywords
    raw_response=$(claude --model claude-sonnet-4-20250514 -p < "$prompt_file" 2>/dev/null || echo '{"keywords": []}')

    # Strip markdown code blocks if present and extract JSON
    response=$(echo "$raw_response" | grep -o '{.*}' | head -1 || echo '{"keywords": []}')

    # Parse JSON response
    keywords_json=$(echo "$response" | jq -r '.keywords // []' 2>/dev/null || echo "[]")

    # Append to keyword files immediately
    echo "$keywords_json" | jq -r '.[]' 2>/dev/null | while read -r keyword; do
        if [[ -n "$keyword" ]]; then
            # Create filename from keyword (lowercase, spaces to hyphens, remove special chars)
            filename=$(echo "$keyword" | tr '[:upper:]' '[:lower:]' | tr ' /' '-' | tr -cd 'a-z0-9-')
            keyword_file="$OUTPUT_DIR/${filename}.md"

            # Create file with header if it doesn't exist
            if [[ ! -f "$keyword_file" ]]; then
                echo "# $keyword" > "$keyword_file"
                echo "" >> "$keyword_file"
                echo "Episodes discussing **$keyword**:" >> "$keyword_file"
                echo "" >> "$keyword_file"
            fi

            # Append episode link
            echo "- [$guest](../episodes/$slug/transcript.md)" >> "$keyword_file"
        fi
    done

    ((PROCESSED++)) || true

    # Small delay to avoid rate limiting
    sleep 1
done

echo ""
echo "Updating README.md..."

# Get unique episode count (exclude README.md and legacy episodes.md)
keyword_files=$(ls "$OUTPUT_DIR"/*.md 2>/dev/null | grep -v README.md | grep -v episodes.md)
unique_episodes=$(grep -h "episodes/.*/transcript.md" $keyword_files 2>/dev/null | sort -u | wc -l | tr -d ' ')

# Build README.md with links to all keyword files
cat > "$OUTPUT_DIR/README.md" << EOF
# Lenny's Podcast Index

*Generated: $(date +%Y-%m-%d) | $unique_episodes episodes indexed*

## Topics

EOF

# Add links to all keyword files sorted alphabetically (exclude README.md and legacy episodes.md)
ls "$OUTPUT_DIR"/*.md 2>/dev/null | grep -v README.md | grep -v episodes.md | sort | while read -r file; do
    name=$(basename "$file" .md)
    # Convert filename to title case
    title=$(echo "$name" | tr '-' ' ' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) tolower(substr($i,2))}1')
    count=$(grep -c "^- \[" "$file" 2>/dev/null || echo "0")
    echo "- [$title]($name.md) ($count episodes)" >> "$OUTPUT_DIR/README.md"
done

echo ""
echo "Done! Processed $PROCESSED new episodes."
echo "  - README.md (main entry point)"
echo "  - $(ls "$OUTPUT_DIR"/*.md 2>/dev/null | grep -v README.md | wc -l | tr -d ' ') keyword files"
echo ""
echo "Temp files at: $TEMP_DIR"
