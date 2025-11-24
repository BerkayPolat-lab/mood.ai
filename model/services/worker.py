"""
Worker service for processing audio mood analysis jobs.
Fetches queued jobs from Supabase, runs YAMNet and Wav2Vec2 inference,
and updates job status and predictions.
"""

import os
import time
import tempfile
import requests
import numpy as np
import librosa
import soundfile as sf
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from supabase import create_client, Client
import tensorflow as tf
import tensorflow_hub as hub
from transformers import pipeline
import torch

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
tf.get_logger().setLevel('ERROR')


class AudioMoodWorker:
    """Worker for processing audio mood analysis jobs."""
    
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
        
        # Initialize Wav2Vec2-based emotion model
        print("Loading Wav2Vec2 emotion model...")
        try:
            # superb/hubert-base-superb-er is a Wav2Vec2-based model for emotion recognition
            self.emotion_classifier = pipeline(
                "audio-classification",
                model="superb/hubert-base-superb-er",
                device=0 if torch.cuda.is_available() else -1
            )
            print("Wav2Vec2 emotion model loaded successfully")
        except Exception as e:
            print(f"Warning: Could not load Wav2Vec2 emotion model: {e}")
            print("Falling back to feature-based emotion estimation")
            self.emotion_classifier = None
        
        print("Worker initialized successfully")
    
    def _load_yamnet_class_names(self) -> list:
        """Load YAMNet class names from GitHub (official source)."""
        try:
            # Use raw GitHub URL to get the CSV file directly
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
            
            # Download audio file using signed URL (most reliable method)
            # Extract file path from stored URL
            audio_file_path = upload["audio_file_path"]
            print(f"Downloading audio from: {audio_file_path}")
            
            # Generate signed URL and download
            audio_data, sample_rate = self._download_audio_with_signed_url(audio_file_path)
            
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
    
    def _download_audio_with_signed_url(self, file_path_or_url: str) -> Tuple[Optional[np.ndarray], Optional[int]]:
        """
        Download audio file using a signed URL (most reliable method).
        
        Signed URLs are better than public URLs because:
        1. They work regardless of bucket privacy settings
        2. They're more reliable (avoid 400 errors from public URL encoding issues)
        3. They're time-limited for security
        4. They work with nested paths without encoding issues
        
        Args:
            file_path_or_url: Either a file path (user_id/filename) or full public URL
            
        Returns:
            Tuple of (audio_data, sample_rate) or (None, None) on error
        """
        bucket = "audio_files"
        try:
            if '/storage/v1/object/public/' in file_path_or_url:
                # Extract path from public URL
                # Format: https://project.supabase.co/storage/v1/object/public/bucket/path
                parts = file_path_or_url.split('/storage/v1/object/public/')
                if len(parts) == 2:
                    bucket_and_path = parts[1]
                    bucket = bucket_and_path.split('/')[0]
                    file_path = '/'.join(bucket_and_path.split('/')[1:])
                else:
                    return None, None
            else:
                # Assume it's already a file path
                file_path = file_path_or_url
            
            # Use direct download (more reliable than signed URLs for server-side)
            # Signed URLs are better for client-side, but direct download works better
            # for server-side workers with service role key
            return self._download_audio_direct(bucket, file_path)
            
            # Download using signed URL
            response = requests.get(signed_url, timeout=30)
            response.raise_for_status()
            
            # Determine file extension from path
            file_ext = file_path.split('.')[-1].lower() if '.' in file_path else 'wav'
            if file_ext not in ['wav', 'mp3', 'm4a', 'ogg', 'webm']:
                file_ext = 'wav'
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}') as tmp_file:
                tmp_file.write(response.content)
                tmp_path = tmp_file.name
            
            # Load audio using librosa
            audio_data, sample_rate = librosa.load(tmp_path, sr=16000, duration=30)
            
            # Clean up
            os.unlink(tmp_path)
            
            return audio_data, sample_rate
            
        except Exception as e:
            print(f"Error downloading with signed URL: {str(e)}")
            return None, None
    
    def _download_audio_direct(self, bucket: str, file_path: str) -> Tuple[Optional[np.ndarray], Optional[int]]:
        """
        Fallback: Download audio file directly using Storage API.
        
        Args:
            bucket: Storage bucket name
            file_path: Path to the file in the bucket
            
        Returns:
            Tuple of (audio_data, sample_rate) or (None, None) on error
        """
        try:
            # Download directly using Storage API
            file_response = self.supabase.storage.from(bucket).download(file_path)
            
            if not file_response:
                return None, None
            
            # Determine file extension from path
            file_ext = file_path.split('.')[-1].lower() if '.' in file_path else 'wav'
            if file_ext not in ['wav', 'mp3', 'm4a', 'ogg', 'webm']:
                file_ext = 'wav'
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}') as tmp_file:
                tmp_file.write(file_response)
                tmp_path = tmp_file.name
            
            # Load audio using librosa
            audio_data, sample_rate = librosa.load(tmp_path, sr=16000, duration=30)
            
            # Clean up
            os.unlink(tmp_path)
            
            return audio_data, sample_rate
            
        except Exception as e:
            print(f"Error downloading directly: {str(e)}")
            return None, None
    
    def _download_and_load_audio(self, url: str) -> Tuple[Optional[np.ndarray], Optional[int]]:
        """
        Download audio file and load it using librosa.
        
        Args:
            url: URL of the audio file (public Supabase Storage URL)
            
        Returns:
            Tuple of (audio_data, sample_rate) or (None, None) on error
        """
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()  # Raises exception if HTTP error
            
            # Determine file extension from URL
            file_ext = url.split('.')[-1].lower() if '.' in url else 'wav'
            if file_ext not in ['wav', 'mp3', 'm4a', 'ogg', 'webm']:
                file_ext = 'wav'  # Default fallback
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}') as tmp_file:
                tmp_file.write(response.content) 
                tmp_path = tmp_file.name  
            
            # Load audio using librosa (resamples to 16kHz for YAMNet)
            audio_data, sample_rate = librosa.load(tmp_path, sr=16000, duration=30)
            
            # Clean up temporary file
            os.unlink(tmp_path)
            
            return audio_data, sample_rate
            
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error downloading audio: {e}")
            print(f"URL: {url}")
            print(f"Status code: {e.response.status_code if hasattr(e, 'response') else 'unknown'}")
            return None, None
        except Exception as e:
            print(f"Error downloading/loading audio: {str(e)}")
            print(f"URL: {url}")
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
        Run emotion detection using Wav2Vec2-based model.
        
        Args:
            audio_data: Audio waveform data
            sample_rate: Sample rate of the audio
            
        Returns:
            Dictionary with emotion detection results
        """
        try:
            if self.emotion_classifier is None:
                raise Exception("Emotion classifier not initialized")
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                sf.write(tmp_file.name, audio_data, sample_rate)
                tmp_path = tmp_file.name
            
            results = self.emotion_classifier(tmp_path)
            
            os.unlink(tmp_path)
            
            if isinstance(results, list) and len(results) > 0:
                top_emotion = results[0]
                emotion_label = top_emotion.get("label", "neutral")
                emotion_score = top_emotion.get("score", 0.0)
            else:
                emotion_label = "neutral"
                emotion_score = 0.5
            
            return {
                "emotion": emotion_label,
                "emotion_score": float(emotion_score)
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

