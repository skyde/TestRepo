import Foundation

enum SpeechServiceError: LocalizedError {
    case invalidURL
    case noData
    case apiError(String)
    case decodingError
    case noTranscription

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid API URL"
        case .noData:
            return "No data received from API"
        case .apiError(let message):
            return "API Error: \(message)"
        case .decodingError:
            return "Failed to decode API response"
        case .noTranscription:
            return "No transcription returned"
        }
    }
}

class GoogleSpeechService {
    private let apiEndpoint = "https://speech.googleapis.com/v1/speech:recognize"

    func transcribe(audioData: Data, apiKey: String) async throws -> String {
        guard var urlComponents = URLComponents(string: apiEndpoint) else {
            throw SpeechServiceError.invalidURL
        }

        urlComponents.queryItems = [URLQueryItem(name: "key", value: apiKey)]

        guard let url = urlComponents.url else {
            throw SpeechServiceError.invalidURL
        }

        // Prepare the request body
        let audioContent = audioData.base64EncodedString()

        let requestBody: [String: Any] = [
            "config": [
                "encoding": "LINEAR16",
                "sampleRateHertz": 16000,
                "languageCode": "en-US",
                "enableAutomaticPunctuation": true,
                "model": "latest_long"
            ],
            "audio": [
                "content": audioContent
            ]
        ]

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(withJSONObject: requestBody)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw SpeechServiceError.noData
        }

        if httpResponse.statusCode != 200 {
            if let errorJson = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let error = errorJson["error"] as? [String: Any],
               let message = error["message"] as? String {
                throw SpeechServiceError.apiError(message)
            }
            throw SpeechServiceError.apiError("HTTP \(httpResponse.statusCode)")
        }

        guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw SpeechServiceError.decodingError
        }

        // Parse the response
        guard let results = json["results"] as? [[String: Any]],
              let firstResult = results.first,
              let alternatives = firstResult["alternatives"] as? [[String: Any]],
              let firstAlternative = alternatives.first,
              let transcript = firstAlternative["transcript"] as? String else {

            // Check if there are no results (silence)
            if json["results"] == nil || (json["results"] as? [[String: Any]])?.isEmpty == true {
                return ""
            }

            throw SpeechServiceError.noTranscription
        }

        return transcript
    }
}
