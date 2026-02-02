import SwiftUI
import AppKit
import Carbon.HIToolbox

class AppDelegate: NSObject, NSApplicationDelegate {
    private var statusItem: NSStatusItem!
    private var popover: NSPopover!
    private var recordingManager: RecordingManager!
    private var eventMonitor: Any?

    func applicationDidFinishLaunching(_ notification: Notification) {
        // Create the recording manager
        recordingManager = RecordingManager()

        // Create the status bar item
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)

        if let button = statusItem.button {
            button.image = NSImage(systemSymbolName: "mic.fill", accessibilityDescription: "Voice to Text")
            button.action = #selector(togglePopover)
            button.target = self
        }

        // Create the popover
        popover = NSPopover()
        popover.contentSize = NSSize(width: 320, height: 400)
        popover.behavior = .transient
        popover.contentViewController = NSHostingController(
            rootView: ContentView(recordingManager: recordingManager)
        )

        // Register global hotkey (Cmd+Shift+R)
        registerGlobalHotkey()

        // Request microphone permission
        requestMicrophonePermission()

        // Request accessibility permission for typing
        requestAccessibilityPermission()

        print("VoiceToText started. Click the mic icon or press Cmd+Shift+R to record.")
    }

    private func requestMicrophonePermission() {
        switch AVCaptureDevice.authorizationStatus(for: .audio) {
        case .authorized:
            print("Microphone access already authorized")
        case .notDetermined:
            AVCaptureDevice.requestAccess(for: .audio) { granted in
                if granted {
                    print("Microphone access granted")
                } else {
                    print("Microphone access denied")
                }
            }
        case .denied, .restricted:
            print("Microphone access denied or restricted. Please enable in System Preferences.")
        @unknown default:
            break
        }
    }

    private func requestAccessibilityPermission() {
        let options = [kAXTrustedCheckOptionPrompt.takeUnretainedValue() as String: true]
        let trusted = AXIsProcessTrustedWithOptions(options as CFDictionary)
        if !trusted {
            print("Accessibility access needed for typing. Please enable in System Preferences > Privacy & Security > Accessibility")
        }
    }

    private func registerGlobalHotkey() {
        // Monitor for Cmd+Shift+R globally
        eventMonitor = NSEvent.addGlobalMonitorForEvents(matching: .keyDown) { [weak self] event in
            if event.modifierFlags.contains([.command, .shift]) && event.keyCode == 15 { // 15 = R key
                DispatchQueue.main.async {
                    self?.recordingManager.toggleRecording()
                }
            }
        }

        // Also monitor locally when app is focused
        NSEvent.addLocalMonitorForEvents(matching: .keyDown) { [weak self] event in
            if event.modifierFlags.contains([.command, .shift]) && event.keyCode == 15 {
                DispatchQueue.main.async {
                    self?.recordingManager.toggleRecording()
                }
                return nil
            }
            return event
        }
    }

    @objc func togglePopover() {
        if let button = statusItem.button {
            if popover.isShown {
                popover.performClose(nil)
            } else {
                popover.show(relativeTo: button.bounds, of: button, preferredEdge: .minY)
                NSApp.activate(ignoringOtherApps: true)
            }
        }
    }

    func applicationWillTerminate(_ notification: Notification) {
        if let monitor = eventMonitor {
            NSEvent.removeMonitor(monitor)
        }
    }
}

import AVFoundation
