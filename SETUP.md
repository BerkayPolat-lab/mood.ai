# mood.ai - Setup Guide

Complete step-by-step installation instructions for setting up the mood.ai application.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js** 18+ ([Download](https://nodejs.org/))
- **Python** 3.9+ ([Download](https://www.python.org/downloads/))
- **Git** ([Download](https://git-scm.com/downloads))
- **GitHub account** (for cloning the repository)
- **Supabase account** (free tier works - [Sign up](https://supabase.com))
- **Hugging Face account** (for accessing the fine-tuned model - [Sign up](https://huggingface.co))

---

## Step 1: Clone the Repository

1. Open your terminal/command prompt
2. Navigate to the directory where you want to clone the project
3. Clone the repository:

```bash
git clone https://github.com/BerkayPolat-lab/mood.ai.git
cd mood.ai
```

---

## Step 2: Set Up Supabase Project

### 2.1 Create a Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign in (or create an account)
2. Click **"New Project"** in the dashboard
3. Fill in the project details:
   - **Project Name**: `mood-ai` (or your preferred name)
   - **Database Password**: Create a strong password and **save it securely** (you'll need it later)
   - **Region**: Choose the region closest to you
4. Click **"Create new project"**
5. Wait 2-3 minutes for the project to be fully provisioned

### 2.2 Get Supabase Credentials

1. In your Supabase project dashboard, go to **Settings** → **API**
2. Copy the following values:
   - **Project URL** (under "Project URL")
   - **`anon` `public` key** (under "Project API keys" → "anon public")
3. Go to **Settings** → **API** → **Service Role** (scroll down)
4. Copy the **`service_role` key** (⚠️ **Keep this secret** - it has admin access)

---

## Step 3: Set Up Supabase Storage

### 3.1 Create Storage Bucket

1. In your Supabase dashboard, go to **Storage** (left sidebar)
2. Click **"Create a new bucket"**
3. Configure the bucket:
   - **Name**: `audio_files`
   - **Public bucket**: **No** (keep it private)
4. Click **"Create bucket"**

### 3.2 Set Up Storage Policies

1. Go to **Storage** → **Policies** (or click on the `audio_files` bucket → **Policies**)
2. Create a policy for authenticated users to upload files:
   - Click **"New Policy"** → **"For full customization"**
   - **Policy name**: `Allow authenticated uploads`
   - **Allowed operation**: `INSERT`
   - **Target roles**: `authenticated`
   - **Policy definition**: `true`
   - Click **"Review"** → **"Save policy"**

3. Create a policy for authenticated users to read files:
   - Click **"New Policy"** → **"For full customization"**
   - **Policy name**: `Allow authenticated reads`
   - **Allowed operation**: `SELECT`
   - **Target roles**: `authenticated`
   - **Policy definition**: `true`
   - Click **"Review"** → **"Save policy"**

---

## Step 4: Set Up Database Schema

1. In your Supabase dashboard, go to **SQL Editor** (left sidebar)
2. Click **"New query"**
3. Open the file `infra/schema.sql` from your cloned repository
4. Copy **all** the SQL code from the file
5. Paste it into the Supabase SQL Editor
6. Click **"Run"** (or press `Cmd/Ctrl + Enter`)
7. Verify the tables were created:
   - Go to **Table Editor** (left sidebar)
   - You should see these tables: `uploads`, `jobs`, `predictions`, `playlists`

---

## Step 5: Set Up Environment Variables

### 5.1 Frontend Environment Variables

1. In the **root directory** of the project, create a file named `.env.local`:

```bash
# In the root directory (mood.ai/)
touch .env.local
```

2. Open `.env.local` in a text editor and add:

```env
NEXT_PUBLIC_SUPABASE_PROJECT_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_API_KEY=your-anon-public-key-here
```

**Replace the values:**
- `your-project-id.supabase.co` → Your Supabase Project URL from Step 2.2
- `your-anon-public-key-here` → Your `anon public` key from Step 2.2

### 5.2 Backend Worker Environment Variables

1. Navigate to the `model` directory:

```bash
cd model
```

2. Create a file named `.env.local`:

```bash
touch .env.local
```

3. Open `model/.env.local` in a text editor and add:

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
HF_ACCESS_TOKEN=your-huggingface-token-here
```

**Replace the values:**
- `your-project-id.supabase.co` → Your Supabase Project URL (same as frontend)
- `your-service-role-key-here` → Your `service_role` key from Step 2.2
- `your-huggingface-token-here` → Your Hugging Face access token (see Step 5.3)

### 5.3 Get Hugging Face Access Token

1. Go to [huggingface.co](https://huggingface.co) and sign in (or create an account)
2. Go to **Settings** → **Access Tokens** (or visit [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens))
3. Click **"New token"**
4. Configure the token:
   - **Name**: `mood-ai-worker` (or your preferred name)
   - **Type**: **Read** (read access is sufficient)
5. Click **"Generate a token"**
6. **Copy the token immediately** (you won't be able to see it again)
7. Paste it into `model/.env.local` as `HF_ACCESS_TOKEN`

---

## Step 6: Install Node.js Dependencies

1. Make sure you're in the **root directory** of the project:

```bash
# If you're in the model directory, go back to root
cd ..
```

2. Install dependencies:

```bash
npm install
```

This will install all required Node.js packages (Next.js, Supabase, React, etc.)

---

## Step 7: Install Python Dependencies

1. Navigate to the `model` directory:

```bash
cd model
```

2. Create a Python virtual environment (recommended):

```bash
python3 -m venv myenv
```

3. Activate the virtual environment:

**On macOS/Linux:**
```bash
source myenv/bin/activate
```

**On Windows:**
```bash
myenv\Scripts\activate
```

You should see `(myenv)` at the beginning of your terminal prompt.

4. Install Python dependencies:

```bash
pip install -r requirements.txt
```

This will install:
- Supabase Python client
- TensorFlow and TensorFlow Hub (for YAMNet)
- PyTorch and Transformers (for HuBERT emotion detection)
- Audio processing libraries (librosa, soundfile)
- Other required dependencies

**Note**: This may take several minutes, especially when installing TensorFlow and PyTorch.

---

## Step 8: Run the Application

### 8.1 Start the Development Server

1. Make sure you're in the **root directory** of the project
2. Start the Next.js development server:

```bash
npm run dev
```

3. You should see output like:
```
  ▲ Next.js 16.0.3
  - Local:        http://localhost:3000
```

4. The application is now running at [http://localhost:3000](http://localhost:3000)

### 8.2 Start the ML Worker (Separate Terminal)

1. Open a **new terminal window/tab** (keep the dev server running)
2. Navigate to the `model` directory:

```bash
cd model
```

3. Activate the virtual environment (if not already activated):

**On macOS/Linux:**
```bash
source myenv/bin/activate
```

**On Windows:**
```bash
myenv\Scripts\activate
```

4. Run the worker:

```bash
python services/worker.py
```

**OR** (alternative method):

```bash
python3 -m services.worker
```

5. You should see output like:
```
Loading YAMNet model...
Loading fine-tuned HuBERT emotion classifier...
Worker initialized successfully
Polling for jobs...
```

The worker will now:
- Poll for queued jobs every 5 seconds
- Download audio files from Supabase Storage
- Run YAMNet for sound classification
- Run HuBERT for emotion detection
- Store results in the database

---

## Step 9: Test the Application

1. Open your browser and go to [http://localhost:3000](http://localhost:3000)
2. You should see the landing page
3. Click **"Sign Up"** to create a new account
4. Fill in your email and password, then click **"Sign Up"**
5. After sign-up, you'll be redirected to the dashboard
6. Upload an audio file:
   - Click **"Select Audio File"**
   - Choose an audio file (MP3, WAV, OGG, WebM, or M4A)
   - File must be **0-30 seconds** in duration
   - Click **"Upload & Analyze"**
7. Wait a few seconds for the worker to process the file
8. Check the **"Analysis Results"** section below to see the results

---

## Need Help?

- Check the [README.md](README.md) for more information
- Review [Supabase Documentation](https://supabase.com/docs)
- Check [Next.js Documentation](https://nextjs.org/docs)

---

