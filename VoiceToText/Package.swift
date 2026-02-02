// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "VoiceToText",
    platforms: [
        .macOS(.v13)
    ],
    products: [
        .executable(name: "VoiceToText", targets: ["VoiceToText"])
    ],
    dependencies: [],
    targets: [
        .executableTarget(
            name: "VoiceToText",
            dependencies: [],
            path: "Sources/VoiceToText"
        )
    ]
)
