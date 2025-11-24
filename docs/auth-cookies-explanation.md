# Supabase Authentication & Cookies Explained

## The Key Concept: Cookies ARE the Token Storage

When Supabase returns tokens, they're automatically stored in **HTTP cookies** by the `@supabase/ssr` library. The cookies themselves contain the tokens.

## What Cookies Are Created?

Supabase creates multiple cookies to store authentication data:

1. **`sb-<project-ref>-auth-token`** - Contains the access token and refresh token
   - This is the main cookie storing both tokens
   - Format: Encrypted/signed JSON containing both tokens

2. **Additional cookies** may be created for:
   - Session metadata
   - CSRF protection
   - Token expiration tracking

## Complete Authentication Cycle

### Step 1: User Signs In (Client-Side)

```typescript
// app/sign-in/page.tsx
const { data, error } = await supabase.auth.signInWithPassword({
  email,
  password,
});
```

**What happens:**
1. Client sends credentials to Supabase API
2. Supabase validates credentials
3. Supabase returns: `{ access_token, refresh_token, expires_at, user }`
4. `@supabase/ssr` client automatically stores tokens in cookies
5. Cookies are set in the browser with HttpOnly, Secure, SameSite flags

**Cookies after sign-in:**
```
sb-xxxxx-auth-token: {
  access_token: "eyJhbGc...",
  refresh_token: "v1.xxxxx...",
  expires_at: 1234567890,
  expires_in: 3600
}
```

### Step 2: Subsequent Requests (Middleware/Proxy)

```typescript
// proxy.ts
await supabase.auth.getUser()
```

**What happens:**
1. Middleware reads cookies from the request
2. Extracts access token from cookie
3. Checks if token is expired
4. If expired:
   - Uses refresh token from cookie
   - Calls Supabase to get new access token
   - Updates cookie with new tokens
5. If not expired:
   - Uses existing access token
   - No cookie update needed

**Cookie flow:**
```
Request comes in
  ↓
Middleware reads: sb-xxxxx-auth-token cookie
  ↓
Extracts: access_token, refresh_token
  ↓
Checks: Is access_token expired?
  ├─ NO → Use existing token ✅
  └─ YES → Refresh:
      ├─ Call Supabase with refresh_token
      ├─ Get new access_token
      └─ Update cookie with new tokens ✅
```

### Step 3: Server Components Use Auth

```typescript
// Server Component
const supabase = await createClient()
const { data: { user } } = await supabase.auth.getUser()
```

**What happens:**
1. Server Component calls `createClient()`
2. Client reads cookies (via `getAll()`)
3. Extracts access token from cookie
4. Uses token to authenticate API calls
5. If token refresh needed, `setAll()` is called (but fails silently in Server Components)
6. Middleware already handled refresh, so tokens are fresh

## Why Cookies Instead of localStorage?

### Security Benefits:
1. **HttpOnly flag**: JavaScript can't access cookies (XSS protection)
2. **Secure flag**: Only sent over HTTPS
3. **SameSite flag**: CSRF protection
4. **Server-side access**: Middleware can read/write cookies

### SSR Compatibility:
- Server Components can read cookies
- Middleware can refresh tokens before rendering
- Works seamlessly with Next.js App Router

## Cookie Structure Example

When you inspect cookies in browser DevTools, you'll see:

```
Name: sb-xxxxx-auth-token
Value: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzA...
Domain: .yourdomain.com
Path: /
Expires: Session (or specific date)
HttpOnly: ✓
Secure: ✓
SameSite: Lax
```

The cookie value is an encrypted/signed JWT containing:
- Access token
- Refresh token
- Expiration timestamps
- User metadata

## Token Refresh Flow in Detail

### Scenario: Access Token Expires

```
Time: 0:00 - User signs in
├─ Access token expires: 1 hour
└─ Refresh token expires: 30 days
   Cookie: { access_token: "abc123", refresh_token: "xyz789" }

Time: 0:59 - User makes request (token expiring soon)
├─ Middleware intercepts
│  ├─ Reads cookie: { access_token: "abc123", refresh_token: "xyz789" }
│  ├─ Checks expiration: 1 minute left
│  ├─ Calls: supabase.auth.getUser()
│  ├─ Supabase: "Token expiring, let me refresh"
│  ├─ Uses refresh_token: "xyz789"
│  ├─ Gets new access_token: "def456"
│  └─ Updates cookie: { access_token: "def456", refresh_token: "xyz789" }
└─ Server Component runs with fresh token ✅

Time: 1:05 - User makes another request (token expired)
├─ Middleware intercepts
│  ├─ Reads cookie: { access_token: "def456", refresh_token: "xyz789" }
│  ├─ Checks expiration: Expired 5 minutes ago
│  ├─ Calls: supabase.auth.getUser()
│  ├─ Supabase: "Token expired, refreshing..."
│  ├─ Uses refresh_token: "xyz789"
│  ├─ Gets new access_token: "ghi789"
│  └─ Updates cookie: { access_token: "ghi789", refresh_token: "xyz789" }
└─ Server Component runs with fresh token ✅
```

## Cookie Update Process

When middleware refreshes tokens:

```typescript
// proxy.ts - setAll() function
setAll(cookiesToSet) {
  // cookiesToSet = [
  //   {
  //     name: 'sb-xxxxx-auth-token',
  //     value: 'new-encrypted-token-data',
  //     options: { httpOnly: true, secure: true, sameSite: 'lax', ... }
  //   }
  // ]
  
  cookiesToSet.forEach(({ name, value, options }) => {
    // Update request cookies (for current request)
    request.cookies.set(name, value)
    
    // Update response cookies (sent to browser)
    supabaseResponse.cookies.set(name, value, options)
  })
}
```

**Result:**
- Browser receives updated cookie in response
- Next request includes fresh token
- User stays authenticated seamlessly

## Summary

**Cookies = Token Storage**

1. **Sign In**: Tokens stored in cookies automatically
2. **Every Request**: Middleware reads cookies, checks expiration
3. **Token Refresh**: Middleware updates cookies with new tokens
4. **Server Components**: Read cookies to get current user
5. **Seamless Auth**: User never notices token refreshes

The cookies ARE the authentication mechanism - they persist tokens across requests, enable server-side auth, and provide security through HttpOnly/Secure flags.

