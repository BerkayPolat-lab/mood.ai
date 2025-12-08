# mood.ai - Audio Mood Analyzer

A Next.js web application that analyzes audio clips (speech, music, ambient sounds) to detect emotion and sound-type using machine learning.

## Features

- 🔐 Supabase Authentication (Sign In/Sign Up)
- 🎵 Audio Upload (10-20 second clips)
- 🤖 ML Pipeline Integration for mood analysis
- 📊 Detailed mood insights (emotion, energy level, confidence scores)
- 🎨 Modern, vibrant UI with custom color palette

## What it Does?

Mood.ai allows users to upload an audio clip (speech, music, etc.) and detects the conveyed emotion and the form of sound (speech, siren, etc.) in the recording. The analysis results component showcases the past audio uploads and the authentication system provides a connection between the clips and the user. 

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/BerkayPolat-lab/mood.ai.git
cd mood.ai
```

2. The application runs with Supabase. Therefore:

Go to supabase.com and sign in. Create a new project and store the Supabase API keys in a .env.local file (in the project root).  

```env
NEXT_PUBLIC_SUPABASE_PROJECT_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_API_KEY=your_supabase_anon_key
```

3. Use the infra/schema.sql file to build the tables. Set up Supabase storage with a new bucket:

Run the SQL queries from `schema.sql` in your Supabase SQL Editor to create the required tables:
- `uploads` - Stores uploaded audio files
- `jobs` - Tracks ML pipeline processing jobs
- `predictions` - Stores ML inference results


4. Install dependencies (root repository):

```bash
npm install
```

5. Create model/.env.local. Add the Supabase API keys and Hugging Face access token:

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
HF_ACCESS_TOKEN=your-huggingface-token-here
```

6. Install python dependencies:

```bash
# Navigate to model directory
cd model

# Create a virtual environment (recommended)
python3 -m venv myenv

# Activate virtual environment
# On macOS/Linux:
source myenv/bin/activate
# On Windows:
# myenv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

7. Run the development server:

```
npm run dev
```

8. Run the ML Worker (Separate terminal):

```
# Navigate to model directory
cd model

# Activate virtual environment if not already activated
source myenv/bin/activate  # macOS/Linux
# OR
# myenv\Scripts\activate  # Windows

# Run the worker
python services/worker.py
## or
python3 -m services.worker
```

9. Open [http://localhost:3000](http://localhost:3000) in your browser or check out the website [mood-ai-gamma.vercel.app](mood-ai-gamma.vercel.app)

## Video Links

- [Demo Video](./videos/demo.mp4)

- [Technical Walkthrough Video](./videos/technical_walkthrough.mp4)


## Evaluation

### Model Performance on RAVDESS Test Set

The fine-tuned HuBERT model (`superb/hubert-base-superb-er`) was evaluated on a speaker-independent test set from the RAVDESS dataset.

**Baseline Model Performance:**

| | **s3prl** | **transformers** |
|---|-----------|------------------|
| **superb/hubert-base-superb-er** | **0.6492** | **0.6359** |

**Overall Performance:**
- **Test Loss**: 1.2383
- **Test Accuracy**: 60.00%

**Classification Report:**

| Emotion   | Precision | Recall | F1-Score | Support |
|-----------|-----------|--------|----------|---------|
| neutral   | 0.6429    | 0.9000 | 0.7500   | 40      |
| calm      | 0.6102    | 0.9000 | 0.7273   | 80      |
| happy     | 0.4634    | 0.4750 | 0.4691   | 80      |
| sad       | 0.6500    | 0.3250 | 0.4333   | 80      |
| angry     | 0.6364    | 0.7000 | 0.6667   | 80      |
| fearful   | 0.8182    | 0.2250 | 0.3529   | 80      |
| surprise  | 0.7857    | 0.5500 | 0.6471   | 80      |
| disgust   | 0.5072    | 0.8750 | 0.6422   | 80      |
|           |           |        |          |         |
| **Macro Avg** | 0.6392 | 0.6188 | 0.5861 | 600     |
| **Weighted Avg** | 0.6390 | 0.6000 | 0.5751 | 600     |

**Confusion Matrix:**

```
                neutral  calm  happy  sad  angry  fearful  surprise  disgust
neutral           36      4      0     0      0        0         0        0
calm               6     72      0     2      0        0         0        0
happy              8      2     38     2      4        0         0       26
sad                2     40      8    26      0        0         4        0
angry              2      0      0     0     56        0         4       18
fearful            0      0     32    10      0       18         4       16
surprise           2      0      2     0     24        0        44        8
disgust            0      0      2     0      4        4         0       70
```

**Training Details:**
- **Dataset**: RAVDESS (Ryerson Audio-Visual Database of Emotional Speech and Song)
- **Training Strategy**: Freeze all HuBERT layers, train only classification head
- **Trainable Parameters**: 728,341 / 94,704,277 (0.77%)
- **Split**: Speaker-independent (16 actors train, 3 actors validation, 5 actors test)
- **Best Validation Accuracy**: 61.67% (achieved at epoch 13 with early stopping)

## Color Palette

- **Primary**: Electric Purple (#7C3AED), Vibrant Blue (#3B82F6), Aqua Cyan (#06B6D4)
- **Secondary**: Hot Pink (#EC4899), Neon Green (#10B981)
- **Neutrals**: Rich Black (#0F0F10), Charcoal (#1F2937), Soft Gray (#9CA3AF), Off-White (#F3F4F6)
