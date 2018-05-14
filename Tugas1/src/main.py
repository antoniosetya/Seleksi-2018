import urllib.request
import traceback
import time
from bs4 import BeautifulSoup
import json

data_dir = "./data/"
# Given code number 1 - 7, returns region code. See function for details
region_code = ["KanDex","JDex","HDex","SDex","UDex","KalDex","ADex"]
pokemons = []
state = {}

def CleanDexNmbr(nmbr):
    return int(nmbr[2:5])

def IsNmbrInList(data,number):
    found = False
    for elm in data:
        if (elm["no"] == number):
            found = True
            break
    return found

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
                # Grabs initial Pokemon data
                pkmns = tbl.find_all("tr",style="background:#FFF")
                for rows in pkmns:
                    datas = rows.find_all("td")
                    number = CleanDexNmbr(datas[1].contents[0])
                    name = datas[3].a.string
                    ext_link = "https://bulbapedia.bulbagarden.net" + datas[3].a.get("href")
                    # Adds data to the list
                    if not IsNmbrInList(pokemon_list,int(number)):
                        pokemon_list.append({"no" : number, "name" : name, "link" : ext_link})

    # Dumps data to JSON file
    with open(data_dir + "init_list.json","w") as f:
        json.dump(pokemon_list,f)
    pokemons = pokemon_list

def SingleScrape(index):
    global pokemons
    hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
           }
    req = urllib.request.Request(pokemons[index]["link"],headers=hdr)
    with urllib.request.urlopen(req) as response:
        html = response.read()
        soup = BeautifulSoup(html,'html.parser')
    main_data = soup.find("div",attrs={"id" : "mw-content-text"})
    metadata = main_data.find("table",attrs={"class" : "roundy"}).find_all("td",attrs={"class" : "roundy"})
    # Determines whether this Pokemon has alternate forms
    # LATERRR

    # Extracts type data
    meta_type = (metadata[1].find_all("table"))[1].find_all("td")
    type = []
    for td in meta_type:
        type.append(td.find("span").find("b").contents[0])
    #print(type)

    # Extracts abilities
    meta_ability = metadata[2].find_all("td")
    ability = []
    for td in meta_ability:
        if not td.has_attr("style"):
            ability.append(td.find("a").find("span").contents[0])
    #print(ability)

    # Extracts height and weight
    meta_h = metadata[6]
    meta_w = metadata[7]
    height = (((meta_h.find_all("tr"))[0].find_all("td")[1].contents[0])[1:])[:-1]
    weight = (((meta_w.find_all("tr"))[0].find_all("td")[1].contents[0])[1:])[:-1]
    #print(height + " | " + weight)

    # Extracts when this Pokemon is introduced
    when_str = (main_data.find_all("table",attrs={"class" : "roundy"}))[23].find("th").find("small").contents[0]
    #print(when_str)

    # Extracts base stats of this Pokemon
    try:
        stat_table = main_data.find("span",attrs={"id" : "Base_stats"}).next_element.next_element.next_element.next_element.next_element.next_element.next_element
        stat_elements = stat_table.find_all("tr")
        hp = ((stat_elements[2].find("table").find_all("th"))[1].contents[0])[1:-1]
    except:
        stat_table = main_data.find("span",attrs={"id" : "Base_stats"}).next_element.next_element.next_element
        stat_elements = stat_table.find_all("tr")
        hp = ((stat_elements[2].find("table").find_all("th"))[1].contents[0])[1:-1]
        #print(hp)
    atk = ((stat_elements[4].find("table").find_all("th"))[1].contents[0])[1:-1]
    #print(atk)
    defn = ((stat_elements[6].find("table").find_all("th"))[1].contents[0])[1:-1]
    #print(defn)
    spatk = ((stat_elements[8].find("table").find_all("th"))[1].contents[0])[1:-1]
    #print(spatk)
    spdef = ((stat_elements[10].find("table").find_all("th"))[1].contents[0])[1:-1]
    #print(spdef)
    spe = ((stat_elements[12].find("table").find_all("th"))[1].contents[0])[1:-1]
    #print(spe)

    # Inserting results into out array
    out = {}
    out["no"] = pokemons[index]["no"]
    out["name"] = pokemons[index]["name"]
    out["type"] = type
    out["ability"] = ability
    out["weight"] = weight
    out["stats"] = {"hp" : hp, "atk" : atk, "def" : defn, "spatk" : spatk, "spdef" : spdef, "spe" : spe}
    return out

def Scrape(i,initial = []):
    global pokemons
    count = len(pokemons)
    out = initial
    not_scrapped = []
    curIndex = 0
    try:
        for now in range(i,count):
            try:
                print("Scraping " + pokemons[now]["name"] + " (#" + str(pokemons[now]["no"]) + ")...")
                out.append(SingleScrape(now))
                print(pokemons[now]["name"] + " (#" + str(pokemons[now]["no"]) + ") scrapped")
            except KeyboardInterrupt:
                print("Ctrl-C pressed, stopping...")
                break
            except:
                traceback.print_exc()
                print("Error in scraping " + pokemons[now]["name"] + " (#" + str(pokemons[now]["no"]) + "), skipping...")
                not_scrapped.append(now)
            finally:
                time.sleep(0.5)
    except KeyboardInterrupt:
        print("Ctrl-C pressed, stopping...")
        pass
    state = {}
    state["lastScrapped"] = now
    state["notScrapped"] = not_scrapped
    try:
        with open(data_dir + "main_data.json","r") as f:
            prev_data = json.load(f)
    except:
        prev_data = []
    out = prev_data + out
    # Sort data based on Dex number
    out.sort(key=lambda x:x["no"])
    with open(data_dir + "state.json","w") as f:
        json.dump(state,f)
    with open(data_dir + "main_data.json","w") as f:
        json.dump(out,f)
    print("\n\n")
    print("Saved " + str(len(out)) + " entries with " + str(len(not_scrapped)) + " entries skipped.")

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
# Even though state.json exists, if main_data.json doesn't exists, it will ignore it
try:
    f = open(data_dir + "main_data.json","r")
    f.close()
    with open(data_dir + "state.json","r") as f:
        state = json.load(f)
except FileNotFoundError:
    pass
except JSONDecodeError:
    pass

print("\nWhat do you want to do?")
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
        print("Scraping job started...!")
        Scrape(0)
        valid = True
    elif (sel == "2"):
        GetInitList()
        valid = True
    elif ((sel == "R" or sel == "r") and state):
        temp = []
        if state["notScrapped"]:
            print("Scrapping errored entries first... ")
            while state["notScrapped"]:
                current = state["notScrapped"].pop()
                try:
                    print("Scraping " + pokemons[current]["name"] + " (#" + str(pokemons[current]["no"]) + ")...")
                    temp.append(SingleScrape(current))
                    print(pokemons[current]["name"] + " (#" + str(pokemons[current]["no"]) + ") scrapped")
                except KeyboardInterrupt:
                    break
                except:
                    traceback.print_exc()
                    print("Error in scraping " + pokemons[current]["name"] + " (#" + str(pokemons[current]["no"]) + "), will try later...")
                    state["notScrapped"].append(current)
        print("Resuming...")
        Scrape(state["lastScrapped"],temp)
        valid = True
    elif (sel == "E" or sel == "e"):
        print("Buh bye...!")
        valid = True
    else:
        print("Input is not valid!")