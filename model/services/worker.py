import os
import time
import tempfile
import requests
import numpy as np
import librosa
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from supabase import create_client, Client
import tensorflow as tf
import tensorflow_hub as hub
import torch
from .emotion_classifier import create_emotion_classifier

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
tf.get_logger().setLevel('ERROR')


class AudioMoodWorker:
    
    def __init__(self):
        """Initialize the worker with Supabase client and ML models."""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set"
            )
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        print("Loading YAMNet model...")
        self.yamnet_model = hub.load('https://tfhub.dev/google/yamnet/1')
        self.yamnet_class_names = self._load_yamnet_class_names()
        
        print("Loading fine-tuned HuBERT emotion classifier...")
        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            hf_token = os.getenv("HF_ACCESS_TOKEN")
            
            if not hf_token:
                raise ValueError(
                    "HF_ACCESS_TOKEN must be set in model/.env.local. "
                    "Get your token from https://huggingface.co/settings/tokens"
                )
            
            self.emotion_classifier = create_emotion_classifier(
                model_name="BerkayPolat/hubert_ravdess_emotion",
                hf_token=hf_token,
                device=device
            )
            print("Fine-tuned emotion classifier loaded successfully")
        except Exception as e:
            print(f"Error: Could not load fine-tuned emotion classifier: {e}")
            print("Worker cannot proceed without emotion classifier")
            raise
        
        print("Worker initialized successfully")
    
    def _load_yamnet_class_names(self) -> list:
        """Load YAMNet class names from GitHub (official source)."""
        try:
            yamnet_class_map_url = "https://raw.githubusercontent.com/tensorflow/models/master/research/audioset/yamnet/yamnet_class_map.csv"
            
            response = requests.get(yamnet_class_map_url, timeout=10)
            response.raise_for_status()
            
            class_names = []
            for line in response.text.strip().split('\n')[1:]:  # Skip header
                parts = line.strip().split(',')
                if len(parts) >= 3:
                    display_name = parts[2].strip('"')
                    class_names.append(display_name)
            
            if class_names:
                print(f"Loaded {len(class_names)} YAMNet class names from GitHub")
                return class_names
            else:
                raise Exception("No class names loaded from CSV")
                
        except Exception as e:
            print(f"Warning: Could not load YAMNet class names: {e}")
            print("Using fallback: numbered class names")
            return [f"Class_{i}" for i in range(521)]
    
    def process_job(self, job_id: str) -> Dict[str, Any]:
        """
        Process a single job.
        
        Args:
            job_id: UUID of the job to process
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Fetch job details
            job_response = self.supabase.table("jobs").select("*, uploads(*)").eq("id", job_id).single().execute()
            
            if not job_response.data:
                return {"success": False, "error": "Job not found"}
            
            job = job_response.data
            upload = job.get("uploads")
            
            if not upload:
                return {"success": False, "error": "Upload not found"}
            
            self.supabase.table("jobs").update({
                "status": "processing",
                "started_at": datetime.utcnow().isoformat()
            }).eq("id", job_id).execute()
            
            stored_path = upload["audio_file_path"]
            print(f"Downloading audio from path: {stored_path}")
            
            if '/storage/v1/object/public/' in stored_path:
                parts = stored_path.split('/storage/v1/object/public/')
                if len(parts) == 2:
                    bucket_and_path = parts[1]
                    file_path = '/'.join(bucket_and_path.split('/')[1:])
                else:
                    raise Exception(f"Could not extract file path from URL: {stored_path}")
            else:
                file_path = stored_path
            
            audio_data, sample_rate = self._download_audio_with_signed_url(file_path)
            
            if audio_data is None:
                raise Exception("Failed to download or load audio file")
            
            print("Running YAMNet inference...")
            yamnet_results = self._run_yamnet(audio_data, sample_rate)
            
            print("Running emotion detection...")
            emotion_results = self._run_emotion_detection(audio_data, sample_rate)
            
            mood_analysis = self._combine_results(
                yamnet_results, emotion_results
            )
            
            ## In the future, add the inference time to the prediction data.
            inference_time = 2.0  # Placeholder
            
            prediction_data = {
                "user_id_sha256": job["user_id_sha256"],
                "upload_id": upload["id"],
                "scores": mood_analysis,
                "model_version": "1.0.0",
                "inference_time": inference_time,
                "model_name": "yamnet-wav2vec2-emotion"
            }
            
            prediction_response = self.supabase.table("predictions").insert(
                prediction_data
            ).execute()
            
            self.supabase.table("jobs").update({"status": "completed", "finished_at": datetime.utcnow().isoformat()}).eq("id", job_id).execute()
            
            print(f"Job {job_id} completed successfully")
            
            return {
                "success": True,
                "job_id": job_id,
                "prediction": mood_analysis
            }
            
        except Exception as e:
            print(f"Error processing job {job_id}: {str(e)}")
            
            # Update job status to failed
            self.supabase.table("jobs").update({"status": "failed","error": str(e), "finished_at": datetime.utcnow().isoformat()}).eq("id", job_id).execute()
            
            return {
                "success": False,
                "error": str(e)
            }
    
    def _download_audio_with_signed_url(self, file_path: str) -> Tuple[Optional[np.ndarray], Optional[int]]:
        try:
            try:
                signed_urls_response = self.supabase.storage.from_("audio_files").create_signed_urls([file_path], expires_in=3600)
                
                if not signed_urls_response or len(signed_urls_response) == 0:
                    print(f"Failed to generate signed URL for: {file_path}")
                    return None, None
                
                signed_url_data = signed_urls_response[0]
                signed_url = signed_url_data.get('signedURL') or signed_url_data.get('signed_url')
                
                if not signed_url:
                    print(f"No signed URL in response: {signed_url_data}")
                    return None, None
                
                print(f"Generated signed URL (expires in 1 hour)")
                
            except Exception as e:
                print(f"Error generating signed URL: {str(e)}")
            
            response = requests.get(signed_url, timeout=30)
            response.raise_for_status()
            
            file_ext = file_path.split('.')[-1].lower() if '.' in file_path else 'wav'
            if file_ext not in ['wav', 'mp3', 'm4a', 'ogg', 'webm']:
                file_ext = 'wav'
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}') as tmp_file:
                tmp_file.write(response.content)
                tmp_path = tmp_file.name
            
            audio_data, sample_rate = librosa.load(tmp_path, sr=16000, duration=30)
            
            os.unlink(tmp_path)
            
            return audio_data, sample_rate
            
        except Exception as e:
            print(f"Error downloading with signed URL: {str(e)}")
            return None, None
        
    def _run_yamnet(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """
        Run YAMNet inference for sound classification.
        
        Args:
            audio_data: Audio waveform data
            sample_rate: Sample rate of the audio
            
        Returns:
            Dictionary with classification results
        """
        try:
            # YAMNet expects 16kHz audio
            if sample_rate != 16000:
                audio_data = librosa.resample(
                    audio_data, orig_sr=sample_rate, target_sr=16000
                )
                sample_rate = 16000
            
            scores, embeddings, spectrogram = self.yamnet_model(audio_data)
            
            scores_mean = np.mean(scores, axis=0)
            top_indices = np.argsort(scores_mean)[::-1][:5]
            
            top_classes = []
            for idx in top_indices:
                class_name = self.yamnet_class_names[idx] if idx < len(self.yamnet_class_names) else f"Class_{idx}"
                top_classes.append({
                    "class": class_name,
                    "score": float(scores_mean[idx])
                })
            
            primary_class = top_classes[0]["class"] if top_classes else "Unknown"
            
            return {
                "sound_classification": primary_class,
                "top_classes": top_classes,
                "confidence": float(top_classes[0]["score"]) if top_classes else 0.0
            }
            
        except Exception as e:
            print(f"Error running YAMNet: {str(e)}")
            return {
                "sound_classification": "Unknown",
                "top_classes": [],
                "confidence": 0.0
            }
    
    def _run_emotion_detection(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """
        Run emotion detection using custom HuBERT-based model with 100 emotions.
        
        Args:
            audio_data: Audio waveform data
            sample_rate: Sample rate of the audio
            
        Returns:
            Dictionary with emotion detection results
        """
        try:
            if self.emotion_classifier is None:
                raise Exception("Emotion classifier not initialized")
            
            # Use the predict method which returns the same format
            result = self.emotion_classifier.predict(audio_data, sample_rate)
            
            return {
                "emotion": result.get("emotion", "neutral"),
                "emotion_score": float(result.get("emotion_score", 0.5))
            }
            
        except Exception as e:
            print(f"Error running emotion detection: {str(e)}")
            raise
    
    
    def _combine_results(self, yamnet_results: Dict[str, Any], emotion_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combine YAMNet and emotion results - returns raw model outputs.
        
        Args:
            yamnet_results: YAMNet classification results
            emotion_results: Emotion detection results
            
        Returns:
            Combined results with raw model outputs
        """
        # Return raw outputs from both models
        return {
            "sound_classification": yamnet_results.get("sound_classification", "Unknown"),
            "yamnet_top_classes": yamnet_results.get("top_classes", []),
            "yamnet_confidence": yamnet_results.get("confidence", 0.0),
            "emotion": emotion_results.get("emotion", "neutral"),
            "emotion_score": emotion_results.get("emotion_score", 0.0)
        }
    
    def run(self, poll_interval: int = 5):
        """
        Main worker loop that polls for queued jobs.
        
        Args:
            poll_interval: Seconds to wait between polls
        """
        print("Worker started. Polling for queued jobs...")
        
        while True:
            try:
                # Fetch queued jobs
                jobs_response = self.supabase.table("jobs").select(
                    "id"
                ).eq("status", "queued").limit(1).execute()
                
                if jobs_response.data and len(jobs_response.data) > 0:
                    job = jobs_response.data[0]
                    job_id = job["id"]
                    
                    print(f"Processing job: {job_id}")
                    result = self.process_job(job_id)
                    
                    if result["success"]:
                        print(f"✓ Job {job_id} completed successfully")
                    else:
                        print(f"✗ Job {job_id} failed: {result.get('error')}")
                else:
                    time.sleep(poll_interval)
                    
            except KeyboardInterrupt:
                print("\nWorker stopped by user")
                break
            except Exception as e:
                print(f"Error in worker loop: {str(e)}")
                time.sleep(poll_interval)


if __name__ == "__main__":
    from dotenv import load_dotenv
    import pathlib
    
    script_dir = pathlib.Path(__file__).parent.parent
    env_path = script_dir / ".env.local"
    
    load_dotenv(env_path)
    print(f"Loaded environment from: {env_path}")
    
    worker = AudioMoodWorker()
    worker.run(poll_interval=5)

