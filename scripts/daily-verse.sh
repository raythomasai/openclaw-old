#!/bin/bash
# Daily Bible Verse - 8:15 AM CT
# Fetches verse of the day from labs.bible.org and sends via iMessage

VERSE=$(curl -s "https://labs.bible.org/api/?passage=votd&formatting=plain")
SOURCE=$(curl -s "https://labs.bible.org/api/?passage=votd&formatting=plain" | grep -o '^[A-Za-z]* [0-9]*:[0-9]*')

imsg send --to "raymondhthomas@gmail.com" --text "📖 Daily Bible Verse ($SOURCE): $VERSE"
