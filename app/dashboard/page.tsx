"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";

export default function DashboardPage() {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const supabase = createClient();

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
    };

    checkUser();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    router.push("/");
    router.refresh();
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
            Welcome! Audio upload functionality will be available here soon.
          </p>

          <div className="bg-[#1F2937] rounded-xl p-8 border border-[#1F2937]">
            <p className="text-[#9CA3AF] text-center">
              Audio upload and analysis features coming soon...
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}

