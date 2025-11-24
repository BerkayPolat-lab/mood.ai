# Worker Setup Guide

## Overview

The worker service processes audio files uploaded to Supabase by:
1. Fetching queued jobs from the database
2. Downloading audio files from Supabase Storage (`audio_files` bucket)
3. Running YAMNet for sound classification
4. Running emotion detection (feature-based, ready for Wav2Vec2 fine-tuning)
5. Storing results in the `predictions` table
6. Updating job status (`queued` → `processing` → `completed`/`failed`)

## Prerequisites

- Python 3.8+
- Supabase project with:
  - `audio_files` storage bucket created
  - Database tables: `uploads`, `jobs`, `predictions`
  - Service role key (for bypassing RLS)

## Installation

1. Install Python dependencies:
```bash
cd model
pip install -r requirements.txt
```

## Running the Worker

### Direct Python execution
```bash
cd model
python services/worker.py
```

## How It Works

### Job Processing Flow

```
1. Worker polls for jobs with status='queued'
   ↓
2. Updates job status to 'processing'
   ↓
3. Fetches upload record (gets audio_file_path)
   ↓
4. Downloads audio file from Supabase Storage
   ↓
5. Runs YAMNet inference (sound classification)
   ↓
6. Runs emotion detection (feature-based or Wav2Vec2)
   ↓
7. Combines results into mood analysis
   ↓
8. Inserts prediction into database
   ↓
9. Updates job status to 'completed' or 'failed'
```

### Models Used

#### YAMNet
- **Purpose**: Sound classification (521 audio event classes)
- **Input**: 16kHz mono audio
- **Output**: Top sound classes with confidence scores
- **Model**: Pre-trained TensorFlow Hub model

#### Emotion Detection
- **Current**: Feature-based estimation (energy, tempo, spectral features)
- **Future**: Fine-tuned Wav2Vec2 model (ready for integration)
- **Output**: Emotion label (calm, happy, sad, neutral, etc.)

### Output Format (Future Implementation)

Results are stored in the `predictions` table with this JSON structure:

```json
{
  "mood": "calm",
  "emotion": "content",
  "energy_level": "low",
  "confidence": 0.91,
  "sound_classification": "Speech",
  "yamnet_confidence": 0.85,
  "emotion_confidence": 0.97
}
```

## Production Deployment

### Docker
Create `model/Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/ ./services/
COPY .env .env

CMD ["python", "services/worker.py"]
```

Build and run:
```bash
docker build -t mood-worker ./model
docker run -d --name mood-worker mood-worker
```

## Monitoring

### Logs
The worker prints status messages:
- `"Processing job: {job_id}"` - Job started
- `"✓ Job {job_id} completed successfully"` - Job completed
- `"✗ Job {job_id} failed: {error}"` - Job failed

### Database Monitoring
Query job status:
```sql
SELECT status, COUNT(*) 
FROM jobs 
GROUP BY status;
```

Check recent jobs:
```sql
SELECT id, status, started_at, finished_at, error
FROM jobs
ORDER BY created_at DESC
LIMIT 10;
```

## Troubleshooting

### "Job not found" error
- Verify the job exists in the database
- Check Supabase connection credentials

### "Upload not found" error
- Verify the upload record exists
- Check foreign key relationship

### "Failed to download audio file"
- Check `audio_file_path` in uploads table
- Verify Supabase Storage bucket is accessible
- Check network connectivity

### Model loading errors
- Ensure all dependencies are installed
- Check available disk space (models are large)
- Verify internet connection (models download from TensorFlow Hub/HuggingFace)

### Memory issues
- Reduce batch size if processing multiple files
- Use GPU if available (automatically detected)
- Consider processing one job at a time

