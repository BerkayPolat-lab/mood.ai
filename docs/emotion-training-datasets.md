# Recommended Dataset for Single-Dataset Training

## Primary Recommendation: **RAVDESS** ⭐

### Overview

**RAVDESS (Ryerson Audio-Visual Database of Emotional Speech and Song)** is the recommended dataset for training your emotion classifier with a single, efficient approach.

**Key Details:**
- **Size**: ~7,350 audio files
- **Emotions**: 8 categories (neutral, calm, happy, sad, angry, fearful, surprise, disgust)
- **Actors**: 24 professional actors (12 male, 12 female)
- **Format**: 16kHz WAV files
- **Duration**: Variable (typically 1-4 seconds)
- **Modalities**: Speech only, speech + video, song only
- **License**: Free for research and educational use
- **Download**: Available on [Kaggle](https://www.kaggle.com/datasets/uwrfkaggler/ravdess-emotional-speech-audio)

### Why RAVDESS?

1. **Easy Accessibility**
   - Direct download from Kaggle (no license approval needed)
   - Well-organized file structure
   - Good documentation

2. **High Quality**
   - Professional actors with consistent performances
   - Clean audio recordings
   - Balanced emotion distribution
   - Widely used in research (well-validated)

3. **Good Dataset Size**
   - ~7,350 files provides sufficient training data
   - Enough samples per emotion class for robust training
   - Good train/val/test split potential

4. **Perfect Format Compatibility**
   - 16kHz audio (matches HuBERT's expected input)
   - WAV format (standard, easy to process)
   - Consistent quality

5. **Reasonable Emotion Count**
   - 8 emotions is a good balance:
     - Not too few (6 emotions too limited)
     - Not too many (easier to train than 30+)
     - Covers primary emotional spectrum

### Emotion Categories in RAVDESS

The dataset contains 8 emotion labels:
1. **Neutral** - No emotion
2. **Calm** - Peaceful, relaxed
3. **Happy** - Joyful, cheerful
4. **Sad** - Sorrowful, melancholic
5. **Angry** - Irritated, furious
6. **Fearful** - Anxious, scared
7. **Surprise** - Shocked, astonished
8. **Disgust** - Revulsion, repulsion

### Dataset Structure

RAVDESS files are named with a specific pattern:
```
[Modality]-[Vocal Channel]-[Emotion]-[Emotional Intensity]-[Statement]-[Repetition]-[Actor].wav
```

Example: `03-01-03-02-01-01-01.wav`
- 03 = Speech only
- 01 = Normal vocal channel
- 03 = Happy emotion
- 02 = Normal intensity
- 01 = Statement 1
- 01 = First repetition
- 01 = Actor 1

### Download Instructions

1. **From Kaggle (Easiest)**:
   ```bash
   # Install kaggle CLI
   pip install kaggle
   
   # Download dataset
   kaggle datasets download -d uwrfkaggler/ravdess-emotional-speech-audio
   
   # Extract
   unzip ravdess-emotional-speech-audio.zip
   ```

2. **Direct Download**:
   - Visit: https://www.kaggle.com/datasets/uwrfkaggler/ravdess-emotional-speech-audio
   - Click "Download" button
   - Extract the ZIP file

### Data Preparation

The dataset comes organized in folders. You'll need to:
1. Extract all WAV files
2. Parse filenames to extract emotion labels
3. Create train/validation/test splits
4. Ensure 16kHz sampling rate (already correct)
5. Normalize audio levels

---

## Alternative: EmoGator (If You Want More Emotions)

If you prefer more emotion categories, **EmoGator** is a good alternative:

- **Size**: 32,130 samples (larger)
- **Emotions**: 30 categories (more fine-grained)
- **Format**: Vocal bursts (non-verbal)
- **License**: Open-source
- **Access**: HuggingFace Datasets or research paper

**Trade-offs:**
- ✅ More emotions (30 vs 8)
- ✅ Larger dataset
- ❌ Less established/validated
- ❌ May be harder to access/format
- ❌ Vocal bursts (non-verbal) vs speech

**Recommendation**: Stick with RAVDESS unless you specifically need 30 emotions.

---

## Recommended Training Approach

### 1. Dataset-Specific Configuration

Update your classifier to use RAVDESS emotions automatically:

```python
# RAVDESS emotion labels (in order from dataset)
RAVDESS_EMOTIONS = [
    "neutral",
    "calm", 
    "happy",
    "sad",
    "angry",
    "fearful",
    "surprise",
    "disgust"
]
```

### 2. Training Strategy

1. **Freeze HuBERT Base**:
   - Keep pre-trained features frozen
   - Only train 8-class classifier head
   - Faster training, less overfitting

2. **Data Splitting**:
   - Train: 70% (~5,145 files)
   - Validation: 15% (~1,103 files)
   - Test: 15% (~1,103 files)
   - **Speaker-independent split**: Use different actors for train/val/test

3. **Training Hyperparameters**:
   - Learning rate: 1e-3 to 1e-4
   - Batch size: 16-32
   - Epochs: 20-50 (with early stopping)
   - Optimizer: Adam or AdamW
   - Loss: Cross-Entropy (8 classes)

4. **Data Augmentation** (Optional):
   - Speed perturbation (±10%)
   - Pitch shifting (±2 semitones)
   - Background noise injection
   - Time stretching

### 3. Expected Performance

With RAVDESS and HuBERT:
- **Baseline accuracy**: ~70-80% (without fine-tuning)
- **With trained classifier head**: ~85-92% (on test set)
- **With data augmentation**: +2-5% improvement

---

## Implementation Steps

1. **Download RAVDESS dataset**
2. **Create dataset loader** (parse filenames, load audio)
3. **Update classifier** to use 8 emotions from RAVDESS
4. **Create training script** with proper data splits
5. **Train classifier head** (frozen HuBERT base)
6. **Evaluate** on test set

---

## Next Steps

After choosing RAVDESS:
- The classifier will automatically use 8 emotions
- No need for emotion mapping
- Simpler training pipeline
- Faster iteration and experimentation

---
