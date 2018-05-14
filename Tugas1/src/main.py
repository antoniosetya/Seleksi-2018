import urllib.request
from bs4 import BeautifulSoup
import json

data_dir = "./data/"
# Given code number 1 - 7, returns region code. See function for details
region_code = ["KanDex","JDex","HDex","SDex","UDex","KalDex","ADex"]
pokemons = []
state = {}

def CleanDexNmbr(nmbr):
    return nmbr[2:5]

def GetInitList():
    # Grabbing initial Pokemon data (list of all Pokemon)
    # Request headers. Without this, Bulbapedia will reject the request (as error 403 Forbidden)
    print("Requesting data from server...")
    hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
           }
    # Here comes the actual request sent to server
    req = urllib.request.Request("https://bulbapedia.bulbagarden.net/wiki/List_of_Pok%C3%A9mon_by_National_Pok%C3%A9dex_number",headers=hdr)
    with urllib.request.urlopen(req) as response:
        html = response.read()
        soup = BeautifulSoup(html,'html.parser')

    # Stores initial Pokemon data
    pokemon_list = []
    # The list are in <table> tag...
    tables = soup.find_all('table')

    # ..., but there's several <table> tags in this document.
    # We have to select which table contains the correct information
    # and then extract list from that table. The correct table has a <th>
    # with 'Ndex' inside the <th> element

    print("Parsing data...")
    c = 0
    for tbl in tables:
        identifier = tbl.find_all("th")
        if identifier:
            try :
                if (identifier[1].contents[0] == " Ndex\n"):
                    correct = True
                else:
                    correct = False
            except:
                correct = False
                pass
            if correct:
                # Grabs region of Dex
                temp_reg = region_code[c]
                c = c + 1
                # Grabs initial Pokemon data
                pkmns = tbl.find_all("tr",style="background:#FFF")
                for rows in pkmns:
                    datas = rows.find_all("td")
                    number = CleanDexNmbr(datas[1].contents[0])
                    name = datas[3].a.string
                    ext_link = "https://bulbapedia.bulbagarden.net" + datas[3].a.get("href")
                    # Adds data to the list
                    pokemon_list.append({"no" : number, "name" : name, "link" : ext_link})

    # Dumps data to JSON file
    with open(data_dir + "init_list.json","w") as f:
        json.dump(pokemon_list,f)
    pokemons = pokemon_list

# Trying to load initial data
try:
    with open(data_dir + "init_list.json","r") as f:
        pokemons = json.load(f)
except FileNotFoundError:
    print("Initial data not found...")
except JSONDecodeError:
    print("Initial data is corrupted...")

# Grabs initial data if no initial data found
if not pokemons:
    print("Attempting to get initial Pokemon data...")
    GetInitList()

# Trying to load last state of scraping, in case it is interrupted
try:
    with open(data_dir + "state.json","r") as f:
        state = json.load(f)
except FileNotFoundError:
    pass
except JSONDecodeError:
    pass

print("What do you want to do?")
print("---------------------------------")
print("1. Start scraping data.")
print("2. Refresh initial data.")
if state:
    print("R. Resume from last scrapped data")
print("E. Exit")
print("---------------------------------")

valid = False

while not valid:
    sel = input("Your choice : ")
    if (sel == "1"):
        # Start scraping
        valid = True
    elif (sel == "2"):
        GetInitList()
        valid = True
    elif ((sel == "R" or sel == "r") and state):
        # start scraping
        valid = True
    elif (sel == "E" or sel == "e"):
        print("Buh bye...!")
        valid = True
    else:
        print("Input is not valid!")
