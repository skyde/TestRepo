import AVFoundation
import Foundation

class AudioRecorder: NSObject {
    private var audioEngine: AVAudioEngine?
    private var audioFile: AVAudioFile?
    private var recordingURL: URL?

    override init() {
        super.init()
    }

    func startRecording() {
        // Create a temporary file for recording
        let tempDir = FileManager.default.temporaryDirectory
        recordingURL = tempDir.appendingPathComponent("voice_recording_\(UUID().uuidString).wav")

        guard let url = recordingURL else { return }

        audioEngine = AVAudioEngine()
        guard let audioEngine = audioEngine else { return }

        let inputNode = audioEngine.inputNode
        let recordingFormat = inputNode.outputFormat(forBus: 0)

        // Use a format suitable for Google Speech-to-Text (16kHz mono LINEAR16)
        guard let outputFormat = AVAudioFormat(
            commonFormat: .pcmFormatInt16,
            sampleRate: 16000,
            channels: 1,
            interleaved: true
        ) else {
            print("Failed to create output format")
            return
        }

        // Create format converter
        guard let converter = AVAudioConverter(from: recordingFormat, to: outputFormat) else {
            print("Failed to create audio converter")
            return
        }

        do {
            audioFile = try AVAudioFile(
                forWriting: url,
                settings: outputFormat.settings,
                commonFormat: .pcmFormatInt16,
                interleaved: true
            )
        } catch {
            print("Failed to create audio file: \(error)")
            return
        }

        inputNode.installTap(onBus: 0, bufferSize: 4096, format: recordingFormat) { [weak self] buffer, _ in
            guard let self = self,
                  let audioFile = self.audioFile else { return }

            // Calculate output buffer size based on sample rate ratio
            let ratio = outputFormat.sampleRate / recordingFormat.sampleRate
            let outputFrameCapacity = AVAudioFrameCount(Double(buffer.frameLength) * ratio)

            guard let outputBuffer = AVAudioPCMBuffer(
                pcmFormat: outputFormat,
                frameCapacity: outputFrameCapacity
            ) else { return }

            var error: NSError?
            let inputBlock: AVAudioConverterInputBlock = { _, outStatus in
                outStatus.pointee = .haveData
                return buffer
            }

            converter.convert(to: outputBuffer, error: &error, withInputFrom: inputBlock)

            if let error = error {
                print("Conversion error: \(error)")
                return
            }

            do {
                try audioFile.write(from: outputBuffer)
            } catch {
                print("Failed to write audio: \(error)")
            }
        }

        do {
            try audioEngine.start()
            print("Recording started")
        } catch {
            print("Failed to start audio engine: \(error)")
        }
    }

    func stopRecording(completion: @escaping (Data?) -> Void) {
        audioEngine?.stop()
        audioEngine?.inputNode.removeTap(onBus: 0)
        audioFile = nil

        guard let url = recordingURL else {
            completion(nil)
            return
        }

        // Read the audio file and return as data
        do {
            let data = try Data(contentsOf: url)
            // Clean up temp file
            try? FileManager.default.removeItem(at: url)
            completion(data)
        } catch {
            print("Failed to read audio file: \(error)")
            completion(nil)
        }
    }
}
