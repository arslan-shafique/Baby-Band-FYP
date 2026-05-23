### **Corrected Implementation Plan**

#### **Stage 1 - Data Preparation**

**dataset.py**

1\. Load DaC → parse filenames → map labels

2\. Load baby_crying → parse folders → map labels

3\. Harmonize to 6 classes, drop: hug, awake

4\. Resample all → 16kHz mono WAV → data/processed/

5\. Trim silence (top_db=20) → pad/truncate → 3 sec fixed

6\. Normalize amplitude → \[-1, 1\]

7\. Stratified 80/10/10 split

8\. Save → splits.csv (filepath, label, split, source_dataset)

9\. Plot class distribution

#### **Stage 2 - Augmentation (offline, once)**

**augment.py**

1\. Load splits.csv (train split only)

2\. Compute per-class augmentation count → target ~1500/class

3\. For each underrepresented sample:

\- TimeStretch(0.85-1.15)

\- PitchShift(±2 semitones)

\- AddBackgroundNoise(ESC-50, SNR 10-20dB)

\- TimeMask(5-15% of duration)

4\. Save augmented WAVs → data/augmented/

5\. Append augmented entries to splits.csv

#### **Stage 3 - Feature Extraction (offline, once)**

**features.py**

1\. extract_features(audio_path) → 2D efficient graph array

a. Load audio → 16kHz, 3 sec, 48000 samples

b. Spectrogram (STFT):

n_fft=512, hop_length=375, window='hann'

→ magnitude spectrogram (257, 128)

→ convert to dB

c. Mel Spectrogram:

n_mels=128, n_fft=512, hop_length=375

fmin=0, fmax=8000

→ (128, 128), dB scale

d. MFCC:

n_mfcc=40, same n_fft, hop_length

→ MFCC (40, 128)

→ delta (40, 128)

→ delta-delta (40, 128)

→ stack → (120, 128)

e. Efficient Graph construction:

\- Remove redundant freq bins from Spectrogram

that overlap with Mel Spectrogram

\- Concat Spectrogram + Mel Spectrogram → (H1, 128)

\- Concat MFCC block along freq axis → (H1+120, 128)

\- Final shape: (~305, 128) - no resizing, no interpolation

f. Normalize per-channel to \[0, 1\]

g. Add channel dim → (~305, 128, 1) for Conv2D input

2\. Process all entries in splits.csv

3\. Save each as .npy → features/{split}/{label}\_{id}.npy

4\. Save feature shape to config.json

#### **Stage 4 - Model**

**model.py**

1\. build_model(input_shape, num_classes=6)

Input: (H, 128, 1) # H = efficient graph height

CNN Local Blocks (×4):

Conv2D(32→64→128→128, kernel=5×5, stride=2)

\+ BN + ReLU + MaxPool + Dropout(0.3)

Reshape:

Flatten spatial → (seq_len, features)

Attention (×2):

MultiHeadAttention(heads=8, key_dim=16)

\+ Add & Norm residual

LSTM Stack:

LSTM(256, return_sequences=True)

LSTM(128, return_sequences=True)

LSTM(64, return_sequences=True)

LSTM(32, return_sequences=False)

Dropout(0.3)

Classifier:

Dense(6, softmax)

2\. Compile:

optimizer = SGD(lr=0.8) # paper uses SGD lr=8e-1

loss = sparse_categorical_crossentropy

metrics = \[accuracy\]

Note on optimizer: the paper uses SGD with lr=0.8, not Adam. Use that first, then switch to Adam if it doesn't converge - SGD at 0.8 is aggressive.

#### **Stage 5 - Training**

**train.py**

1\. Build tf.data.Dataset from .npy files

\- No augmentation here, already done offline

\- Batch(32), prefetch(AUTOTUNE), shuffle(train only)

2\. Compute class weights (sklearn)

3\. model.fit() with:

\- EarlyStopping(patience=10, restore_best_weights=True)

\- ReduceLROnPlateau(factor=0.5, patience=5, min_lr=1e-6)

\- ModelCheckpoint(save_best_only=True)

4\. Save history → training_history.json

#### **Stage 6 - Evaluation**

**evaluate.py**

1\. Load best checkpoint

2\. Evaluate on test set:

\- Accuracy, F1 per class

\- Confusion matrix

\- Classification report (sklearn)

3\. Cross-dataset experiment:

\- Retrain on DaC only (hungry, discomfort, belly_pain, burping)

\- Test on baby_crying (hungry, discomfort only - overlapping)

\- Report generalization gap

#### **Stage 7 - Export**

**export.py**

1\. Save model.h5

2\. Save label_map.json

{0:"hungry", 1:"tired", 2:"discomfort",

3:"belly_pain", 4:"diaper", 5:"burping"}

3\. Save feature config (sr, duration, n_fft, hop_length, n_mels, n_mfcc)

→ inference must use identical params

#### **Final File Structure**

smart_baby_band/

├── data/

│ ├── raw/

│ │ ├── donate_a_cry/

│ │ └── baby_crying/

│ ├── processed/ # resampled, trimmed, normalized WAVs

│ ├── augmented/ # augmented WAVs

│ └── splits.csv

│

├── features/

│ ├── train/

│ ├── val/

│ └── test/

│

├── models/

│ ├── best_model.h5

│ ├── label_map.json

│ └── feature_config.json

│

├── dataset.py

├── augment.py

├── features.py

├── model.py

├── train.py

├── evaluate.py

├── export.py
