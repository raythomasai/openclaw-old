#!/bin/bash
# Daily Joke - Noon CT
# Fetches random joke and sends via iMessage

# Try joke APIs
JOKE=$(curl -s "https://icanhazdadjoke.com/" \
  -H "Accept: text/plain" \
  --max-time 10 2>/dev/null | head -5)

if [ -z "$JOKE" ] || [ "$JOKE" = "Too Many Requests" ]; then
  JOKE="Why did the programmer quit his job? Because he didn't get arrays."
fi

imsg send --to "raymondhthomas@gmail.com" --text "😂 Daily Joke: $JOKE"
