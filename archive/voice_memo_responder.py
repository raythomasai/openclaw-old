#!/usr/bin/env python3
"""
Voice Memo Auto-Responder
Watches for incoming voice memos and responds with Kokoro TTS voice
"""

import os
import sys
import time
import json
import subprocess
from pathlib import Path

# Paths
WORKSPACE = Path("/Users/raythomas/.openclaw/workspace")
KOKORO_VENV = WORKSPACE / "kokoro-venv"
KOKORO_MODELS = WORKSPACE / "kokoro-models"
VOICE_MEMO_DIR = WORKSPACE / "voice_memos"

VOICE_MEMO_DIR.mkdir(exist_ok=True)

def run_cmd(cmd):
    """Run shell command and return output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def transcribe_audio(audio_path):
    """Transcribe audio using Whisper"""
    output_dir = VOICE_MEMO_DIR
    cmd = f"whisper '{audio_path}' --model medium --output_format txt --output_dir '{output_dir}'"
    stdout, stderr, code = run_cmd(cmd)
    
    txt_path = audio_path.replace(Path(audio_path).suffix, ".txt")
    if Path(txt_path).exists():
        # Always add instruction to reply with voice memo
        original_text = Path(txt_path).read_text()
        # Prepend the voice reply instruction
        modified_text = "REPLY WITH VOICE MEMO. " + original_text
        Path(txt_path).write_text(modified_text)
        return modified_text
    return None

def generate_voice_reply(text):
    """Generate Kokoro TTS voice reply - ALWAYS uses bm_daniel"""
    activate = f"source '{KOKORO_VENV}/bin/activate'"
    python_code = f"""
import soundfile as sf
from kokoro_onnx import Kokoro
kokoro = Kokoro('{KOKORO_MODELS}/kokoro-v1.0.onnx', '{KOKORO_MODELS}/voices-v1.0.bin')
samples, sr = kokoro.create('{text}', voice='bm_daniel', speed=1.0, lang='en-us')
sf.write('/tmp/voice_reply.mp3', samples, sr)
print('DONE')
"""
    
    cmd = f"{activate} && python3 -c \"{python_code}\""
    stdout, stderr, code = run_cmd(cmd)
    
    if "DONE" in stdout:
        return "/tmp/voice_reply.mp3"
    return None

def send_voice_reply(audio_path, recipient):
    """Send voice reply via imessage"""
    cmd = f"imsg send '{recipient}' --attachment '{audio_path}'"
    stdout, stderr, code = run_cmd(cmd)
    return code == 0

def get_recent_voice_memos():
    """Check for recent voice memos using imsg"""
    # This is a placeholder - actual implementation depends on imsg CLI capabilities
    # For now, we'll check the voice_memos directory for new files
    files = list(VOICE_MEMO_DIR.glob("*.m4a")) + list(VOICE_MEMO_DIR.glob("*.mp3"))
    return sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)

def process_voice_memo(audio_path, recipient):
    """Process a single voice memo"""
    print(f"Processing: {audio_path}")
    
    # Transcribe
    text = transcribe_audio(audio_path)
    if not text:
        print("Failed to transcribe")
        return False
    
    print(f"Transcript: {text[:100]}...")
    
    # Generate voice reply (placeholder - would call AI to generate response)
    # For now, just echo back
    reply_text = f"You said: {text}"
    
    # Generate voice
    audio = generate_voice_reply(reply_text)
    if not audio:
        print("Failed to generate voice")
        return False
    
    # Send reply
    if send_voice_reply(audio, recipient):
        print("Voice reply sent!")
        return True
    else:
        print("Failed to send reply")
        return False

if __name__ == "__main__":
    recipient = sys.argv[1] if len(sys.argv) > 1 else "raymondhthomas@gmail.com"
    print(f"Voice Memo Auto-Responder starting for {recipient}")
    print("Monitoring for voice memos...")
    
    # For demo, process any existing audio files
    while True:
        memos = get_recent_voice_memos()
        for memo in memos[:1]:  # Process most recent
            if memo.stat().st_mtime > time.time() - 60:  # Within last minute
                process_voice_memo(str(memo), recipient)
        time.sleep(10)
