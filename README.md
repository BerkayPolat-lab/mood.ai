# mood.ai - Audio Mood Analyzer

A Next.js web application that analyzes audio clips (speech, music, ambient sounds) to detect mood, emotion, and energy levels using machine learning.

## Features

- 🔐 Supabase Authentication (Sign In/Sign Up)
- 🎵 Audio Upload (10-20 second clips)
- 🤖 ML Pipeline Integration for mood analysis
- 📊 Detailed mood insights (emotion, energy level, confidence scores)
- 🎨 Modern, vibrant UI with custom color palette

## Tech Stack

- **Framework**: Next.js 16 (App Router)
- **Authentication**: Supabase Auth
- **Database**: PostgreSQL (via Supabase)
- **Styling**: Tailwind CSS 4
- **TypeScript**: Full type safety

## Getting Started

### Prerequisites

- Node.js 18+ installed
- A Supabase project (sign up at [supabase.com](https://supabase.com))

### Installation

1. Clone the repository and install dependencies:

```bash
npm install
```

2. Set up environment variables:

Create a `.env.local` file in the root directory:

```env
NEXT_PUBLIC_SUPABASE_PROJECT_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_API_KEY=your_supabase_anon_key
```

3. Set up the database:

Run the SQL queries from `schema.sql` in your Supabase SQL Editor to create the required tables:
- `uploads` - Stores uploaded audio files
- `jobs` - Tracks ML pipeline processing jobs
- `predictions` - Stores ML inference results

4. Run the development server:

```bash
npm run dev
```

5. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Database Schema

The application uses three main tables:

### uploads
- `id` (UUID) - Primary key
- `audio_file_path` (TEXT) - Path to uploaded audio file
- `file_size` (BIGINT) - Size of the file in bytes
- `user_id_sha256` (TEXT) - SHA256 hash of user ID
- `created_at` (TIMESTAMP) - Upload timestamp

### jobs
- `id` (UUID) - Primary key
- `upload_id` (UUID) - Foreign key to uploads table
- `user_id_sha256` (TEXT) - SHA256 hash of user ID
- `status` (TEXT) - Job status: 'queued', 'processing', 'completed', 'failed'
- `error` (TEXT) - Error message if job failed
- `started_at` (TIMESTAMP) - Job start time
- `finished_at` (TIMESTAMP) - Job completion time
- `created_at` (TIMESTAMP) - Job creation timestamp

### predictions
- `id` (UUID) - Primary key
- `user_id_sha256` (TEXT) - SHA256 hash of user ID
- `upload_id` (UUID) - Foreign key to uploads table
- `scores` (JSONB) - ML pipeline output (mood, emotion, energy_level, confidence)
- `model_version` (TEXT) - Version of the ML model used
- `inference_time` (FLOAT) - Time taken for inference
- `model_name` (TEXT) - Name of the ML model
- `created_at` (TIMESTAMP) - Prediction timestamp

## Color Palette

- **Primary**: Electric Purple (#7C3AED), Vibrant Blue (#3B82F6), Aqua Cyan (#06B6D4)
- **Secondary**: Hot Pink (#EC4899), Neon Green (#10B981)
- **Neutrals**: Rich Black (#0F0F10), Charcoal (#1F2937), Soft Gray (#9CA3AF), Off-White (#F3F4F6)

## Project Structure

```
mood.ai/
├── app/
│   ├── page.tsx          # Landing page
│   ├── sign-in/          # Sign in page
│   ├── sign-up/          # Sign up page
│   ├── dashboard/        # User dashboard (after authentication)
│   ├── layout.tsx        # Root layout
│   └── globals.css       # Global styles with color palette
├── lib/
│   ├── supabase/         # Supabase client configuration
│   └── utils.ts          # Utility functions (SHA256 hashing)
├── schema.sql            # PostgreSQL database schema
└── package.json          # Dependencies
```

## Next Steps

- Implement audio upload functionality
- Integrate ML pipeline for mood analysis
- Add audio playback and visualization
- Display prediction results in dashboard
- Add user history and analytics

## Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [Supabase Documentation](https://supabase.com/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
