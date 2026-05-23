# Smart Baby Band - Cry Classification Pipeline

This folder implements the end-to-end machine learning pipeline for classifying infant cries into 4 distinct categories: `hungry`, `tired`, `discomfort`, and `diaper`.

## Overview

The pipeline harmonizes two major datasets (`donateacry` and `baby_crying`), extracts advanced "Efficient Graph" features (a combination of STFT, Mel Spectrogram, and MFCC representations), and trains a robust deep learning architecture comprising Convolutional Neural Networks (CNN), Multi-Head Attention, and Long Short-Term Memory (LSTM) layers.

---

## 1. Data Layout

*Note: The pipeline was optimized down to 4 target classes (`hungry`, `tired`, `discomfort`, `diaper`) to maximize performance on limited data.*

To use the pipeline, place the raw datasets in the `data/raw/` folder as follows:

```text
smart_baby_band/
├── data/
│   ├── raw/
│   │   ├── donateacry-corpus-master/donateacry_corpus_cleaned_and_updated_data/
│   │   ├── baby-crying/raw/
│   │   └── esc50/ (optional, for background noise augmentation)
```

**Dataset Mapping:**

- **Donate-a-Cry (DaC):** Keeps `belly_pain`, `burping`, `discomfort`, `hungry`, `tired`.
- **Baby Crying:** Maps `sleepy` → `tired`, `uncomfortable` → `discomfort`, keeps `diaper` and `hungry`. Unused labels (`awake`, `hug`) are dropped.

---

## 2. Model Architecture

The deep learning model is built sequentially to process audio as spatial-temporal data:

1. **CNN Local Blocks (4x):** Extracts local spatial-frequency features using 5x5 Conv2D layers with strides=(1, 1), Batch Normalization, ReLU, L2 Regularization, and Dropout(0.3).
2. **Stacked LSTM (2x):** Learns temporal dependencies directly from the flattened CNN sequence without crushing the time axis. Uses LSTM(128) returning sequences, followed by LSTM(64) compressing the final sequence state.
3. **Classifier:** Dense layer with Softmax activation outputting probabilities for the 4 target classes.
4. **Loss Function:** Optimized explicitly with **Categorical Focal Loss (alpha=0.25, gamma=2.0)** to heavily penalize majority class bias and mathematically force the network to prioritize minority classes.

---

## 3. Feature Extraction

For computational efficiency and noise reduction, audio files are pre-processed offline:

- **Resampling:** 16kHz mono WAV.
- **Duration:** 3.0 seconds (audio is wrapped using `np.tile` if too short, replacing dead zero-padding).
- **Component:** **Mel Spectrogram** (128 bands, N_FFT=512, Min-Max normalized).
- **Final Shape:** A clean `(128, 128, 1)` tensor shape per 3-second sample.

---

## 4. Experimental History & Findings

During the development of this pipeline, several massive architectural and data experiments were performed to break past the theoretical 60% accuracy ceiling on small datasets:

1. **Extreme Augmentation (1500 target):**
   - **Result:** ~55% Accuracy. `tired` recall collapsed to 0.00.
   - **Finding:** Over-augmenting minority classes with `TimeStretch` and `PitchShift` generated too many synthetic clones (3.7x the natural data), causing the CNN to overfit on artifacts instead of natural acoustic sounds.
2. **Dynamic SpecAugment & Z-Score Normalization:**
   - **Result:** ~50% Accuracy. Mode collapse (predicted `hungry` for everything).
   - **Finding:** Masking out frequency/time bands randomly during `tf.data` loading was too destructive for the `128x128` Mel Spectrograms. Combined with Z-Score normalization, it destroyed the fragile minority class signals.
3. **YAMNet Transfer Learning (TensorFlow Hub):**
   - **Result:** 61% Accuracy. `tired` recall collapsed back to 0.00.
   - **Finding:** Google's massive YAMNet model was tested as a feature extractor. While overall accuracy slightly increased, its generalized human-sound features failed to identify the narrow frequency bands of a "tired" baby.
4. **The "Goldilocks" Custom CNN (Baseline Model):**
   - **Result:** 60.0% Accuracy, Macro F1 of 0.50, `tired` recall restored to 0.59.
   - **Finding:** Reverting to the custom 5x5 CNN, dropping `TARGET_COUNT` in `augment.py` to 300 (to lightly balance classes without creating synthetic bias), and wrapping audio successfully trained a robust model that learns minority classes fairly.
5. **Final Refactor: Focal Loss + CNN+LSTM:**
   - **Result:** 56% Accuracy, `diaper` recall surged to 0.62.
   - **Finding:** By stripping out Self-Attention and compiling the model natively with `Categorical Focal Loss`, the model perfectly executed its mathematical directive. It sacrificed a few percentage points of raw majority-class accuracy to heavily prioritize the minority classes, yielding the fairest, most balanced feature extractor yet.

---

## 4. Execution Order & Usage

Run the following scripts in order to execute the pipeline from start to finish:

### Stage 1: Data Preparation

```bash
python dataset.py
```

- Aggregates raw audio, trims silence, resamples, and normalizes to `[-1, 1]`.
- Creates an 80/10/10 stratified train/val/test split and saves metadata to `data/processed/splits.csv`.

### Stage 2: Data Augmentation

```bash
python augment.py
```

- Performs offline augmentation strictly on the training split to resolve class imbalances (~600 samples per class).
- Utilizes `TimeStretch`, `PitchShift`, `TimeMask`, and `AddBackgroundNoise` (safely injected using the ESC-50 dataset).

### Stage 3: Feature Extraction

```bash
python features.py
```

- Processes all augmented and raw audio into the 2D Efficient Graph `.npy` tensors.
- Stores them sequentially inside `features/{split}/`.

### Stage 4: Training

```bash
python train.py
```

- Builds scalable `tf.data.Dataset` pipelines dynamically loading the `.npy` files.
- Applies class weights and uses `EarlyStopping`, `ReduceLROnPlateau`, and `ModelCheckpoint`.
- Training history is saved into the `logs/` directory.

### Stage 5: Evaluation

```bash
python evaluate.py
```

- Loads the best checkpoint and scores accuracy and F1 metrics on the test set.
- Generates a visual `confusion_matrix.png` heatmap in the `logs/` directory.
- Runs the cross-dataset experiment (generalization gap). *Use `--skip-cross-dataset` to bypass.*

### Stage 6: Model Export

```bash
python export.py
```

- Prepares the final compiled `model.h5`, maps indices using `label_map.json`, and validates the `feature_config.json`.

---

## 5. Outputs & Artifacts

Upon successful completion, the directory will be populated with:

- **`data/processed/`**: Cleaned WAV files and `splits.csv` metadata.
- **`data/augmented/`**: Generated augmentation WAVs.
- **`features/{train, val, test}/`**: Pre-computed `.npy` feature tensors.
- **`logs/`**: Training histories (`.json`) and evaluation plots (`.png`).
- **`models/`**:
  - `best_model.h5`: Trained Keras Checkpoint.
  - `model.h5`: Final exported model.
  - `label_map.json`: String mappings for class indices.
  - `feature_config.json`: Configuration dictionary to mirror audio pipeline in production.
