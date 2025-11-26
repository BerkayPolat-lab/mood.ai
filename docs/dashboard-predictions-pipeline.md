# Dashboard Predictions Display Pipeline Plan

## Overview
Implement a feature to display past audio file uploads and their associated mood analysis results on the dashboard page. Results should be fetched from Supabase, ordered chronologically (newest first), and displayed with all relevant scores and metadata.

**Performance Requirements:**
- Display maximum of **10 most recent predictions**
- **Cache the last 5 predictions** client-side for instant display and improved performance
- Cache enables faster page loads by serving cached data immediately while fetching updates in background

## Database Schema Reference

### Tables Involved

**`uploads` table:**
- `id` (UUID, Primary Key)
- `audio_file_path` (TEXT) - Path to audio file in storage
- `file_size` (BIGINT) - File size in bytes
- `user_id_sha256` (TEXT) - SHA256 hash of user ID
- `created_at` (TIMESTAMP) - Upload timestamp

**`predictions` table:**
- `id` (UUID, Primary Key)
- `user_id_sha256` (TEXT) - SHA256 hash of user ID
- `upload_id` (UUID, Foreign Key → `uploads.id`)
- `scores` (JSONB) - Mood analysis results
- `model_version` (TEXT) - Model version used
- `inference_time` (FLOAT) - Time taken for inference
- `model_name` (TEXT) - Name of the model
- `created_at` (TIMESTAMP) - Prediction timestamp

**`scores` JSONB Structure:**
```json
{
  "sound_classification": "Speech",
  "yamnet_top_classes": [
    {"class": "Speech", "score": 0.95},
    {"class": "Conversation", "score": 0.03}
  ],
  "yamnet_confidence": 0.95,
  "emotion": "happy",
  "emotion_score": 0.87
}
```

## Pipeline Flow

```
User visits Dashboard
        ↓
Check Authentication (existing)
        ↓
Check Client-Side Cache
  - Look for cached predictions (last 5)
  - If cache exists and fresh (< 30 seconds), display immediately
        ↓
Generate user_id_sha256 from user.id
        ↓
Fetch Predictions with Uploads JOIN
  - Filter by user_id_sha256
  - Order by predictions.created_at DESC
  - LIMIT 10 (only fetch 10 most recent)
  - Include upload metadata (file_path, file_size, created_at)
        ↓
Transform Data for Display
  - Parse scores JSONB
  - Format timestamps
  - Extract file metadata
        ↓
Update Cache
  - Store last 5 predictions in cache
  - Set cache timestamp
        ↓
Render Results Component
  - Display up to 10 predictions chronologically (newest first)
  - Show scores, emotion, sound classification
  - Show upload timestamp and file info
  - Handle loading/error states
```

## Implementation Plan

### Phase 1: Server Action for Fetching Predictions

**1.1 Create Server Action**

File: `app/actions/predictions.ts`

```typescript
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
    // depending on the relationship cardinality
    const transformedPredictions: PredictionWithUpload[] = (predictions || []).map((pred: any) => ({
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
```

**Key Points:**
- Server action ensures authentication
- Uses `sha256(user.id)` to match stored `user_id_sha256`
- **Single Query JOIN**: Uses Supabase's nested select syntax to fetch predictions and uploads in one query
  - More efficient than separate queries (1 database round trip vs 2+)
  - Automatically handles the foreign key relationship (`predictions.upload_id → uploads.id`)
  - Returns nested object structure for easy data access
- Orders by `created_at DESC` (newest first)
- **LIMIT 10**: Only fetches the 10 most recent predictions for optimal performance
- Only fetches necessary fields: id, upload_id, scores, created_at, and upload metadata (id, file_size, created_at)
- Excludes: inference_time, model_name, model_version, audio_file_path (not needed for display)
- Handles nested Supabase response structure

### Phase 2: Dashboard Component Updates

**2.1 Update Dashboard Page**

File: `app/dashboard/page.tsx`

Add state, caching, and effects to fetch predictions:

```typescript
"use client";

import { useEffect, useState, useMemo } from "react";
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

  // ... existing handleSignOut function ...

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
          loadPredictions(user.id, false); // false = update in background
        }
      )
      .subscribe();

    // Cleanup subscription on unmount
    return () => {
      supabase.removeChannel(channel);
    };
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
    
    // Note: Supabase Realtime subscription will automatically trigger
    // when prediction is inserted, but we can also do initial check
    // after a short delay for immediate feedback
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

  // ... existing loading/return JSX ...
  
  return (
    <div className="min-h-screen bg-[#0F0F10] text-[#F3F4F6]">
      {/* Navigation - existing */}
      
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
          
          {/* NEW: Predictions Section */}
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
```

**Key Changes:**
- Add state for predictions, loading, and error
- **Client-side caching**: Cache last 5 predictions in `sessionStorage` (30-second duration)
- **Cache-first loading**: Check cache before fetching from server
- **Background refresh**: If cache exists, display immediately and fetch fresh data in background
- **Supabase Realtime subscription**: Automatically updates predictions when new ones are inserted (replaces polling)
  - Listens for INSERT events on predictions table
  - Filters by user_id_sha256 for user-specific updates
  - Clears cache and reloads when new prediction detected
- **Cache invalidation**: Clear cache on new upload, realtime update, or manual refresh
- Call `fetchUserPredictions()` after user authentication
- Pass predictions to new `PredictionsList` component
- Add refresh callback for after uploads
- **Display limit**: Only show up to 10 predictions (server already limits to 10)
- Import `sha256` utility for generating user_id_sha256 for realtime filter

**2.2 Update AudioUpload Component**

File: `app/components/AudioUpload.tsx`

Add optional callback prop:

```typescript
interface AudioUploadProps {
  onUploadSuccess?: () => void;
}

export default function AudioUpload({ onUploadSuccess }: AudioUploadProps) {
  // ... existing code ...
  
  const handleUpload = async () => {
    // ... existing upload logic ...
    
    if (result.success) {
      setSuccess(true);
      // ... existing cleanup ...
      
      // Call success callback if provided
      if (onUploadSuccess) {
        onUploadSuccess();
      }
    }
    
    // ... rest of function ...
  };
  
  // ... rest of component ...
}
```

### Phase 3: Predictions List Component

**3.1 Create PredictionsList Component**

File: `app/components/PredictionsList.tsx`

```typescript
"use client";

import { PredictionWithUpload } from "@/app/actions/predictions";
import { formatDistanceToNow } from "date-fns";

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
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const formatTimestamp = (timestamp: string): string => {
    try {
      return formatDistanceToNow(new Date(timestamp), { addSuffix: true });
    } catch {
      return new Date(timestamp).toLocaleString();
    }
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

// Helper component for individual prediction cards
function PredictionCard({ prediction }: { prediction: PredictionWithUpload }) {
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
```

**Key Features:**
- Displays predictions chronologically (newest first)
- **Displays maximum 10 predictions** (server already limits to 10)
- Shows emotion, sound classification, and confidence scores
- Displays top YAMNet classifications
- Shows file metadata and timestamps
- Handles loading, error, and empty states
- Emotion-based color coding
- Responsive design matching existing dashboard style

### Phase 4: Dependencies

**4.1 Add date-fns Package**

File: `package.json`

```json
{
  "dependencies": {
    "date-fns": "^3.0.0"
  }
}
```

Install:
```bash
npm install date-fns
```

**Purpose:** Format relative timestamps ("2 hours ago", "3 days ago", etc.)

### Phase 5: Real-time Updates with Supabase Realtime

**5.1 Supabase Realtime Subscription**

Use Supabase Realtime subscriptions for instant updates when new predictions are inserted:

```typescript
// In DashboardPage component - replaces polling
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
        loadPredictions(user.id, false); // false = update in background
      }
    )
    .subscribe();
  
  return () => {
    supabase.removeChannel(channel);
  };
}, [user, supabase]);
```

**Benefits of Realtime over Polling:**
- **Instant Updates**: Gets notified immediately when a prediction is inserted (no delay)
- **Efficient**: No unnecessary API calls - only triggers on actual database changes
- **Lower Server Load**: No repeated polling requests
- **Better UX**: Users see new predictions as soon as they're ready
- **WebSocket Connection**: Maintains a persistent connection for real-time updates

**How it Works:**
1. Subscribes to PostgreSQL changes on the `predictions` table
2. Filters by `user_id_sha256` to only receive updates for the current user
3. Listens for `INSERT` events (new predictions)
4. Automatically clears cache and reloads predictions when new one is detected
5. Cleans up subscription when component unmounts

## Implementation Steps

### Step 1: Create Server Action
- [ ] Create `app/actions/predictions.ts`
- [ ] Implement `fetchUserPredictions()` function with LIMIT 10
- [ ] Test authentication and data fetching
- [ ] Verify query returns maximum 10 results

### Step 2: Install Dependencies
- [ ] Add `date-fns` package: `npm install date-fns`
- [ ] Verify installation in `package.json`

### Step 3: Create PredictionsList Component
- [ ] Create `app/components/PredictionsList.tsx`
- [ ] Implement `PredictionCard` sub-component
- [ ] Add loading, error, and empty states
- [ ] Style to match existing dashboard theme

### Step 4: Update Dashboard Page
- [ ] Add state for predictions, loading, error
- [ ] Import `sha256` utility for realtime filter
- [ ] Implement client-side caching functions (`getCachedPredictions`, `setCachedPredictions`)
- [ ] Add cache-first loading strategy (check cache before fetch)
- [ ] Implement background refresh when cache exists
- [ ] **Set up Supabase Realtime subscription** for automatic updates
  - [ ] Subscribe to INSERT events on predictions table
  - [ ] Filter by user_id_sha256 for user-specific updates
  - [ ] Handle cache clearing and reload on new prediction
  - [ ] Clean up subscription on component unmount
- [ ] Add cache invalidation on upload/refresh/realtime update
- [ ] Integrate `fetchUserPredictions()` call with LIMIT 10
- [ ] Add `PredictionsList` component to JSX
- [ ] Implement refresh functionality with cache clearing

### Step 5: Update AudioUpload Component
- [ ] Add optional `onUploadSuccess` callback prop
- [ ] Call callback after successful upload

### Step 6: Testing
- [ ] Test with user who has predictions
- [ ] Test with user who has no predictions
- [ ] Test authentication edge cases
- [ ] Test error handling
- [ ] Verify chronological ordering
- [ ] Test refresh functionality
- [ ] Verify UI matches design system
- [ ] **Test caching:**
  - [ ] Verify cache stores last 5 predictions
  - [ ] Verify cache displays immediately on page load
  - [ ] Verify background refresh updates cache
  - [ ] Verify cache expires after 30 seconds (explain rationale in documentation)
  - [ ] Verify cache clears on new upload
  - [ ] Verify cache clears on manual refresh
  - [ ] Verify cache clears on realtime update
  - [ ] Test with multiple users (cache isolation)
- [ ] **Test display limits:**
  - [ ] Verify maximum 10 predictions displayed
  - [ ] Verify server query returns max 10 results
  - [ ] Test with user having > 10 predictions

### Step 7: Realtime Testing
- [ ] Test Supabase Realtime subscription
  - [ ] Verify subscription establishes connection
  - [ ] Test receiving INSERT events for new predictions
  - [ ] Verify cache clears and predictions reload automatically
  - [ ] Test subscription cleanup on component unmount
  - [ ] Test with multiple users (verify filter works correctly)
  - [ ] Test subscription reconnection on network issues

### Step 8: Optional Enhancements
- [ ] Add pagination for large result sets (beyond 10)
- [ ] Add filtering/sorting options
- [ ] Add audio playback from stored files
- [ ] Add visualization charts for emotion trends

## Error Handling

1. **Authentication Errors**: Redirect to sign-in page
2. **API Errors**: Display error message with retry button
3. **Empty Results**: Show friendly empty state message
4. **Network Errors**: Retry with exponential backoff
5. **Malformed Data**: Skip invalid predictions, log errors

## Performance Considerations

1. **Data Fetching**: 
   - Fetch only necessary fields
   - Use indexed columns (user_id_sha256, created_at)
   - **LIMIT 10**: Server query limited to 10 most recent predictions
   - Reduces database load and response size

2. **Client-Side Caching**:
   - **Cache last 5 predictions** in `sessionStorage`
   - Cache duration: **30 seconds** (see rationale below)
   - Cache key includes user ID for multi-user support
   - **Cache-first strategy**: Display cached data immediately if available
   - **Background refresh**: Fetch fresh data in background while showing cache
   - Improves perceived performance and reduces API calls
   - **Why 30 seconds?**
     - Predictions don't change after creation (immutable data)
     - Short enough to feel fresh, long enough to provide instant loading
     - Typical user navigation patterns fit within 30-second window
     - Realtime subscriptions ensure new predictions appear immediately (bypasses cache)
     - Balances performance gains with data freshness needs

3. **Supabase Realtime Subscriptions**:
   - **Instant updates**: No polling delay - predictions appear as soon as they're created
   - **Efficient**: Only triggers on actual database changes (INSERT events)
   - **WebSocket connection**: Maintains persistent connection for real-time updates
   - **Lower server load**: No repeated polling requests every few seconds
   - **Better UX**: Users see new predictions immediately without page refresh
   - **Automatic cache invalidation**: Clears cache and reloads when new prediction detected

4. **Rendering**:
   - Use React key props for list items
   - Memoize expensive computations
   - Limit display to 10 items (already limited by server query)
   - Efficient re-renders with proper state management

5. **Cache Management**:
   - Cache automatically invalidated after 30 seconds
   - Cache cleared on new upload
   - Cache cleared on manual refresh
   - Cache stored per-user in sessionStorage (survives page refresh within session)

## Security Considerations

1. **Authentication**: Server action validates user authentication
2. **Authorization**: Filter by `user_id_sha256` to ensure users only see their own predictions
3. **Data Validation**: Validate and sanitize all displayed data
4. **SQL Injection**: Supabase client handles parameterization automatically

## Database Query Optimization

The query uses:
- Indexed `user_id_sha256` column (fast filtering)
- Indexed `created_at` column (fast sorting)
- JOIN on foreign key (indexed `upload_id`)
- Ordered by `created_at DESC` (uses index)
- **LIMIT 10**: Reduces query result size and database load
- Only fetches necessary columns for display

## Caching Strategy Details

### Cache Storage
- **Location**: Browser `sessionStorage`
- **Key Format**: `predictions_cache_{userId}`
- **Cache Size**: Last 5 predictions only
- **Duration**: 30 seconds (configurable via `CACHE_DURATION_MS`)

### Cache Flow
1. **On Page Load**:
   - Check `sessionStorage` for cached predictions
   - If cache exists and is fresh (< 30s old), display immediately
   - Fetch fresh data in background
   - Update cache with fresh data

2. **On New Upload**:
   - Clear existing cache
   - Wait 2 seconds for worker processing
   - Fetch fresh predictions
   - Update cache

3. **On Manual Refresh**:
   - Clear existing cache
   - Fetch fresh predictions
   - Update cache

4. **Cache Invalidation**:
   - Automatically expires after 30 seconds
   - Cleared on upload success
   - Cleared on manual refresh
   - Per-user isolation (cache key includes user ID)

### Benefits
- **Instant Display**: Cached predictions show immediately on page load
- **Reduced API Calls**: Fewer requests to Supabase when cache is valid
- **Better UX**: No loading spinner for returning users (if cache is fresh)
- **Background Updates**: Fresh data fetched in background while showing cache
- **Minimal Storage**: Only stores 5 predictions, uses sessionStorage (cleared on tab close)

## Future Enhancements

1. **Pagination**: Add "Load More" button to fetch older predictions beyond 10
2. **Filtering**: Filter by emotion, date range, etc.
3. **Sorting**: Sort by emotion score, confidence, etc.
4. **Export**: Export predictions as CSV/JSON
5. **Charts**: Visualize emotion trends over time
6. **Audio Playback**: Play audio files directly from dashboard
7. **Download**: Download original audio files
8. **Cache Configuration**: Allow users to configure cache duration
9. **IndexedDB Caching**: Use IndexedDB for larger cache storage if needed

