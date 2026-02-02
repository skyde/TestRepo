#!/bin/bash

# Build script for VoiceToText macOS app

set -e

echo "Building VoiceToText..."

# Build in release mode
swift build -c release

echo "Build complete!"
echo ""
echo "Creating app bundle..."

# Create app bundle structure
APP_NAME="VoiceToText"
APP_BUNDLE="${APP_NAME}.app"

rm -rf "$APP_BUNDLE"
mkdir -p "$APP_BUNDLE/Contents/MacOS"
mkdir -p "$APP_BUNDLE/Contents/Resources"

# Copy executable
cp ".build/release/${APP_NAME}" "$APP_BUNDLE/Contents/MacOS/"

# Copy Info.plist
cp "Sources/${APP_NAME}/Info.plist" "$APP_BUNDLE/Contents/"

echo "App bundle created: $APP_BUNDLE"
echo ""
echo "To run the app:"
echo "  open $APP_BUNDLE"
echo ""
echo "Or to run directly:"
echo "  ./.build/release/VoiceToText"
echo ""
echo "Don't forget to:"
echo "1. Set your Google Cloud API key in Settings"
echo "2. Grant Microphone access when prompted"
echo "3. Grant Accessibility access in System Preferences"
