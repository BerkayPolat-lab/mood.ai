import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#0F0F10] text-[#F3F4F6]">
      {/* Navigation */}
      <nav className="container mx-auto px-6 py-6 flex justify-between items-center">
        <div className="text-2xl font-bold bg-gradient-to-r from-[#7C3AED] via-[#3B82F6] to-[#06B6D4] bg-clip-text text-transparent">
          mood.ai
        </div>
        <div className="flex gap-4">
          <Link
            href="/sign-in"
            className="px-6 py-2 rounded-lg border border-[#1F2937] hover:border-[#7C3AED] transition-colors"
          >
            Sign In
          </Link>
          <Link
            href="/sign-up"
            className="px-6 py-2 rounded-lg bg-gradient-to-r from-[#7C3AED] to-[#3B82F6] hover:from-[#6D28D9] hover:to-[#2563EB] transition-all"
          >
            Sign Up
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="container mx-auto px-6 py-20">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-6xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-[#7C3AED] via-[#3B82F6] to-[#06B6D4] bg-clip-text text-transparent">
            Analyze Your Mood
            <br />
            Through Audio
          </h1>
          <p className="text-xl md:text-2xl text-[#9CA3AF] mb-12 max-w-2xl mx-auto">
            Upload a 10-20 second audio clip and discover the emotional insights
            hidden in speech, music, or ambient sounds using advanced ML
            analysis.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/sign-up"
              className="px-8 py-4 rounded-lg bg-gradient-to-r from-[#7C3AED] to-[#3B82F6] hover:from-[#6D28D9] hover:to-[#2563EB] transition-all text-lg font-semibold"
            >
              Get Started
            </Link>
            <Link
              href="/sign-in"
              className="px-8 py-4 rounded-lg border-2 border-[#3B82F6] hover:bg-[#3B82F6]/10 transition-all text-lg font-semibold"
            >
              Sign In
            </Link>
          </div>
        </div>

        {/* Features Grid */}
        <div className="mt-32 grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          <div className="p-6 rounded-xl bg-[#1F2937] border border-[#1F2937] hover:border-[#7C3AED] transition-colors">
            <div className="w-12 h-12 rounded-lg bg-gradient-to-r from-[#7C3AED] to-[#3B82F6] mb-4 flex items-center justify-center">
              <svg
                className="w-6 h-6 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
                />
              </svg>
            </div>
            <h3 className="text-xl font-semibold mb-2">Audio Analysis</h3>
            <p className="text-[#9CA3AF]">
              Upload speech, music, or ambient sounds for comprehensive mood
              detection.
            </p>
          </div>

          <div className="p-6 rounded-xl bg-[#1F2937] border border-[#1F2937] hover:border-[#06B6D4] transition-colors">
            <div className="w-12 h-12 rounded-lg bg-gradient-to-r from-[#06B6D4] to-[#3B82F6] mb-4 flex items-center justify-center">
              <svg
                className="w-6 h-6 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                />
              </svg>
            </div>
            <h3 className="text-xl font-semibold mb-2">ML-Powered</h3>
            <p className="text-[#9CA3AF]">
              Advanced machine learning models analyze emotion, energy, and mood
              with high accuracy.
            </p>
          </div>

          <div className="p-6 rounded-xl bg-[#1F2937] border border-[#1F2937] hover:border-[#EC4899] transition-colors">
            <div className="w-12 h-12 rounded-lg bg-gradient-to-r from-[#EC4899] to-[#7C3AED] mb-4 flex items-center justify-center">
              <svg
                className="w-6 h-6 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <h3 className="text-xl font-semibold mb-2">Detailed Insights</h3>
            <p className="text-[#9CA3AF]">
              Get comprehensive mood analysis including emotion, energy level,
              and confidence scores.
            </p>
          </div>
        </div>

        {/* Example Output */}
        <div className="mt-32 max-w-2xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-8">
            Example Analysis Output
          </h2>
          <div className="bg-[#1F2937] rounded-xl p-8 border border-[#1F2937]">
            <pre className="text-[#9CA3AF] font-mono text-sm overflow-x-auto">
              {JSON.stringify(
                {
                  mood: "calm",
                  emotion: "content",
                  energy_level: "low",
                  confidence: 0.91,
                },
                null,
                2
              )}
            </pre>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="container mx-auto px-6 py-12 mt-20 border-t border-[#1F2937]">
        <div className="text-center text-[#9CA3AF]">
          <p>&copy; 2025 mood.ai. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
