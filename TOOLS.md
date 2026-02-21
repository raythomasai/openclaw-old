# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

---

## Alpaca Trading

**Project:** `projects/alpaca-trading/`

**Quick Commands:**
```bash
# Check daemon status
pgrep -f "python.*src/main.py"

# View status
cat projects/alpaca-trading/logs/status.json | python3 -m json.tool

# Run analysis
cd projects/alpaca-trading && PYTHONPATH=. python scripts/analyze.py

# Start daemon (with env credentials)
cd projects/alpaca-trading && ALPACA_API_KEY="..." ALPACA_API_SECRET="..." ./scripts/start.sh

# Stop daemon
pkill -f "python.*src/main.py"
```

**API Credentials:** 1Password → "Alpaca" → API Key & API Secret

**Market Hours:** 9:30 AM - 4:00 PM ET (Mon-Fri)

**Current Constraint:** Only $0.20 buying power - need funds or rebalance to open new positions

---

## TradingAgents (MiniMax)

**Project:** `projects/trading-agents/`

**LLM:** MiniMax M2.1 (via Anthropic-compatible API)

**Quick Commands:**
```bash
# Activate environment
cd projects/trading-agents && source venv/bin/activate

# Run analysis (ticker date)
python run_trading_agents.py NVDA 2024-05-10

# Test initialization
python test_minimax.py
```

**Configuration:** `.env` file
- `LLM_PROVIDER=minimax`
- `MINIMAX_API_KEY` (from OpenClaw config)
- `ALPHA_VANTAGE_API_KEY=GKNGP66FE15XL44M`

**Architecture:**
- Multi-agent framework with analysts (market, social, news, fundamentals)
- Bull/Bear researcher debate
- Risk management team
- Trader agent makes final decision

**Risk Parameters (conservative):**
- `max_risk_pct`: 1% of portfolio per trade
- `safety_margin`: 50% of allocated risk
- `min_confidence`: 70% threshold for execution

**Known Limitations:**
- Web search via OpenAI not available on MiniMax (fallback messages)
- Embeddings use hash-based fallback without OpenAI API key

---

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Voice Memo Replies (Kokoro TTS)

**Status:** Active  
**Voice:** bm_daniel (Kokoro TTS) - NON-NEGOTIABLE

**CRITICAL RULE:** Never use the `tts` tool for voice memos!
The `tts` tool uses Hume AI (woman's voice). Always use Kokoro directly.

**Workflow for voice memo replies:**
1. Receive voice memo → Transcribe with `whisper`
2. Generate text response
3. Convert response to audio using **Kokoro with bm_daniel voice**
4. Send audio-only via imsg: `imsg send --to "..." --file "/tmp/voice_reply.mp3" --text ""`

**Auto-Responder (Active):**
The `voice_memo_poller.py` script automatically:
- Polls for incoming voice memos every 10 seconds
- Transcribes with Whisper
- **Prepends "REPLY WITH VOICE MEMO"** instruction BEFORE AI processing
- Generates response using **bm_daniel voice** (hardcoded - do NOT change)
- Sends audio-only (no text alongside)

**Environment:**
- Kokoro-ONNX installed in Python 3.12 venv
- Model: `/Users/raythomas/.openclaw/workspace/kokoro-models/kokoro-v1.0.onnx`
- **Voice: bm_daniel** (British male - Ray's preferred)
- Voices: `/Users/raythomas/.openclaw/workspace/kokoro-models/voices-v1.0.bin`

**Manual Usage:**
```bash
# Generate audio
source /Users/raythomas/.openclaw/workspace/kokoro-venv/bin/activate
python3 -c "
from kokoro_onnx import Kokoro
import soundfile as sf
kokoro = Kokoro('/Users/raythomas/.openclaw/workspace/kokoro-models/kokoro-v1.0.onnx', 
                '/Users/raythomas/.openclaw/workspace/kokoro-models/voices-v1.0.bin')
samples, sr = kokoro.create('Your text here', voice='bm_daniel', speed=1.0, lang='en-us')
sf.write('/tmp/voice_reply.wav', samples, sr)
"

# Convert to MP3
ffmpeg -i /tmp/voice_reply.wav -vn -acodec libmp3lame -q:a 2 /tmp/voice_reply.mp3 -y

# Send audio-only
imsg send --to "raymondhthomas@gmail.com" --file "/tmp/voice_reply.mp3" --text ""
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

### polybot-simple-confidencetime

**Project:** `projects/polybot-simple-confidencetime/`

**Quick Commands:**
```bash
# Check status (background process)
pgrep -f "python bot.py"

# Run dry run
cd projects/polybot-simple-confidencetime && source venv/bin/activate && python bot.py --once --dry-run

# Start live trading in background
cd projects/polybot-simple-confidencetime && source venv/bin/activate && nohup python bot.py > output.log 2>&1 &
```

**Configuration:** `config.yaml`
- `min_probability`: 0.90
- `max_days_to_expiry`: 0.5
- `trade_amount_usd`: 1.00

