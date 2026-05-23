import requests
import os

# Select a processed training file
filename = "../ml_model/cry_classification/data/processed/processed_0.wav"

if not os.path.exists(filename):
    print(f"File not found: {filename}")
    exit(1)

with open(filename, "rb") as f:
    # Skip the 44-byte WAV header to get pure PCM data
    f.read(44)
    pcm_data = f.read()

print(f"Sending {len(pcm_data)} bytes to /predict...")

headers = {
    "Content-Type": "application/octet-stream"
}

try:
    response = requests.post("http://localhost:8000/predict", data=pcm_data, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
