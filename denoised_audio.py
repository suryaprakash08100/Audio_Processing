import noisereduce as nr
import librosa
import soundfile as sf
import sys
import os

def denoise_file(input_path, output_path=None):
    if not os.path.exists(input_path):
        print(f"File not found: {input_path}")
        return

    print(f"Loading {input_path}")
    y, sr = librosa.load(input_path, sr=None)

    print("Applying noise reduction...")
    reduced_noise = nr.reduce_noise(y=y, sr=sr)

    if not output_path:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_denoised{ext}"

    sf.write(output_path, reduced_noise, sr)
    print(f"Saved denoised file to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python denoise_audio.py <path_to_audio.wav>")
    else:
        denoise_file(sys.argv[1])





