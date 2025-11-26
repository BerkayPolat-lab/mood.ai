"use client";

import { formatDistanceToNow } from "date-fns";
import { PredictionWithUpload } from "@/app/actions/predictions";

interface PredictionCardProps {
  prediction: PredictionWithUpload;
}

export default function PredictionCard({ prediction }: PredictionCardProps) {
  const formatTimestamp = (timestamp: string): string => {
    try {
      return formatDistanceToNow(new Date(timestamp), { addSuffix: true });
    } catch {
      return new Date(timestamp).toLocaleString();
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const getEmotionColor = (emotion: string): string => {
    const emotionColors: Record<string, string> = {
      happy: "text-[#10B981]",
      sad: "text-[#3B82F6]",
      angry: "text-[#EF4444]",
      neutral: "text-[#9CA3AF]",
      excited: "text-[#F59E0B]",
      calm: "text-[#06B6D4]",
      surprised: "text-[#8B5CF6]",
      fearful: "text-[#6366F1]",
      disgusted: "text-[#EC4899]",
    };
    return emotionColors[emotion.toLowerCase()] || "text-[#9CA3AF]";
  };

  const scores = prediction.scores;

  return (
    <div className="bg-[#0F0F10] rounded-lg p-6 border border-[#1F2937] hover:border-[#7C3AED]/50 transition-colors">
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div>
          <div className="text-sm text-[#9CA3AF]">
            {formatTimestamp(prediction.created_at)}
          </div>
        </div>
      </div>

      {/* Emotion & Sound Classification */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          <div className="text-sm text-[#9CA3AF] mb-1">Emotion</div>
          <div className={`text-2xl font-bold capitalize ${getEmotionColor(scores.emotion)}`}>
            {scores.emotion}
          </div>
          <div className="text-sm text-[#6B7280]">
            Confidence: {(scores.emotion_score * 100).toFixed(1)}%
          </div>
        </div>
        <div>
          <div className="text-sm text-[#9CA3AF] mb-1">Sound Type</div>
          <div className="text-xl font-semibold text-[#F3F4F6]">
            {scores.sound_classification}
          </div>
          <div className="text-sm text-[#6B7280]">
            Confidence: {(scores.yamnet_confidence * 100).toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Top Classes */}
      {scores.yamnet_top_classes && scores.yamnet_top_classes.length > 0 && (
        <div className="mb-4">
          <div className="text-sm text-[#9CA3AF] mb-2">Top Classifications</div>
          <div className="flex flex-wrap gap-2">
            {scores.yamnet_top_classes.slice(0, 3).map((item, idx) => (
              <span
                key={idx}
                className="px-3 py-1 rounded-full bg-[#1F2937] text-xs text-[#9CA3AF] border border-[#1F2937]"
              >
                {item.class} ({(item.score * 100).toFixed(0)}%)
              </span>
            ))}
          </div>
        </div>
      )}

      {/* File Info */}
      <div className="pt-4 border-t border-[#1F2937]">
        <div className="flex justify-between text-xs text-[#6B7280]">
          <span>File size: {formatFileSize(prediction.upload.file_size)}</span>
          <span>
            Uploaded: {formatTimestamp(prediction.upload.created_at)}
          </span>
        </div>
      </div>
    </div>
  );
}

