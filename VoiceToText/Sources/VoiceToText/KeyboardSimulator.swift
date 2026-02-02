import Foundation
import Carbon.HIToolbox
import AppKit

class KeyboardSimulator {
    /// Types text at the current cursor position using CGEvents
    func typeText(_ text: String) {
        // Use the clipboard method as it's more reliable for special characters
        typeUsingClipboard(text)
    }

    /// Types text by temporarily using the clipboard and pasting
    private func typeUsingClipboard(_ text: String) {
        let pasteboard = NSPasteboard.general

        // Save current clipboard content
        let previousContents = pasteboard.string(forType: .string)

        // Set our text to clipboard
        pasteboard.clearContents()
        pasteboard.setString(text, forType: .string)

        // Small delay to ensure clipboard is updated
        usleep(50000) // 50ms

        // Simulate Cmd+V
        simulatePaste()

        // Restore previous clipboard after a delay
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
            if let previous = previousContents {
                pasteboard.clearContents()
                pasteboard.setString(previous, forType: .string)
            }
        }
    }

    /// Simulates Cmd+V keystroke
    private func simulatePaste() {
        let source = CGEventSource(stateID: .combinedSessionState)

        // Key code for 'V' is 9
        let vKeyCode: CGKeyCode = 9

        // Create key down event with Command modifier
        guard let keyDown = CGEvent(keyboardEventSource: source, virtualKey: vKeyCode, keyDown: true) else {
            print("Failed to create key down event")
            return
        }
        keyDown.flags = .maskCommand

        // Create key up event with Command modifier
        guard let keyUp = CGEvent(keyboardEventSource: source, virtualKey: vKeyCode, keyDown: false) else {
            print("Failed to create key up event")
            return
        }
        keyUp.flags = .maskCommand

        // Post the events
        keyDown.post(tap: .cghidEventTap)
        usleep(10000) // 10ms delay
        keyUp.post(tap: .cghidEventTap)
    }

    /// Alternative method: type character by character using CGEvents
    /// This is slower but doesn't affect the clipboard
    func typeCharacterByCharacter(_ text: String) {
        let source = CGEventSource(stateID: .combinedSessionState)

        for character in text {
            if let keyCode = keyCodeForCharacter(character) {
                let needsShift = characterNeedsShift(character)

                guard let keyDown = CGEvent(keyboardEventSource: source, virtualKey: keyCode, keyDown: true),
                      let keyUp = CGEvent(keyboardEventSource: source, virtualKey: keyCode, keyDown: false) else {
                    continue
                }

                if needsShift {
                    keyDown.flags = .maskShift
                    keyUp.flags = .maskShift
                }

                keyDown.post(tap: .cghidEventTap)
                usleep(5000) // 5ms delay between keystrokes
                keyUp.post(tap: .cghidEventTap)
                usleep(5000)
            } else {
                // For characters we don't have a keycode for, use Unicode input
                typeUnicodeCharacter(character, source: source)
            }
        }
    }

    private func typeUnicodeCharacter(_ character: Character, source: CGEventSource?) {
        guard let event = CGEvent(keyboardEventSource: source, virtualKey: 0, keyDown: true) else { return }

        var unicodeString = [UniChar](String(character).utf16)
        event.keyboardSetUnicodeString(stringLength: unicodeString.count, unicodeString: &unicodeString)
        event.post(tap: .cghidEventTap)

        guard let upEvent = CGEvent(keyboardEventSource: source, virtualKey: 0, keyDown: false) else { return }
        upEvent.post(tap: .cghidEventTap)
    }

    private func keyCodeForCharacter(_ char: Character) -> CGKeyCode? {
        let keyCodeMap: [Character: CGKeyCode] = [
            "a": 0, "s": 1, "d": 2, "f": 3, "h": 4, "g": 5, "z": 6, "x": 7, "c": 8, "v": 9,
            "b": 11, "q": 12, "w": 13, "e": 14, "r": 15, "y": 16, "t": 17, "1": 18, "2": 19,
            "3": 20, "4": 21, "6": 22, "5": 23, "=": 24, "9": 25, "7": 26, "-": 27, "8": 28,
            "0": 29, "]": 30, "o": 31, "u": 32, "[": 33, "i": 34, "p": 35, "l": 37, "j": 38,
            "'": 39, "k": 40, ";": 41, "\\": 42, ",": 43, "/": 44, "n": 45, "m": 46, ".": 47,
            "`": 50, " ": 49, "\n": 36, "\t": 48
        ]

        let lowercaseChar = Character(char.lowercased())
        return keyCodeMap[lowercaseChar]
    }

    private func characterNeedsShift(_ char: Character) -> Bool {
        let shiftCharacters = Set("ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()_+{}|:\"<>?~")
        return shiftCharacters.contains(char)
    }
}
