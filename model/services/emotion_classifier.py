"""
Custom emotion classifier with 100 emotions.
Replaces the classification layer of HuBERT base model.
"""

import torch
import torch.nn as nn
from transformers import (AutoModelForAudioClassification, AutoFeatureExtractor, AutoConfig)
from typing import Dict, Any, List, Tuple
import numpy as np

from ..emotions import EMOTIONS, get_num_emotions, IDX_TO_EMOTION


class CustomEmotionClassifier:
    """
    Custom emotion classifier that uses HuBERT base with 100 emotion labels.
    """
    
    def __init__(self, base_model_name: str = "superb/hubert-base-superb-er", num_emotions: int = None, device: str = None):
        """
        Initialize custom emotion classifier.
        
        Args:
            base_model_name: HuggingFace model name to use as base
            num_emotions: Number of emotion classes (defaults to 100 from emotions.py)
            device: Device to run on ('cuda', 'cpu', or None for auto)
        """
        self.base_model_name = base_model_name
        self.num_emotions = num_emotions or get_num_emotions()
        self.emotions = EMOTIONS
        
        # Auto-detect device if not provided
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        print(f"Loading base model: {base_model_name}")
        print(f"Using device: {self.device}")
        print(f"Number of emotions: {self.num_emotions}")
        
        self.feature_extractor = AutoFeatureExtractor.from_pretrained(base_model_name, trust_remote_code=True)
        
        self.config = AutoConfig.from_pretrained(base_model_name, trust_remote_code=True)
        
        original_num_labels = getattr(self.config, 'num_labels', None)
        self.config.num_labels = self.num_emotions
        
        print(f"Original num_labels: {original_num_labels}, New num_labels: {self.num_emotions}")
        
        try:
            base_model = AutoModelForAudioClassification.from_pretrained(base_model_name, config=self.config, trust_remote_code=True, ignore_mismatched_sizes=True  )
            
            hidden_size = getattr(self.config, 'hidden_size', 768)
            
            if hasattr(base_model, 'classifier'):
                original_classifier = base_model.classifier
                if isinstance(original_classifier, nn.Linear):
                    hidden_size = original_classifier.in_features
                elif isinstance(original_classifier, nn.Sequential):
                    for layer in reversed(original_classifier):
                        if isinstance(layer, nn.Linear):
                            hidden_size = layer.in_features
                            break
            elif hasattr(base_model, 'projector') and hasattr(base_model.projector, 'out_features'):
                hidden_size = base_model.projector.out_features
            elif hasattr(base_model, 'hubert'):
                hidden_size = getattr(base_model.hubert.config, 'hidden_size', hidden_size)
            
            print(f"Detected hidden size: {hidden_size}")
            
            new_classifier = nn.Linear(hidden_size, self.num_emotions)
            
            if hasattr(base_model, 'classification_head'):
                base_model.classification_head = new_classifier
            else:
                base_model.classifier = new_classifier
            
            self.model = base_model.to(self.device)
            self.model.eval() 
            
            print("Model loaded and classification head replaced successfully")
            print(f"New classifier output size: {self.num_emotions}")
            
        except Exception as e:
            print(f"Error loading model: {e}")
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
            
            top_indices = np.argsort(probs)[::-1][:5]
            
            results = []
            for idx in top_indices:
                emotion = IDX_TO_EMOTION.get(int(idx), f"emotion_{idx}")
                score = float(probs[idx])
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


def create_emotion_classifier(device: str = None) -> CustomEmotionClassifier:
    """
    Factory function to create a custom emotion classifier.
    
    Args:
        device: Device to run on ('cuda', 'cpu', or None for auto)
        
    Returns:
        CustomEmotionClassifier instance
    """
    return CustomEmotionClassifier(device=device)

