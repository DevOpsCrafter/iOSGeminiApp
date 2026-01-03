// ContentView.swift – SwiftUI UI with a single button
import SwiftUI
import PhotosUI

struct ContentView: View {
    @State private var showingImagePicker = false
    @State private var selectedImage: UIImage?
    @State private var isSharing = false
    @State private var statusMessage = ""

    var body: some View {
        VStack(spacing: 30) {
            if let img = selectedImage {
                Image(uiImage: img)
                    .resizable()
                    .scaledToFit()
                    .frame(maxHeight: 300)
            } else {
                Image(systemName: "photo")
                    .resizable()
                    .scaledToFit()
                    .frame(width: 150, height: 150)
                    .foregroundColor(.secondary)
            }

            Button(action: generateAndShare) {
                Text("Generate & Post")
                    .font(.title2)
                    .bold()
                    .padding()
                    .frame(maxWidth: .infinity)
                    .background(Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(12)
            }
            .disabled(isSharing)

            if !statusMessage.isEmpty {
                Text(statusMessage)
                    .foregroundColor(.gray)
                    .multilineTextAlignment(.center)
            }
        }
        .padding()
        // Correct placement of .sheet modifier
        .sheet(isPresented: $showingImagePicker) {
            PhotoPicker(image: $selectedImage,
                        isPresented: $showingImagePicker,
                        statusMessage: $statusMessage)
        }
    }

    // MARK: – Core Flow
    func generateAndShare() {
        statusMessage = "Opening Gemini app…"
        // 1️⃣ Open Gemini app via URL scheme (if supported). If not, user manually opens it.
        if let url = URL(string: "gemini://") {
            UIApplication.shared.open(url, options: [:]) { success in
                if success {
                    // Give the user a moment to generate & save the image.
                    DispatchQueue.main.asyncAfter(deadline: .now() + 5) {
                        // 2️⃣ Present Photo Picker to let user select the newly saved image.
                        showingImagePicker = true
                    }
                } else {
                    statusMessage = "Could not open Gemini app. Please open it manually, generate an image, and save it to Photos."
                }
            }
        } else {
            statusMessage = "Gemini URL scheme not available. Please open Gemini app manually."
        }
    }
}

// MARK: – Photo Picker Wrapper
struct PhotoPicker: UIViewControllerRepresentable {
    @Binding var image: UIImage?
    @Binding var isPresented: Bool
    @Binding var statusMessage: String

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    func makeUIViewController(context: Context) -> PHPickerViewController {
        var config = PHPickerConfiguration(photoLibrary: .shared())
        config.filter = .images
        config.selectionLimit = 1
        let picker = PHPickerViewController(configuration: config)
        picker.delegate = context.coordinator
        return picker
    }

    func updateUIViewController(_ uiViewController: PHPickerViewController, context: Context) {}

    class Coordinator: NSObject, PHPickerViewControllerDelegate {
        var parent: PhotoPicker
        init(_ parent: PhotoPicker) { self.parent = parent }
        func picker(_ picker: PHPickerViewController, didFinishPicking results: [PHPickerResult]) {
            parent.isPresented = false
            guard let provider = results.first?.itemProvider, provider.canLoadObject(ofClass: UIImage.self) else {
                parent.statusMessage = "No image selected."
                return
            }
            provider.loadObject(ofClass: UIImage.self) { (obj, err) in
                DispatchQueue.main.async {
                    if let img = obj as? UIImage {
                        self.parent.image = img
                        // 3️⃣ Share to Instagram
                        InstagramSharer.share(image: img)
                    } else {
                        self.parent.statusMessage = "Failed to load image."
                    }
                }
            }
        }
    }
}

// MARK: – Instagram Sharing Helper
struct InstagramSharer {
    static func share(image: UIImage) {
        // Save image to temporary file (required for UIActivityViewController)
        let tmpURL = FileManager.default.temporaryDirectory.appendingPathComponent("gemini_image.jpg")
        do {
            try image.jpegData(compressionQuality: 0.9)?.write(to: tmpURL)
        } catch {
            // In a real app you would surface an alert.
            return
        }
        // Build caption with exactly five hashtags
        let caption = "#gemini #aiart #creative #instapost #free"
        // Present share sheet limited to Instagram
        let activityVC = UIActivityViewController(activityItems: [tmpURL, caption], applicationActivities: nil)
        activityVC.excludedActivityTypes = [.postToTwitter, .postToFacebook, .mail, .message, .assignToContact]
        // Find topmost view controller
        if let root = UIApplication.shared.windows.first?.rootViewController {
            root.present(activityVC, animated: true, completion: nil)
        }
    }
}

// MARK: – App Entry Point
@main
struct iOSGeminiApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
