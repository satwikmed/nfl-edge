export interface TeamSummary {
  id: string;
  name: string;
  abbreviation: string;
  city: string;
  state: string;
  conference: string;
  division: string;
  latitude: number;
  longitude: number;
  wins: number;
  losses: number;
  ties: number;
  composite_grade: string;
  composite_score: number;
  rank: number;
  grades: {
    play_calling: string;
    fourth_down: string;
    roster_cap: string;
    defense: string;
    game_management: string;
  };
  scores: {
    play_calling: number;
    fourth_down: number;
    roster_cap: number;
    defense: number;
    game_management: number;
  };
  offensive_epa: number;
  defensive_epa: number;
}

export interface TeamData extends TeamSummary {
  stadium: string;
  offensive_profile: OffensiveProfile;
  defensive_profile: DefensiveProfile;
  roster_profile: RosterProfile;
  play_calling: PlayCallingAnalysis;
  roster_value: RosterValueAnalysis;
  in_game_decisions: InGameDecisionAnalysis;
}

export interface OffensiveProfile {
  total_plays: number;
  pass_rate: number;
  run_rate: number;
  epa_per_play: number;
  pass_epa_per_play: number;
  run_epa_per_play: number;
  success_rate: number;
  explosive_rate: number;
  explosive_plays: number;
  shotgun_rate: number;
  no_huddle_rate: number;
  plays_per_game: number;
  avg_depth_of_target: number;
  deep_pass_rate: number;
  touchdowns: number;
  turnovers: number;
  down_tendencies: Record<string, { plays: number; pass_rate: number; run_rate: number; avg_epa: number }>;
  personnel: Record<string, { plays: number; usage_rate: number; epa_per_play: number; success_rate: number; pass_rate: number }>;
  formations: Record<string, { plays: number; usage_rate: number; epa_per_play: number }>;
  red_zone: { plays: number; pass_rate: number; epa_per_play: number; td_rate: number };
}

export interface DefensiveProfile {
  total_plays_faced: number;
  epa_per_play_allowed: number;
  pass_epa_allowed: number;
  run_epa_allowed: number;
  success_rate_allowed: number;
  sacks: number;
  sack_rate: number;
  interceptions: number;
  fumbles_forced: number;
  turnover_rate: number;
  explosive_allowed: number;
  explosive_rate_allowed: number;
  third_down_conversion_allowed: number;
  third_down_epa_allowed: number;
  avg_yards_per_play_allowed: number;
  touchdowns_allowed: number;
  down_defense: Record<string, { plays: number; epa_allowed: number; success_rate_allowed: number; avg_yards_allowed: number }>;
  red_zone_defense: { plays: number; td_rate_allowed: number; epa_per_play_allowed: number };
  first_half_epa_allowed?: number;
  second_half_epa_allowed?: number;
  halftime_adjustment?: number;
}

export interface RosterProfile {
  total_players: number;
  avg_age: number;
  median_age: number;
  avg_experience: number;
  age_distribution: { under_25: number; '25_to_29': number; '30_plus': number };
  experience_distribution: { years_1_3: number; years_4_7: number; years_8_plus: number };
  position_groups: Record<string, { count: number; avg_age: number | null; avg_experience: number | null }>;
  cap_allocation?: Record<string, { total_cap: number; pct_of_cap: number; players: number; avg_cap_hit: number; max_cap_hit: number }>;
  total_cap_used?: number;
  top_contracts?: Array<{ player_id: string; name: string; position: string; cap_hit: number; dead_cap: number; free_agent_year: number | null }>;
  upcoming_free_agents?: Array<{ name: string; position: string; age: number; cap_hit: number; free_agent_year: number }>;
}

export interface PlayCallingAnalysis {
  fourth_down_analysis: {
    decisions: Array<{
      game_id: string;
      week: number;
      quarter: number;
      yard_line: number;
      yards_to_go: number;
      score_diff: number;
      actual_decision: string;
      recommended_decision: string;
      correct: boolean;
      ep_actual: number;
      ep_optimal: number;
      ep_left_on_table: number;
      description: string;
    }>;
    summary: {
      total_fourth_downs: number;
      correct_decisions: number;
      incorrect_decisions: number;
      accuracy_pct: number;
      total_ep_left_on_table: number;
      went_for_it_count: number;
      punted_count: number;
      fg_count: number;
      should_have_gone_for_it: number;
    };
  };
  tendency_analysis: {
    tendency_matrix: Record<string, {
      down: number;
      distance: string;
      plays: number;
      pass_rate: number;
      run_rate: number;
      predictability: number;
      pass_epa: number;
      run_epa: number;
    }>;
    most_predictable: Array<{
      down: number;
      distance: string;
      predictability: number;
      pass_rate: number;
    }>;
    avg_predictability: number;
    quarter_tendencies: Record<string, { plays: number; pass_rate: number; epa_per_play: number }>;
    half_comparison: Record<string, { plays: number; pass_rate: number; epa_per_play: number }>;
  };
  efficiency_analysis: {
    personnel_efficiency: Array<{
      personnel: string;
      plays: number;
      usage_rate: number;
      epa_per_play: number;
      success_rate: number;
      pass_rate: number;
    }>;
    field_zone_efficiency: Array<{
      zone: string;
      plays: number;
      epa_per_play: number;
      pass_rate: number;
      success_rate: number;
    }>;
    recommendations: string[];
  };
  recommendations: string[];
}

export interface RosterValueAnalysis {
  value_analysis: {
    roster: Array<PlayerValue>;
    top_5_vor: Array<PlayerValue>;
    bottom_5_vor: Array<PlayerValue>;
    most_overpaid: Array<PlayerValue>;
    most_underpaid: Array<PlayerValue>;
    total_cap_used: number;
    cap_space: number;
  };
  recommendations: {
    re_sign_candidates: Array<RosterRecommendation>;
    cut_candidates: Array<RosterRecommendation>;
    trade_candidates: Array<RosterRecommendation>;
    draft_needs: Array<{ position_group: string; avg_vor: number; avg_age: number; reason: string; priority: string }>;
    cap_projection: {
      current_cap_used: number;
      current_cap_space: number;
      cut_savings: number;
      dead_cap_from_cuts: number;
    };
  };
}

export interface PlayerValue {
  player_id: string;
  name: string;
  position: string;
  position_group: string;
  age: number | null;
  games: number;
  total_epa: number;
  epa_per_play: number;
  vor: number;
  cap_hit: number;
  cap_pct: number;
  dead_cap: number;
  cap_efficiency: number;
  free_agent_year: number | null;
  passing_yards: number;
  rushing_yards: number;
  receiving_yards: number;
  total_tds: number;
}

export interface RosterRecommendation {
  name: string;
  position: string;
  age: number;
  vor: number;
  cap_hit: number;
  reason: string;
  dead_cap?: number;
  cap_savings?: number;
}

export interface InGameDecisionAnalysis {
  win_probability_analysis: {
    biggest_positive_plays: Array<WPPlay>;
    biggest_negative_plays: Array<WPPlay>;
    game_summaries: Array<{
      game_id: string;
      week: number;
      total_wpa: number;
      max_wp: number;
      min_wp: number;
      wp_volatility: number;
    }>;
    season_total_wpa: number;
    avg_wpa_per_play: number;
  };
  two_point_analysis: {
    attempts: Array<{
      game_id: string;
      week: number;
      quarter: number;
      result: string;
      successful: boolean;
      was_correct_decision: boolean;
      description: string;
    }>;
    total_attempts: number;
    successful_conversions: number;
    correct_decisions: number;
    incorrect_decisions: number;
    decision_accuracy: number;
    missed_opportunities: number;
    conversion_rate: number;
  };
  timeout_analysis: {
    total_timeouts: number;
    timeouts_by_quarter: Record<string, number>;
    wasted_timeouts: number;
    strategic_timeouts: number;
    waste_rate: number;
    grade: string;
  };
  clutch_performance: {
    clutch_plays: number;
    clutch_epa: number;
    clutch_success_rate: number;
    overall_epa: number;
    overall_success_rate: number;
    clutch_differential: number;
    performs_better_under_pressure: boolean;
    clutch_touchdowns: number;
    clutch_turnovers: number;
  };
  recommendations: string[];
  estimated_wins_impact: number;
}

export interface WPPlay {
  game_id: string;
  week: number;
  quarter: number;
  wpa: number;
  wp_after: number;
  description: string;
  play_type: string;
  yards: number;
}

// Team colors for visualization
export const TEAM_COLORS: Record<string, { primary: string; secondary: string }> = {
  ARI: { primary: '#97233F', secondary: '#000000' },
  ATL: { primary: '#A71930', secondary: '#000000' },
  BAL: { primary: '#241773', secondary: '#9E7C0C' },
  BUF: { primary: '#00338D', secondary: '#C60C30' },
  CAR: { primary: '#0085CA', secondary: '#101820' },
  CHI: { primary: '#0B162A', secondary: '#C83803' },
  CIN: { primary: '#FB4F14', secondary: '#000000' },
  CLE: { primary: '#311D00', secondary: '#FF3C00' },
  DAL: { primary: '#003594', secondary: '#869397' },
  DEN: { primary: '#FB4F14', secondary: '#002244' },
  DET: { primary: '#0076B6', secondary: '#B0B7BC' },
  GB:  { primary: '#203731', secondary: '#FFB612' },
  HOU: { primary: '#03202F', secondary: '#A71930' },
  IND: { primary: '#002C5F', secondary: '#A2AAAD' },
  JAX: { primary: '#006778', secondary: '#9F792C' },
  KC:  { primary: '#E31837', secondary: '#FFB81C' },
  LV:  { primary: '#1b1b22', secondary: '#A5ACAF' },
  LAC: { primary: '#0080C6', secondary: '#FFC20E' },
  LAR: { primary: '#003594', secondary: '#FFA300' },
  MIA: { primary: '#008E97', secondary: '#FC4C02' },
  MIN: { primary: '#4F2683', secondary: '#FFC62F' },
  NE:  { primary: '#002244', secondary: '#C60C30' },
  NO:  { primary: '#D3BC8D', secondary: '#101820' },
  NYG: { primary: '#0B2265', secondary: '#A71930' },
  NYJ: { primary: '#125740', secondary: '#000000' },
  PHI: { primary: '#004C54', secondary: '#A5ACAF' },
  PIT: { primary: '#FFB612', secondary: '#101820' },
  SF:  { primary: '#AA0000', secondary: '#B3995D' },
  SEA: { primary: '#002244', secondary: '#69BE28' },
  TB:  { primary: '#D50A0A', secondary: '#FF7900' },
  TEN: { primary: '#0C2340', secondary: '#4B92DB' },
  WAS: { primary: '#5A1414', secondary: '#FFB612' },
};
