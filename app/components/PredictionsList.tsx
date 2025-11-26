"use client";

import { PredictionWithUpload } from "@/app/actions/predictions";
import PredictionCard from "./PredictionCard";

interface PredictionsListProps {
  predictions: PredictionWithUpload[];
  loading: boolean;
  error: string | null;
  onRefresh?: () => void;
}

export default function PredictionsList({
  predictions,
  loading,
  error,
  onRefresh,
}: PredictionsListProps) {
  if (loading) {
    return (
      <div className="bg-[#1F2937] rounded-xl p-8 border border-[#1F2937]">
        <h2 className="text-2xl font-semibold mb-4 text-[#F3F4F6]">
          Analysis Results
        </h2>
        <div className="text-center py-8 text-[#9CA3AF]">Loading predictions...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-[#1F2937] rounded-xl p-8 border border-[#1F2937]">
        <h2 className="text-2xl font-semibold mb-4 text-[#F3F4F6]">
          Analysis Results
        </h2>
        <div className="p-4 rounded-lg bg-red-500/20 border border-red-500/50 text-red-400">
          {error}
        </div>
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="mt-4 px-4 py-2 rounded-lg bg-[#7C3AED] hover:bg-[#6D28D9] transition-colors"
          >
            Retry
          </button>
        )}
      </div>
    );
  }

  if (predictions.length === 0) {
    return (
      <div className="bg-[#1F2937] rounded-xl p-8 border border-[#1F2937]">
        <h2 className="text-2xl font-semibold mb-4 text-[#F3F4F6]">
          Analysis Results
        </h2>
        <div className="text-center py-8 text-[#9CA3AF]">
          No analysis results yet. Upload an audio file to get started!
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[#1F2937] rounded-xl p-8 border border-[#1F2937]">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-semibold text-[#F3F4F6]">
          Analysis Results
        </h2>
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="text-sm px-4 py-2 rounded-lg border border-[#1F2937] hover:border-[#7C3AED] transition-colors text-[#9CA3AF]"
          >
            Refresh
          </button>
        )}
      </div>

      <div className="space-y-6">
        {predictions.map((prediction) => (
          <PredictionCard key={prediction.id} prediction={prediction} />
        ))}
      </div>
    </div>
  );
}

