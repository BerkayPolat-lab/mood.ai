"use client";

import { useState, useRef } from "react";
import { uploadAudioFile } from "@/app/actions/upload";

interface AudioUploadProps {
  onUploadSuccess?: () => void;
}

export default function AudioUpload({ onUploadSuccess }: AudioUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [duration, setDuration] = useState<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    setError(null);
    setSuccess(false);

    // Validate file type
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

    if (!validAudioTypes.includes(selectedFile.type)) {
      setError(
        "Invalid file type. Please select an audio file (MP3, WAV, OGG, WebM, M4A)."
      );
      return;
    }

    const audio = new Audio();
    audio.preload = "metadata";

    audio.onloadedmetadata = () => {
      const audioDuration = audio.duration;
      setDuration(audioDuration);

      // Validate duration (0-30 seconds)
      if (audioDuration > 30) {
        setError(
          `Audio duration must be between 0-30 seconds. Your file is ${audioDuration.toFixed(
            1
          )} seconds.`
        );
        setFile(null);
        if (fileInputRef.current) {
          fileInputRef.current.value = "";
        }
        return;
      }

      setFile(selectedFile);
    };

    audio.onerror = () => {
      setError("Could not read audio file. Please try another file.");
    };

    const objectUrl = URL.createObjectURL(selectedFile);
    audio.src = objectUrl;
    audioRef.current = audio;
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);
    setSuccess(false);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const result = await uploadAudioFile(formData);

      if (result.success) {
        setSuccess(true);
        setFile(null);
        setDuration(null);
        if (fileInputRef.current) {
          fileInputRef.current.value = "";
        }
        // Clean up audio object URL
        if (audioRef.current) {
          URL.revokeObjectURL(audioRef.current.src);
          audioRef.current = null;
        }
        
        // Call success callback if provided
        if (onUploadSuccess) {
          onUploadSuccess();
        }
      } else {
        setError(result.error || "Upload failed");
      }
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred");
    } finally {
      setUploading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setDuration(null);
    setError(null);
    setSuccess(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
    if (audioRef.current) {
      URL.revokeObjectURL(audioRef.current.src);
      audioRef.current = null;
    }
  };

  return (
    <div className="bg-[#1F2937] rounded-xl p-8 border border-[#1F2937]">
      <h2 className="text-2xl font-semibold mb-4 text-[#F3F4F6]">
        Upload Audio Clip
      </h2>
      <p className="text-[#9CA3AF] mb-6">
        Upload a 0-30 second audio clip (speech, music, or ambient sound) for
        mood analysis.
      </p>

      {success && (
        <div className="mb-4 p-4 rounded-lg bg-[#10B981]/20 border border-[#10B981]/50 text-[#10B981]">
          ✓ Audio uploaded successfully! Processing will begin shortly.
        </div>
      )}

      {error && (
        <div className="mb-4 p-4 rounded-lg bg-red-500/20 border border-red-500/50 text-red-400">
          {error}
        </div>
      )}

      <div className="space-y-4">
        <div>
          <label
            htmlFor="audio-file"
            className="block text-sm font-medium mb-2 text-[#F3F4F6]"
          >
            Select Audio File
          </label>
          <input
            ref={fileInputRef}
            id="audio-file"
            type="file"
            accept="audio/*"
            onChange={handleFileSelect}
            disabled={uploading}
            className="w-full px-4 py-3 rounded-lg bg-[#0F0F10] border border-[#1F2937] text-[#F3F4F6] focus:outline-none focus:border-[#7C3AED] transition-colors disabled:opacity-50 disabled:cursor-not-allowed file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-[#7C3AED] file:text-white file:cursor-pointer hover:file:bg-[#6D28D9]"
          />
        </div>

        {file && duration !== null && (
          <div className="p-4 rounded-lg bg-[#0F0F10] border border-[#1F2937]">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-[#9CA3AF]">File:</span>
              <span className="text-sm font-medium text-[#F3F4F6]">
                {file.name}
              </span>
            </div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-[#9CA3AF]">Size:</span>
              <span className="text-sm font-medium text-[#F3F4F6]">
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-[#9CA3AF]">Duration:</span>
              <span
                className={`text-sm font-medium ${
                  duration >= 0 && duration <= 30
                    ? "text-[#10B981]"
                    : "text-red-400"
                }`}
              >
                {duration.toFixed(1)} seconds
              </span>
            </div>
          </div>
        )}

        <div className="flex gap-4">
          <button
            onClick={handleUpload}
            disabled={!file || uploading || (duration !== null && (duration < 0 || duration > 30))}
            className="flex-1 px-6 py-3 rounded-lg bg-gradient-to-r from-[#7C3AED] to-[#3B82F6] hover:from-[#6D28D9] hover:to-[#2563EB] transition-all font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {uploading ? "Uploading..." : "Upload & Analyze"}
          </button>
          {file && (
            <button
              onClick={handleReset}
              disabled={uploading}
              className="px-6 py-3 rounded-lg border border-[#1F2937] hover:border-[#9CA3AF] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Clear
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

