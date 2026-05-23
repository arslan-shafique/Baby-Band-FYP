# Cry Detection Model

This directory contains the machine learning model for detecting baby cries from audio input.

## Project Structure

- `data/`: Contains raw and processed audio data.
- `notebooks/`: Jupyter notebooks for data exploration and experimentation.
- `src/`: Source code for the model.
  - `config.py`: Configuration parameters.
  - `dataset.py`: Data loading and preprocessing.
  - `model.py`: Model architecture.
  - `train.py`: Training script.
  - `inference.py`: Inference script for making predictions.
- `models/`: Saved model checkpoints.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Place raw audio files in `data/raw/`.

3. Run training:
   ```bash
   python src/train.py
   ```
