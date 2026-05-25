'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { TeamData, TEAM_COLORS } from '@/lib/types';
import {
  formatGrade,
  formatCurrency,
  formatPercent,
  formatEPA,
  getGradeColor,
  getScoreColor
} from '@/lib/data';
import FootballField from '@/components/ui/football-field';

export default function TeamDetailPage() {
  const params = useParams();
  const router = useRouter();
  const teamId = (params.id as string)?.toUpperCase();
  
  const [team, setTeam] = useState<TeamData | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'play_calling' | 'roster' | 'decisions' | 'field'>('overview');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!teamId) return;
    setLoading(true);
    fetch(`/data/team_${teamId.toLowerCase()}.json`)
      .then((res) => {
        if (!res.ok) throw new Error('Team not found');
        return res.json();
      })
      .then((data) => {
        setTeam(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, [teamId]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0a0a0f]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 rounded-full border-2 border-emerald-500 border-t-transparent animate-spin" />
          <span className="text-xs text-white/40 tracking-wider uppercase font-medium">Analyzing Team Profile...</span>
        </div>
      </div>
    );
  }

  if (!team) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-[#0a0a0f] gap-4">
        <h1 className="text-xl font-semibold">Team Not Found</h1>
        <Link href="/" className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-xs hover:bg-white/10 transition-colors">
          Return to Command Center
        </Link>
      </div>
    );
  }

  const primaryColor = TEAM_COLORS[team.abbreviation]?.primary || '#10b981';
  const secondaryColor = TEAM_COLORS[team.abbreviation]?.secondary || '#000000';

  return (
    <div className="min-h-screen pb-16">
      {/* Dynamic Glow Background based on Team Colors */}
      <div className="absolute top-0 left-0 right-0 h-[400px] overflow-hidden pointer-events-none z-0 opacity-15">
        <div
          className="absolute -top-[20%] left-1/2 -translate-x-1/2 w-[800px] h-[400px] rounded-full blur-[120px]"
          style={{
            background: `radial-gradient(ellipse at center, ${primaryColor} 0%, transparent 70%)`
          }}
        />
      </div>

      {/* Team Header */}
      <header className="relative z-10 px-6 pt-8 pb-4 max-w-[1400px] mx-auto">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-white/5 pb-8">
          <div className="flex items-center gap-6">
            {/* Team Logo / Badge */}
            <div
              className="w-20 h-20 rounded-2xl flex items-center justify-center font-bold text-2xl tracking-tighter shadow-xl"
              style={{
                background: `linear-gradient(135deg, ${primaryColor} 0%, ${
                  secondaryColor === '#000000' ? '#272730' : secondaryColor
                } 100%)`,
                color: '#ffffff',
                border: `1px solid rgba(255,255,255,0.2)`,
                boxShadow: `0 8px 30px ${primaryColor}30`,
              }}
            >
              {team.abbreviation}
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-3xl font-bold tracking-tight">{team.name}</h1>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-white/5 border border-white/10 text-white/60 uppercase tracking-wider">
                  {team.conference} {team.division}
                </span>
              </div>
              <p className="text-white/40 text-xs mt-1">
                Stadium: <span className="text-white/70 font-medium">{team.stadium}</span> · Season: 2025
              </p>
              <div className="mt-3 flex items-center gap-4 text-sm font-semibold">
                <span className="text-white/80">Record: {team.wins}-{team.losses}</span>
                <span className="text-white/30">|</span>
                <span className="text-white/50 text-xs font-normal">Win Pct: {((team.wins / (team.wins + team.losses || 1)) * 100).toFixed(1)}%</span>
              </div>
            </div>
          </div>

          {/* Grades Card */}
          <div className="flex items-center gap-4 bg-white/3 border border-white/5 p-4 rounded-xl backdrop-blur-md">
            <div className="text-center px-4 border-r border-white/5">
              <div className="text-[10px] text-white/30 uppercase tracking-wider font-semibold">Composite</div>
              <div
                className="text-2xl font-extrabold mt-1"
                style={{ color: getGradeColor(team.composite_grade) }}
              >
                {team.composite_grade}
              </div>
            </div>
            <div className="grid grid-cols-5 gap-5 px-4">
              <div className="text-center">
                <div className="text-[9px] text-white/30 uppercase tracking-wide whitespace-nowrap">Play-Call</div>
                <div className="text-sm font-bold mt-0.5" style={{ color: getGradeColor(team.grades.play_calling) }}>
                  {team.grades.play_calling}
                </div>
              </div>
              <div className="text-center">
                <div className="text-[9px] text-white/30 uppercase tracking-wide whitespace-nowrap">4th Down</div>
                <div className="text-sm font-bold mt-0.5" style={{ color: getGradeColor(team.grades.fourth_down) }}>
                  {team.grades.fourth_down}
                </div>
              </div>
              <div className="text-center">
                <div className="text-[9px] text-white/30 uppercase tracking-wide whitespace-nowrap">Roster Cap</div>
                <div className="text-sm font-bold mt-0.5" style={{ color: getGradeColor(team.grades.roster_cap) }}>
                  {team.grades.roster_cap}
                </div>
              </div>
              <div className="text-center">
                <div className="text-[9px] text-white/30 uppercase tracking-wide whitespace-nowrap">Defense</div>
                <div className="text-sm font-bold mt-0.5" style={{ color: getGradeColor(team.grades.defense) }}>
                  {team.grades.defense}
                </div>
              </div>
              <div className="text-center">
                <div className="text-[9px] text-white/30 uppercase tracking-wide whitespace-nowrap">Game Mgmt</div>
                <div className="text-sm font-bold mt-0.5" style={{ color: getGradeColor(team.grades.game_management) }}>
                  {team.grades.game_management}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Tab Controls */}
        <div className="mt-8 flex gap-2 overflow-x-auto pb-2 border-b border-white/5">
          <button
            onClick={() => setActiveTab('overview')}
            className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
          >
            Overview & Profile
          </button>
          <button
            onClick={() => setActiveTab('play_calling')}
            className={`tab-btn ${activeTab === 'play_calling' ? 'active' : ''}`}
          >
            Engine A: Play-Calling
          </button>
          <button
            onClick={() => setActiveTab('roster')}
            className={`tab-btn ${activeTab === 'roster' ? 'active' : ''}`}
          >
            Engine B: Roster Value
          </button>
          <button
            onClick={() => setActiveTab('decisions')}
            className={`tab-btn ${activeTab === 'decisions' ? 'active' : ''}`}
          >
            Engine C: In-Game Decisions
          </button>
          <button
            onClick={() => setActiveTab('field')}
            className={`tab-btn ${activeTab === 'field' ? 'active' : ''}`}
          >
            Field Spatial Analytics
          </button>
        </div>
      </header>

      {/* Tab Panels */}
      <main className="relative z-10 px-6 max-w-[1400px] mx-auto mt-6">
        
        {/* PANEL: OVERVIEW */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fade-in-up">
            {/* Column 1: Offensive Profile */}
            <div className="glass-card p-6 flex flex-col gap-6">
              <h2 className="text-base font-semibold border-b border-white/5 pb-3 text-emerald-400">Offensive Identity</h2>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="kpi-card">
                  <div className="text-[10px] text-white/40 uppercase">Plays/Game</div>
                  <div className="text-lg font-bold mt-1 text-white">{team.offensive_profile.plays_per_game}</div>
                </div>
                <div className="kpi-card">
                  <div className="text-[10px] text-white/40 uppercase">Pass Rate</div>
                  <div className="text-lg font-bold mt-1 text-white">{formatPercent(team.offensive_profile.pass_rate)}</div>
                </div>
                <div className="kpi-card">
                  <div className="text-[10px] text-white/40 uppercase">EPA / Play</div>
                  <div className="text-lg font-bold mt-1 text-white">{formatEPA(team.offensive_profile.epa_per_play)}</div>
                </div>
                <div className="kpi-card">
                  <div className="text-[10px] text-white/40 uppercase">Success Rate</div>
                  <div className="text-lg font-bold mt-1 text-white">{formatPercent(team.offensive_profile.success_rate)}</div>
                </div>
              </div>

              {/* Pass/Run EPA split */}
              <div className="space-y-3">
                <h3 className="text-xs font-semibold text-white/60">EPA Efficiency Split</h3>
                <div className="space-y-2 text-xs">
                  <div>
                    <div className="flex justify-between text-white/50 mb-1">
                      <span>Pass EPA/Play</span>
                      <span className="font-mono text-white">{formatEPA(team.offensive_profile.pass_epa_per_play)}</span>
                    </div>
                    <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                      <div className="h-full bg-cyan-500" style={{ width: `${Math.max(0, (team.offensive_profile.pass_epa_per_play + 0.3) / 0.6 * 100)}%` }} />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-white/50 mb-1">
                      <span>Run EPA/Play</span>
                      <span className="font-mono text-white">{formatEPA(team.offensive_profile.run_epa_per_play)}</span>
                    </div>
                    <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                      <div className="h-full bg-amber-500" style={{ width: `${Math.max(0, (team.offensive_profile.run_epa_per_play + 0.3) / 0.6 * 100)}%` }} />
                    </div>
                  </div>
                </div>
              </div>

              {/* Personnel groups */}
              <div className="space-y-3">
                <h3 className="text-xs font-semibold text-white/60">Top Personnel Groupings</h3>
                <div className="space-y-2">
                  {Object.entries(team.offensive_profile.personnel || {}).slice(0, 3).map(([pName, pVal]) => (
                    <div key={pName} className="flex items-center justify-between text-xs bg-white/2 p-2.5 rounded-lg border border-white/5">
                      <span className="font-mono text-white/80 font-semibold">{pName}</span>
                      <div className="flex gap-4 text-right">
                        <div>
                          <div className="text-[9px] text-white/30">USAGE</div>
                          <div>{formatPercent(pVal.usage_rate)}</div>
                        </div>
                        <div>
                          <div className="text-[9px] text-white/30">EPA/PLAY</div>
                          <div className={pVal.epa_per_play >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                            {formatEPA(pVal.epa_per_play)}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Column 2: Defensive Profile */}
            <div className="glass-card p-6 flex flex-col gap-6">
              <h2 className="text-base font-semibold border-b border-white/5 pb-3 text-cyan-400">Defensive Identity</h2>

              <div className="grid grid-cols-2 gap-4">
                <div className="kpi-card">
                  <div className="text-[10px] text-white/40 uppercase">Plays Faced</div>
                  <div className="text-lg font-bold mt-1 text-white">{team.defensive_profile.total_plays_faced}</div>
                </div>
                <div className="kpi-card">
                  <div className="text-[10px] text-white/40 uppercase">EPA/Play Allowed</div>
                  <div className="text-lg font-bold mt-1 text-white">{formatEPA(team.defensive_profile.epa_per_play_allowed)}</div>
                </div>
                <div className="kpi-card">
                  <div className="text-[10px] text-white/40 uppercase">Sacks</div>
                  <div className="text-lg font-bold mt-1 text-white">{team.defensive_profile.sacks}</div>
                </div>
                <div className="kpi-card">
                  <div className="text-[10px] text-white/40 uppercase">Turnovers Forced</div>
                  <div className="text-lg font-bold mt-1 text-white">
                    {team.defensive_profile.interceptions + team.defensive_profile.fumbles_forced}
                  </div>
                </div>
              </div>

              {/* Pass/Run Allowed EPA split */}
              <div className="space-y-3">
                <h3 className="text-xs font-semibold text-white/60">EPA Allowed Split (Negative is Good)</h3>
                <div className="space-y-2 text-xs">
                  <div>
                    <div className="flex justify-between text-white/50 mb-1">
                      <span>Pass EPA Allowed</span>
                      <span className="font-mono text-white">{formatEPA(team.defensive_profile.pass_epa_allowed)}</span>
                    </div>
                    <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                      <div className="h-full bg-cyan-500" style={{ width: `${Math.max(0, (-team.defensive_profile.pass_epa_allowed + 0.3) / 0.6 * 100)}%` }} />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-white/50 mb-1">
                      <span>Run EPA Allowed</span>
                      <span className="font-mono text-white">{formatEPA(team.defensive_profile.run_epa_allowed)}</span>
                    </div>
                    <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                      <div className="h-full bg-amber-500" style={{ width: `${Math.max(0, (-team.defensive_profile.run_epa_allowed + 0.3) / 0.6 * 100)}%` }} />
                    </div>
                  </div>
                </div>
              </div>

              {/* Down breakdown */}
              <div className="space-y-3">
                <h3 className="text-xs font-semibold text-white/60">Defensive Down Breakdown</h3>
                <div className="grid grid-cols-4 gap-2 text-center text-xs">
                  {[1, 2, 3, 4].map((down) => {
                    const downInfo = team.defensive_profile.down_defense?.[String(down)];
                    if (!downInfo) return null;
                    return (
                      <div key={down} className="bg-white/2 p-2 rounded-lg border border-white/5">
                        <div className="text-[9px] text-white/30">{down}{['st','nd','rd','th'][down > 3 ? 3 : down - 1]} Down</div>
                        <div className="font-semibold text-white/90 mt-1">{formatEPA(downInfo.epa_allowed)}</div>
                        <div className="text-[9px] text-white/40 mt-0.5">{formatPercent(downInfo.success_rate_allowed)}</div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Column 3: Roster Identity */}
            <div className="glass-card p-6 flex flex-col gap-6">
              <h2 className="text-base font-semibold border-b border-white/5 pb-3 text-amber-400">Roster Identity</h2>

              <div className="grid grid-cols-2 gap-4">
                <div className="kpi-card">
                  <div className="text-[10px] text-white/40 uppercase">Total Players</div>
                  <div className="text-lg font-bold mt-1 text-white">{team.roster_profile.total_players}</div>
                </div>
                <div className="kpi-card">
                  <div className="text-[10px] text-white/40 uppercase">Avg Age</div>
                  <div className="text-lg font-bold mt-1 text-white">{team.roster_profile.avg_age}</div>
                </div>
                <div className="kpi-card">
                  <div className="text-[10px] text-white/40 uppercase">Avg Experience</div>
                  <div className="text-lg font-bold mt-1 text-white">{team.roster_profile.avg_experience} yrs</div>
                </div>
                <div className="kpi-card">
                  <div className="text-[10px] text-white/40 uppercase">Cap Allocation</div>
                  <div className="text-lg font-bold mt-1 text-white">
                    {formatCurrency(team.roster_profile.total_cap_used || 0)}
                  </div>
                </div>
              </div>

              {/* Age curves */}
              <div className="space-y-3">
                <h3 className="text-xs font-semibold text-white/60">Age Demographics</h3>
                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                  <div className="bg-emerald-500/5 border border-emerald-500/10 p-2.5 rounded-lg">
                    <div className="text-[9px] text-emerald-400 uppercase font-semibold">Under 25</div>
                    <div className="text-base font-bold mt-1 text-white">{team.roster_profile.age_distribution.under_25}</div>
                  </div>
                  <div className="bg-cyan-500/5 border border-cyan-500/10 p-2.5 rounded-lg">
                    <div className="text-[9px] text-cyan-400 uppercase font-semibold">25 to 29</div>
                    <div className="text-base font-bold mt-1 text-white">{team.roster_profile.age_distribution['25_to_29']}</div>
                  </div>
                  <div className="bg-rose-500/5 border border-rose-500/10 p-2.5 rounded-lg">
                    <div className="text-[9px] text-rose-400 uppercase font-semibold">30 Plus</div>
                    <div className="text-base font-bold mt-1 text-white">{team.roster_profile.age_distribution['30_plus']}</div>
                  </div>
                </div>
              </div>

              {/* Roster Top paid contracts */}
              <div className="space-y-3">
                <h3 className="text-xs font-semibold text-white/60">Top Cap Hits</h3>
                <div className="space-y-2 text-xs">
                  {team.roster_profile.top_contracts?.slice(0, 3).map((c) => (
                    <div key={c.player_id} className="flex justify-between items-center bg-white/2 p-2.5 rounded-lg border border-white/5">
                      <div>
                        <span className="font-semibold text-white/90">{c.name}</span>
                        <span className="text-[10px] text-white/30 ml-2 font-mono uppercase">{c.position}</span>
                      </div>
                      <span className="font-semibold text-white/70">{formatCurrency(c.cap_hit)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* PANEL: PLAY-CALLING */}
        {activeTab === 'play_calling' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fade-in-up">
            {/* Left Column: 4th Down Decisions Summary & Detail */}
            <div className="lg:col-span-2 glass-card p-6 flex flex-col gap-6">
              <div className="flex justify-between items-center border-b border-white/5 pb-3">
                <h2 className="text-base font-semibold text-emerald-400">4th Down Decision Analytics</h2>
                <div className="flex gap-2 text-xs">
                  <span className="bg-white/5 border border-white/10 px-2.5 py-1 rounded-md text-white/70">
                    Accuracy: {team.play_calling.fourth_down_analysis.summary.accuracy_pct}%
                  </span>
                  <span className="bg-rose-500/10 border border-rose-500/20 px-2.5 py-1 rounded-md text-rose-400">
                    EP Lost: {team.play_calling.fourth_down_analysis.summary.total_ep_left_on_table}
                  </span>
                </div>
              </div>

              {/* KPI metrics */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="kpi-card text-center">
                  <div className="text-[9px] text-white/40 uppercase">Total 4th Downs</div>
                  <div className="text-xl font-bold mt-1 text-white">{team.play_calling.fourth_down_analysis.summary.total_fourth_downs}</div>
                </div>
                <div className="kpi-card text-center">
                  <div className="text-[9px] text-white/40 uppercase">Optimal Decisions</div>
                  <div className="text-xl font-bold mt-1 text-emerald-400">{team.play_calling.fourth_down_analysis.summary.correct_decisions}</div>
                </div>
                <div className="kpi-card text-center">
                  <div className="text-[9px] text-white/40 uppercase">Went For It</div>
                  <div className="text-xl font-bold mt-1 text-white">{team.play_calling.fourth_down_analysis.summary.went_for_it_count}</div>
                </div>
                <div className="kpi-card text-center">
                  <div className="text-[9px] text-white/40 uppercase">Should Have Gone</div>
                  <div className="text-xl font-bold mt-1 text-rose-400">{team.play_calling.fourth_down_analysis.summary.should_have_gone_for_it}</div>
                </div>
              </div>

              {/* Decision Log */}
              <div className="space-y-3">
                <h3 className="text-xs font-semibold text-white/60">Key 4th Down Decision Log</h3>
                <div className="overflow-x-auto">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Week/Qtr</th>
                        <th>Situation</th>
                        <th>Actual</th>
                        <th>Optimal</th>
                        <th>EP Cost</th>
                        <th>Description</th>
                      </tr>
                    </thead>
                    <tbody>
                      {team.play_calling.fourth_down_analysis.decisions.slice(0, 5).map((d, i) => (
                        <tr key={i}>
                          <td className="font-mono text-xs">W{d.week} Q{d.quarter}</td>
                          <td>
                            <div className="font-semibold text-white/80">{d.yard_line} yd line</div>
                            <div className="text-[10px] text-white/30">{d.yards_to_go} to go · Diff {d.score_diff}</div>
                          </td>
                          <td className="text-xs uppercase font-medium">{d.actual_decision.replace('_', ' ')}</td>
                          <td className="text-xs uppercase font-semibold text-emerald-400">{d.recommended_decision.replace('_', ' ')}</td>
                          <td className="font-mono text-rose-400 font-semibold">{d.ep_left_on_table > 0 ? `-${d.ep_left_on_table.toFixed(1)}` : '0.0'}</td>
                          <td className="text-[11px] text-white/40 max-w-[200px] truncate">{d.description}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Right Column: Predictability, Efficiency, & Recommendations */}
            <div className="flex flex-col gap-6">
              {/* Predictability */}
              <div className="glass-card p-6 flex flex-col gap-4">
                <h2 className="text-base font-semibold border-b border-white/5 pb-3 text-amber-400">Predictability Profile</h2>
                <div className="kpi-card flex items-center justify-between">
                  <div>
                    <div className="text-[10px] text-white/40 uppercase">Predictability Index</div>
                    <div className="text-2xl font-bold mt-1 text-white">{(team.play_calling.tendency_analysis.avg_predictability * 100).toFixed(0)}</div>
                  </div>
                  <div className="text-xs text-white/45 text-right font-medium">
                    {team.play_calling.tendency_analysis.avg_predictability > 0.4 ? 'High predictability situation' : 'Balanced play-calling'}
                  </div>
                </div>

                <div className="space-y-3">
                  <h3 className="text-xs font-semibold text-white/60">Most Predictable Situations</h3>
                  <div className="space-y-2">
                    {team.play_calling.tendency_analysis.most_predictable.map((p, idx) => (
                      <div key={idx} className="flex justify-between items-center text-xs bg-white/2 p-2.5 rounded-lg border border-white/5">
                        <div>
                          <span className="font-bold text-white">{p.down}{['st','nd','rd','th'][p.down > 3 ? 3 : p.down - 1]} & {p.distance}</span>
                        </div>
                        <div className="text-right">
                          <span className="text-white/40 mr-2">Pass Rate:</span>
                          <span className="font-semibold text-amber-400">{formatPercent(p.pass_rate)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Recommendations */}
              <div className="glass-card p-6 flex flex-col gap-4 flex-1">
                <h2 className="text-base font-semibold border-b border-white/5 pb-3 text-emerald-400">Actionable Play-Calling Upgrades</h2>
                <div className="space-y-3 flex-1 overflow-y-auto max-h-[350px]">
                  {team.play_calling.recommendations.map((rec, i) => (
                    <div key={i} className="rec-card">
                      {rec}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* PANEL: ROSTER VALUE */}
        {activeTab === 'roster' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fade-in-up">
            {/* Left Column: Player VOR & Cap Efficiency Ratings */}
            <div className="lg:col-span-2 glass-card p-6 flex flex-col gap-6">
              <div className="flex justify-between items-center border-b border-white/5 pb-3">
                <h2 className="text-base font-semibold text-emerald-400">Roster Value Over Replacement (VOR)</h2>
                <span className="text-xs text-white/40 font-mono">Total Roster Cap: {formatCurrency(team.roster_value.value_analysis.total_cap_used)}</span>
              </div>

              {/* Key players table */}
              <div className="space-y-3">
                <h3 className="text-xs font-semibold text-white/60">Top 8 Value Contributors (Ranked by VOR)</h3>
                <div className="overflow-x-auto">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Player</th>
                        <th>Pos</th>
                        <th>Age</th>
                        <th>Cap Hit</th>
                        <th>VOR</th>
                        <th>Cap Efficiency</th>
                        <th>Production</th>
                      </tr>
                    </thead>
                    <tbody>
                      {team.roster_value.value_analysis.roster.slice(0, 8).map((p) => (
                        <tr key={p.player_id}>
                          <td>
                            <div className="font-semibold text-white/90">{p.name}</div>
                            <div className="text-[10px] text-white/30">{p.position_group} · {p.games} games</div>
                          </td>
                          <td className="font-mono text-xs text-white/50">{p.position}</td>
                          <td>{p.age || 'N/A'}</td>
                          <td className="font-mono text-xs">{formatCurrency(p.cap_hit)}</td>
                          <td className={`font-mono font-semibold ${p.vor >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>{p.vor >= 0 ? '+' : ''}{p.vor.toFixed(1)}</td>
                          <td className="font-mono">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                              p.cap_efficiency >= 2 ? 'bg-emerald-500/10 text-emerald-400' :
                              p.cap_efficiency >= 0 ? 'bg-cyan-500/10 text-cyan-400' :
                              'bg-rose-500/10 text-rose-400'
                            }`}>
                              {p.cap_efficiency.toFixed(1)}x
                            </span>
                          </td>
                          <td className="text-xs text-white/50 font-medium">
                            {p.passing_yards > 0 && `${p.passing_yards} Yds, ${p.total_tds} TD`}
                            {p.rushing_yards > 0 && p.passing_yards === 0 && `${p.rushing_yards} Rush Yds, ${p.total_tds} TD`}
                            {p.receiving_yards > 0 && `${p.receiving_yards} Rec Yds, ${p.total_tds} TD`}
                            {p.passing_yards === 0 && p.rushing_yards === 0 && p.receiving_yards === 0 && 'Depth / Defensive contributor'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Right Column: Roster Recommendations */}
            <div className="flex flex-col gap-6">
              {/* Draft Needs & Priorities */}
              <div className="glass-card p-6 flex flex-col gap-4">
                <h2 className="text-base font-semibold border-b border-white/5 pb-3 text-cyan-400">Draft Needs & Priorities</h2>
                <div className="space-y-3">
                  {team.roster_value.recommendations.draft_needs.map((n, i) => (
                    <div key={i} className="bg-white/2 p-3 rounded-lg border border-white/5 flex items-center justify-between text-xs">
                      <div>
                        <div className="font-bold text-white flex items-center gap-2">
                          {n.position_group}
                          <span className={`px-1.5 py-0.5 rounded text-[8px] font-semibold ${
                            n.priority === 'HIGH' ? 'bg-rose-500/15 text-rose-400' : 'bg-amber-500/15 text-amber-400'
                          }`}>
                            {n.priority}
                          </span>
                        </div>
                        <div className="text-[10px] text-white/45 mt-1">{n.reason}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-[9px] text-white/30">AVG VOR</div>
                        <div className="font-semibold text-rose-400">{n.avg_vor}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Roster & Cap Adjustments */}
              <div className="glass-card p-6 flex flex-col gap-4 flex-1">
                <h2 className="text-base font-semibold border-b border-white/5 pb-3 text-amber-400">Actionable Cap & Roster Changes</h2>
                <div className="space-y-3 overflow-y-auto max-h-[300px]">
                  {/* Re-signs */}
                  {team.roster_value.recommendations.re_sign_candidates.slice(0, 2).map((c, i) => (
                    <div key={`re-${i}`} className="bg-emerald-500/5 border border-emerald-500/10 p-3 rounded-lg text-xs">
                      <div className="font-bold text-emerald-400">Re-sign Candidate: {c.name} ({c.position})</div>
                      <div className="text-white/50 mt-1">{c.reason}</div>
                    </div>
                  ))}
                  {/* Cuts */}
                  {team.roster_value.recommendations.cut_candidates.slice(0, 2).map((c, i) => (
                    <div key={`cut-${i}`} className="bg-rose-500/5 border border-rose-500/10 p-3 rounded-lg text-xs">
                      <div className="font-bold text-rose-400">Salary Cut Candidate: {c.name} ({c.position})</div>
                      <div className="text-white/50 mt-1">{c.reason}</div>
                      <div className="mt-2 text-[10px] font-mono text-white/30">
                        Cap savings: {formatCurrency(c.cap_savings || 0)} · Dead cap: {formatCurrency(c.dead_cap || 0)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* PANEL: IN-GAME DECISIONS */}
        {activeTab === 'decisions' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fade-in-up">
            {/* Left Column: Win Probability Swings */}
            <div className="lg:col-span-2 glass-card p-6 flex flex-col gap-6">
              <div className="flex justify-between items-center border-b border-white/5 pb-3">
                <h2 className="text-base font-semibold text-emerald-400">Win Probability Added (WPA) Swings</h2>
                <span className="text-xs text-white/40 font-mono">Season total WPA: {team.in_game_decisions.win_probability_analysis.season_total_wpa}</span>
              </div>

              {/* KPI metrics */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="kpi-card text-center">
                  <div className="text-[9px] text-white/40 uppercase">Clutch EPA/Play</div>
                  <div className="text-xl font-bold mt-1 text-white">{formatEPA(team.in_game_decisions.clutch_performance.clutch_epa)}</div>
                </div>
                <div className="kpi-card text-center">
                  <div className="text-[9px] text-white/40 uppercase">Clutch Differential</div>
                  <div className={`text-xl font-bold mt-1 ${
                    team.in_game_decisions.clutch_performance.clutch_differential >= 0 ? 'text-emerald-400' : 'text-rose-400'
                  }`}>
                    {formatEPA(team.in_game_decisions.clutch_performance.clutch_differential)}
                  </div>
                </div>
                <div className="kpi-card text-center">
                  <div className="text-[9px] text-white/40 uppercase">Timeout Efficiency</div>
                  <div className="text-xl font-bold mt-1 text-white">{team.in_game_decisions.timeout_analysis.grade}</div>
                </div>
                <div className="kpi-card text-center">
                  <div className="text-[9px] text-white/40 uppercase">2pt Decision Acc</div>
                  <div className="text-xl font-bold mt-1 text-white">{team.in_game_decisions.two_point_analysis.decision_accuracy}%</div>
                </div>
              </div>

              {/* Big plays */}
              <div className="space-y-4">
                <h3 className="text-xs font-semibold text-white/60">Top Game-Changing Play Swings</h3>
                <div className="space-y-2.5">
                  {team.in_game_decisions.win_probability_analysis.biggest_positive_plays.slice(0, 3).map((p, idx) => (
                    <div key={`pos-${idx}`} className="flex justify-between items-center bg-emerald-500/2 border border-emerald-500/5 p-3 rounded-xl text-xs">
                      <div className="flex-1 pr-4">
                        <span className="font-bold text-white/90">W{p.week} Q{p.quarter}</span>
                        <p className="text-white/50 text-[11px] mt-1 line-clamp-1">{p.description}</p>
                      </div>
                      <div className="text-right shrink-0">
                        <div className="text-[9px] text-white/30">WPA</div>
                        <div className="font-mono font-bold text-emerald-400">+{formatPercent(p.wpa)}</div>
                      </div>
                    </div>
                  ))}
                  {team.in_game_decisions.win_probability_analysis.biggest_negative_plays.slice(0, 3).map((p, idx) => (
                    <div key={`neg-${idx}`} className="flex justify-between items-center bg-rose-500/2 border border-rose-500/5 p-3 rounded-xl text-xs">
                      <div className="flex-1 pr-4">
                        <span className="font-bold text-white/90">W{p.week} Q{p.quarter}</span>
                        <p className="text-white/50 text-[11px] mt-1 line-clamp-1">{p.description}</p>
                      </div>
                      <div className="text-right shrink-0">
                        <div className="text-[9px] text-white/30">WPA</div>
                        <div className="font-mono font-bold text-rose-400">{formatPercent(p.wpa)}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Right Column: In-game Recommendations */}
            <div className="flex flex-col gap-6">
              {/* Timeout & 2-point details */}
              <div className="glass-card p-6 flex flex-col gap-4">
                <h2 className="text-base font-semibold border-b border-white/5 pb-3 text-cyan-400">Timeout & 2-Point Decisions</h2>
                <div className="space-y-4 text-xs">
                  <div>
                    <div className="flex justify-between text-white/50 mb-1">
                      <span>Wasted Timeouts</span>
                      <span className="text-rose-400 font-semibold">{team.in_game_decisions.timeout_analysis.wasted_timeouts}</span>
                    </div>
                    <p className="text-[10px] text-white/40 leading-relaxed">
                      Timeouts used in non-strategic situations during early quarters, limiting crucial late-game options.
                    </p>
                  </div>
                  <div>
                    <div className="flex justify-between text-white/50 mb-1">
                      <span>Missed 2pt Opportunities</span>
                      <span className="text-rose-400 font-semibold">{team.in_game_decisions.two_point_analysis.missed_opportunities}</span>
                    </div>
                    <p className="text-[10px] text-white/40 leading-relaxed">
                      Kicked extra points when win probability models strongly recommended attempting a two-point conversion.
                    </p>
                  </div>
                </div>
              </div>

              {/* Recommendations */}
              <div className="glass-card p-6 flex flex-col gap-4 flex-1">
                <h2 className="text-base font-semibold border-b border-white/5 pb-3 text-emerald-400">Actionable Coach Decisions</h2>
                <div className="space-y-3 flex-1 overflow-y-auto max-h-[300px]">
                  {team.in_game_decisions.recommendations.map((rec, i) => (
                    <div key={i} className="rec-card">
                      {rec}
                    </div>
                  ))}
                  {team.in_game_decisions.recommendations.length === 0 && (
                    <div className="text-xs text-white/30 text-center py-8">No critical decision changes recommended.</div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* PANEL: FIELD ANALYTICS */}
        {activeTab === 'field' && (
          <FootballField
            efficiencyData={team.play_calling.efficiency_analysis.field_zone_efficiency}
            recommendations={team.play_calling.efficiency_analysis.recommendations}
          />
        )}
      </main>
    </div>
  );
}
