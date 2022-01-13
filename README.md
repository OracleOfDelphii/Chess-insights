# Welcome to Chess-insights!
You can use this python application to analyze any chess.com account, thanks to the chess.com public API.
Currently i have written a nice little CLI for the app, GUI will come later when it has more features.

# How to install
 

 1. create a virtual env by command `python -m venv venv`(optional).
 2. activate the environment.
windows:  `.\venv\Scripts\activate`   	
    Linux: `./venv/bin/activate`
 1. install required modules via pip: `pip install -r requirements.txt`
 2. `python insights.py`

 

## Features
Monthly analysis of games and profiles.
advanced filters for games(e.g. variant, least amount of moves, time control, color, etc.)
Visualization with Matplotlib

## Packages used:
chess.com Python wrapper: [link](https://github.com/sarartur/chess.com)