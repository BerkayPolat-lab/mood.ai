"""
Custom emotion classifier using fine-tuned HuBERT model from Hugging Face.
"""

import os
import torch
import torch.nn as nn
from transformers import (AutoModelForAudioClassification, AutoFeatureExtractor, AutoConfig)
from typing import Dict, Any, List, Tuple
import numpy as np
from huggingface_hub import login


class CustomEmotionClassifier:
    """
    Custom emotion classifier using fine-tuned HuBERT model from Hugging Face.
    """
    
    # Emotion index mapping: model output (1-8) -> array index (0-7)
    EMOTION_MAPPING = {
        1: 0,  # neutral
        2: 1,  # calm
        3: 2,  # happy
        4: 3,  # sad
        5: 4,  # angry
        6: 5,  # fearful
        7: 6,  # surprise
        8: 7   # disgust
    }
    
    # Index to emotion name mapping (0-7)
    INDEX_TO_EMOTION = {
        0: "neutral",
        1: "calm",
        2: "happy",
        3: "sad",
        4: "angry",
        5: "fearful",
        6: "surprise",
        7: "disgust"
    }
    
    def __init__(self, model_name: str = "BerkayPolat/hubert_ravdess_emotion", hf_token: str = None, device: str = None):
        """
        Initialize custom emotion classifier with fine-tuned model.
        
        Args:
            model_name: HuggingFace model repository name
            hf_token: Hugging Face access token (if None, tries to get from HF_ACCESS_TOKEN env var)
            device: Device to run on ('cuda', 'cpu', or None for auto)
        """
        self.model_name = model_name
        
        # Auto-detect device if not provided
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        # Get HF token from parameter or environment
        if hf_token is None:
            hf_token = os.getenv("HF_ACCESS_TOKEN")
        
        if not hf_token:
            raise ValueError(
                "HF_ACCESS_TOKEN must be set in environment or passed as parameter. "
                "Get your token from https://huggingface.co/settings/tokens"
            )
        
        # Login to Hugging Face with token
        try:
            login(token=hf_token, add_to_git_credential=False)
            print("Authenticated with Hugging Face")
        except Exception as e:
            print(f"Warning: Could not login to Hugging Face: {e}")
            print("Trying to load model with token in headers...")
        
        print(f"Loading fine-tuned model: {model_name}")
        print(f"Using device: {self.device}")
        
        try:
            # Load feature extractor
            self.feature_extractor = AutoFeatureExtractor.from_pretrained(
                model_name,
                token=hf_token,
                trust_remote_code=True
            )
            
            # Load config to get number of labels
            self.config = AutoConfig.from_pretrained(
                model_name,
                token=hf_token,
                trust_remote_code=True
            )
            
            # Get number of emotion classes from config
            self.num_emotions = getattr(self.config, 'num_labels', None)
            if self.num_emotions is None:
                # Try to infer from id2label
                if hasattr(self.config, 'id2label') and self.config.id2label:
                    self.num_emotions = len(self.config.id2label)
                else:
                    print("Warning: Could not determine number of emotions, defaulting to 8")
                    self.num_emotions = 8
            
            print(f"Number of emotion classes: {self.num_emotions}")
            
            # Load the fine-tuned model (already has correct classification head)
            self.model = AutoModelForAudioClassification.from_pretrained(
                model_name,
                token=hf_token,
                trust_remote_code=True
            )
            
            self.model = self.model.to(self.device)
            self.model.eval()
            
            print(f"Fine-tuned model loaded successfully on {self.device}")
            print(f"Model has {self.num_emotions} emotion classes")
            
        except Exception as e:
            print(f"Error loading fine-tuned model: {e}")
            print(f"Error details: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def __call__(self, audio_input: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Classify emotion from audio input.
        
        Args:
            audio_input: Dictionary with 'raw' (np.ndarray) and 'sampling_rate' (int)
            
        Returns:
            List of dictionaries with 'label' and 'score' keys, sorted by score descending
        """
        try:
            raw_audio = audio_input.get("raw")
            sampling_rate = audio_input.get("sampling_rate", 16000)
            
            if raw_audio is None:
                raise ValueError("Audio input must contain 'raw' key with audio data")
            
            if isinstance(raw_audio, np.ndarray):
                audio_array = raw_audio.tolist()
            else:
                audio_array = raw_audio
            
            inputs = self.feature_extractor(audio_array, sampling_rate=sampling_rate, return_tensors="pt", padding=True).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            if hasattr(outputs, 'logits'):
                logits = outputs.logits
            elif isinstance(outputs, tuple):
                logits = outputs[0]
            else:
                logits = outputs
            
            probs = torch.nn.functional.softmax(logits, dim=-1)
            
            probs = probs.cpu().numpy().flatten()
            
            # Map model outputs to emotion indices
            # Model outputs are 0-indexed (0-7), but model labels are 1-8
            # So probs[0] corresponds to model label 1, probs[1] to model label 2, etc.
            mapped_probs = np.zeros(8)
            for model_output_idx in range(len(probs)):
                # model_output_idx is 0-7, model label is model_output_idx + 1 (1-8)
                model_label = model_output_idx + 1
                if model_label in self.EMOTION_MAPPING:
                    emotion_idx = self.EMOTION_MAPPING[model_label]
                    mapped_probs[emotion_idx] = probs[model_output_idx]
            
            # Get top 5 emotions by probability
            top_indices = np.argsort(mapped_probs)[::-1][:5]
            
            results = []
            for emotion_idx in top_indices:
                # Get emotion name from mapped index
                emotion = self.INDEX_TO_EMOTION.get(int(emotion_idx), f"emotion_{emotion_idx}")
                score = float(mapped_probs[emotion_idx])
                results.append({
                    "label": emotion,
                    "score": score
                })
            
            return results
            
        except Exception as e:
            print(f"Error during emotion classification: {e}")
            raise
    
    def predict(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """
        Predict emotion from audio data.
        
        Args:
            audio_data: Audio waveform as numpy array
            sample_rate: Sample rate of the audio
            
        Returns:
            Dictionary with 'emotion' and 'emotion_score' keys
        """
        results = self({
            "raw": audio_data,
            "sampling_rate": sample_rate
        })
        
        if len(results) > 0:
            top_result = results[0]
            return {
                "emotion": top_result["label"],
                "emotion_score": top_result["score"]
            }
        else:
            return {
                "emotion": "neutral",
                "emotion_score": 0.5
            }


def create_emotion_classifier(model_name: str = "BerkayPolat/hubert_ravdess_emotion", hf_token: str = None, device: str = None) -> CustomEmotionClassifier:
    """
    Factory function to create a custom emotion classifier with fine-tuned model.
    
    Args:
        model_name: HuggingFace model repository name
        hf_token: Hugging Face access token (if None, tries to get from HF_ACCESS_TOKEN env var)
        device: Device to run on ('cuda', 'cpu', or None for auto)
        
    Returns:
        CustomEmotionClassifier instance
    """
    return CustomEmotionClassifier(model_name=model_name, hf_token=hf_token, device=device)

