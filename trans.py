import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import whisper
import keyboard

fs = 16000  # sample rate
audio_buffer = []

print("Press 's' to start recording, 'q' to stop...")

# Wait for 's'
keyboard.wait('s')
print("Recording started... Press 'q' to stop")

def callback(indata, frames, time, status):
    if status:
        print(status)
    audio_buffer.append(indata.copy())

# Start recording (non-blocking)
stream = sd.InputStream(samplerate=fs, channels=1, dtype='int16', callback=callback)
stream.start()

# Wait for 'q'
keyboard.wait('q')

# Stop recording
stream.stop()
stream.close()

print("Recording stopped")

# Convert buffer → numpy array
audio_np = np.concatenate(audio_buffer, axis=0)

# Save audio
write("audio.wav", fs, audio_np)
print("Audio saved as audio.wav")

# Load Whisper model
import torch
device = "cuda" if torch.cuda.is_available() else "cpu"
model = whisper.load_model("medium.en", device=device)

# Transcribe
result = model.transcribe("audio.wav")

print("\nTranscription:")
print(result["text"])