# 2048 — Enhanced Edition

Controls (In-Game)
Key      Action 
← ↑ ↓ →  Move tiles 
U        Undo last move 
R        Restart 
S        Save game 
P        Pause / Resume 
T        Toggle Dark/Light theme 
M        Toggle Sound on/off 
3–6      Change board size 
ESC      Return to main menu 

How to Run
execute main.py

Data Files (auto-created in 'data/')
- leaderboard.json = top 5 scores
- stats.json       = lifetime stats
- savedata.json    =last saved game
- best.txt         =all-time best score


>Score counter should animate upward (rolling digits) rather than jumping instantly
>Hint system — show the single best next move as a subtle arrow or tile highlight, togglable from options. This keeps casual players engaged
>Undo limit tokens (e.g. 3 per game shown as icons in the HUD) — much better UX than unlimited undo which trivializes the game
>Time Attack could use a visual timer bar across the top of the board (shrinking red bar) in addition to the number
>Challenge mode needs a "preview" before starting — show the starting board and goal without committing
>Level/rank system based on total score across all games — Beginner → Apprentice → Expert → Master → Grandmaster. Shows in profile with a progress bar to next rank. This gives players a long-term goal beyond individual games
>Volume levels, theme preference, and sound/music on/off are not saved to disk — closing and reopening the game resets them. This needs a data/settings.json file
>High contrast mode for the board