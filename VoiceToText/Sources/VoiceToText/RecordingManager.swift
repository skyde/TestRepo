import SwiftUI
import AVFoundation
import Combine

@MainActor
class RecordingManager: ObservableObject {
    @Published var isRecording = false
    @Published var statusMessage = "Ready to record"
    @Published var transcribedText = ""
    @Published var isProcessing = false
    @Published var errorMessage: String?

    private var audioRecorder: AudioRecorder?
    private let speechService = GoogleSpeechService()
    private let keyboardSimulator = KeyboardSimulator()

    @AppStorage("googleApiKey") var apiKey: String = ""
    @AppStorage("autoTypeEnabled") var autoTypeEnabled: Bool = true

    init() {
        audioRecorder = AudioRecorder()
    }

    func toggleRecording() {
        if isRecording {
            stopRecording()
        } else {
            startRecording()
        }
    }

    func startRecording() {
        guard !apiKey.isEmpty else {
            errorMessage = "Please set your Google Cloud API key in Settings"
            statusMessage = "API key required"
            return
        }

        errorMessage = nil
        isRecording = true
        statusMessage = "Recording... Press Cmd+Shift+R or click Stop to finish"
        transcribedText = ""

        audioRecorder?.startRecording()
    }

    func stopRecording() {
        isRecording = false
        statusMessage = "Processing..."
        isProcessing = true

        audioRecorder?.stopRecording { [weak self] audioData in
            Task { @MainActor in
                guard let self = self else { return }

                if let data = audioData {
                    await self.processAudio(data)
                } else {
                    self.statusMessage = "Recording failed"
                    self.errorMessage = "Failed to capture audio"
                    self.isProcessing = false
                }
            }
        }
    }

    private func processAudio(_ audioData: Data) async {
        do {
            let text = try await speechService.transcribe(audioData: audioData, apiKey: apiKey)

            self.transcribedText = text
            self.statusMessage = "Transcription complete"

            if autoTypeEnabled && !text.isEmpty {
                // Small delay to ensure focus returns to original app
                try? await Task.sleep(nanoseconds: 100_000_000) // 0.1 seconds
                keyboardSimulator.typeText(text)
                self.statusMessage = "Text typed at cursor"
            }
        } catch {
            self.errorMessage = error.localizedDescription
            self.statusMessage = "Transcription failed"
        }

        self.isProcessing = false
    }

    func copyToClipboard() {
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(transcribedText, forType: .string)
        statusMessage = "Copied to clipboard"
    }

    func typeText() {
        guard !transcribedText.isEmpty else { return }
        keyboardSimulator.typeText(transcribedText)
        statusMessage = "Text typed at cursor"
    }
}
