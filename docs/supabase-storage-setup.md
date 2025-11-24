# Supabase Storage Setup

## Create Storage Bucket

To enable audio file uploads, you need to create a storage bucket in Supabase:

1. Go to your Supabase project dashboard
2. Navigate to **Storage** in the sidebar
3. Click **New bucket**
4. Configure the bucket:
   - **Name**: `audio-uploads`
   - **Public bucket**: ✅ Yes (or No if you want private storage)
   - **File size limit**: 10 MB (or your preferred limit)
   - **Allowed MIME types**: 
     - `audio/mpeg`
     - `audio/mp3`
     - `audio/wav`
     - `audio/wave`
     - `audio/x-wav`
     - `audio/ogg`
     - `audio/webm`
     - `audio/mp4`
     - `audio/x-m4a`

5. Click **Create bucket**

## Set Up Storage Policies

If you made the bucket private, you'll need to set up Row Level Security (RLS) policies:

### Policy: Users can upload their own files

```sql
CREATE POLICY "Users can upload audio files"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (
  bucket_id = 'audio-uploads' AND
  (storage.foldername(name))[1] = auth.uid()::text
);
```

### Policy: Users can read their own files

```sql
CREATE POLICY "Users can read their own audio files"
ON storage.objects
FOR SELECT
TO authenticated
USING (
  bucket_id = 'audio-uploads' AND
  (storage.foldername(name))[1] = auth.uid()::text
);
```

### Policy: Users can delete their own files

```sql
CREATE POLICY "Users can delete their own audio files"
ON storage.objects
FOR DELETE
TO authenticated
USING (
  bucket_id = 'audio-uploads' AND
  (storage.foldername(name))[1] = auth.uid()::text
);
```

## Public Bucket (Alternative)

If you made the bucket public, files will be accessible to anyone with the URL. This is simpler but less secure. The upload action will still work, but you may want to add additional access controls.

## Verify Setup

After creating the bucket, test the upload functionality in the dashboard. The upload should:
1. Successfully upload the file to Supabase Storage
2. Create a record in the `uploads` table
3. Create a record in the `jobs` table with status `queued`

