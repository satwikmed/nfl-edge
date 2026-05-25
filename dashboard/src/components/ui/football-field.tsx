"use client";

import { useState } from "react";
import { formatPercent, formatEPA } from "@/lib/data";

interface FieldZoneData {
  zone: string;
  plays: number;
  epa_per_play: number;
  pass_rate: number;
  success_rate: number;
}

interface FootballFieldProps {
  efficiencyData: FieldZoneData[];
  recommendations: string[];
}

export default function FootballField({ efficiencyData, recommendations }: FootballFieldProps) {
  const [selectedZone, setSelectedZone] = useState<string | null>(null);

  // Map zone data for easy lookup
  const zonesMap = efficiencyData.reduce((acc, curr) => {
    acc[curr.zone] = curr;
    return acc;
  }, {} as Record<string, FieldZoneData>);

  const fieldZones = [
    {
      id: "red_zone",
      label: "Opponent Red Zone",
      desc: "Deep inside opponent 20-yard line. Crucial scoring area.",
      x: "80%",
      y: "15%",
      w: "20%",
      h: "70%",
    },
    {
      id: "opp_40_20",
      label: "Opponent 40-20 Yard Zone",
      desc: "Inside opponent territory. Scoring drives are finalized or stall here.",
      x: "60%",
      y: "15%",
      w: "20%",
      h: "70%",
    },
    {
      id: "midfield",
      label: "Midfield Area",
      desc: "Between the 40s. Heavy passing and strategic play-calling zone.",
      x: "40%",
      y: "15%",
      w: "20%",
      h: "70%",
    },
    {
      id: "own_20_40",
      label: "Own 20-40 Yard Zone",
      desc: "Base offensive setup zone. Running game and short passes define this area.",
      x: "20%",
      y: "15%",
      w: "20%",
      h: "70%",
    },
  ];

  function getZoneStatus(epa: number) {
    if (epa > 0.08) return { label: "Elite Efficiency", color: "text-emerald-400", border: "border-emerald-500/40", bg: "bg-emerald-500/10" };
    if (epa >= 0.0) return { label: "Positive/Average", color: "text-cyan-400", border: "border-cyan-500/40", bg: "bg-cyan-500/10" };
    return { label: "Weak Point", color: "text-rose-400", border: "border-rose-500/40", bg: "bg-rose-500/10" };
  }

  // Find overall weak spots
  const weakZones = efficiencyData.filter((d) => d.epa_per_play < 0);
  const strongZones = efficiencyData.filter((d) => d.epa_per_play >= 0.05);

  const activeZoneInfo = selectedZone ? zonesMap[selectedZone] : null;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fade-in-up">
      {/* 2D Interactive Field Map */}
      <div className="lg:col-span-2 glass-card p-6 flex flex-col gap-6 relative overflow-hidden">
        <div>
          <h2 className="text-base font-semibold text-emerald-400">On-Field Movement & Spatial Efficiency</h2>
          <p className="text-[11px] text-white/40 mt-1">
            Click on any zone of the football field to analyze player performance and play-calling efficiency.
          </p>
        </div>

        {/* Field Graphic Container */}
        <div className="relative w-full aspect-[2.1] bg-[#0c1a10] rounded-xl border border-white/5 p-4 flex items-center overflow-hidden">
          {/* Field Lines */}
          <div className="absolute inset-0 flex pointer-events-none opacity-20">
            {/* Yard lines */}
            {Array.from({ length: 11 }).map((_, i) => (
              <div
                key={i}
                className="absolute top-0 bottom-0 border-l border-white h-full"
                style={{ left: `${(i / 10) * 100}%` }}
              />
            ))}
            {/* End zones */}
            <div className="absolute top-0 bottom-0 left-0 w-[5%] bg-rose-500/10 border-r border-white/50" />
            <div className="absolute top-0 bottom-0 right-0 w-[5%] bg-emerald-500/10 border-l border-white/50" />
          </div>

          {/* Interactive Zone Overlays */}
          <div className="absolute inset-0 z-10">
            {fieldZones.map((z) => {
              const data = zonesMap[z.id];
              const epa = data?.epa_per_play ?? 0;
              const isSelected = selectedZone === z.id;
              
              // Colors based on EPA
              let fillStyle = "rgba(16, 185, 129, 0.03)";
              let strokeStyle = "rgba(255, 255, 255, 0.1)";
              if (epa > 0.08) {
                fillStyle = isSelected ? "rgba(16, 185, 129, 0.25)" : "rgba(16, 185, 129, 0.12)";
                strokeStyle = "rgba(16, 185, 129, 0.4)";
              } else if (epa >= 0.0) {
                fillStyle = isSelected ? "rgba(6, 182, 212, 0.25)" : "rgba(6, 182, 212, 0.12)";
                strokeStyle = "rgba(6, 182, 212, 0.4)";
              } else {
                fillStyle = isSelected ? "rgba(239, 68, 68, 0.25)" : "rgba(239, 68, 68, 0.12)";
                strokeStyle = "rgba(239, 68, 68, 0.4)";
              }

              return (
                <div
                  key={z.id}
                  onClick={() => setSelectedZone(z.id)}
                  className="absolute cursor-pointer transition-all duration-200 hover:scale-[1.01] hover:z-20 group"
                  style={{
                    left: z.x,
                    top: z.y,
                    width: z.w,
                    height: z.h,
                    backgroundColor: fillStyle,
                    border: `1px solid ${isSelected ? "rgba(255,255,255,0.6)" : strokeStyle}`,
                    borderRadius: "8px",
                  }}
                >
                  <div className="absolute inset-0 flex flex-col items-center justify-center p-2 text-center select-none">
                    <span className="text-[10px] uppercase font-bold tracking-wider text-white/70 group-hover:text-white transition-colors">
                      {z.id === "red_zone" ? "Red Zone" : z.id === "opp_40_20" ? "Opp 40-20" : z.id === "midfield" ? "Midfield" : "Own 20-40"}
                    </span>
                    <span className="text-xs font-mono font-bold mt-1 text-white">
                      {formatEPA(epa)}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Goal posts */}
          <div className="absolute left-[2.5%] top-1/2 -translate-y-1/2 w-1.5 h-10 bg-yellow-500 rounded-full opacity-40" />
          <div className="absolute right-[2.5%] top-1/2 -translate-y-1/2 w-1.5 h-10 bg-yellow-500 rounded-full opacity-40" />
        </div>

        {/* Selected Zone Detail Panel */}
        <div className="mt-4 bg-white/2 border border-white/5 rounded-xl p-5">
          {activeZoneInfo ? (
            <div>
              <div className="flex justify-between items-center border-b border-white/5 pb-2.5 mb-4">
                <div>
                  <h3 className="text-sm font-semibold text-white">
                    {fieldZones.find((z) => z.id === activeZoneInfo.zone)?.label}
                  </h3>
                  <p className="text-[10px] text-white/45 mt-0.5">
                    {fieldZones.find((z) => z.id === activeZoneInfo.zone)?.desc}
                  </p>
                </div>
                <span className={`px-2.5 py-0.5 rounded-full text-[9px] font-semibold tracking-wider uppercase border ${
                  getZoneStatus(activeZoneInfo.epa_per_play).border
                } ${getZoneStatus(activeZoneInfo.epa_per_play).color} ${getZoneStatus(activeZoneInfo.epa_per_play).bg}`}>
                  {getZoneStatus(activeZoneInfo.epa_per_play).label}
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="kpi-card text-center">
                  <div className="text-[9px] text-white/40 uppercase">Plays Run</div>
                  <div className="text-base font-bold mt-1 text-white">{activeZoneInfo.plays}</div>
                </div>
                <div className="kpi-card text-center">
                  <div className="text-[9px] text-white/40 uppercase">EPA / Play</div>
                  <div className={`text-base font-bold mt-1 ${activeZoneInfo.epa_per_play >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                    {formatEPA(activeZoneInfo.epa_per_play)}
                  </div>
                </div>
                <div className="kpi-card text-center">
                  <div className="text-[9px] text-white/40 uppercase">Pass Rate</div>
                  <div className="text-base font-bold mt-1 text-white">{formatPercent(activeZoneInfo.pass_rate)}</div>
                </div>
                <div className="kpi-card text-center">
                  <div className="text-[9px] text-white/40 uppercase">Success Rate</div>
                  <div className="text-base font-bold mt-1 text-white">{formatPercent(activeZoneInfo.success_rate)}</div>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center text-xs text-white/30 py-6">
              ← Click any zone on the field above to inspect play-by-play analytics.
            </div>
          )}
        </div>
      </div>

      {/* Field Weak & Strong Points Summary */}
      <div className="flex flex-col gap-6">
        {/* Spatial Weak Spots & Strengths */}
        <div className="glass-card p-6 flex flex-col gap-4">
          <h2 className="text-base font-semibold border-b border-white/5 pb-3 text-rose-400">On-Field Weak Spots</h2>
          <div className="space-y-3">
            {weakZones.map((w) => (
              <div key={w.zone} className="bg-rose-500/5 border border-rose-500/10 p-3.5 rounded-xl text-xs">
                <div className="font-bold text-rose-400">
                  {fieldZones.find((z) => z.id === w.zone)?.label || w.zone}
                </div>
                <div className="text-white/50 mt-1">
                  Produces a negative <span className="font-mono text-rose-300 font-bold">{formatEPA(w.epa_per_play)}</span> EPA per play. Opponents successfully cluster defensive coverages in this region.
                </div>
              </div>
            ))}
            {weakZones.length === 0 && (
              <div className="bg-emerald-500/5 border border-emerald-500/10 p-3.5 rounded-xl text-xs">
                <div className="font-bold text-emerald-400">No Major Weak Spots</div>
                <div className="text-white/50 mt-1">
                  No areas of the field return negative play efficiency metrics. Play-calling is well distributed.
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Actionable recommendations */}
        <div className="glass-card p-6 flex flex-col gap-4 flex-1">
          <h2 className="text-base font-semibold border-b border-white/5 pb-3 text-emerald-400">Spatial Strategy Upgrades</h2>
          <div className="space-y-3 overflow-y-auto max-h-[300px]">
            {recommendations.slice(0, 3).map((rec, i) => (
              <div key={i} className="rec-card text-xs">
                {rec}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
