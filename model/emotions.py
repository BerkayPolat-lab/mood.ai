"""
Emotion labels for custom emotion classification model.
Supports dataset-specific emotion sets for efficient training.
"""

# RAVDESS Dataset Emotions (8 classes) - Recommended for single-dataset training
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


EMOTIONS = RAVDESS_EMOTIONS

EMOTION_TO_IDX = {emotion: idx for idx, emotion in enumerate(EMOTIONS)}
IDX_TO_EMOTION = {idx: emotion for emotion, idx in EMOTION_TO_IDX.items()}

def get_emotion_by_index(idx: int) -> str:
    """Get emotion label by index."""
    return IDX_TO_EMOTION.get(idx, "unknown")

def get_index_by_emotion(emotion: str) -> int:
    """Get emotion index by label."""
    return EMOTION_TO_IDX.get(emotion.lower(), -1)

def get_num_emotions() -> int:
    """Get total number of emotions."""
    return len(EMOTIONS)

def use_ravdess_emotions():
    """Use RAVDESS emotion set (8 emotions)."""
    global EMOTIONS, EMOTION_TO_IDX, IDX_TO_EMOTION
    EMOTIONS = RAVDESS_EMOTIONS
    EMOTION_TO_IDX = {emotion: idx for idx, emotion in enumerate(EMOTIONS)}
    IDX_TO_EMOTION = {idx: emotion for emotion, idx in EMOTION_TO_IDX.items()}
    return EMOTIONS

