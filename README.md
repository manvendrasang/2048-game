# 2048 — Enhanced Edition v2.0
## Features

Feature             Details 
Game Modes          Classic (infinite), Target (race to 2048, time logged), Time Attack (score race vs clock) 
Leaderboard         Top 5 scores saved locally with mode, time, date 
Stats Screen        Games played, highest tile ever, total/avg score, total/avg moves 
Particle Bursts     Different burst for 256 / 512 / 1024 / 2048+ merges 
Screen Shake        On game over 
Sound Effects       Procedurally generated — move, merge, undo, win, lose, click 
Dark / Light Theme  Toggle with 'T' 
Pause Screen        'P' to pause/resume 
Undo                Up to 10 undos per game 
Save / Load         'S' to save, 'L' to load (also from main menu) 
Board Sizes         Keys '3'–'6' switch board size mid-game 

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