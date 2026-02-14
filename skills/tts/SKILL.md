---
name: tts
description: FOR TEXT REQUESTS ONLY. Use Kokoro TTS for voice memos (bm_daniel). This tool uses Hume AI.
---

# Text-to-Speech (TTS)

**FOR TEXT REQUESTS ONLY.** For voice memos, use Kokoro with bm_daniel (see TOOLS.md).

## Usage

```bash
HUME_API_KEY="..." HUME_SECRET_KEY="..." node {baseDir}/scripts/generate_hume_speech.js --text "Hello" --output "output.mp3"
```

## Important

- **Voice memos**: Use Kokoro with bm_daniel (NOT this tool)
- **This tool**: Only for general TTS when user asks for audio in text
