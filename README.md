# Voice to Text for macOS

Record your voice and transcribe it to text using Google Cloud Speech-to-Text API, then type the result at your cursor position.

## Options

There are three ways to use this tool:

| Method | Best For | Hotkey Support |
|--------|----------|----------------|
| **Hammerspoon (Recommended)** | Regular use, power users | Built-in global hotkey |
| **Standalone Shell Script** | Quick testing, minimal setup | Use with Karabiner/BTT |
| **Swift App** | Native macOS experience | Built-in global hotkey |

---

## Option 1: Hammerspoon (Recommended)

The easiest way to use voice-to-text with full hotkey support.

### Prerequisites

```bash
# Install Hammerspoon
brew install --cask hammerspoon

# Install sox for audio recording
brew install sox
```

### Setup

1. **Copy the Spoon to Hammerspoon:**
   ```bash
   cp -r VoiceToText.spoon ~/.hammerspoon/Spoons/
   ```

2. **Add to your `~/.hammerspoon/init.lua`:**
   ```lua
   -- Load VoiceToText
   hs.loadSpoon("VoiceToText")

   -- Set your Google Cloud API key
   spoon.VoiceToText:setApiKey("YOUR_GOOGLE_CLOUD_API_KEY")

   -- Start with default hotkey (Cmd+Shift+R)
   spoon.VoiceToText:start()
   ```

3. **Reload Hammerspoon** (click menubar icon → Reload Config)

### Usage

- Press `Cmd+Shift+R` to start recording
- Press `Cmd+Shift+R` again to stop and transcribe
- Text is automatically typed at your cursor position

### Custom Hotkey

```lua
spoon.VoiceToText:setApiKey("YOUR_KEY")
spoon.VoiceToText:bindHotkeys({
    toggle = {{"ctrl", "alt"}, "r"}  -- Ctrl+Alt+R
})
```

---

## Option 2: Standalone Shell Script

For quick testing or use with other hotkey tools (Karabiner, BetterTouchTool).

### Prerequisites

```bash
# Install sox for audio recording
brew install sox
```

### Setup

```bash
# Set your API key
export GOOGLE_SPEECH_API_KEY="YOUR_GOOGLE_CLOUD_API_KEY"

# Add to your ~/.zshrc or ~/.bashrc to persist
echo 'export GOOGLE_SPEECH_API_KEY="YOUR_KEY"' >> ~/.zshrc
```

### Usage

```bash
# Run the script
./voice-to-text-standalone.sh

# Recording starts immediately
# Press Ctrl+C to stop and transcribe
```

### With Karabiner-Elements

Create a hotkey that runs the script:

```json
{
  "type": "basic",
  "from": { "key_code": "r", "modifiers": { "mandatory": ["command", "shift"] } },
  "to": [{ "shell_command": "/path/to/voice-to-text-standalone.sh" }]
}
```

---

## Option 3: Swift App

A native macOS menu bar app. See [VoiceToText/README.md](VoiceToText/README.md) for details.

```bash
cd VoiceToText
./build.sh
open VoiceToText.app
```

---

## Google Cloud API Setup

All methods require a Google Cloud API key:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable **Cloud Speech-to-Text API**:
   - APIs & Services → Library → Search "Cloud Speech-to-Text API" → Enable
4. Create an API key:
   - APIs & Services → Credentials → Create Credentials → API Key
5. Copy the key

### API Key Security

For corporate use, you may want to restrict your API key:
- Go to Credentials → Click your API key → Add restrictions
- Restrict to "Cloud Speech-to-Text API" only

---

## Permissions Required

### Microphone Access
macOS will prompt for microphone access on first use.

### Accessibility (for auto-typing)
Go to: **System Preferences → Privacy & Security → Accessibility**
- Add Terminal (for shell script)
- Add Hammerspoon (for Hammerspoon method)
- Or add VoiceToText.app (for Swift app)

---

## Troubleshooting

### "sox: command not found"
```bash
brew install sox
```

### Text not typing at cursor
1. Grant Accessibility permission in System Preferences
2. Restart the app/script after granting permission

### API errors
1. Verify your API key is correct
2. Check Speech-to-Text API is enabled in Google Cloud Console
3. Check your billing/quota in Google Cloud

### Recording too quiet
```bash
# List audio devices
sox -V6 -n -d trim 0 0 2>&1 | grep "Input"

# Use a specific device
rec -d "USB Microphone" -r 16000 -c 1 output.wav
```

---

## License

MIT License
