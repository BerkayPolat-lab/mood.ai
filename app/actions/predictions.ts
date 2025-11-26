"use server";

import { createClient } from "@/lib/supabase/server";
import { sha256 } from "@/lib/utils";

export interface PredictionWithUpload {
  id: string;
  upload_id: string;
  scores: {
    sound_classification: string;
    yamnet_top_classes: Array<{ class: string; score: number }>;
    yamnet_confidence: number;
    emotion: string;
    emotion_score: number;
  };
  created_at: string;
  upload: {
    id: string;
    file_size: number;
    created_at: string;
  };
}

export interface FetchPredictionsResult {
  success: boolean;
  predictions?: PredictionWithUpload[];
  error?: string;
}

export async function fetchUserPredictions(): Promise<FetchPredictionsResult> {
  try {
    const supabase = await createClient();
    
    // Get authenticated user
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    
    if (authError || !user) {
      return {
        success: false,
        error: "Authentication required",
      };
    }
    
    // Generate user_id_sha256
    const userIdSha256 = sha256(user.id);
    
    // Fetch predictions with uploads join
    // LIMIT 10: Only fetch the 10 most recent predictions for performance
    const { data: predictions, error: fetchError } = await supabase
      .from("predictions")
      .select(`
        id,
        upload_id,
        scores,
        created_at,
        uploads (
          id,
          file_size,
          created_at
        )
      `)
      .eq("user_id_sha256", userIdSha256)
      .order("created_at", { ascending: false })
      .limit(10);
    
    if (fetchError) {
      return {
        success: false,
        error: `Failed to fetch predictions: ${fetchError.message}`,
      };
    }
    
    // Transform data - Supabase returns nested structure
    // The "uploads" field comes back as either an array or single object
    type SupabasePredictionResponse = {
      id: string;
      upload_id: string;
      scores: PredictionWithUpload['scores'];
      created_at: string;
      uploads: {
        id: string;
        file_size: number;
        created_at: string;
      } | Array<{
        id: string;
        file_size: number;
        created_at: string;
      }>;
    };

    const transformedPredictions: PredictionWithUpload[] = (predictions || []).map((pred: SupabasePredictionResponse) => ({
      id: pred.id,
      upload_id: pred.upload_id,
      scores: pred.scores,
      created_at: pred.created_at,
      upload: Array.isArray(pred.uploads) ? pred.uploads[0] : pred.uploads,
    }));
    
    return {
      success: true,
      predictions: transformedPredictions,
    };
    
  } catch (error) {
    console.error("Error fetching predictions:", error);
    return {
      success: false,
      error: error instanceof Error ? error.message : "An unexpected error occurred",
    };
  }
}

