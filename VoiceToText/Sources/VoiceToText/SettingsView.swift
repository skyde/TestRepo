import SwiftUI

struct SettingsView: View {
    @AppStorage("googleApiKey") private var apiKey: String = ""
    @AppStorage("autoTypeEnabled") private var autoTypeEnabled: Bool = true
    @Environment(\.dismiss) private var dismiss

    @State private var showApiKey = false
    @State private var tempApiKey = ""

    var body: some View {
        VStack(spacing: 20) {
            Text("Settings")
                .font(.title2)
                .fontWeight(.semibold)

            Form {
                Section {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Google Cloud API Key")
                            .font(.headline)

                        HStack {
                            if showApiKey {
                                TextField("Enter your API key", text: $tempApiKey)
                                    .textFieldStyle(.roundedBorder)
                            } else {
                                SecureField("Enter your API key", text: $tempApiKey)
                                    .textFieldStyle(.roundedBorder)
                            }

                            Button(action: { showApiKey.toggle() }) {
                                Image(systemName: showApiKey ? "eye.slash" : "eye")
                            }
                            .buttonStyle(.borderless)
                        }

                        Text("Get your API key from the Google Cloud Console with Speech-to-Text API enabled.")
                            .font(.caption)
                            .foregroundColor(.secondary)

                        Link("Open Google Cloud Console",
                             destination: URL(string: "https://console.cloud.google.com/apis/credentials")!)
                            .font(.caption)
                    }
                }

                Section {
                    VStack(alignment: .leading, spacing: 8) {
                        Toggle("Auto-type after transcription", isOn: $autoTypeEnabled)

                        Text("When enabled, transcribed text will automatically be typed at your cursor position.")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }

                Section {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Permissions")
                            .font(.headline)

                        Text("This app requires:")
                            .font(.caption)
                            .foregroundColor(.secondary)

                        VStack(alignment: .leading, spacing: 4) {
                            Label("Microphone access for recording", systemImage: "mic.fill")
                            Label("Accessibility for typing text", systemImage: "keyboard")
                        }
                        .font(.caption)

                        Button("Open System Preferences") {
                            if let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy") {
                                NSWorkspace.shared.open(url)
                            }
                        }
                        .buttonStyle(.link)
                        .font(.caption)
                    }
                }
            }
            .formStyle(.grouped)

            HStack {
                Button("Cancel") {
                    dismiss()
                }
                .keyboardShortcut(.cancelAction)

                Spacer()

                Button("Save") {
                    apiKey = tempApiKey
                    dismiss()
                }
                .keyboardShortcut(.defaultAction)
                .buttonStyle(.borderedProminent)
            }
        }
        .padding()
        .frame(width: 450, height: 450)
        .onAppear {
            tempApiKey = apiKey
        }
    }
}
