"use server";

import { createClient } from "@/lib/supabase/server";
import { sha256 } from "@/lib/utils";
import { revalidatePath } from "next/cache";

export interface UploadResult {
  success: boolean;
  uploadId?: string;
  jobId?: string;
  error?: string;
}

export async function uploadAudioFile(formData: FormData): Promise<UploadResult> {
  try {
    const supabase = await createClient();

    const {data: { user }, error: authError} = await supabase.auth.getUser();

    if (authError || !user) {
      return {
        success: false,
        error: "Authentication required. Please sign in.",
      };
    }

    const file = formData.get("file") as File;
    if (!file) {
      return {
        success: false,
        error: "No file provided",
      };
    }

    const validAudioTypes = [
      "audio/mpeg",
      "audio/mp3",
      "audio/wav",
      "audio/wave",
      "audio/x-wav",
      "audio/ogg",
      "audio/webm",
      "audio/mp4",
      "audio/x-m4a",
    ];

    if (!validAudioTypes.includes(file.type)) {
      return {
        success: false,
        error: `Invalid file type. Supported formats: MP3, WAV, OGG, WebM, M4A`,
      };
    }

    // Validate file size (max 10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      return {
        success: false,
        error: "File size exceeds 10MB limit",
      };
    }

    // Generate unique file path
    const fileExt = file.name.split(".").pop();
    const fileName = `${Date.now()}-${Math.random().toString(36).substring(7)}.${fileExt}`;
    const filePath = `${user.id}/${fileName}`;

    // Upload file to Supabase Storage
    const { error: uploadError } = await supabase.storage.from("audio_files").upload(filePath, file, {
        contentType: file.type,
        upsert: false,
      });

    if (uploadError) {
      return {
        success: false,
        error: `Upload failed: ${uploadError.message}`,
      };
    }

    // Get public URL for the file
    const {data: { publicUrl }} = supabase.storage.from("audio_files").getPublicUrl(filePath);

    const userIdSha256 = sha256(user.id);

    const { data: uploadRecord, error: insertError } = await supabase
      .from("uploads")
      .insert({
        audio_file_path: publicUrl,
        file_size: file.size,
        user_id_sha256: userIdSha256,
      })
      .select()
      .single();

    if (insertError || !uploadRecord) {
      await supabase.storage.from("audio_files").remove([filePath]);

      return {
        success: false,
        error: `Database error: ${insertError?.message || "Failed to create upload record"}`,
      };
    }

    const { data: jobRecord, error: jobError } = await supabase.from("jobs").insert({
        upload_id: uploadRecord.id,
        user_id_sha256: userIdSha256,
        status: "queued",
      })
      .select()
      .single();

    if (jobError || !jobRecord) {
      return {
        success: false,
        error: `Job creation error: ${jobError?.message || "Failed to create job"}`,
      };
    }

    // Revalidate dashboard to show new upload
    revalidatePath("/dashboard");

    return {
      success: true,
      uploadId: uploadRecord.id,
      jobId: jobRecord.id,
    };
  } catch (error) {
    console.error("Upload error:", error);
    const errorMessage =
      error instanceof Error ? error.message : "An unexpected error occurred";
    return {
      success: false,
      error: errorMessage,
    };
  }
}

