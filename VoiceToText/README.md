# Voice to Text for macOS

A simple macOS menu bar app that records your voice and transcribes it to text using Google Cloud Speech-to-Text API, then types the text at your cursor position.

## Features

- **Menu Bar App**: Lives in your menu bar for quick access
- **Global Hotkey**: Press `Cmd+Shift+R` to start/stop recording from anywhere
- **Auto-Type**: Automatically types transcribed text at your cursor position
- **Google Cloud Speech-to-Text**: High-quality transcription using Google's API
- **Clipboard Support**: Copy transcriptions to clipboard

## Requirements

- macOS 13.0 (Ventura) or later
- Xcode 15+ or Swift 5.9+ (for building)
- Google Cloud account with Speech-to-Text API enabled

## Setup

### 1. Get a Google Cloud API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Cloud Speech-to-Text API**:
   - Go to "APIs & Services" > "Library"
   - Search for "Cloud Speech-to-Text API"
   - Click "Enable"
4. Create an API key:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "API Key"
   - Copy the API key

### 2. Build the App

```bash
cd VoiceToText
swift build -c release
```

The built executable will be at `.build/release/VoiceToText`

### 3. Create an App Bundle (Optional but Recommended)

For a proper macOS app with icon and permissions:

```bash
# Create app bundle structure
mkdir -p VoiceToText.app/Contents/MacOS
mkdir -p VoiceToText.app/Contents/Resources

# Copy executable
cp .build/release/VoiceToText VoiceToText.app/Contents/MacOS/

# Copy Info.plist
cp Sources/VoiceToText/Info.plist VoiceToText.app/Contents/
```

### 4. Grant Permissions

The app requires two permissions:

#### Microphone Access
- When you first run the app, macOS will prompt you for microphone access
- Or go to: System Preferences > Privacy & Security > Microphone

#### Accessibility Access (for typing)
- Go to: System Preferences > Privacy & Security > Accessibility
- Add VoiceToText to the list and enable it
- This is required to type text at your cursor position

## Usage

1. **Launch the app** - A microphone icon will appear in your menu bar
2. **Configure API key** - Click the icon and go to Settings to enter your Google Cloud API key
3. **Start recording** - Either:
   - Click the menu bar icon and click "Start Recording"
   - Press `Cmd+Shift+R` from anywhere
4. **Stop recording** - Press `Cmd+Shift+R` again or click "Stop Recording"
5. **Text appears** - The transcribed text will be typed at your current cursor position

## Settings

- **Google Cloud API Key**: Your API key for Speech-to-Text
- **Auto-type after transcription**: Toggle whether text is automatically typed

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Cmd+Shift+R` | Start/Stop recording |

## Troubleshooting

### "API key required" error
Make sure you've entered your Google Cloud API key in Settings.

### Text not typing at cursor
1. Make sure Accessibility access is granted
2. Check System Preferences > Privacy & Security > Accessibility
3. Try removing and re-adding the app

### No audio recorded
1. Check microphone permissions in System Preferences
2. Make sure your microphone is working
3. Try a different audio input device

### API errors
1. Verify your API key is correct
2. Check that the Speech-to-Text API is enabled in Google Cloud Console
3. Check your Google Cloud billing/quota

## Privacy

- Audio is recorded locally and sent directly to Google Cloud
- Recordings are deleted immediately after transcription
- API keys are stored in macOS User Defaults (local storage)

## Building with Xcode

If you prefer using Xcode:

1. Generate an Xcode project:
   ```bash
   swift package generate-xcodeproj
   ```

2. Open `VoiceToText.xcodeproj`

3. Build and run

## License

MIT License
