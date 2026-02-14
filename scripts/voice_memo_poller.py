#!/usr/bin/env python3
"""
Voice Memo Auto-Responder - Simple Polling Version
Checks for new voice memos and responds with Kokoro TTS voice
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime, timezone

# Configuration
WORKSPACE = Path("/Users/raythomas/.openclaw/workspace")
KOKORO_VENV = WORKSPACE / "kokoro-venv"
KOKORO_MODELS = WORKSPACE / "kokoro-models"
RECIPIENT = "raymondhthomas@gmail.com"
CHAT_ID = "1"  # Ray's chat

# Track processed messages
processed_ids = set()
last_check = datetime.now(timezone.utc)

def run_cmd(cmd, timeout=30):
    """Run shell command with timeout"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "Timeout", -1

def transcribe_audio(audio_path):
    """Transcribe audio using Whisper"""
    output_dir = WORKSPACE / "voice_memos"
    output_dir.mkdir(exist_ok=True)
    
    cmd = f"whisper '{audio_path}' --model medium --output_format txt --output_dir '{output_dir}'"
    stdout, stderr, code = run_cmd(cmd)
    
    txt_path = Path(audio_path).with_suffix(".txt")
    if txt_path.exists():
        # Always add instruction to reply with voice memo
        original_text = txt_path.read_text()
        # Prepend the voice reply instruction
        modified_text = "REPLY WITH VOICE MEMO. " + original_text
        txt_path.write_text(modified_text)
        return modified_text
    return None

def generate_ai_response(transcript):
    """Generate AI response - prepends voice instruction to ensure voice output"""
    # Simple acknowledgment response
    response = f"I heard your message. Thanks for sending a voice memo!"
    return response

def generate_voice_reply(text):
    """Generate Kokoro TTS voice reply - ALWAYS uses bm_daniel"""
    # Remove instruction from audio
    clean_text = text.replace("REPLY WITH VOICE MEMO. ", "").replace("REPLY WITH VOICE MEMO", "")
    
    activate = f"source '{KOKORO_VENV}/bin/activate'"
    
    # Escape quotes for Python
    escaped_text = clean_text.replace('"', '\\"').replace("'", "\\'")
    
    # IMPORTANT: Always use bm_daniel voice - do NOT change this
    python_code = f'''
import soundfile as sf
from kokoro_onnx import Kokoro
kokoro = Kokoro("{KOKORO_MODELS}/kokoro-v1.0.onnx", "{KOKORO_MODELS}/voices-v1.0.bin")
samples, sr = kokoro.create("{escaped_text}", voice="bm_daniel", speed=1.0, lang="en-us")
sf.write("/tmp/voice_reply.wav", samples, sr)
print("DONE")
'''
    
    cmd = f"{activate} && python3 -c '{python_code}'"
    stdout, stderr, code = run_cmd(cmd, timeout=60)
    
    # Convert to MP3 for iMessage compatibility
    os.system('ffmpeg -i /tmp/voice_reply.wav -vn -acodec libmp3lame -q:a 2 /tmp/voice_reply.mp3 -y 2>/dev/null')
    
    if "DONE" in stdout or os.path.exists("/tmp/voice_reply.mp3"):
        return "/tmp/voice_reply.mp3"
    return None

def send_message(text, attachment=None):
    """Send message via imsg - audio only"""
    if attachment:
        # Send audio only, no text message
        cmd = f'imsg send --to "{RECIPIENT}" --file "{attachment}"'
    else:
        cmd = f'imsg send "{RECIPIENT}" --message ""'
    
    stdout, stderr, code = run_cmd(cmd)
    return code == 0

def check_for_voice_memos():
    """Check for new voice memos using imsg history"""
    global last_check
    
    # Get recent messages
    stdout, stderr, code = run_cmd(f"imsg history --chat-id {CHAT_ID} --limit 5 --attachments --json-output", timeout=10)
    
    if not stdout:
        return []
    
    messages = []
    try:
        # Parse JSON response
        for line in stdout.strip().split('\n'):
            if line.strip():
                msg = json.loads(line)
                messages.append(msg)
    except json.JSONDecodeError:
        pass
    
    # Filter for voice memos
    voice_memos = []
    for msg in messages:
        msg_time = datetime.fromisoformat(msg.get("created_at", "").replace("Z", "+00:00"))
        if msg_time > last_check:
            # Check for audio attachments
            for att in msg.get("attachments", []):
                mime = att.get("mime_type", "").lower()
                transfer_name = att.get("transfer_name", "").lower()
                # Check mime type or audio file extensions
                if mime.startswith("audio/") or any(ext in transfer_name for ext in [".m4a", ".mp3", ".wav", ".aac", ".caf", "audio"]):
                    voice_memos.append({
                        "id": msg.get("id"),
                        "text": msg.get("text", ""),
                        "attachment": att
                    })
                    print(f"📨 New voice memo: {msg.get('id')}")
    
    if messages:
        # Update last_check to most recent message time
        latest = messages[0].get("created_at", "")
        if latest:
            last_check = datetime.fromisoformat(latest.replace("Z", "+00:00")).astimezone(timezone.utc)
    
    return voice_memos

def process_voice_memo(memo):
    """Process a voice memo"""
    msg_id = memo["id"]
    if msg_id in processed_ids:
        return False
    
    processed_ids.add(msg_id)
    print(f"Processing: {msg_id}")
    
    # Download attachment if needed
    att = memo["attachment"]
    audio_path = att.get("original_path", "")
    
    if not audio_path or not os.path.exists(audio_path):
        print("Attachment not found locally")
        return False
    
    # Transcribe
    transcript = transcribe_audio(audio_path)
    if not transcript:
        print("Failed to transcribe")
        return False
    
    print(f"📝 {transcript[:80]}...")
    
    # Generate response (includes voice instruction for AI)
    response_text = generate_ai_response(transcript)
    
    # Generate voice
    voice_path = generate_voice_reply(response_text)
    if not voice_path:
        print("Failed to generate voice")
        return False
    
    # Send voice reply ONLY (no text)
    if send_message(None, voice_path):
        print("✅ Voice reply sent!")
        return True
    else:
        print("Failed to send")
        return False

def main():
    """Main polling loop"""
    print(f"🔔 Voice Memo Auto-Responder Starting")
    print(f"👤 Monitoring: {RECIPIENT}")
    print(f"🔄 Polling every 10 seconds...")
    print("-" * 40)
    
    while True:
        try:
            memos = check_for_voice_memos()
            for memo in reversed(memos):
                process_voice_memo(memo)
        except Exception as e:
            print(f"⚠️ Error: {e}")
        
        time.sleep(10)

if __name__ == "__main__":
    main()
