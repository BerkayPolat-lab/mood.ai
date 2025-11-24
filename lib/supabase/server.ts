import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

export async function createClient() {
  const cookieStore = await cookies()

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_PROJECT_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_API_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll()
        },
        setAll() {
          // No-op: Cookie updates are handled by middleware/proxy
          // Server Components cannot write cookies, and middleware
          // already refreshes tokens before Server Components run.
          // Parameter intentionally omitted as it's not used.
        },
      },
    }
  )
}

