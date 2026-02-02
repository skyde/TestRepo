import SwiftUI

struct ContentView: View {
    @ObservedObject var recordingManager: RecordingManager
    @State private var showingSettings = false

    var body: some View {
        VStack(spacing: 16) {
            // Header
            HStack {
                Text("Voice to Text")
                    .font(.headline)
                Spacer()
                Button(action: { showingSettings = true }) {
                    Image(systemName: "gear")
                }
                .buttonStyle(.plain)
            }

            Divider()

            // Status indicator
            HStack {
                Circle()
                    .fill(statusColor)
                    .frame(width: 10, height: 10)
                Text(recordingManager.statusMessage)
                    .font(.caption)
                    .foregroundColor(.secondary)
                Spacer()
            }

            // Recording button
            Button(action: {
                recordingManager.toggleRecording()
            }) {
                HStack {
                    Image(systemName: recordingManager.isRecording ? "stop.fill" : "mic.fill")
                    Text(recordingManager.isRecording ? "Stop Recording" : "Start Recording")
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 12)
            }
            .buttonStyle(.borderedProminent)
            .tint(recordingManager.isRecording ? .red : .accentColor)
            .disabled(recordingManager.isProcessing)

            // Keyboard shortcut hint
            Text("Shortcut: ⌘⇧R")
                .font(.caption2)
                .foregroundColor(.secondary)

            // Processing indicator
            if recordingManager.isProcessing {
                HStack {
                    ProgressView()
                        .scaleEffect(0.8)
                    Text("Transcribing...")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }

            // Error message
            if let error = recordingManager.errorMessage {
                HStack {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundColor(.orange)
                    Text(error)
                        .font(.caption)
                        .foregroundColor(.orange)
                }
                .padding(8)
                .background(Color.orange.opacity(0.1))
                .cornerRadius(8)
            }

            // Transcribed text
            if !recordingManager.transcribedText.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Transcription:")
                        .font(.caption)
                        .foregroundColor(.secondary)

                    ScrollView {
                        Text(recordingManager.transcribedText)
                            .font(.body)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .textSelection(.enabled)
                    }
                    .frame(maxHeight: 120)
                    .padding(8)
                    .background(Color(NSColor.textBackgroundColor))
                    .cornerRadius(8)

                    HStack {
                        Button("Copy") {
                            recordingManager.copyToClipboard()
                        }
                        .buttonStyle(.bordered)

                        Button("Type at Cursor") {
                            recordingManager.typeText()
                        }
                        .buttonStyle(.bordered)
                    }
                }
            }

            Spacer()

            // Footer
            HStack {
                Button("Settings...") {
                    showingSettings = true
                }
                .buttonStyle(.link)

                Spacer()

                Button("Quit") {
                    NSApplication.shared.terminate(nil)
                }
                .buttonStyle(.link)
                .foregroundColor(.red)
            }
            .font(.caption)
        }
        .padding()
        .frame(width: 300, height: 380)
        .sheet(isPresented: $showingSettings) {
            SettingsView()
        }
    }

    private var statusColor: Color {
        if recordingManager.isRecording {
            return .red
        } else if recordingManager.isProcessing {
            return .orange
        } else if recordingManager.errorMessage != nil {
            return .yellow
        } else {
            return .green
        }
    }
}
