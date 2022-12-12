from PIL import Image
import pandas as pd
import requests
import numpy as np

def get_account_info(key, summoner_name):
    """
    get account information with given summoner name

    Parameters
    ---
    key: string
        Input string for api authentication 
    summoner_name: string
        Input string as api input for interested summoner name
    
    Returns
    ---
    new_text: dictionary
        dictionary that contains different information such as encrypted summoner id, puuid of the summoner, etc..
    """
    r = requests.get("https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/"
                     +summoner_name+"?api_key=" + key)
    data = r.json()
    return data

def get_account_basic(key, summoner_name):
    """
    get summoner ranked statistics with given summoner name

    Parameters
    ---
    key: string
        Input string for api authentication 
    summoner_name: string
        Input string as api input for interested summoner name
    
    Returns
    ---
    data: dictionary
        dictionary that contains summoner's rank information
    """
    encrypted_summoner_id = get_account_info(key, summoner_name)['id']
    r = requests.get("https://na1.api.riotgames.com/lol/league/v4/entries/by-summoner/"+
        encrypted_summoner_id+"?api_key="+key)
    data = r.json()
    print("Summoner: "+ data[0]['summonerName'])
    if len(data) == 0:
        print("Summoner has no ranked information")
    else:
        print(data[0]['queueType'] + ": "+str(data[0]['wins'])+' wins, '+str(data[0]['losses'])+ ' losses')
        if len(data) == 2:
            print(data[1]['queueType'] + ": "+str(data[1]['wins'])+' wins, '+str(data[1]['losses'])+ ' losses')
    return data

def get_match_list(key, puuid, count = 10):
    """
    get match ids with given summoner's puuid

    Parameters
    ---
    key: string
        Input string for api authentication 
    puuid: string
        Input string as api input for interested summoner's puuid
    count: int
        Input for number of games that are searched for
    
    Returns
    ---
    data: list
        list that contains summoner's match id
    """
    r = requests.get("https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/"+
                    puuid+"/ids?start=0&count="+str(count)+"&api_key="+key)
    data = r.json()
    return data

def get_match_info(key, match_id):
    """
    get all match information with given match id

    Parameters
    ---
    key: string
        Input string for api authentication 
    match_id: string
        Input string for interested match
    
    Returns
    ---
    data: dictionary
        dictionary that contains all details of match
    """
    r = requests.get("https://americas.api.riotgames.com/lol/match/v5/matches/"+
                    match_id+"?api_key="+key)
    data = r.json()
    return data

def get_summoner_recent_games(key, summoner_name, count = 10):
    """
    get summoner's recent match history

    Parameters
    ---
    key: string
        Input string for api authentication 
    summoner_name: string
        Input string as api input for interested summoner name
    count: int
        Input for number of games that are searched for
    
    Returns
    ---
    data: dataframe
        dataframe that contains match information for recent games such as kills, deaths and etc..
    """
    info = get_account_info(key, summoner_name = summoner_name)
    match_list = get_match_list(key, info['puuid'], count)
    results = []
    for match in match_list:
        match_info = get_match_info(key, match)
        for player in match_info['info']['participants']:
            if player['puuid'] == info['puuid']:
                results.append([player['kills'],player['deaths'],player['assists'],player['championName'],player['lane'],player['win']])
    data = pd.DataFrame(results, columns = ['kills', 'deaths','assists','champion_name','lane','win'])
    return data

def get_player_friend_list(key, summoner_name):
    """
    get summoner's friend list 

    Parameters
    ---
    key: string
        Input string for api authentication 
    summoner_name: string
        Input string as api input for interested summoner name
    
    Returns
    ---
    df1: dataframe
        dataframe that contains the friend list that summoner played with
    """
    info = get_account_info(key, summoner_name = summoner_name)
    match_list = get_match_list(key, info['puuid'])
    results = []
    for match in match_list:
        win_flag = False
        temp = []
        match_info = get_match_info(key, match)
        for player in match_info['info']['participants']:
            if player['puuid'] == info['puuid']:
                win_flag = player['win']
            
            temp.append([player['summonerName'],player['win']])
        for i in temp:
            if win_flag == i[1]:
                results.append(i)
    
    df = pd.DataFrame(results, columns = ['name','win'])
    df1 = df.groupby('name').agg({'win': ['count', 'sum']})
    df1.columns = ['total_games', 'wins']
    df1 = df1.reset_index()
    df1['win_rate']  = round(df1['wins']/df1['total_games'] * 100, 2)
    df1 = df1.loc[(upper(df1["name"]) != upper(summoner_name)) & (df1['total_games'] > 1)].sort_values(by=['total_games'], ascending = False)
    return df1

def compare_two_player(key, summoner1, summoner2):
    """
    compare the statistics of two players from recent games

    Parameters
    ---
    key: string
        Input string for api authentication 
    summoner1: string
        Input string as api input for the first interested summoner name
    summoner2: string
        Input string as api input for the second interested summoner name
    
    Returns
    ---
    df: dataframe
        dataframe that contains statistic comparison between two players
    """
    df1 = get_summoner_recent_games(key, summoner1, 20)
    df2 = get_summoner_recent_games(key, summoner2, 20)
    dict = {}
    dict[summoner1] = [df1['kills'].mean(),df1['deaths'].mean(),df1['assists'].mean()]
    dict[summoner2] = [df2['kills'].mean(),df2['deaths'].mean(),df2['assists'].mean()]
    df = pd.DataFrame.from_dict(dict)
    df = df.set_index(pd.Index(['avg_kill','avg_death','avg_assist']))
    df.plot.bar(rot=0)
    return df

def get_fav_champion(key, summoner_name):
    """
    get summoner's favorite champion from the perspective of mastery

    Parameters
    ---
    key: string
        Input string for api authentication 
    summoner_name: string
        Input string as api input for the interested summoner name
    
    Returns
    ---
    im: image
        image of the summoner's favorite champion
    """
    encrypted_summoner_id = get_account_info(key, summoner_name = summoner_name)['id']
    r = requests.get('https://na1.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-summoner/'
                     +encrypted_summoner_id+'?api_key='+key)
    versions = requests.get('https://ddragon.leagueoflegends.com/api/versions.json')
    champion_data_json = requests.get('https://ddragon.leagueoflegends.com/cdn/'+versions.json()[0]+'/data/en_US/champion.json')
    champion_data = champion_data_json.json()['data']
    dict1 = {}
    for champ in champion_data.keys():
        dict1[champion_data[champ]['key']] = champion_data[champ]['id']
    champ = dict1[str(r.json()[0]['championId'])]
    print(champ)
    im = Image.open(requests.get('http://ddragon.leagueoflegends.com/cdn/12.23.1/img/champion/'+champ+'.png', stream=True).raw)
    return im

    