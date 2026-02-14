#!/usr/bin/env python3
"""
Voice Memo Auto-Responder using imsg watch --json-output
Monitors for incoming voice memos and responds with Kokoro TTS voice
"""

import os
import sys
import json
import subprocess
import threading
from pathlib import Path
from datetime import datetime

# Configuration
WORKSPACE = Path("/Users/raythomas/.openclaw/workspace")
KOKORO_VENV = WORKSPACE / "kokoro-venv"
KOKORO_MODELS = WORKSPACE / "kokoro-models"
RECIPIENT = "raymondhthomas@gmail.com"

# Track processed messages
processed_ids = set()

def run_cmd(cmd, timeout=30):
    """Run shell command with timeout"""
    try:
        result = subprocess.run(
            cmd,  capture_output=True, text=True, timeout=timeout
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
    # Always add instruction FIRST to ensure voice output
    voice_instruction = "REPLY WITH VOICE MEMO. "
    
    # Combine with transcript for AI to process
    full_prompt = voice_instruction + "The user sent this voice memo. Reply conversationally as Jarvis, their helpful assistant: " + transcript
    
    # For now, return a placeholder response
    # In production, this would call OpenClaw's AI API
    # The important thing is the instruction is in the response
    
    # Simple acknowledgment response
    response = f"I heard your voice memo about: {transcript}. Thanks for sending it as a voice memo - I'm replying with voice too!"
    
    return voice_instruction + response

def generate_voice_reply(text):
    """Generate Kokoro TTS voice reply - ALWAYS uses bm_daniel"""
    activate = f"source '{KOKORO_VENV}/bin/activate'"
    
    # Escape quotes for Python
    escaped_text = text.replace('"', '\\"').replace("'", "\\'")
    
    # IMPORTANT: Always use bm_daniel voice - do NOT change this
    python_code = f'''
import soundfile as sf
from kokoro_onnx import Kokoro
kokoro = Kokoro("{KOKORO_MODELS}/kokoro-v1.0.onnx", "{KOKORO_MODELS}/voices-v1.0.bin")
samples, sr = kokoro.create("{escaped_text}", voice="bm_daniel", speed=1.0, lang="en-us")
sf.write("/tmp/voice_reply.mp3", samples, sr)
print("DONE")
'''
    
    cmd = f"{activate} && python3 -c '{python_code}'"
    stdout, stderr, code = run_cmd(cmd, timeout=60)
    
    if "DONE" in stdout or os.path.exists("/tmp/voice_reply.mp3"):
        return "/tmp/voice_reply.mp3"
    return None

def send_message(text, attachment=None):
    """Send message via imsg"""
    if attachment:
        cmd = f'imsg send "{RECIPIENT}" --attachment "{attachment}"'
    else:
        cmd = f'imsg send "{RECIPIENT}" --message "{text}"'
    
    stdout, stderr, code = run_cmd(cmd)
    return code == 0

def process_message(msg_data):
    """Process incoming message"""
    msg_id = msg_data.get("id", "")
    if msg_id in processed_ids:
        return False
    
    # Check if it's a voice memo (has attachment)
    has_audio = False
    for att in msg_data.get("attachments", []):
        if att.get("mimeType", "").startswith("audio/") or \
           any(ext in att.get("filename", "").lower() for ext in [".m4a", ".mp3", ".wav", ".aac"]):
            has_audio = True
            audio_path = att.get("localPath", att.get("url", ""))
            break
    
    if not has_audio:
        return False
    
    print(f"\n📨 Voice memo received: {msg_id}")
    processed_ids.add(msg_id)
    
    # Download attachment if needed
    if audio_path and not os.path.exists(audio_path):
        # Try to download
        cmd = f'imsg history --limit 1 --attachment-download'
        run_cmd(cmd)
    
    if os.path.exists(audio_path):
        # Transcribe
        transcript = transcribe_audio(audio_path)
        if transcript:
            print(f"📝 Transcript: {transcript[:100]}...")
            
            # Generate response
            response_text = generate_ai_response(transcript)
            
            # Generate voice
            voice_path = generate_voice_reply(response_text)
            if voice_path:
                # Send voice reply
                if send_message(response_text, voice_path):
                    print("✅ Voice reply sent!")
                    return True
    
    return False

def watch_messages():
    """Watch for incoming messages using imsg watch --json-output"""
    print(f"🔔 Starting voice memo auto-responder for {RECIPIENT}")
    print("📱 Monitoring for incoming voice memos...")
    
    # Start imsg watch --json-output in background
    process = subprocess.Popen([
        "imsg", "watch", "--chat-id", "1", "--json-output", "--attachments"],
        
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    try:
        for line in process.stdout:
            if not line.strip():
                continue
            
            try:
                msg_data = json.loads(line.strip())
                process_message(msg_data)
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON parse error: {e}")
                continue
                
    except KeyboardInterrupt:
        print("\n👋 Stopping...")
    finally:
        process.terminate()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        RECIPIENT = sys.argv[1]
    watch_messages()
