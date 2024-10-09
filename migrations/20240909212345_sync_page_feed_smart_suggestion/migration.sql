-- Update the smart_suggestions array for the gbb_initial_team
UPDATE "InitialTeam"
SET smart_suggestions = array_append(smart_suggestions, 'Sync PMax page feed data')
WHERE name = 'gbb_initial_team';
