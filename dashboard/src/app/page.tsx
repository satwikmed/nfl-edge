import Link from 'next/link';

export default function LandingPage() {
  return (
    <div className="min-h-[calc(100vh-4rem)] flex flex-col pt-24 pb-32 px-6 max-w-[1200px] mx-auto gap-32">
      
      {/* Hero Section */}
      <section className="flex flex-col items-center text-center space-y-8 animate-fade-in-up">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold tracking-wider uppercase mb-4">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          Live 2025 Analytics Engine
        </div>
        
        <h1 className="text-5xl md:text-7xl font-sans font-light tracking-tight text-balance max-w-4xl">
          Actionable Intelligence for the <span className="font-semibold text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">Modern NFL Franchise</span>
        </h1>
        
        <p className="text-white/70 text-lg md:text-xl font-light leading-relaxed max-w-2xl mx-auto">
          Bridging the gap between raw play-by-play data and on-field strategy. We process millions of data points to objectively grade play-calling efficiency, roster value optimization, and in-game decision management.
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center pt-8">
          <Link href="/map" className="px-8 py-4 bg-white/10 backdrop-blur-md border border-white/20 rounded-full text-white font-semibold hover:bg-white/20 hover:border-emerald-500/50 hover:shadow-[0_0_30px_rgba(16,185,129,0.3)] transition-all duration-300 transform hover:-translate-y-1">
            Launch NFL Edge
          </Link>
          <Link href="/rankings" className="px-8 py-4 bg-transparent border border-white/10 rounded-full text-white/70 font-semibold hover:text-white hover:bg-white/5 transition-all duration-300">
            View League Rankings
          </Link>
        </div>
      </section>

      {/* The Problem & Solution */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
        <div className="space-y-6">
          <h2 className="text-3xl font-semibold tracking-tight">The Signal vs. The Noise</h2>
          <p className="text-white/60 leading-relaxed text-sm">
            Modern NFL front offices are overwhelmed with noise. Expected Points Added (EPA), Completion Percentage Over Expectation (CPOE), and raw counting stats are widely accessible, but they lack contextual leverage.
          </p>
          <p className="text-white/60 leading-relaxed text-sm">
            Our pipeline ingests raw NFL data and applies strict contextual filters—adjusting for game state, win probability leverage, and league-wide baselines—to generate a unified 5-metric composite score that grades the true efficacy of every franchise.
          </p>
        </div>
        <div className="relative aspect-video rounded-2xl overflow-hidden border border-white/10 bg-white/5 backdrop-blur-sm flex items-center justify-center group shadow-2xl">
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 to-cyan-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          <div className="text-center">
            <div className="text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-b from-white to-white/40 mb-2">32</div>
            <div className="text-xs text-white/50 uppercase tracking-widest font-semibold">NFL Franchises Analyzed</div>
          </div>
        </div>
      </section>

      {/* The Three Engines */}
      <section className="space-y-12">
        <div className="text-center space-y-4">
          <h2 className="text-3xl font-semibold tracking-tight">Three Pillars of Analysis</h2>
          <p className="text-white/50 text-sm max-w-2xl mx-auto">Our Python data engineering backend relies on three specialized engines to quantify coaching and management performance.</p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Engine A */}
          <div className="glass-card p-8 rounded-2xl border border-white/5 bg-white/5 hover:bg-white/10 transition-colors flex flex-col gap-4">
            <div className="w-12 h-12 rounded-full bg-emerald-500/20 flex items-center justify-center border border-emerald-500/30 text-emerald-400 font-bold text-lg mb-2">A</div>
            <h3 className="text-xl font-semibold">Play-Calling Efficiency</h3>
            <p className="text-white/50 text-sm leading-relaxed flex-1">
              Evaluates offensive coordination by comparing pass/run tendencies against dynamic league-wide baselines. Analyzes predictability on early downs and computes mathematically optimal 4th-down decision making, factoring in late-game win probability leverage.
            </p>
          </div>

          {/* Engine B */}
          <div className="glass-card p-8 rounded-2xl border border-white/5 bg-white/5 hover:bg-white/10 transition-colors flex flex-col gap-4">
            <div className="w-12 h-12 rounded-full bg-cyan-500/20 flex items-center justify-center border border-cyan-500/30 text-cyan-400 font-bold text-lg mb-2">B</div>
            <h3 className="text-xl font-semibold">Roster Value & Cap</h3>
            <p className="text-white/50 text-sm leading-relaxed flex-1">
              Optimizes General Manager performance by mapping player EPA to their current salary cap hit. Calculates positional Value Over Replacement (VOR) using a strict 55th-percentile starter baseline to identify overpaid veterans and underpaid draft steals.
            </p>
          </div>

          {/* Engine C */}
          <div className="glass-card p-8 rounded-2xl border border-white/5 bg-white/5 hover:bg-white/10 transition-colors flex flex-col gap-4">
            <div className="w-12 h-12 rounded-full bg-indigo-500/20 flex items-center justify-center border border-indigo-500/30 text-indigo-400 font-bold text-lg mb-2">C</div>
            <h3 className="text-xl font-semibold">In-Game Management</h3>
            <p className="text-white/50 text-sm leading-relaxed flex-1">
              Grades the Head Coach on critical game management scenarios. Penalizes wasted timeouts while preserving strategic late-half clock stoppages. Quantifies clutch performance leverage in one-score games during the 4th quarter.
            </p>
          </div>
        </div>
      </section>

      {/* Tech Stack / Architecture */}
      <section className="bg-black/20 border border-white/10 rounded-3xl p-10 md:p-16 backdrop-blur-md">
        <div className="flex flex-col md:flex-row gap-12 items-center">
          <div className="md:w-1/3 space-y-4">
            <h2 className="text-2xl font-semibold tracking-tight">Technical Architecture</h2>
            <p className="text-white/50 text-sm leading-relaxed">
              Built by full-stack engineers to handle massive NFL datasets with zero latency on the client.
            </p>
          </div>
          <div className="md:w-2/3 grid grid-cols-2 sm:grid-cols-4 gap-6">
            <div className="space-y-2">
              <div className="text-xs text-white/40 uppercase tracking-wider font-semibold">Data Pipeline</div>
              <div className="font-medium text-white/80">Python</div>
              <div className="font-medium text-white/80">Pandas & NumPy</div>
            </div>
            <div className="space-y-2">
              <div className="text-xs text-white/40 uppercase tracking-wider font-semibold">Database</div>
              <div className="font-medium text-white/80">SQLite3</div>
              <div className="font-medium text-white/80">SQL Analytics</div>
            </div>
            <div className="space-y-2">
              <div className="text-xs text-white/40 uppercase tracking-wider font-semibold">Frontend</div>
              <div className="font-medium text-white/80">Next.js 16</div>
              <div className="font-medium text-white/80">React & TypeScript</div>
            </div>
            <div className="space-y-2">
              <div className="text-xs text-white/40 uppercase tracking-wider font-semibold">Styling & UI</div>
              <div className="font-medium text-white/80">Tailwind CSS v4</div>
              <div className="font-medium text-white/80">WebGL Shaders</div>
            </div>
          </div>
        </div>
      </section>

    </div>
  );
}
