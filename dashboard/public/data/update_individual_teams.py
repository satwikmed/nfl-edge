import json
import os

# Load recurved teams summary
with open('teams_summary.json', 'r') as f:
    teams_summary = json.load(f)

# Loop over each team and update its corresponding individual file
for team_sum in teams_summary:
    filename = f"team_{team_sum['id'].lower()}.json"
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            team_detail = json.load(f)
        
        # Synchronize recurved grades and scores
        team_detail['composite_grade'] = team_sum['composite_grade']
        team_detail['composite_score'] = team_sum['composite_score']
        team_detail['grades'] = team_sum['grades']
        team_detail['scores'] = team_sum['scores']
        
        # Save back to individual file
        with open(filename, 'w') as f:
            json.dump(team_detail, f, indent=2)
            
        print(f"Successfully synchronized {filename} with recurved values!")
    else:
        print(f"Warning: File {filename} not found.")

print("All individual team detail JSON files are successfully synchronized!")
