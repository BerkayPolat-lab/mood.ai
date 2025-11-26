"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import { sha256 } from "@/lib/utils";
import AudioUpload from "@/app/components/AudioUpload";
import PredictionsList from "@/app/components/PredictionsList";
import { fetchUserPredictions, PredictionWithUpload } from "@/app/actions/predictions";

// Cache interface for client-side caching
interface PredictionsCache {
  predictions: PredictionWithUpload[];
  timestamp: number;
  userId: string;
}

const CACHE_DURATION_MS = 30 * 1000; // Cache valid for 30 seconds
const CACHE_SIZE = 5; // Cache last 5 predictions

export default function DashboardPage() {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [predictions, setPredictions] = useState<PredictionWithUpload[]>([]);
  const [predictionsLoading, setPredictionsLoading] = useState(true);
  const [predictionsError, setPredictionsError] = useState<string | null>(null);
  const router = useRouter();
  const supabase = createClient();

  // Client-side cache for predictions
  const getCachedPredictions = (userId: string): PredictionWithUpload[] | null => {
    try {
      const cacheKey = `predictions_cache_${userId}`;
      const cached = sessionStorage.getItem(cacheKey);
      
      if (!cached) return null;
      
      const cacheData: PredictionsCache = JSON.parse(cached);
      const now = Date.now();
      
      // Check if cache is valid (not expired and same user)
      if (
        cacheData.userId === userId &&
        now - cacheData.timestamp < CACHE_DURATION_MS &&
        cacheData.predictions.length > 0
      ) {
        // Return only the last 5 cached predictions
        return cacheData.predictions.slice(0, CACHE_SIZE);
      }
      
      // Cache expired or invalid, remove it
      sessionStorage.removeItem(cacheKey);
      return null;
    } catch {
      return null;
    }
  };

  const setCachedPredictions = (userId: string, predictions: PredictionWithUpload[]) => {
    try {
      const cacheKey = `predictions_cache_${userId}`;
      const cacheData: PredictionsCache = {
        predictions: predictions.slice(0, CACHE_SIZE), // Only cache last 5
        timestamp: Date.now(),
        userId,
      };
      sessionStorage.setItem(cacheKey, JSON.stringify(cacheData));
    } catch (error) {
      console.warn("Failed to cache predictions:", error);
      // Fail silently - caching is not critical
    }
  };

  useEffect(() => {
    const checkUser = async () => {
      const {
        data: { user },
      } = await supabase.auth.getUser();

      if (!user) {
        router.push("/sign-in");
        return;
      }

      setUser(user);
      setLoading(false);
      
      // Check cache first
      const cached = getCachedPredictions(user.id);
      if (cached && cached.length > 0) {
        setPredictions(cached);
        setPredictionsLoading(false);
        // Fetch fresh data in background
        loadPredictions(user.id, false); // false = don't show loading state
      } else {
        // No cache, fetch immediately
        loadPredictions(user.id, true);
      }
    };

    checkUser();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadPredictions = async (userId: string, showLoading: boolean = true) => {
    if (showLoading) {
      setPredictionsLoading(true);
    }
    setPredictionsError(null);
    
    const result = await fetchUserPredictions();
    
    if (result.success && result.predictions) {
      // Limit to 10 predictions for display
      const limitedPredictions = result.predictions.slice(0, 10);
      setPredictions(limitedPredictions);
      
      // Update cache with fresh data
      setCachedPredictions(userId, limitedPredictions);
    } else {
      setPredictionsError(result.error || "Failed to load predictions");
    }
    
    if (showLoading) {
      setPredictionsLoading(false);
    }
  };

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    router.push("/");
    router.refresh();
  };

  // Set up Supabase Realtime subscription for new predictions
  useEffect(() => {
    if (!user) return;

    const userIdSha256 = sha256(user.id);

    // Subscribe to new predictions for this user
    const channel = supabase
      .channel('predictions-changes')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'predictions',
          filter: `user_id_sha256=eq.${userIdSha256}`,
        },
        (payload) => {
          console.log('New prediction detected:', payload.new);
          // Clear cache and reload predictions when new one is inserted
          try {
            const cacheKey = `predictions_cache_${user.id}`;
            sessionStorage.removeItem(cacheKey);
          } catch {
            // Ignore cache errors
          }
          // Fetch fresh predictions in background
          loadPredictions(user.id, false).catch((err) => {
            console.error('Error reloading predictions after realtime update:', err);
          });
        }
      )
      .subscribe();
    
    return () => {
      supabase.removeChannel(channel);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, supabase]);

  // Refresh predictions after upload (Realtime subscription will also trigger)
  const handleUploadSuccess = () => {
    if (!user) return;
    
    // Clear cache on new upload to force fresh fetch
    try {
      const cacheKey = `predictions_cache_${user.id}`;
      sessionStorage.removeItem(cacheKey);
    } catch {
      // Ignore cache errors
    }
    
    setTimeout(() => {
      if (user) {
        loadPredictions(user.id, false); // false = update in background
      }
    }, 2000);
  };

  // Refresh handler for manual refresh
  const handleRefresh = () => {
    if (!user) return;
    
    // Clear cache and fetch fresh
    try {
      const cacheKey = `predictions_cache_${user.id}`;
      sessionStorage.removeItem(cacheKey);
    } catch {
      // Ignore cache errors
    }
    
    loadPredictions(user.id, true);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0F0F10] text-[#F3F4F6] flex items-center justify-center">
        <div className="text-[#9CA3AF]">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0F0F10] text-[#F3F4F6]">
      {/* Navigation */}
      <nav className="container mx-auto px-6 py-6 flex justify-between items-center border-b border-[#1F2937]">
        <Link
          href="/"
          className="text-2xl font-bold bg-gradient-to-r from-[#7C3AED] via-[#3B82F6] to-[#06B6D4] bg-clip-text text-transparent"
        >
          mood.ai
        </Link>
        <div className="flex items-center gap-4">
          <span className="text-[#9CA3AF] text-sm">{user?.email}</span>
          <button
            onClick={handleSignOut}
            className="px-4 py-2 rounded-lg border border-[#1F2937] hover:border-[#EC4899] transition-colors text-sm"
          >
            Sign Out
          </button>
        </div>
      </nav>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-12">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-[#7C3AED] to-[#3B82F6] bg-clip-text text-transparent">
            Dashboard
          </h1>
          <p className="text-[#9CA3AF] mb-8">
            Upload audio clips to analyze mood, emotion, and energy levels.
          </p>

          <AudioUpload onUploadSuccess={handleUploadSuccess} />
          
          {/* Predictions Section */}
          <div className="mt-12">
            <PredictionsList
              predictions={predictions}
              loading={predictionsLoading}
              error={predictionsError}
              onRefresh={handleRefresh}
            />
          </div>
        </div>
      </main>
    </div>
  );
}
