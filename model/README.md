# Audio Mood Analysis Worker

This worker service processes audio files uploaded to Supabase, runs YAMNet and Wav2Vec2 inference, and stores results in the database.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Worker

```bash
python model/services/worker.py
```

The worker will:
1. Poll for jobs with status `queued`
2. Update job status to `processing`
3. Download audio file from Supabase Storage
4. Run YAMNet for sound classification
5. Run Wav2Vec2-based emotion detection
6. Store results in `predictions` table
7. Update job status to `completed` or `failed`

## Models Used

- **YAMNet**: Sound classification (521 audio event classes)
- **Wav2Vec2**: Emotion detection (using pre-trained emotion models)

