
# Welcome to Chess-insights!

### You can use this python application to analyze any chess.com account, thanks to the chess.com public API.

Currently i have written a nice little CLI for the app, and GUI will come later when it has more features.

# How to install

  

 1. create a virtual env by command `python -m venv venv`(**optional**).

 2. activate the environment.

	**windows**: `.\venv\Scripts\activate`

	**Linux**: `./venv/bin/activate`

 3. install required modules via pip: `pip install -r requirements.txt`
 4. If there is no GUI backend installed(**matplotlib requires a GUI
    backend to render diagrams**):   you can install and use any GUI
    backend you want, i recommend **Pyqt5**. 
    `pip install pyqt5`
 5. Run the program with `python insights.py`

  

  

## Features

 - [x] Monthly analysis of games and profiles.
 - [x] advanced filters for games(e.g. variant, least amount of moves,
       time control, color, etc.)
 - [x] Visualization with Matplotlib

  

## Packages used:

chess.com Python wrapper: [link](https://github.com/sarartur/chess.com)


## Screenshots:

<p align="center">
<img   src="/screenshots/1.jpg?raw=true" width="400"  />
<img    src="/screenshots/2.jpg?raw=true" width="400"  />
<img   src="/screenshots/3.jpg?raw=true" width="400" />
<img     src="/screenshots/4.jpg?raw=true" width="400"   />
</p>