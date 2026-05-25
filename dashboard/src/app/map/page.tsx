'use client';

import { useEffect, useState, useMemo, useRef } from 'react';
import Link from 'next/link';
import { TeamSummary, TEAM_COLORS } from '@/lib/types';
import { formatGrade, formatEPA } from '@/lib/data';

type MetricKey = 'composite_score' | 'offensive_epa' | 'defensive_epa' | 'play_calling' | 'fourth_down' | 'roster_cap' | 'defense' | 'game_management';

const METRIC_OPTIONS: { key: MetricKey; label: string }[] = [
  { key: 'composite_score', label: 'Overall Rating' },
  { key: 'offensive_epa', label: 'Offensive EPA' },
  { key: 'defensive_epa', label: 'Defensive EPA' },
  { key: 'play_calling', label: 'Play-Calling Efficiency' },
  { key: 'roster_cap', label: 'Roster Cap Efficiency' },
  { key: 'game_management', label: 'Game Management' },
];

function getMetricValue(team: TeamSummary, metric: MetricKey): number {
  if (metric === 'composite_score') return team.composite_score;
  if (metric === 'offensive_epa') return team.offensive_epa;
  if (metric === 'defensive_epa') return -team.defensive_epa; // Invert: lower allowed (more negative) = better defense
  return team.scores[metric as keyof typeof team.scores] || 0;
}

export default function HomePage() {
  const [teams, setTeams] = useState<TeamSummary[]>([]);
  const [xAxis, setXAxis] = useState<MetricKey>('offensive_epa');
  const [yAxis, setYAxis] = useState<MetricKey>('defensive_epa');
  const [hoveredTeam, setHoveredTeam] = useState<TeamSummary | null>(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch('/data/teams_summary.json')
      .then(res => res.json())
      .then(setTeams);
  }, []);

  // Calculate coordinates, averages, and scaling
  const chartData = useMemo(() => {
    if (teams.length === 0) return { points: [], avgX: 0, avgY: 0, minX: 0, maxX: 0, minY: 0, maxY: 0 };

    const xVals = teams.map(t => getMetricValue(t, xAxis));
    const yVals = teams.map(t => getMetricValue(t, yAxis));

    const avgX = xVals.reduce((a, b) => a + b, 0) / teams.length;
    const avgY = yVals.reduce((a, b) => a + b, 0) / teams.length;

    const minX = Math.min(...xVals);
    const maxX = Math.max(...xVals);
    const minY = Math.min(...yVals);
    const maxY = Math.max(...yVals);

    // Padding factor to avoid points rendering exactly on the edge
    const padX = (maxX - minX) * 0.1 || 1;
    const padY = (maxY - minY) * 0.1 || 1;

    const points = teams.map(team => {
      const xVal = getMetricValue(team, xAxis);
      const yVal = getMetricValue(team, yAxis);

      // Map values to 0-100 percentage coordinates
      const pctX = ((xVal - (minX - padX)) / ((maxX + padX) - (minX - padX))) * 100;
      const pctY = 100 - (((yVal - (minY - padY)) / ((maxY + padY) - (minY - padY))) * 100); // 100 is bottom in SVG

      // Quadrant check
      // Q1: Top-Right (Above average X, Above average Y)
      // Q2: Top-Left (Below average X, Above average Y)
      // Q3: Bottom-Left (Below average X, Below average Y)
      // Q4: Bottom-Right (Above average X, Below average Y)
      let quadrant = 3;
      if (xVal >= avgX && yVal >= avgY) quadrant = 1;
      else if (xVal < avgX && yVal >= avgY) quadrant = 2;
      else if (xVal >= avgX && yVal < avgY) quadrant = 4;

      return {
        team,
        xVal,
        yVal,
        pctX,
        pctY,
        quadrant,
      };
    });

    const avgPctX = ((avgX - (minX - padX)) / ((maxX + padX) - (minX - padX))) * 100;
    const avgPctY = 100 - (((avgY - (minY - padY)) / ((maxY + padY) - (minY - padY))) * 100);

    return {
      points,
      avgX,
      avgY,
      avgPctX,
      avgPctY,
      minX,
      maxX,
      minY,
      maxY,
    };
  }, [teams, xAxis, yAxis]);

  // Group teams by quadrant
  const groupedQuadrants = useMemo(() => {
    const groups: Record<number, any[]> = { 1: [], 2: [], 3: [], 4: [] };
    chartData.points.forEach(p => {
      groups[p.quadrant].push(p);
    });
    return groups;
  }, [chartData.points]);

  const xLabel = METRIC_OPTIONS.find(o => o.key === xAxis)?.label || '';
  const yLabel = METRIC_OPTIONS.find(o => o.key === yAxis)?.label || '';

  return (
    <div className="min-h-screen">
      {/* Hero & Axis Config */}
      <section className="relative px-6 pt-12 pb-6 max-w-[1400px] mx-auto">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div>
            <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-white via-white to-white/50 bg-clip-text text-transparent">
              NFL Quadrant Intelligence
            </h1>
            <p className="mt-2 text-white/40 text-xs max-w-xl leading-relaxed">
              Compare any two metrics to divide the league into 4 distinct quadrants based on actual season performance. Labels and dots automatically update dynamically.
            </p>
          </div>

          {/* Selectors for axes */}
          <div className="flex flex-wrap items-center gap-3 bg-white/2 border border-white/5 rounded-2xl p-4 backdrop-blur-xl">
            <div className="flex flex-col gap-1.5">
              <span className="text-[10px] uppercase tracking-wider text-white/30 font-semibold">X-Axis Metric</span>
              <select
                value={xAxis}
                onChange={(e) => setXAxis(e.target.value as MetricKey)}
                className="bg-white/5 text-xs text-white/80 rounded-lg px-3 py-2 border border-white/10 outline-none cursor-pointer hover:border-white/20 transition-all font-medium"
              >
                {METRIC_OPTIONS.filter(opt => opt.key !== yAxis).map(opt => (
                  <option key={opt.key} value={opt.key} className="bg-[#0f0f15] text-white">
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <span className="text-[10px] uppercase tracking-wider text-white/30 font-semibold">Y-Axis Metric</span>
              <select
                value={yAxis}
                onChange={(e) => setYAxis(e.target.value as MetricKey)}
                className="bg-white/5 text-xs text-white/80 rounded-lg px-3 py-2 border border-white/10 outline-none cursor-pointer hover:border-white/20 transition-all font-medium"
              >
                {METRIC_OPTIONS.filter(opt => opt.key !== xAxis).map(opt => (
                  <option key={opt.key} value={opt.key} className="bg-[#0f0f15] text-white">
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </section>

      {/* Main Graph Section */}
      <section className="px-6 max-w-[1400px] mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* SVG Quadrant Scatter Plot */}
          <div className="lg:col-span-2 flex flex-col gap-3">
            <div
              ref={chartRef}
              className="glass-card p-6 relative overflow-hidden h-[540px] flex items-center justify-center cursor-crosshair border border-white/10"
              onMouseMove={(e) => {
                const rect = chartRef.current?.getBoundingClientRect();
                if (rect) setMousePos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
              }}
            >
              {/* Plot Background details & divisers */}
              <div className="absolute inset-0 pointer-events-none opacity-20">
                {/* Horizontal Divider Label */}
                <div
                  className="absolute left-6 right-6 border-t border-dashed border-white"
                  style={{ top: `${chartData.avgPctY}%` }}
                />
                {/* Vertical Divider Label */}
                <div
                  className="absolute top-6 bottom-6 border-l border-dashed border-white"
                  style={{ left: `${chartData.avgPctX}%` }}
                />
              </div>

              {/* Quadrant Labels in Corners */}
              <div className="absolute top-4 right-4 text-right pointer-events-none">
                <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 uppercase tracking-wide">
                  Q1: Elite Contenders
                </span>
                <div className="text-[8px] text-white/30 mt-0.5">High {xLabel} · High {yLabel}</div>
              </div>

              <div className="absolute top-4 left-4 pointer-events-none">
                <span className="text-[10px] font-bold text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20 uppercase tracking-wide">
                  Q2: High {yLabel}
                </span>
                <div className="text-[8px] text-white/30 mt-0.5">Low {xLabel} · High {yLabel}</div>
              </div>

              <div className="absolute bottom-4 left-4 pointer-events-none">
                <span className="text-[10px] font-bold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20 uppercase tracking-wide">
                  Q3: Rebuilding / Low Performance
                </span>
                <div className="text-[8px] text-white/30 mt-0.5">Low {xLabel} · Low {yLabel}</div>
              </div>

              <div className="absolute bottom-4 right-4 text-right pointer-events-none">
                <span className="text-[10px] font-bold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20 uppercase tracking-wide">
                  Q4: High {xLabel}
                </span>
                <div className="text-[8px] text-white/30 mt-0.5">High {xLabel} · Low {yLabel}</div>
              </div>

              {/* Plot container */}
              <div className="w-full h-full relative mt-6 mb-6 ml-6 mr-6">
                {/* Horizontal axis label */}
                <div className="absolute bottom-0 left-0 right-0 text-center pointer-events-none pb-1">
                  <span className="text-[9px] uppercase tracking-widest text-white/40 font-bold bg-[#0c0c12]/80 px-3 py-1 rounded border border-white/5">
                    {xLabel} → (Average: {xAxis.includes('epa') ? formatEPA(chartData.avgX) : chartData.avgX.toFixed(2)})
                  </span>
                </div>

                {/* Vertical axis label */}
                <div className="absolute left-0 top-0 bottom-0 flex items-center pointer-events-none pl-1">
                  <span className="text-[9px] uppercase tracking-widest text-white/40 font-bold bg-[#0c0c12]/80 px-3 py-1 rounded border border-white/5 rotate-270 origin-left -translate-x-3">
                    {yLabel} ↑ (Average: {yAxis.includes('epa') ? formatEPA(chartData.avgY) : chartData.avgY.toFixed(2)})
                  </span>
                </div>

                {/* Draw scatter points */}
                {chartData.points.map(pt => {
                  const teamColor = TEAM_COLORS[pt.team.abbreviation]?.primary || '#10b981';
                  const isHovered = hoveredTeam?.id === pt.team.id;

                  return (
                    <Link key={pt.team.id} href={`/team/${pt.team.id}`}>
                      <div
                        className="absolute group z-20 cursor-pointer transition-all duration-300"
                        style={{
                          left: `${pt.pctX}%`,
                          top: `${pt.pctY}%`,
                          transform: 'translate(-50%, -50%)',
                        }}
                        onMouseEnter={() => setHoveredTeam(pt.team)}
                        onMouseLeave={() => setHoveredTeam(null)}
                      >
                        {/* Glow ring */}
                        <div
                          className="absolute w-8 h-8 rounded-full border border-white/10 group-hover:scale-125 transition-transform duration-300 flex items-center justify-center"
                          style={{
                            backgroundColor: isHovered ? `${teamColor}15` : 'transparent',
                            borderColor: isHovered ? teamColor : 'rgba(255,255,255,0.08)',
                            boxShadow: isHovered ? `0 0 12px ${teamColor}` : 'none',
                          }}
                        >
                          {/* Inner Dot */}
                          <div
                            className="w-2.5 h-2.5 rounded-full transition-transform duration-300 group-hover:scale-75"
                            style={{ backgroundColor: teamColor }}
                          />
                        </div>

                        {/* Visual abbreviation text label next to point */}
                        <span
                          className={`absolute left-9 top-1 text-[9px] font-bold px-1.5 py-0.5 rounded shadow-lg backdrop-blur-md transition-all duration-300 border ${
                            isHovered
                              ? 'text-white border-white/20 bg-white/10 scale-110 font-black'
                              : 'text-white/60 border-white/5 bg-white/5'
                          }`}
                        >
                          {pt.team.abbreviation}
                        </span>
                      </div>
                    </Link>
                  );
                })}
              </div>

              {/* Hover Tooltip */}
              {hoveredTeam && (
                <div
                  className="tooltip pointer-events-none transition-all duration-150"
                  style={{
                    left: mousePos.x + 16,
                    top: mousePos.y - 12,
                    opacity: 1,
                  }}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className="grade-badge text-xs"
                      style={{
                        background: formatGrade(hoveredTeam.composite_grade).bg,
                        color: formatGrade(hoveredTeam.composite_grade).color,
                      }}
                    >
                      {hoveredTeam.composite_grade}
                    </div>
                    <div>
                      <div className="font-semibold text-white">{hoveredTeam.name}</div>
                      <div className="text-[10px] text-white/40">
                        {hoveredTeam.wins}-{hoveredTeam.losses} · {hoveredTeam.division}
                      </div>
                    </div>
                  </div>
                  
                  <div className="mt-3 pt-2.5 border-t border-white/5 grid grid-cols-2 gap-x-4 gap-y-1.5 text-[10px]">
                    <div className="flex justify-between">
                      <span className="text-white/30">Overall Rating:</span>
                      <span className="font-mono text-white font-semibold">{hoveredTeam.composite_score}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-white/30">Play-Calling:</span>
                      <span className="font-mono text-white font-semibold">{hoveredTeam.grades.play_calling}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-white/30">4th Down:</span>
                      <span className="font-mono text-white font-semibold">{hoveredTeam.grades.fourth_down}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-white/30">Roster Cap:</span>
                      <span className="font-mono text-white font-semibold">{hoveredTeam.grades.roster_cap}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-white/30">Def. Execution:</span>
                      <span className="font-mono text-white font-semibold">{hoveredTeam.grades.defense}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-white/30">Game Mgmt:</span>
                      <span className="font-mono text-white font-semibold">{hoveredTeam.grades.game_management}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Sidebar Quadrant breakdown lists */}
          <div className="flex flex-col gap-4">
            <h3 className="text-xs font-semibold text-white/40 uppercase tracking-widest px-1">Quadrant Standings</h3>
            
            <div className="flex flex-col gap-3 max-h-[490px] overflow-y-auto pr-1 select-none">
              {/* Quadrant 1 */}
              <div className="bg-emerald-950/10 border border-emerald-500/10 rounded-2xl p-4 flex flex-col gap-2">
                <div className="flex justify-between items-center">
                  <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider">Q1: Elite Contenders ({groupedQuadrants[1]?.length || 0})</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                </div>
                <div className="flex flex-wrap gap-1.5 mt-1">
                  {groupedQuadrants[1]?.map(pt => (
                    <Link key={pt.team.id} href={`/team/${pt.team.id}`}>
                      <span className="text-[10px] font-bold px-2 py-1 rounded bg-white/3 border border-white/5 text-white hover:text-emerald-400 hover:border-emerald-500/30 transition-all cursor-pointer">
                        {pt.team.abbreviation}
                      </span>
                    </Link>
                  ))}
                  {groupedQuadrants[1]?.length === 0 && <span className="text-[10px] text-white/20">Empty</span>}
                </div>
              </div>

              {/* Quadrant 2 */}
              <div className="bg-cyan-950/10 border border-cyan-500/10 rounded-2xl p-4 flex flex-col gap-2">
                <div className="flex justify-between items-center">
                  <span className="text-[10px] font-bold text-cyan-400 uppercase tracking-wider">Q2: High Defense/Efficiency ({groupedQuadrants[2]?.length || 0})</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                </div>
                <div className="flex flex-wrap gap-1.5 mt-1">
                  {groupedQuadrants[2]?.map(pt => (
                    <Link key={pt.team.id} href={`/team/${pt.team.id}`}>
                      <span className="text-[10px] font-bold px-2 py-1 rounded bg-white/3 border border-white/5 text-white hover:text-cyan-400 hover:border-cyan-500/30 transition-all cursor-pointer">
                        {pt.team.abbreviation}
                      </span>
                    </Link>
                  ))}
                  {groupedQuadrants[2]?.length === 0 && <span className="text-[10px] text-white/20">Empty</span>}
                </div>
              </div>

              {/* Quadrant 4 */}
              <div className="bg-amber-950/10 border border-amber-500/10 rounded-2xl p-4 flex flex-col gap-2">
                <div className="flex justify-between items-center">
                  <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider">Q4: High Offense/Output ({groupedQuadrants[4]?.length || 0})</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                </div>
                <div className="flex flex-wrap gap-1.5 mt-1">
                  {groupedQuadrants[4]?.map(pt => (
                    <Link key={pt.team.id} href={`/team/${pt.team.id}`}>
                      <span className="text-[10px] font-bold px-2 py-1 rounded bg-white/3 border border-white/5 text-white hover:text-amber-400 hover:border-amber-500/30 transition-all cursor-pointer">
                        {pt.team.abbreviation}
                      </span>
                    </Link>
                  ))}
                  {groupedQuadrants[4]?.length === 0 && <span className="text-[10px] text-white/20">Empty</span>}
                </div>
              </div>

              {/* Quadrant 3 */}
              <div className="bg-rose-950/10 border border-rose-500/10 rounded-2xl p-4 flex flex-col gap-2">
                <div className="flex justify-between items-center">
                  <span className="text-[10px] font-bold text-rose-400 uppercase tracking-wider">Q3: Rebuilding Tier ({groupedQuadrants[3]?.length || 0})</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
                </div>
                <div className="flex flex-wrap gap-1.5 mt-1">
                  {groupedQuadrants[3]?.map(pt => (
                    <Link key={pt.team.id} href={`/team/${pt.team.id}`}>
                      <span className="text-[10px] font-bold px-2 py-1 rounded bg-white/3 border border-white/5 text-white hover:text-rose-400 hover:border-rose-500/30 transition-all cursor-pointer">
                        {pt.team.abbreviation}
                      </span>
                    </Link>
                  ))}
                  {groupedQuadrants[3]?.length === 0 && <span className="text-[10px] text-white/20">Empty</span>}
                </div>
              </div>
            </div>
          </div>

        </div>
      </section>

      {/* Quick Rankings */}
      <section className="px-6 py-12 max-w-[1400px] mx-auto">
        <h2 className="text-lg font-semibold mb-6 text-white/80 animate-fade-in-up">League Power Rankings</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 animate-fade-in-up">
          {teams.slice(0, 32).map((team, idx) => {
            const gradeInfo = formatGrade(team.composite_grade);
            return (
              <Link key={team.id} href={`/team/${team.id}`}>
                <div className="glass-card p-4 flex items-center gap-3 group cursor-pointer transition-all hover:border-white/10">
                  <span className="text-xs font-mono text-white/20 w-5">{idx + 1}</span>
                  <div
                    className="grade-badge text-xs"
                    style={{ background: gradeInfo.bg, color: gradeInfo.color }}
                  >
                    {team.composite_grade}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium truncate group-hover:text-white transition-colors">
                      {team.name}
                    </div>
                    <div className="text-[10px] text-white/30">
                      {team.wins}-{team.losses} · Score: {team.composite_score}
                    </div>
                  </div>
                  <div className="text-right text-[10px] text-white/20">
                    <div>OFF: {formatEPA(team.offensive_epa)}</div>
                    <div>DEF: {formatEPA(team.defensive_epa)}</div>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      </section>
    </div>
  );
}
