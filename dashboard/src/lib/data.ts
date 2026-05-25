import { TeamSummary, TeamData } from './types';

const BASE_URL = process.env.NODE_ENV === 'development' ? '' : '';

export async function getTeamsSummary(): Promise<TeamSummary[]> {
  // Use dynamic import for static JSON in Next.js
  const data = await import('../../public/data/teams_summary.json');
  return data.default as TeamSummary[];
}

export async function getTeamData(teamId: string): Promise<TeamData | null> {
  try {
    const data = await import(`../../public/data/team_${teamId.toLowerCase()}.json`);
    return data.default as TeamData;
  } catch {
    return null;
  }
}

export function formatGrade(grade: string): { text: string; color: string; bg: string } {
  const gradeMap: Record<string, { color: string; bg: string }> = {
    'A+': { color: '#10b981', bg: 'rgba(16,185,129,0.15)' },
    'A':  { color: '#10b981', bg: 'rgba(16,185,129,0.15)' },
    'A-': { color: '#34d399', bg: 'rgba(52,211,153,0.15)' },
    'B+': { color: '#60a5fa', bg: 'rgba(96,165,250,0.15)' },
    'B':  { color: '#60a5fa', bg: 'rgba(96,165,250,0.15)' },
    'B-': { color: '#93c5fd', bg: 'rgba(147,197,253,0.15)' },
    'C+': { color: '#fbbf24', bg: 'rgba(251,191,36,0.15)' },
    'C':  { color: '#fbbf24', bg: 'rgba(251,191,36,0.15)' },
    'C-': { color: '#fcd34d', bg: 'rgba(252,211,77,0.15)' },
    'D+': { color: '#f97316', bg: 'rgba(249,115,22,0.15)' },
    'D':  { color: '#f97316', bg: 'rgba(249,115,22,0.15)' },
    'D-': { color: '#fb923c', bg: 'rgba(251,146,60,0.15)' },
    'F':  { color: '#ef4444', bg: 'rgba(239,68,68,0.15)' },
  };

  const info = gradeMap[grade] || gradeMap['F'];
  return { text: grade, ...info };
}

export function formatCurrency(value: number): string {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`;
  return `$${value}`;
}

export function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function formatEPA(value: number): string {
  const prefix = value >= 0 ? '+' : '';
  return `${prefix}${value.toFixed(3)}`;
}

export function getGradeColor(grade: string): string {
  return formatGrade(grade).color;
}

export function getScoreColor(score: number): string {
  if (score >= 90) return '#10b981';
  if (score >= 80) return '#60a5fa';
  if (score >= 70) return '#fbbf24';
  if (score >= 60) return '#f97316';
  return '#ef4444';
}
