from pathlib import Path

file_path = Path("../lennys-podcast-transcripts/episodes/adam-fishman/transcript.md")
text = file_path.read_text(encoding="utf-8", errors="ignore")

#basic statclear
num_characters = len(text)
num_words = len(text.split())
num_lines = len(text.splitlines())

print(f"File name: {file_path}")
print(f"Number of characters: {num_characters}")
print(f"Number of words: {num_words}")
print(f"Number of lines: {num_lines}")

print("\n---- Preview of the transcript ----\n")
print(text[:500])  # Print the first 500 characters of the transcript

