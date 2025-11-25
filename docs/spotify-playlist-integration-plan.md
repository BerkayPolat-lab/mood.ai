# Spotify Recommendations Integration Pipeline Plan

## Overview
Integrate Spotify API to fetch mood-based track recommendations after emotion detection completes. Store recommended tracks in Supabase `playlists` table linked to the user's upload.

## Architecture Decision

**Separation of Concerns**: Create a new module `model/services/spotify_client.py` containing:
- `SpotifyRecommendationClient` class
- Emotion-to-audio-features mapping dictionary
- All Spotify API interaction logic

**Import into Worker**: Minimal integration in `worker.py` - just instantiate and call the recommendation method.

## Database Schema

### Playlists Table
Created in `infra/schema.sql` with the following structure:
- `id` (UUID, Primary Key)
- `upload_id` (UUID, Foreign Key → `uploads.id`)
- `spotify_playlist_id` (TEXT, Unique - Spotify's playlist ID) - *Note: Can store "recommendations" or track list ID for now*
- `name` (TEXT) - Playlist name (can be generated from emotion)
- `description` (TEXT) - Playlist description
- `owner` (JSONB) - Owner information (display_name, id, external_urls, etc.)
- `images` (JSONB) - Array of playlist cover images (can be empty for recommendations)
- `link` (TEXT) - Spotify playlist URL or recommendations link
- `created_at` (TIMESTAMP) - Creation timestamp

**Note**: This schema can store either playlists or recommendations. For recommendations-only phase, `spotify_playlist_id` can store a reference ID, and `link` can store a custom recommendations URL.

## Pipeline Flow

```
Audio Upload → Emotion Detection → Prediction Saved
                                          ↓
                          Extract Emotion & Emotion Score
                                          ↓
                          SpotifyRecommendationClient.get_recommendations()
                                          ↓
                          Map Emotion → Spotify Audio Features
                                          ↓
                          Request Access Token (OAuth 2.0)
                                          ↓
                          GET /v1/recommendations from Spotify API
                                          ↓
                          Return Track Recommendations
                                          ↓
                          (Optional: Log recommendations for debugging)
                                          ↓
                          Job Complete ✓
```

**Key Points**:
- Recommendations are fetched but not stored in this phase
- No database writes for recommendations (can be added later)
- Worker continues successfully even if recommendations fail

## Pipeline Architecture

### Phase 1: Create New Spotify Client Module

**1.1 File Structure**
Create new file: `model/services/spotify_client.py`

This file will contain:
- `SpotifyRecommendationClient` class
- `EMOTION_TO_FEATURES` mapping dictionary (module-level constant)
- All Spotify API interaction logic

**1.2 Class Structure**

```python
# model/services/spotify_client.py

import os
import requests
import base64
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

# Emotion-to-Spotify Audio Features Mapping
# Stored at module level in the same file
EMOTION_TO_FEATURES = {
    "happy": {
        "target_valence": 0.8,
        "target_energy": 0.7,
        "target_danceability": 0.7,
        "seed_genres": "pop,indie-pop,electronic"
    },
    "sad": {
        "target_valence": 0.2,
        "target_energy": 0.3,
        "target_danceability": 0.3,
        "seed_genres": "sad,indie,acoustic"
    },
    "angry": {
        "target_valence": 0.3,
        "target_energy": 0.9,
        "target_danceability": 0.5,
        "seed_genres": "rock,metal,hardcore"
    },
    "neutral": {
        "target_valence": 0.5,
        "target_energy": 0.5,
        "target_danceability": 0.5,
        "seed_genres": "pop,indie"
    },
    "excited": {
        "target_valence": 0.9,
        "target_energy": 0.9,
        "target_danceability": 0.9,
        "seed_genres": "dance,electronic,pop"
    },
    "calm": {
        "target_valence": 0.6,
        "target_energy": 0.2,
        "target_danceability": 0.3,
        "seed_genres": "ambient,chill,acoustic"
    },
    "surprised": {
        "target_valence": 0.7,
        "target_energy": 0.8,
        "target_danceability": 0.6,
        "seed_genres": "indie,alternative,electronic"
    },
    "fearful": {
        "target_valence": 0.2,
        "target_energy": 0.4,
        "target_danceability": 0.2,
        "seed_genres": "ambient,electronic,experimental"
    },
    "disgusted": {
        "target_valence": 0.2,
        "target_energy": 0.3,
        "target_danceability": 0.2,
        "seed_genres": "alternative,indie,experimental"
    },
}


class SpotifyRecommendationClient:
    """
    Client for fetching track recommendations from Spotify API based on mood/emotion.
    
    Handles:
    - OAuth 2.0 Client Credentials flow
    - Token management and refresh
    - Emotion to audio features mapping
    - Fetching track recommendations
    """
    
    def __init__(self):
        """Initialize Spotify API client with credentials from environment."""
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.access_token = None
        self.token_expires_at = None
        self.api_base_url = "https://api.spotify.com/v1"
        
        if not self.client_id or not self.client_secret:
            raise ValueError(
                "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set in environment"
            )
    
    def _get_access_token(self) -> str:
        """
        Get or refresh Spotify access token using Client Credentials flow.
        
        Returns:
            Access token string
            
        Raises:
            Exception: If token generation fails
        """
        # Check if token exists and is still valid
        if self.access_token and self.token_expires_at:
            if datetime.now() < self.token_expires_at:
                return self.access_token
        
        # Request new token
        auth_url = "https://accounts.spotify.com/api/token"
        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {"grant_type": "client_credentials"}
        
        response = requests.post(auth_url, headers=headers, data=data, timeout=10)
        response.raise_for_status()
        
        token_data = response.json()
        self.access_token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 3600)
        
        # Set expiration time (subtract 60 seconds as buffer)
        self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
        
        return self.access_token
    
    def _map_emotion_to_features(self, emotion: str, emotion_score: float) -> Dict[str, Any]:
        """
        Map detected emotion to Spotify audio features.
        
        Args:
            emotion: Detected emotion label (e.g., "happy", "sad")
            emotion_score: Confidence score of the emotion (0.0 - 1.0)
            
        Returns:
            Dictionary with Spotify API parameters for recommendations
        """
        # Get base features for emotion
        features = EMOTION_TO_FEATURES.get(emotion.lower(), EMOTION_TO_FEATURES["neutral"])
        
        # Optionally adjust based on emotion_score (higher confidence = more extreme features)
        # For now, return base features
        return features.copy()
    
    def get_recommendations(
        self,
        emotion: str,
        emotion_score: float,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get track recommendations from Spotify API based on detected emotion.
        
        Args:
            emotion: Detected emotion label
            emotion_score: Confidence score of the emotion
            limit: Number of tracks to recommend (1-100, default 20)
            
        Returns:
            Dictionary containing:
            - success: bool
            - tracks: List of track objects (if success)
            - error: str (if not success)
        """
        try:
            # Get access token
            token = self._get_access_token()
            
            # Map emotion to audio features
            audio_features = self._map_emotion_to_features(emotion, emotion_score)
            
            # Prepare request parameters
            params = {
                "limit": min(max(limit, 1), 100),  # Clamp between 1-100
                "target_valence": audio_features.get("target_valence"),
                "target_energy": audio_features.get("target_energy"),
                "target_danceability": audio_features.get("target_danceability"),
            }
            
            # Add seed_genres if available
            if "seed_genres" in audio_features:
                params["seed_genres"] = audio_features["seed_genres"]
            
            # Make API request
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.api_base_url}/recommendations",
                headers=headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            recommendations_data = response.json()
            tracks = recommendations_data.get("tracks", [])
            
            return {
                "success": True,
                "tracks": tracks,
                "emotion": emotion,
                "audio_features": audio_features
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Spotify API request failed: {str(e)}"
            if hasattr(e.response, 'text'):
                error_msg += f" - Response: {e.response.text}"
            
            return {
                "success": False,
                "error": error_msg,
                "tracks": []
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "tracks": []
            }
```

### Phase 2: Worker Integration

**2.1 Update `AudioMoodWorker` Class**

Minimal changes to `worker.py` - just import and use:

```python
# At the top of worker.py
from .spotify_client import SpotifyRecommendationClient

class AudioMoodWorker:
    
    def __init__(self):
        # ... existing initialization ...
        
        # Initialize Spotify client (optional, can be None if credentials not set)
        try:
            self.spotify_client = SpotifyRecommendationClient()
            print("Spotify recommendation client initialized")
        except ValueError as e:
            print(f"Warning: Spotify client not initialized: {e}")
            self.spotify_client = None
```

**2.2 Update `process_job` Method**

Add recommendations fetching after prediction is saved:

```python
def process_job(self, job_id: str) -> Dict[str, Any]:
    # ... existing prediction logic ...
    
    # Save prediction (existing code)
    prediction_response = self.supabase.table("predictions").insert(
        prediction_data
    ).execute()
    
    # NEW: Get Spotify recommendations
    if self.spotify_client:
        try:
            emotion_label = emotion_results.get("emotion", "neutral")
            emotion_score = emotion_results.get("emotion_score", 0.5)
            
            recommendations = self.spotify_client.get_recommendations(
                emotion=emotion_label,
                emotion_score=emotion_score,
                limit=20
            )
            
            if recommendations["success"]:
                print(f"Got {len(recommendations['tracks'])} Spotify recommendations for emotion: {emotion_label}")
                # TODO: Store recommendations in database (future step)
            else:
                print(f"Warning: Failed to get Spotify recommendations: {recommendations.get('error')}")
        except Exception as e:
            print(f"Warning: Error fetching Spotify recommendations: {str(e)}")
            # Don't fail the job if recommendations fail
    
    # ... rest of existing code ...
```

## API Endpoints Used

### 1. Get Access Token (OAuth 2.0 Client Credentials)
**Endpoint**: `POST https://accounts.spotify.com/api/token`

**Headers**:
- `Authorization`: `Basic {base64(client_id:client_secret)}`
- `Content-Type`: `application/x-www-form-urlencoded`

**Body**:
```
grant_type=client_credentials
```

**Response**:
```json
{
  "access_token": "NgCXRKc...MzYjw",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

**Reference**: https://developer.spotify.com/documentation/general/guides/authorization/client-credentials/

### 2. Get Recommendations
**Endpoint**: `GET https://api.spotify.com/v1/recommendations`

**Headers**:
- `Authorization`: `Bearer {access_token}`

**Query Parameters**:
- `seed_genres` (optional): Comma-separated genre seeds (e.g., "pop,rock,indie")
- `target_valence` (optional): 0.0 - 1.0 (positivity/happiness)
- `target_energy` (optional): 0.0 - 1.0 (intensity/energy)
- `target_danceability` (optional): 0.0 - 1.0 (danceability)
- `limit` (optional): Number of tracks (1-100, default 20)

**Example Request**:
```
GET https://api.spotify.com/v1/recommendations?seed_genres=pop&target_valence=0.8&target_energy=0.7&limit=20
```

**Response**:
```json
{
  "tracks": [
    {
      "album": {...},
      "artists": [...],
      "available_markets": [...],
      "disc_number": 1,
      "duration_ms": 237040,
      "explicit": false,
      "external_ids": {...},
      "external_urls": {
        "spotify": "https://open.spotify.com/track/..."
      },
      "href": "https://api.spotify.com/v1/tracks/...",
      "id": "...",
      "is_local": false,
      "name": "Track Name",
      "popularity": 85,
      "preview_url": "...",
      "track_number": 1,
      "type": "track",
      "uri": "spotify:track:..."
    }
  ],
  "seeds": [...]
}
```

**Reference**: https://developer.spotify.com/documentation/web-api/reference/get-recommendations

## Implementation Steps

### Step 1: Database Setup
- [x] Create `playlists` table in schema.sql
- [ ] Run migration in Supabase to create the table (optional for now, can store recommendations later)

### Step 2: Spotify API Setup
- [ ] Register application on [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications)
- [ ] Obtain `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET`
- [ ] Add credentials to environment variables (`.env.local`)

### Step 3: Create Spotify Client Module
- [ ] Create new file `model/services/spotify_client.py`
- [ ] Define `EMOTION_TO_FEATURES` mapping dictionary at module level
- [ ] Implement `SpotifyRecommendationClient` class:
  - [ ] `__init__()` - Initialize with environment variables
  - [ ] `_get_access_token()` - OAuth 2.0 Client Credentials flow
  - [ ] `_map_emotion_to_features()` - Map emotion to Spotify parameters
  - [ ] `get_recommendations()` - Main public method to fetch recommendations

### Step 4: Worker Integration
- [ ] Add import statement in `worker.py`: `from .spotify_client import SpotifyRecommendationClient`
- [ ] Initialize `self.spotify_client` in `AudioMoodWorker.__init__()` (with error handling)
- [ ] Add recommendations call in `process_job()` after prediction is saved
- [ ] Add error handling (don't fail job if recommendations fail)
- [ ] Add logging for debugging

### Step 5: Testing
- [ ] Test `SpotifyRecommendationClient` standalone with various emotions
- [ ] Verify token generation and refresh works correctly
- [ ] Test recommendations API with different emotion inputs
- [ ] Verify recommendations are returned correctly
- [ ] Test error scenarios:
  - [ ] Invalid credentials
  - [ ] Token expiration
  - [ ] API rate limiting
  - [ ] Network errors
- [ ] Integration test with worker pipeline

### Step 6: Future Enhancements (Not in Current Scope)
- [ ] Store recommendations in database
- [ ] Create playlists from recommendations
- [ ] Add tracks to playlists
- [ ] Save playlist metadata to database

## Error Handling Strategy

1. **Spotify API Failures**: 
   - Log error but don't fail the job
   - Return `{"success": False, "error": "...", "tracks": []}` from `get_recommendations()`
   - Allow prediction to complete successfully
   - Worker continues even if recommendations fail

2. **Missing Credentials**:
   - Catch `ValueError` in `__init__()` if credentials not set
   - Set `self.spotify_client = None`
   - Skip recommendations step gracefully

3. **Token Expiration**:
   - Check `token_expires_at` before each API call
   - Automatically refresh token if expired or close to expiring (60s buffer)
   - Implemented in `_get_access_token()` method

4. **Rate Limiting**:
   - Spotify API rate limits: See response headers `Retry-After`
   - For now: Return error, log it
   - Future: Implement exponential backoff and retry logic

5. **Invalid Emotion Input**:
   - Default to `EMOTION_TO_FEATURES["neutral"]` if emotion not found
   - Handle case-insensitive emotion matching

## Environment Variables Required

Add to `.env.local`:
```bash
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

**Note**: Client Credentials flow does not require redirect URI. Only needed if switching to Authorization Code flow in the future.

## Dependencies

**No additional dependencies required!** Uses standard library `requests` which is already in the project.

If `requests` is not in `model/requirements.txt`, add:
```
requests>=2.31.0
```

## File Structure

After implementation:
```
model/
  services/
    __init__.py
    worker.py           # Main worker (minimal changes)
    spotify_client.py   # NEW: Spotify recommendations client
```

## Code Organization Benefits

1. **Separation of Concerns**: Spotify logic isolated from ML worker logic
2. **Maintainability**: Easier to test and modify Spotify integration independently
3. **Reusability**: `SpotifyRecommendationClient` can be used by other parts of the application
4. **Clean Worker**: `worker.py` stays focused on ML pipeline
5. **Easy Testing**: Can test Spotify client without loading ML models

## Future Enhancements (Not in Current Scope)

- **Playlist Creation**: Add methods to create playlists from recommendations
- **Track Storage**: Store recommended tracks in database for later use
- **User Playlists**: Switch to Authorization Code flow for user-specific playlists
- **Caching**: Cache recommendations based on emotion to reduce API calls
- **Playlist Customization**: Generate playlist names/descriptions from emotion
- **Batch Processing**: Support multiple recommendations in one API call
- **Retry Logic**: Implement exponential backoff for rate limiting

## Notes

- **Client Credentials Flow**: No user authentication needed - perfect for server-side recommendations
- **No User Context**: Recommendations are based purely on emotion, not user preferences
- **Public API**: All recommendations are public (no user account required)
- **Graceful Degradation**: Worker continues successfully even if Spotify API is unavailable

