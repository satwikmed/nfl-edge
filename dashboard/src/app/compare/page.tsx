'use client';

import { useEffect, useState } from 'react';
import { TeamSummary, TeamData } from '@/lib/types';
import { formatGrade, formatPercent, formatEPA, formatCurrency } from '@/lib/data';

export default function ComparePage() {
  const [summaries, setSummaries] = useState<TeamSummary[]>([]);
  const [teamAId, setTeamAId] = useState<string>('');
  const [teamBId, setTeamBId] = useState<string>('');
  const [teamA, setTeamA] = useState<TeamData | null>(null);
  const [teamB, setTeamB] = useState<TeamData | null>(null);

  useEffect(() => {
    fetch('/data/teams_summary.json')
      .then((res) => res.json())
      .then((data) => {
        setSummaries(data);
        if (data.length >= 2) {
          setTeamAId(data[0].id);
          setTeamBId(data[1].id);
        }
      });
  }, []);

  useEffect(() => {
    if (!teamAId) return;
    fetch(`/data/team_${teamAId.toLowerCase()}.json`)
      .then((res) => res.json())
      .then(setTeamA);
  }, [teamAId]);

  useEffect(() => {
    if (!teamBId) return;
    fetch(`/data/team_${teamBId.toLowerCase()}.json`)
      .then((res) => res.json())
      .then(setTeamB);
  }, [teamBId]);

  return (
    <div className="min-h-screen px-6 py-12 max-w-[1400px] mx-auto animate-fade-in-up">
      <div className="border-b border-white/5 pb-8 mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Franchise Head-to-Head Comparison</h1>
        <p className="text-xs text-white/40 mt-1.5">
          Select any two teams to compare offensive identity, defensive capabilities, roster efficiency, and decision profiles.
        </p>
      </div>

      {/* Selectors */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div>
          <label className="block text-xs uppercase tracking-wider text-white/40 mb-2 font-medium">Team A</label>
          <select
            value={teamAId}
            onChange={(e) => setTeamAId(e.target.value)}
            className="w-full bg-white/5 hover:bg-white/8 border border-white/10 hover:border-white/20 transition-all rounded-xl px-4 py-3 text-sm text-white/80 focus:outline-none focus:border-emerald-500/50 backdrop-blur-md cursor-pointer font-medium"
          >
            {summaries.map((s) => (
              <option key={s.id} value={s.id} className="bg-[#161622] text-white">
                {s.name} ({s.abbreviation})
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs uppercase tracking-wider text-white/40 mb-2 font-medium">Team B</label>
          <select
            value={teamBId}
            onChange={(e) => setTeamBId(e.target.value)}
            className="w-full bg-white/5 hover:bg-white/8 border border-white/10 hover:border-white/20 transition-all rounded-xl px-4 py-3 text-sm text-white/80 focus:outline-none focus:border-emerald-500/50 backdrop-blur-md cursor-pointer font-medium"
          >
            {summaries.map((s) => (
              <option key={s.id} value={s.id} className="bg-[#161622] text-white">
                {s.name} ({s.abbreviation})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Comparison Grid */}
      {teamA && teamB && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Team A stats */}
          <div className="glass-card p-6 flex flex-col gap-6">
            <div className="text-center pb-4 border-b border-white/5">
              <span className="text-2xl font-bold">{teamA.name}</span>
              <div className="mt-2 flex items-center justify-center gap-2">
                <span className="text-sm font-semibold">{teamA.wins}-{teamA.losses}</span>
                <span
                  className="grade-badge text-[10px] w-6 h-6 rounded-md font-bold"
                  style={{
                    background: formatGrade(teamA.composite_grade).bg,
                    color: formatGrade(teamA.composite_grade).color,
                  }}
                >
                  {teamA.composite_grade}
                </span>
              </div>
            </div>

            {/* Overall scores */}
            <div className="space-y-4">
              <h3 className="text-xs font-semibold text-emerald-400 uppercase tracking-wide">Overall Grades</h3>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="kpi-card text-center col-span-2">
                  <div className="text-[9px] text-white/30">PLAY-CALLING EFFICIENCY</div>
                  <div className="font-bold text-sm mt-1" style={{ color: formatGrade(teamA.grades.play_calling).color }}>
                    {teamA.grades.play_calling} ({teamA.scores.play_calling})
                  </div>
                </div>
                <div className="kpi-card text-center">
                  <div className="text-[9px] text-white/30">4TH DOWN DECISIONS</div>
                  <div className="font-bold text-sm mt-1" style={{ color: formatGrade(teamA.grades.fourth_down).color }}>
                    {teamA.grades.fourth_down} ({teamA.scores.fourth_down})
                  </div>
                </div>
                <div className="kpi-card text-center">
                  <div className="text-[9px] text-white/30">ROSTER CAP EFFICIENCY</div>
                  <div className="font-bold text-sm mt-1" style={{ color: formatGrade(teamA.grades.roster_cap).color }}>
                    {teamA.grades.roster_cap} ({teamA.scores.roster_cap})
                  </div>
                </div>
                <div className="kpi-card text-center">
                  <div className="text-[9px] text-white/30">DEFENSIVE EXECUTION</div>
                  <div className="font-bold text-sm mt-1" style={{ color: formatGrade(teamA.grades.defense).color }}>
                    {teamA.grades.defense} ({teamA.scores.defense})
                  </div>
                </div>
                <div className="kpi-card text-center">
                  <div className="text-[9px] text-white/30">GAME MANAGEMENT</div>
                  <div className="font-bold text-sm mt-1" style={{ color: formatGrade(teamA.grades.game_management).color }}>
                    {teamA.grades.game_management} ({teamA.scores.game_management})
                  </div>
                </div>
              </div>
            </div>

            {/* Identity values */}
            <div className="space-y-4">
              <h3 className="text-xs font-semibold text-emerald-400 uppercase tracking-wide">Efficiency Profiles</h3>
              <div className="space-y-3 text-xs">
                <div className="flex justify-between items-center bg-white/2 p-2.5 rounded-lg border border-white/5">
                  <span className="text-white/50">Offensive EPA/play</span>
                  <span className="font-mono font-bold">{formatEPA(teamA.offensive_profile.epa_per_play)}</span>
                </div>
                <div className="flex justify-between items-center bg-white/2 p-2.5 rounded-lg border border-white/5">
                  <span className="text-white/50">Defensive EPA allowed</span>
                  <span className="font-mono font-bold">{formatEPA(teamA.defensive_profile.epa_per_play_allowed)}</span>
                </div>
                <div className="flex justify-between items-center bg-white/2 p-2.5 rounded-lg border border-white/5">
                  <span className="text-white/50">Pass Rate</span>
                  <span className="font-mono font-bold">{formatPercent(teamA.offensive_profile.pass_rate)}</span>
                </div>
                <div className="flex justify-between items-center bg-white/2 p-2.5 rounded-lg border border-white/5">
                  <span className="text-white/50">Roster Avg Age</span>
                  <span className="font-mono font-bold">{teamA.roster_profile.avg_age} yrs</span>
                </div>
              </div>
            </div>
          </div>

          {/* Metric Labels & Direct Comparison Diff */}
          <div className="glass-card p-6 flex flex-col justify-center gap-6 bg-white/1 border-dashed">
            <h2 className="text-center font-bold text-lg text-white/80">Comparative Metrics</h2>
            
            <div className="space-y-6">
              <div className="text-center">
                <div className="text-xs text-white/30 uppercase tracking-wider">Composite Score Diff</div>
                <div className="text-2xl font-extrabold mt-1 text-white">
                  {Math.abs(teamA.composite_score - teamB.composite_score).toFixed(1)}
                  <span className="text-xs text-white/40 font-normal ml-2">
                    pts in favor of {teamA.composite_score > teamB.composite_score ? teamA.abbreviation : teamB.abbreviation}
                  </span>
                </div>
              </div>

              <div className="text-center">
                <div className="text-xs text-white/30 uppercase tracking-wider">EPA Differential Split</div>
                <div className="text-2xl font-extrabold mt-1 text-white">
                  {formatEPA(teamA.offensive_profile.epa_per_play - teamB.offensive_profile.epa_per_play)}
                  <span className="text-xs text-white/40 font-normal ml-2">Offensive EPA/play diff</span>
                </div>
              </div>

              <div className="text-center">
                <div className="text-xs text-white/30 uppercase tracking-wider">Cap Efficiency Comparison</div>
                <div className="text-sm font-semibold mt-2 text-white/70">
                  {teamA.abbreviation}: {formatCurrency(teamA.roster_profile.total_cap_used || 0)} used
                  <br />
                  {teamB.abbreviation}: {formatCurrency(teamB.roster_profile.total_cap_used || 0)} used
                </div>
              </div>
            </div>
          </div>

          {/* Team B stats */}
          <div className="glass-card p-6 flex flex-col gap-6">
            <div className="text-center pb-4 border-b border-white/5">
              <span className="text-2xl font-bold">{teamB.name}</span>
              <div className="mt-2 flex items-center justify-center gap-2">
                <span className="text-sm font-semibold">{teamB.wins}-{teamB.losses}</span>
                <span
                  className="grade-badge text-[10px] w-6 h-6 rounded-md font-bold"
                  style={{
                    background: formatGrade(teamB.composite_grade).bg,
                    color: formatGrade(teamB.composite_grade).color,
                  }}
                >
                  {teamB.composite_grade}
                </span>
              </div>
            </div>

            {/* Overall scores */}
            <div className="space-y-4">
              <h3 className="text-xs font-semibold text-emerald-400 uppercase tracking-wide">Overall Grades</h3>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="kpi-card text-center col-span-2">
                  <div className="text-[9px] text-white/30">PLAY-CALLING EFFICIENCY</div>
                  <div className="font-bold text-sm mt-1" style={{ color: formatGrade(teamB.grades.play_calling).color }}>
                    {teamB.grades.play_calling} ({teamB.scores.play_calling})
                  </div>
                </div>
                <div className="kpi-card text-center">
                  <div className="text-[9px] text-white/30">4TH DOWN DECISIONS</div>
                  <div className="font-bold text-sm mt-1" style={{ color: formatGrade(teamB.grades.fourth_down).color }}>
                    {teamB.grades.fourth_down} ({teamB.scores.fourth_down})
                  </div>
                </div>
                <div className="kpi-card text-center">
                  <div className="text-[9px] text-white/30">ROSTER CAP EFFICIENCY</div>
                  <div className="font-bold text-sm mt-1" style={{ color: formatGrade(teamB.grades.roster_cap).color }}>
                    {teamB.grades.roster_cap} ({teamB.scores.roster_cap})
                  </div>
                </div>
                <div className="kpi-card text-center">
                  <div className="text-[9px] text-white/30">DEFENSIVE EXECUTION</div>
                  <div className="font-bold text-sm mt-1" style={{ color: formatGrade(teamB.grades.defense).color }}>
                    {teamB.grades.defense} ({teamB.scores.defense})
                  </div>
                </div>
                <div className="kpi-card text-center">
                  <div className="text-[9px] text-white/30">GAME MANAGEMENT</div>
                  <div className="font-bold text-sm mt-1" style={{ color: formatGrade(teamB.grades.game_management).color }}>
                    {teamB.grades.game_management} ({teamB.scores.game_management})
                  </div>
                </div>
              </div>
            </div>

            {/* Identity values */}
            <div className="space-y-4">
              <h3 className="text-xs font-semibold text-emerald-400 uppercase tracking-wide">Efficiency Profiles</h3>
              <div className="space-y-3 text-xs">
                <div className="flex justify-between items-center bg-white/2 p-2.5 rounded-lg border border-white/5">
                  <span className="text-white/50">Offensive EPA/play</span>
                  <span className="font-mono font-bold">{formatEPA(teamB.offensive_profile.epa_per_play)}</span>
                </div>
                <div className="flex justify-between items-center bg-white/2 p-2.5 rounded-lg border border-white/5">
                  <span className="text-white/50">Defensive EPA allowed</span>
                  <span className="font-mono font-bold">{formatEPA(teamB.defensive_profile.epa_per_play_allowed)}</span>
                </div>
                <div className="flex justify-between items-center bg-white/2 p-2.5 rounded-lg border border-white/5">
                  <span className="text-white/50">Pass Rate</span>
                  <span className="font-mono font-bold">{formatPercent(teamB.offensive_profile.pass_rate)}</span>
                </div>
                <div className="flex justify-between items-center bg-white/2 p-2.5 rounded-lg border border-white/5">
                  <span className="text-white/50">Roster Avg Age</span>
                  <span className="font-mono font-bold">{teamB.roster_profile.avg_age} yrs</span>
                </div>
              </div>
            </div>
          </div>

        </div>
      )}
    </div>
  );
}
