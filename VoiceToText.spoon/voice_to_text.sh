#!/bin/bash
#
# Voice to Text - Google Cloud Speech-to-Text API
#
# Usage: voice_to_text.sh <audio_file> <api_key>
#
# This script takes a WAV audio file and transcribes it using
# Google Cloud Speech-to-Text API.
#

set -e

AUDIO_FILE="$1"
API_KEY="$2"

if [[ -z "$AUDIO_FILE" ]] || [[ -z "$API_KEY" ]]; then
    echo "Usage: $0 <audio_file> <api_key>" >&2
    exit 1
fi

if [[ ! -f "$AUDIO_FILE" ]]; then
    echo "Error: Audio file not found: $AUDIO_FILE" >&2
    exit 1
fi

# Base64 encode the audio file
AUDIO_CONTENT=$(base64 < "$AUDIO_FILE")

# Create the request JSON
REQUEST_JSON=$(cat <<EOF
{
  "config": {
    "encoding": "LINEAR16",
    "sampleRateHertz": 16000,
    "languageCode": "en-US",
    "enableAutomaticPunctuation": true,
    "model": "latest_long"
  },
  "audio": {
    "content": "$AUDIO_CONTENT"
  }
}
EOF
)

# Call Google Speech-to-Text API
RESPONSE=$(curl -s -X POST \
    "https://speech.googleapis.com/v1/speech:recognize?key=${API_KEY}" \
    -H "Content-Type: application/json" \
    -d "$REQUEST_JSON")

# Check for errors
if echo "$RESPONSE" | grep -q '"error"'; then
    ERROR_MSG=$(echo "$RESPONSE" | grep -o '"message"[^,]*' | head -1 | sed 's/"message": *"//;s/"$//')
    echo "API Error: $ERROR_MSG" >&2
    exit 1
fi

# Extract the transcript
# Using sed/grep for compatibility (no jq dependency)
TRANSCRIPT=$(echo "$RESPONSE" | \
    grep -o '"transcript"[^,]*' | \
    head -1 | \
    sed 's/"transcript": *"//;s/"$//' | \
    sed 's/\\n/ /g')

if [[ -n "$TRANSCRIPT" ]]; then
    echo "$TRANSCRIPT"
else
    # No transcript found (silence or no speech detected)
    echo ""
fi
