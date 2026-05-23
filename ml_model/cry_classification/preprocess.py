"""
Audio preprocessing module for both classification and detection pipelines.
Takes raw int16 PCM bytes and outputs a normalized Mel Spectrogram.
"""
import numpy as np
import librosa

def preprocess_audio(audio_bytes: bytes) -> np.ndarray:
    """
    Preprocess raw int16 PCM audio bytes into a normalized Mel Spectrogram.
    Returns: numpy array of shape (1, 128, 128, 1) with dtype float32
    """
    if len(audio_bytes) == 0:
        y = np.zeros(48000, dtype=np.float32)
    else:
        # Convert bytes to float32 numpy array
        y = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    
    target_samples = 48000
    if len(y) > target_samples:
        y = y[:target_samples]
    elif len(y) < target_samples and len(y) > 0:
        repeats = int(np.ceil(target_samples / len(y)))
        y = np.tile(y, repeats)[:target_samples]
        
    # Compute Mel Spectrogram
    # Using hop_length=375 as in features.py to get roughly 128 frames for 3.0s at 16kHz
    mel = librosa.feature.melspectrogram(
        y=y, sr=16000, n_mels=128, n_fft=512, hop_length=375
    )
    
    # Convert to dB
    mel_db = librosa.power_to_db(mel, ref=np.max)
    
    # Ensure exactly 128 frames across time axis
    if mel_db.shape[1] > 128:
        mel_db = mel_db[:, :128]
    elif mel_db.shape[1] < 128:
        pad_width = 128 - mel_db.shape[1]
        mel_db = np.pad(mel_db, ((0, 0), (0, pad_width)), mode='constant')
        
    # Min-Max normalize
    min_val = mel_db.min()
    max_val = mel_db.max()
    mel_db = (mel_db - min_val) / (max_val - min_val + 1e-6)
    
    # Reshape to (1, 128, 128, 1)
    features = np.expand_dims(mel_db, axis=(0, -1))
    return features.astype(np.float32)
