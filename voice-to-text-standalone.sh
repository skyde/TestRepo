#!/bin/bash
#
# Voice to Text - Standalone Shell Script
#
# Records audio from microphone, transcribes using Google Cloud Speech-to-Text,
# and types the result at the cursor position.
#
# Requirements:
#   - sox (brew install sox)
#   - curl (built-in on macOS)
#
# Setup:
#   1. Set your Google Cloud API key: export GOOGLE_SPEECH_API_KEY="your-key"
#   2. Run this script to start recording
#   3. Press Ctrl+C to stop and transcribe
#
# For hotkey support, use with Hammerspoon, Karabiner, or BetterTouchTool
#

set -e

# Configuration
RECORDING_FILE="/tmp/voice_recording_$$.wav"
API_KEY="${GOOGLE_SPEECH_API_KEY:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

cleanup() {
    rm -f "$RECORDING_FILE"
}
trap cleanup EXIT

log() {
    echo -e "${GREEN}[VoiceToText]${NC} $1"
}

error() {
    echo -e "${RED}[Error]${NC} $1" >&2
}

warn() {
    echo -e "${YELLOW}[Warning]${NC} $1"
}

# Check dependencies
check_dependencies() {
    if ! command -v rec &> /dev/null; then
        error "sox is required but not installed."
        echo "Install with: brew install sox"
        exit 1
    fi

    if ! command -v curl &> /dev/null; then
        error "curl is required but not installed."
        exit 1
    fi
}

# Check API key
check_api_key() {
    if [[ -z "$API_KEY" ]]; then
        error "Google Cloud API key not set."
        echo "Set it with: export GOOGLE_SPEECH_API_KEY=\"your-key\""
        echo "Or pass as argument: $0 --api-key YOUR_KEY"
        exit 1
    fi
}

# Record audio
record_audio() {
    log "Recording... Press Ctrl+C to stop"

    # Show recording indicator in terminal
    echo -e "${RED}🔴 RECORDING${NC}"

    # Record at 16kHz mono for Google Speech API
    rec -r 16000 -c 1 -b 16 "$RECORDING_FILE" 2>/dev/null || true

    echo -e "${GREEN}✓ Recording stopped${NC}"
}

# Transcribe audio
transcribe_audio() {
    log "Transcribing..."

    if [[ ! -f "$RECORDING_FILE" ]]; then
        error "Recording file not found"
        exit 1
    fi

    # Check file size (empty recording)
    local file_size=$(stat -f%z "$RECORDING_FILE" 2>/dev/null || stat --format=%s "$RECORDING_FILE" 2>/dev/null)
    if [[ "$file_size" -lt 1000 ]]; then
        warn "Recording too short"
        exit 0
    fi

    # Base64 encode
    local audio_content=$(base64 < "$RECORDING_FILE")

    # Create request JSON
    local request_json=$(cat <<EOF
{
  "config": {
    "encoding": "LINEAR16",
    "sampleRateHertz": 16000,
    "languageCode": "en-US",
    "enableAutomaticPunctuation": true,
    "model": "latest_long"
  },
  "audio": {
    "content": "$audio_content"
  }
}
EOF
)

    # Call API
    local response=$(curl -s -X POST \
        "https://speech.googleapis.com/v1/speech:recognize?key=${API_KEY}" \
        -H "Content-Type: application/json" \
        -d "$request_json")

    # Check for errors
    if echo "$response" | grep -q '"error"'; then
        local error_msg=$(echo "$response" | grep -o '"message"[^,]*' | head -1 | sed 's/"message": *"//;s/"$//')
        error "API Error: $error_msg"
        exit 1
    fi

    # Extract transcript
    local transcript=$(echo "$response" | \
        grep -o '"transcript"[^,]*' | \
        head -1 | \
        sed 's/"transcript": *"//;s/"$//' | \
        sed 's/\\n/ /g')

    if [[ -n "$transcript" ]]; then
        echo "$transcript"
    fi
}

# Type text at cursor using clipboard method
type_text() {
    local text="$1"

    if [[ -z "$text" ]]; then
        warn "No text to type"
        return
    fi

    log "Typing text at cursor..."

    # Save current clipboard
    local old_clipboard=$(pbpaste 2>/dev/null || echo "")

    # Set text to clipboard
    echo -n "$text" | pbcopy

    # Simulate Cmd+V using osascript
    osascript -e 'tell application "System Events" to keystroke "v" using command down'

    # Restore clipboard after a delay
    (sleep 0.5 && echo -n "$old_clipboard" | pbcopy) &

    log "Done!"
}

# Main
main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --api-key)
                API_KEY="$2"
                shift 2
                ;;
            --help|-h)
                echo "Usage: $0 [--api-key KEY]"
                echo ""
                echo "Records audio and transcribes using Google Cloud Speech-to-Text."
                echo "Transcribed text is typed at the current cursor position."
                echo ""
                echo "Options:"
                echo "  --api-key KEY    Google Cloud API key"
                echo "  --help, -h       Show this help"
                echo ""
                echo "Environment:"
                echo "  GOOGLE_SPEECH_API_KEY    API key (alternative to --api-key)"
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    check_dependencies
    check_api_key

    # Record
    record_audio

    # Transcribe
    local transcript=$(transcribe_audio)

    if [[ -n "$transcript" ]]; then
        log "Transcript: $transcript"
        type_text "$transcript"
    else
        warn "No speech detected"
    fi
}

main "$@"
