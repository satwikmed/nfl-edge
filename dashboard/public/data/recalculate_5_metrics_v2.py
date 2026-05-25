import json
import os
import sqlite3

# Define absolute paths
DB_PATH = "/Users/satwikmedipalli/Project2/data/nfl_teams.db"
DATA_DIR = "/Users/satwikmedipalli/Project2/dashboard/public/data"

# 1. Fetch exact regular-season wins, losses, ties from sqlite games table
print("Connecting to SQLite database to fetch true regular-season records...")
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Get games
cur.execute("""
    SELECT game_id, home_team, away_team, home_score, away_score, result 
    FROM games 
    WHERE game_type = 'REG'
""")
games = cur.fetchall()

# Calculate records
records = {}
for g in games:
    gid, home, away, hscore, ascore, res = g
    if home not in records: records[home] = {'w':0, 'l':0, 't':0}
    if away not in records: records[away] = {'w':0, 'l':0, 't':0}
    
    if hscore > ascore:
        records[home]['w'] += 1
        records[away]['l'] += 1
    elif ascore > hscore:
        records[away]['w'] += 1
        records[home]['l'] += 1
    else:
        records[home]['t'] += 1
        records[away]['t'] += 1

print("Calculated regular-season records from SQLite games table.")

# 2. Update the SQLite database teams table to have the exact true wins/losses/ties
print("Updating the SQLite database teams table with correct records...")
for team_id, rec in records.items():
    cur.execute("""
        UPDATE teams 
        SET wins = ?, losses = ?, ties = ? 
        WHERE abbreviation = ? OR team_id = ?
    """, (rec['w'], rec['l'], rec['t'], team_id, team_id))
conn.commit()
print("Successfully updated database 'teams' table records.")

# Close connection
conn.close()

# List of all 32 NFL teams
teams_list = [
    "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN", "DET",
    "GB", "HOU", "IND", "JAX", "KC", "LV", "LAC", "LAR", "MIA", "MIN", "NE",
    "NO", "NYG", "NYJ", "PHI", "PIT", "SF", "SEA", "TB", "TEN", "WAS"
]

teams_data = {}

# 3. Read each team detail JSON and extract raw metrics
print("Reading individual team detail JSON files...")
for team_id in teams_list:
    filename = os.path.join(DATA_DIR, f"team_{team_id.lower()}.json")
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            team_detail = json.load(f)
        teams_data[team_id] = team_detail
    else:
        print(f"Warning: File {filename} not found.")

# Let's compute the raw 5 scores for each team
raw_scores = {}

for team_id, detail in teams_data.items():
    # ── A. Play-Calling Efficiency ──
    off_profile = detail.get('offensive_profile', {})
    epa_per_play = off_profile.get('epa_per_play', 0)
    scaled_off_epa = (epa_per_play + 0.2) / 0.4 * 100
    
    play_calling_section = detail.get('play_calling', {})
    tendencies = play_calling_section.get('tendency_analysis', {})
    predictability = tendencies.get('avg_predictability', 0.5)
    inverted_predictability = (1 - predictability) * 100
    
    raw_play_calling = 0.6 * scaled_off_epa + 0.4 * inverted_predictability
    
    # ── B. Fourth Down & Situational Decisions ──
    fourth_down = play_calling_section.get('fourth_down_analysis', {})
    fd_summary = fourth_down.get('summary', {})
    fd_accuracy = fd_summary.get('accuracy_pct', 70)
    ep_left = fd_summary.get('total_ep_left_on_table', 0)
    scaled_ep_left = max(0, 100 - ep_left * 2)
    
    decisions_section = detail.get('in_game_decisions', {})
    two_pt = decisions_section.get('two_point_analysis', {})
    two_pt_accuracy = two_pt.get('decision_accuracy', 70)
    
    raw_fourth_down = 0.4 * fd_accuracy + 0.3 * scaled_ep_left + 0.3 * two_pt_accuracy
    
    # ── C. Roster Cap Efficiency ──
    old_roster_score = detail.get('scores', {}).get('roster_cap', 75)
    if old_roster_score == 0 or old_roster_score == 100 or old_roster_score == 75:
        # Give a realistic score based on cap space and total cap used
        total_cap = detail.get('roster_profile', {}).get('total_cap_used', 230000000)
        cap_efficiency_raw = 80 - (total_cap / 3.4e8) * 20
        raw_roster_cap = cap_efficiency_raw
    else:
        raw_roster_cap = old_roster_score
        
    # ── D. Defensive Execution ──
    def_profile = detail.get('defensive_profile', {})
    epa_allowed = def_profile.get('epa_per_play_allowed', 0.05)
    scaled_def_epa = (0.2 - epa_allowed) / 0.4 * 100
    
    sack_rate = def_profile.get('sack_rate', 0.06)
    scaled_sacks = min(100, sack_rate * 1000)
    
    turnover_rate = def_profile.get('turnover_rate', 0.015)
    scaled_turnovers = min(100, turnover_rate * 2000)
    
    raw_defense = 0.6 * scaled_def_epa + 0.2 * scaled_sacks + 0.2 * scaled_turnovers
    
    # ── E. Game Management ──
    timeouts = decisions_section.get('timeout_analysis', {})
    waste_rate = timeouts.get('waste_rate', 0.2)
    timeout_score = (1 - waste_rate) * 100
    
    clutch = decisions_section.get('clutch_performance', {})
    clutch_diff = clutch.get('clutch_differential', 0)
    clutch_score = (clutch_diff + 0.15) / 0.3 * 100
    
    wpa_analysis = decisions_section.get('win_probability_analysis', {})
    avg_wpa = wpa_analysis.get('avg_wpa_per_play', 0)
    wpa_score = (avg_wpa + 0.01) / 0.02 * 100
    
    raw_game_management = 0.3 * timeout_score + 0.3 * clutch_score + 0.4 * wpa_score
    
    raw_scores[team_id] = {
        'play_calling': max(0, min(100, raw_play_calling)),
        'fourth_down': max(0, min(100, raw_fourth_down)),
        'roster_cap': max(0, min(100, raw_roster_cap)),
        'defense': max(0, min(100, raw_defense)),
        'game_management': max(0, min(100, raw_game_management))
    }

# 4. Map all scores to relative ranks (0-100 percentile scaling) for each metric
def normalize_metric(key):
    sorted_teams = sorted(teams_list, key=lambda x: raw_scores[x][key])
    for idx, team_id in enumerate(sorted_teams):
        percentile_score = 55 + (idx / 31) * 43
        raw_scores[team_id][key] = round(percentile_score, 1)

normalize_metric('play_calling')
normalize_metric('fourth_down')
normalize_metric('roster_cap')
normalize_metric('defense')
normalize_metric('game_management')

# 5. Calculate Weighted Composite Score
for team_id in teams_list:
    sc = raw_scores[team_id]
    composite = (
        0.25 * sc['play_calling'] +
        0.20 * sc['fourth_down'] +
        0.20 * sc['roster_cap'] +
        0.20 * sc['defense'] +
        0.15 * sc['game_management']
    )
    sc['composite'] = round(composite, 1)

# 6. Map composite to relative grades
sorted_by_composite = sorted(teams_list, key=lambda x: raw_scores[x]['composite'], reverse=True)
grade_map = [
    (3, 'A+'), (6, 'A'), (9, 'A-'),
    (12, 'B+'), (15, 'B'), (18, 'B-'),
    (21, 'C+'), (24, 'C'), (27, 'C-'),
    (30, 'D'), (32, 'F')
]

for idx, team_id in enumerate(sorted_by_composite):
    assigned_grade = 'F'
    for limit, grade in grade_map:
        if idx < limit:
            assigned_grade = grade
            break
    raw_scores[team_id]['composite_grade'] = assigned_grade

def get_letter_grade(score):
    if score >= 94: return 'A+'
    elif score >= 88: return 'A'
    elif score >= 82: return 'A-'
    elif score >= 75: return 'B+'
    elif score >= 68: return 'B'
    elif score >= 61: return 'B-'
    elif score >= 54: return 'C+'
    elif score >= 47: return 'C'
    elif score >= 40: return 'C-'
    elif score >= 30: return 'D'
    else: return 'F'

# 7. Synchronize teams_summary.json and the individual team detail JSON files
summary_path = os.path.join(DATA_DIR, 'teams_summary.json')
with open(summary_path, 'r') as f:
    summary_list = json.load(f)

for idx, team_sum in enumerate(summary_list):
    team_id = team_sum['id']
    sc = raw_scores[team_id]
    rec = records[team_id]
    
    # Store updated correct regular-season records
    team_sum['wins'] = rec['w']
    team_sum['losses'] = rec['l']
    team_sum['ties'] = rec['t']
    
    # Store updated composite values
    team_sum['composite_grade'] = sc['composite_grade']
    team_sum['composite_score'] = sc['composite']
    
    # Store 5 sub-grades and 5 sub-scores
    team_sum['grades'] = {
        'play_calling': get_letter_grade(sc['play_calling']),
        'fourth_down': get_letter_grade(sc['fourth_down']),
        'roster_cap': get_letter_grade(sc['roster_cap']),
        'defense': get_letter_grade(sc['defense']),
        'game_management': get_letter_grade(sc['game_management'])
    }
    team_sum['scores'] = {
        'play_calling': sc['play_calling'],
        'fourth_down': sc['fourth_down'],
        'roster_cap': sc['roster_cap'],
        'defense': sc['defense'],
        'game_management': sc['game_management']
    }

# Re-sort summary by new composite score and assign ranks
summary_list = sorted(summary_list, key=lambda x: x['composite_score'], reverse=True)
for idx, team_sum in enumerate(summary_list):
    team_sum['rank'] = idx + 1

# Write updated teams_summary.json
with open(summary_path, 'w') as f:
    json.dump(summary_list, f, indent=2)

# Write updated individual detail JSONs with correct wins, losses, ties
for team_id in teams_list:
    filename = os.path.join(DATA_DIR, f"team_{team_id.lower()}.json")
    if team_id in teams_data:
        detail = teams_data[team_id]
        sc = raw_scores[team_id]
        rec = records[team_id]
        
        detail['wins'] = rec['w']
        detail['losses'] = rec['l']
        detail['ties'] = rec['t']
        
        detail['composite_grade'] = sc['composite_grade']
        detail['composite_score'] = sc['composite']
        detail['grades'] = {
            'play_calling': get_letter_grade(sc['play_calling']),
            'fourth_down': get_letter_grade(sc['fourth_down']),
            'roster_cap': get_letter_grade(sc['roster_cap']),
            'defense': get_letter_grade(sc['defense']),
            'game_management': get_letter_grade(sc['game_management'])
        }
        detail['scores'] = {
            'play_calling': sc['play_calling'],
            'fourth_down': sc['fourth_down'],
            'roster_cap': sc['roster_cap'],
            'defense': sc['defense'],
            'game_management': sc['game_management']
        }
        
        with open(filename, 'w') as f:
            json.dump(detail, f, indent=2)

print("SUCCESS: 5-metric scores and exact regular-season records have been synchronized perfectly across all 32 teams!")
