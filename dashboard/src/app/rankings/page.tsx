'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { TeamSummary } from '@/lib/types';
import { formatGrade, formatPercent, formatEPA } from '@/lib/data';

type SortKey = 'composite_score' | 'play_calling' | 'fourth_down' | 'roster_cap' | 'defense' | 'game_management' | 'offensive_epa' | 'defensive_epa';

export default function RankingsPage() {
  const [teams, setTeams] = useState<TeamSummary[]>([]);
  const [sortBy, setSortBy] = useState<SortKey>('composite_score');

  useEffect(() => {
    fetch('/data/teams_summary.json')
      .then((res) => res.json())
      .then((data) => setTeams(data));
  }, []);

  const sortedTeams = [...teams].sort((a, b) => {
    if (sortBy === 'offensive_epa') return b.offensive_epa - a.offensive_epa;
    if (sortBy === 'defensive_epa') return a.defensive_epa - b.defensive_epa; // lower is better
    if (sortBy === 'composite_score') return b.composite_score - a.composite_score;
    return b.scores[sortBy as keyof typeof b.scores] - a.scores[sortBy as keyof typeof a.scores];
  });

  return (
    <div className="min-h-screen px-6 py-12 max-w-[1400px] mx-auto animate-fade-in-up">
      <div className="flex flex-col md:flex-row justify-between md:items-center gap-6 border-b border-white/5 pb-8 mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">League Rankings & Metrics</h1>
          <p className="text-xs text-white/40 mt-1.5">
            Rank and compare all 32 franchises across all core profiling and analytical engine outputs.
          </p>
        </div>

        {/* Sort Controls */}
        <div className="flex flex-wrap gap-2">
          {([
            { key: 'composite_score', label: 'Overall Rating' },
            { key: 'play_calling', label: 'Play-Calling' },
            { key: 'fourth_down', label: '4th Down' },
            { key: 'roster_cap', label: 'Roster Cap' },
            { key: 'defense', label: 'Defense' },
            { key: 'game_management', label: 'Game Mgmt' },
          ] as const).map((opt) => (
            <button
              key={opt.key}
              onClick={() => setSortBy(opt.key)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                sortBy === opt.key
                  ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                  : 'bg-white/3 text-white/40 border border-white/5 hover:text-white/70'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      <div className="glass-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="data-table text-xs">
            <thead>
              <tr>
                <th className="w-16">Rank</th>
                <th>Team</th>
                <th>Record</th>
                <th>Play-Calling</th>
                <th>4th Down</th>
                <th>Roster Cap</th>
                <th>Defense</th>
                <th>Game Mgmt</th>
                <th>Composite Rating</th>
              </tr>
            </thead>
            <tbody>
              {sortedTeams.map((team, idx) => {
                const gradeInfo = formatGrade(team.composite_grade);
                return (
                  <tr key={team.id} className="group">
                    <td className="font-mono text-xs text-white/20 font-bold pl-6">{idx + 1}</td>
                    <td>
                      <Link href={`/team/${team.id}`} className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center font-bold text-xs group-hover:border-emerald-500/30 transition-colors">
                          {team.abbreviation}
                        </div>
                        <div>
                          <span className="text-sm font-semibold group-hover:text-emerald-400 transition-colors">{team.name}</span>
                          <span className="text-[10px] text-white/30 ml-2 uppercase font-mono">{team.division}</span>
                        </div>
                      </Link>
                    </td>
                    <td className="font-medium text-white/80">{team.wins}-{team.losses}</td>
                    <td style={{ color: formatGrade(team.grades.play_calling).color }}>
                      {team.grades.play_calling} <span className="text-[10px] text-white/20 ml-1">({team.scores.play_calling})</span>
                    </td>
                    <td style={{ color: formatGrade(team.grades.fourth_down).color }}>
                      {team.grades.fourth_down} <span className="text-[10px] text-white/20 ml-1">({team.scores.fourth_down})</span>
                    </td>
                    <td style={{ color: formatGrade(team.grades.roster_cap).color }}>
                      {team.grades.roster_cap} <span className="text-[10px] text-white/20 ml-1">({team.scores.roster_cap})</span>
                    </td>
                    <td style={{ color: formatGrade(team.grades.defense).color }}>
                      {team.grades.defense} <span className="text-[10px] text-white/20 ml-1">({team.scores.defense})</span>
                    </td>
                    <td style={{ color: formatGrade(team.grades.game_management).color }}>
                      {team.grades.game_management} <span className="text-[10px] text-white/20 ml-1">({team.scores.game_management})</span>
                    </td>
                    <td>
                      <div className="flex items-center gap-2">
                        <span
                          className="grade-badge text-[10px] w-6 h-6 rounded-md font-bold"
                          style={{ background: gradeInfo.bg, color: gradeInfo.color }}
                        >
                          {team.composite_grade}
                        </span>
                        <span className="font-bold text-white">{team.composite_score}</span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
