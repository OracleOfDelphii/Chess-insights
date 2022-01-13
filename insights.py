from chessdotcom import  get_player_profile, Client
from chessdotcom.aio import get_player_profile, Client
import pathlib
import requests
import pycountry
from datetime import datetime
import matplotlib.pyplot as plt 
import numpy as np
from progress.bar import Bar
import seaborn as sns
import pandas as pd
import pprint
import chess.pgn
import io
import re
from asyncio import gather
from math import ceil
import cardinality
from collections import Counter
from chessdotcom import get_player_game_archives 
import time
################################


# a method to get country name based on alpha_2 code of countries
# Chess.com has defined special codes for countries that are not
# in the ISO 3166-1 alpha_2 standard, those countires are listed in special_codes

def get_country_name(player):
    special_codes = {'XA': 'Canary Islands',
            'XB': 'Basque Country',
            'XC': 'Catalonia',
            'XE': 'England',
            'XG': 'Galicia',
            'XK': 'Kosovo', 
            'XP': 'Palestine',
            'XS': 'Scotland',
            'XW': 'Wales',
            'XX': 'International'
            }

    code = pathlib.PurePath(player.country).name

    if code in special_codes:
        return special_codes.get(code)

    return pycountry.countries.get(alpha_2=code).name

def filtered_games(games, **kwargs):
    filtered_games = []
    for game in games.get('games'):
        pgn = io.StringIO(game['pgn'])
        moves = ceil(cardinality.count(chess.pgn.read_game(pgn).mainline_moves()) / 2)

        if kwargs.get("type") == "standard":
            if game["rules"] != "chess":
                continue
        else:
            if game["rules"] == "chess":
                continue

        if kwargs.get("time_class") is not None:
            if kwargs.get("time_class") != game["time_class"]:
                continue
        
        if kwargs.get("minimum_moves") is not None:
            if moves < int(kwargs.get("minimum_moves")):
                continue


        filtered_games.append(game)
    return {"games":filtered_games}


def __prettified_opening(string):
    splitted = string.split("-")
    prettified = ""
    i = 0
    for token in splitted:
        i = i + len(token)
        if i >= 14:
            i = 0
            prettified = prettified + "\n" + token + "-"
        else:
            prettified = prettified + token + "-"

    
    prettified = prettified[:-1]
    return prettified


if __name__  == "__main__":

    print("input username below:")
    
    Client.aio = False
    player_username = input()
    archives = get_player_game_archives(player_username).archives
    first_year_link = archives[0]
    last_year_link = archives[-1]

    pattern = re.compile(r"https://api.chess.com/pub/player/.*/games/20(\d+)/(\d+)")

    first_year = pattern.search(first_year_link).group(1)
    last_year = pattern.search(last_year_link).group(1)


    print(f"select a year between {first_year} and {last_year}")

    year = int(input())
    first_year_first_month = pattern.search(first_year_link).group(2)

    first_year_last_month = 12
    if datetime.now().year % 100 == year:
        first_year_last_month = datetime.now().month


    months = ["Jan: 1", "Feb: 2", "Mar: 3",
    "Apr: 4", "May: 5", "Jun: 6",
    "Jul: 7", "Aug: 8", "Sep: 9",
    "Oct: 10", "Nov: 11", "Dec: 12"]

    last_year_last_month = pattern.search(last_year_link).group(2)

    print("select a month to analyze:")

    if int(year) == int(first_year):
        for i in range(int(first_year_first_month) - 1, first_year_last_month):
            print(months[i])
    else:
        mx = 12
        if int(year) == int(last_year):
            mx = int(last_year_last_month)
        for i in range(0, mx):
            print(months[i])

    input_month = int(input())
        

    print("input time class:", 
    "0: rapid, 1: blitz, 2: bullet")


    time_classes = ["rapid", "blitz", "bullet"]
    time_class = time_classes[int(input())]

    games_url = None

    for url in archives:
        if "20{:02d}/{:02d}".format(year, input_month) in url:
            games_url = url
            break

        
    if games_url:
        print(games_url)
    else:
        exit("archive not found")

    # a json array of all games played at input_month
    js_arr = requests.get(games_url).json()

    
    Client.aio = True
   
 
    countries = {}
    opponents = []

    # filter games based on different criteria
    # type: standard, variant(e.g crazyhouse, chess960, etc)
    # time_class: rapid, blitz, bullet
    # minimum_moves: minimum number of moves in a game
    # to-do: minimum_rating: minimum rating of a player

    js_arr = filtered_games(js_arr, type="standard", time_class=time_class, minimum_moves=10)

    for game in js_arr['games']:
        
        white_username = game['white']['username']
        black_username = game['black']['username']

        if white_username.lower() == player_username.lower():
            player = white_username
            opponent = black_username
        else:
            player = black_username
            opponent = white_username

        opponents = opponents + [opponent]


    responses = []
    # number of profiles to retrieve at each request
    profiles_per_request = 1
    players_count = len(opponents)
    bar = Bar('finding profiles', max=players_count)
    index = 0
 

    while index < players_count:
            cors = [get_player_profile(name) for name in opponents[index:min(index + profiles_per_request, players_count)]]
            try:
                responses += Client.loop.run_until_complete(gather(*cors))
                time.sleep(0.07)
                for i in range(min(profiles_per_request, players_count - index)):
                    bar.next()
                index += profiles_per_request
        
            except Exception as e:
                retry = e.headers.get('Retry-After')
                if retry is None:
                    retry = 3000
                time.sleep(int(retry) / 1000)

    bar.finish()

    for resp in responses:
        player = resp.player
        country = get_country_name(player)
        if not countries.get(country):
            countries[country] = 1
        else:
            countries[country] += 1

    month_games_total = len(js_arr['games'])

    y = np.array([x / month_games_total for x in countries.values()])
    mylabels = countries.keys()

    plt.pie(y, labels = mylabels)
    plt.show() 

    drawn_results = {'stalemate': 0, '50 moves': 0, 'repetition': 0, 'insufficient': 0, 'agreement': 0}
    won_results = {'resignation': 0, 'checkmate': 0, 'time': 0}
    lost_results = {'resignation': 0, 'checkmate': 0, 'time': 0}

    drawn_cnt = 0
    won_cnt = 0
    lost_cnt = 0

    white_win_opening = {}
    white_lose_opening = {}
    white_draw_opening = {}

    black_win_opening = {}
    black_lose_opening = {}
    black_draw_opening = {}

    bar = Bar('Processing games', max=len(js_arr))

    for game in js_arr['games']:
        if game.get('pgn') is None:
            continue
        white_username = game['white']['username']
        black_username = game['black']['username']
        bar.next()
        pgn = io.StringIO(game['pgn'])

        pp = pprint.PrettyPrinter(width=41, compact=True)
        game = chess.pgn.read_game(pgn)

        if game.headers.get('ECOUrl'):
        

            opening = re.search(r"https://www.chess.com/openings/(.*)", game.headers.get('ECOUrl')).group(1)

            termination = game.headers['Termination']

            # drawn

            if "drawn" in termination:
                drawn_cnt += 1
                if white_username.lower() == player_username.lower():
                    if white_draw_opening.get(opening) is None:              
                        white_draw_opening[opening] = 1
                    else:
                        white_draw_opening[opening] += 1
                else:
                    if black_draw_opening.get(opening) is None:
                        black_draw_opening[opening] = 1
                    else:
                        black_draw_opening[opening] += 1
                    

                if '50-move' in termination:
                    drawn_results['50 moves'] += 1
                elif 'insufficient' in termination:
                    drawn_results['insufficient'] += 1
                elif '3-fold' in termination:
                    drawn_results['3-fold'] += 1
                elif 'stalemate' in termination:
                    drawn_results['stalemate'] += 1
                elif 'repetition' in termination:
                    drawn_results['repetition'] += 1
                elif 'agreement' in termination:
                    drawn_results['agreement'] += 1


            elif "won" in termination:
                if player_username.lower() in termination.lower():
                    won_cnt += 1

                    if white_username.lower() == player_username.lower():
                        if white_win_opening.get(opening) is None:
                            white_win_opening[opening] = 1
                        else:
                            white_win_opening[opening] += 1
                    else:
                        if black_win_opening.get(opening) is None:
                            black_win_opening[opening] = 1
                        else:
                            black_win_opening[opening] += 1


                    if "resignation" in termination:
                        won_results['resignation'] += 1
                    elif "checkmate" in termination:
                        won_results['checkmate'] += 1
                    elif "time" in termination:
                        won_results['time'] += 1
                else:
                    lost_cnt += 1
                    if white_username.lower() == player_username.lower():
                        if white_lose_opening.get(opening) is None:
                            white_lose_opening[opening] = 1
                        else:
                            white_lose_opening[opening] += 1
                    else:
                        if black_lose_opening.get(opening) is None:
                            black_lose_opening[opening] = 1
                        else:
                            black_lose_opening[opening] += 1
                            
                if "resignation" in termination:
                    lost_results['resignation'] += 1
                elif "checkmate" in termination:
                    lost_results['checkmate'] += 1
                elif "time" in termination:
                    lost_results['time'] += 1

    bar.finish()

    # visualizing in a pie chart
    ###############################################################################
    def plot_pie(ax, data, title, labels):
            
        def func(pct, allvals):
            absolute = int(np.round(pct/100.*np.sum(allvals)))
            return "{:.1f}%".format(pct, absolute)

        wedges, texts, autotexts = ax.pie(data, autopct=lambda pct: func(pct, data),
                                    textprops=dict(color="w"))

        ax.legend(wedges, labels,
            title=title,
            loc="center left",
            bbox_to_anchor=(1, 0, 0.5, 1))

        plt.setp(autotexts, size=8, weight="bold")
        
        ax.set_title(title)

    ###############################################################################

    fig, ((ax1, ax2, ax3)) = plt.subplots(3, 1, figsize=(12, 12))

    if drawn_cnt > 0:
        data =  [int(x) for x in drawn_results.values()]
        draw_types = ['stalemate', '50 moves', 'repetition', 'insufficient', 'agreement']

        plot_pie(ax1, data, f"Games({time_class}) Drawn", draw_types) 
    ###############################################################################

    if won_cnt > 0:
        data =  [int(x) for x in won_results.values()]
        win_types = ['resignation', 'checkmate', 'timeout']

        plot_pie(ax2, data, f"Games({time_class}) Won", win_types)
    ###############################################################################

    if lost_cnt > 0:
        data =  [int(x) for x in lost_results.values()]
        lose_types = ['resignation', 'checkmate', 'timeout']
        
        plot_pie(ax3, data, f"Games({time_class}) Lost", lose_types)

    plt.show()

    def openings_stats(color, player, **kwargs):
        percentages = {}

        if color == "white":
            A = Counter(white_win_opening)
            B = Counter(white_draw_opening)
            C = Counter(white_lose_opening)
            total_games = A + B + C

            for key, value in white_win_opening.items():
                draw_cnt = 0
                lose_cnt = 0
                win_cnt = value
                if key in white_lose_opening:
                    lose_cnt = white_lose_opening[key]
                if key in white_draw_opening:
                    draw_cnt = white_draw_opening[key]
                
                if kwargs.get("minimum_games") is not None:
                    if win_cnt + lose_cnt + draw_cnt < kwargs.get("minimum_games"):
                        continue
                percentages[key] = win_cnt / (win_cnt + lose_cnt + draw_cnt)

        else:
            A = Counter(black_win_opening)
            B = Counter(black_draw_opening)
            C = Counter(black_lose_opening)
            total_games = A + B + C

            for key, value in black_win_opening.items():
                draw_cnt = 0
                lose_cnt = 0
                win_cnt = value
                if key in black_lose_opening:
                    lose_cnt = black_lose_opening[key]
                if key in black_draw_opening:
                    draw_cnt = black_draw_opening[key]

                if kwargs.get("minimum_games") is not None:
                    if win_cnt + lose_cnt + draw_cnt < kwargs.get("minimum_games"):
                        continue
                
                percentages[key] = win_cnt / (win_cnt + lose_cnt + draw_cnt)

        percentages = dict(sorted(percentages.items(), key= lambda x : x[1], reverse=True)[0:5])
        data = [float(x) for x in percentages.values()]

        if data != []:
            labels =   [__prettified_opening(key) for key in percentages.keys()]

            data = {"Opening": labels,
                "Scores": data}
    
        # Now convert this dictionary type data into a pandas dataframe
        # specifying what are the column names
        df = pd.DataFrame(data, columns=['Opening', 'Scores'])
    

        # Defining the x-axis, the y-axis and the data
        # from where the values are to be taken
        plots = sns.barplot(x="Opening", y="Scores", data=df)

        # Setting the x-acis label and its size
        plt.xlabel(f"Opening({time_class}) with {color}", size=15)

        # Setting the y-axis label and its size
        plt.ylabel("Win percentage", size=15)

        openings = list(percentages.keys())

        for index, p in enumerate(plots.patches):
                _x = p.get_x() + p.get_width() + float(0)
                _y = p.get_y() + p.get_height()
                value = f"{total_games[openings[index]]} games"
                plt.text(_x, _y, value, ha="left")


        plt.show()



    try:
        openings_stats("white", player_username, minimum_games=5)
        openings_stats("black", player_username, minimum_games=5)
    except ValueError:
        print("Not enough data for openings")



