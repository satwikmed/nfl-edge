import type { Metadata } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";
import BackgroundShader from "@/components/ui/background-shader";

const plusJakartaSans = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-plus-jakarta",
  weight: ["300", "400", "500", "600", "700", "800"],
});

export const metadata: Metadata = {
  title: "NFL Edge",
  description: "A full-stack analytics system analyzing play-calling tendencies, roster value efficiency, and in-game decision-making for all 32 NFL teams.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${plusJakartaSans.variable} font-sans antialiased bg-[#0a0a0f] text-white min-h-screen relative`}>
        <BackgroundShader />
        <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/10 bg-white/3 backdrop-blur-[20px]">
          <div className="max-w-[1400px] mx-auto px-6 h-16 flex items-center justify-between">
            <a href="/" className="flex items-center gap-3 group">
              <div className="relative w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 border border-emerald-500/30 flex items-center justify-center shadow-[0_0_15px_rgba(16,185,129,0.3)] group-hover:shadow-[0_0_25px_rgba(16,185,129,0.5)] transition-all duration-300">
                <svg className="w-5 h-5 text-emerald-400 drop-shadow-[0_0_8px_rgba(16,185,129,0.8)]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2" />
                  <polyline points="12 22 12 12" />
                  <polyline points="22 8.5 12 12" />
                  <polyline points="2 8.5 12 12" />
                </svg>
              </div>
              <div>
                <span className="text-sm font-semibold tracking-tight">NFL Edge</span>
                <span className="hidden sm:block text-[10px] text-white/40 tracking-wide uppercase">NFL 2025 Season Analytics</span>
              </div>
            </a>
            <div className="flex items-center gap-6 text-xs text-white/50">
              <a href="/" className="hover:text-white transition-colors">Overview</a>
              <a href="/map" className="hover:text-white transition-colors">Map</a>
              <a href="/rankings" className="hover:text-white transition-colors">Rankings</a>
              <a href="/compare" className="hover:text-white transition-colors">Compare</a>
            </div>
          </div>
        </nav>
        <main className="pt-16 relative z-10">
          {children}
        </main>
      </body>
    </html>
  );
}
