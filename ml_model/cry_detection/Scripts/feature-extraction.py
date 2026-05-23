import os
import numpy as np
from pathlib import Path
import librosa
import pickle
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

DATA_DIR = Path("../data/raw/model 1/audio")
PROCESSED_DIR = Path("../data/processed")

# Create processed directory structure
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
(PROCESSED_DIR / "train").mkdir(exist_ok=True)
(PROCESSED_DIR / "validation").mkdir(exist_ok=True)
(PROCESSED_DIR / "test").mkdir(exist_ok=True)

# Audio parameters
SAMPLING_RATE = 16000
N_MFCC = 13
FRAMES_PER_SAMPLE = 128
FRAME_LENGTH = int(0.025 * SAMPLING_RATE)  # 25 ms
HOP_LENGTH = int(0.010 * SAMPLING_RATE)   # 10 ms

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def log_message(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_msg = f"[{timestamp}] {msg}"
    print(full_msg)
    return full_msg


def extract_mfcc(audio_path, target_frames=FRAMES_PER_SAMPLE):
    """Extract MFCC + delta + delta-delta features from audio file.
    
    Returns shape: (FRAMES_PER_SAMPLE, N_MFCC * 3) = (128, 39)
    - 13 MFCCs (spectral shape)
    - 13 delta MFCCs (velocity / rate of change)
    - 13 delta-delta MFCCs (acceleration)
    """
    try:
        # Load audio
        y, sr = librosa.load(audio_path, sr=SAMPLING_RATE, duration=3.0)

        # Skip very short audio
        if len(y) < SAMPLING_RATE * 0.5:
            return None, False

        # Extract MFCC
        mfcc = librosa.feature.mfcc(
            y=y,
            sr=SAMPLING_RATE,
            n_mfcc=N_MFCC,
            n_fft=FRAME_LENGTH,
            hop_length=HOP_LENGTH
        )

        # Compute delta (1st derivative) and delta-delta (2nd derivative)
        mfcc_delta = librosa.feature.delta(mfcc, order=1)
        mfcc_delta2 = librosa.feature.delta(mfcc, order=2)

        # Stack: (3 * N_MFCC, frames) = (39, frames)
        features = np.concatenate([mfcc, mfcc_delta, mfcc_delta2], axis=0)

        # Transpose to (frames, 39)
        features = features.T

        # Pad or truncate to target frames
        if features.shape[0] < target_frames:
            pad_width = ((0, target_frames - features.shape[0]), (0, 0))
            features = np.pad(features, pad_width, mode='constant', constant_values=0)
        else:
            features = features[:target_frames, :]

        return features.astype(np.float32), True

    except Exception as e:
        return None, False


def process_split(split_name):
    """
    Process a split (train, validation, test) and save MFCC features.
    Returns: X (features), y (labels), count dict
    """
    split_dir = DATA_DIR / split_name

    if not split_dir.exists():
        log_message(f"ERROR: Directory not found: {split_dir}")
        return None, None, None

    X = []
    y = []
    filenames = []
    sample_count = {'cry': 0, 'snoring': 0, 'total': 0}

    log_message(f"\nProcessing {split_name.upper()} set:")
    log_message(f"  Directory: {split_dir}")
    
    # Find all wav files
    files = list(split_dir.rglob("*.wav"))
    
    if len(files) == 0:
        log_message(f"  ERROR: No .wav files found!")
        return None, None, None

    log_message(f"  Found {len(files)} audio files. Extracting features...")

    successful = 0
    for i, audio_file in enumerate(files):
        # Infer label from filename
        filename = audio_file.name
        label = None
        
        if "Infantcry" in filename or "cry" in filename.lower():
            label = 1
            sample_count['cry'] += 1
        elif "Snoring" in filename or "snor" in filename.lower():
            label = 0
            sample_count['snoring'] += 1
        
        if label is not None:
            mfcc, valid = extract_mfcc(audio_file)
            if valid:
                X.append(mfcc)
                y.append(label)
                filenames.append(filename)
                successful += 1

        # Progress update
        if (i + 1) % 500 == 0 and len(files) > 500:
            log_message(f"    Processed {i + 1}/{len(files)} files, {successful} successful")

    if len(X) == 0:
        log_message(f"  ERROR: No valid audio files processed!")
        return None, None, None

    X = np.array(X)
    y = np.array(y)
    sample_count['total'] = len(X)

    log_message(f"  ✓ Extracted {successful} samples")
    log_message(f"    - Crying:  {sample_count['cry']}")
    log_message(f"    - Snoring: {sample_count['snoring']}")
    log_message(f"    - Shape: {X.shape}")

    return X, y, sample_count, filenames


def save_split(X, y, filenames, split_name):
    """Save processed features to disk."""
    output_dir = PROCESSED_DIR / split_name
    
    # Save X, y separately
    X_path = output_dir / f"X_{split_name}.npy"
    y_path = output_dir / f"y_{split_name}.npy"
    
    np.save(X_path, X)
    np.save(y_path, y)
    
    # Save metadata
    metadata = {
        'split': split_name,
        'n_samples': len(X),
        'n_features': X.shape[1],
        'n_coefficients': X.shape[2],
        'sampling_rate': SAMPLING_RATE,
        'n_mfcc': N_MFCC,
        'frames_per_sample': FRAMES_PER_SAMPLE,
        'filenames': filenames
    }
    
    metadata_path = output_dir / f"metadata_{split_name}.pkl"
    with open(metadata_path, 'wb') as f:
        pickle.dump(metadata, f)
    
    log_message(f"    Saved to {output_dir}/")
    log_message(f"      - X_{split_name}.npy ({X.nbytes / 1024 / 1024:.1f} MB)")
    log_message(f"      - y_{split_name}.npy")
    log_message(f"      - metadata_{split_name}.pkl")


# ============================================================================
# MAIN
# ============================================================================

def main():
    log_message("=" * 70)
    log_message("FEATURE EXTRACTION PIPELINE")
    log_message("=" * 70)

    # Check if raw data exists
    if not DATA_DIR.exists():
        log_message(f"\nERROR: Raw data directory not found: {DATA_DIR}")
        log_message(f"Please ensure your ICSD dataset is at: {DATA_DIR}")
        return False

    log_message(f"\nRaw data directory: {DATA_DIR}")
    log_message(f"Output directory: {PROCESSED_DIR}")

    # Process each split
    splits = ['train', 'validation', 'test']
    all_successful = True

    for split in splits:
        log_message(f"\n{'=' * 70}")
        X, y, counts, filenames = process_split(split)
        
        if X is None:
            log_message(f"  ✗ Failed to process {split} set")
            all_successful = False
            continue
        
        # Save features
        log_message(f"\n  Saving {split} features...")
        save_split(X, y, filenames, split)

    # Summary
    log_message(f"\n{'=' * 70}")
    log_message("FEATURE EXTRACTION COMPLETE")
    log_message(f"{'=' * 70}")

    if all_successful:
        log_message(f"\n✓ All splits processed successfully!")
        log_message(f"\nProcessed data saved to: {PROCESSED_DIR}/")
        log_message(f"\nReady for training. Run: train_model.py")
        return True
    else:
        log_message(f"\n✗ Some splits failed to process")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)