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
onErrorStop = False
exitWhenDone = True

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
    # If no ability in list, then the first td element contains that ability
    # This occurs when a Pokemon has only one alternative ability
    if not ability:
        ability.append(meta_ability[0].find("span").contents[0])
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
    stat_header = soup.find("span",attrs={"id" : "Base_stats"})
    if (stat_header is None):
        # Also for Hoopa, dunno why
        stat_header = soup.find("span",attrs={"id" : "Stats"}).next_element.next_element.next_element
    try:
        stat_table = stat_header.next_element.next_element.next_element.next_element.next_element.next_element.next_element
        stat_elements = stat_table.find_all("tr")
        hp = ((stat_elements[2].find("table").find_all("th"))[1].contents[0])[1:-1]
    except:
        try:
            stat_table = stat_header.next_element.next_element.next_element
            stat_elements = stat_table.find_all("tr")
            hp = ((stat_elements[2].find("table").find_all("th"))[1].contents[0])[1:-1]
        except:
            # Exclusive for Hoopa, dunno why
            stat_table = stat_header.next_element.next_element.next_element.next_element
            print(stat_table)
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

def Scrape(i,initial = [],init_not_scrapped = []):
    global pokemons
    count = len(pokemons)
    out = initial
    not_scrapped = init_not_scrapped
    curIndex = 0
    if (i < count):
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
                    not_scrapped.append(now)
                    if onErrorStop:
                        print("Error in scraping " + pokemons[now]["name"] + " (#" + str(pokemons[now]["no"]) + "), stopping operation...")
                        break
                    else:
                        print("Error in scraping " + pokemons[now]["name"] + " (#" + str(pokemons[now]["no"]) + "), skipping...")
                finally:
                    time.sleep(0.5)
        except KeyboardInterrupt:
            print("Ctrl-C pressed, stopping...")
            pass
    else:
        now = 807
    print("\n")
    state = {}
    state["lastScrapped"] = now
    state["notScrapped"] = not_scrapped
    try:
        if (out[-1]["no"] == (count - 1)):
            state["lastScrapped"] = state["lastScrapped"] + 1
    except:
        pass
    count = len(out)
    try:
        with open(data_dir + "main_data.json","r") as f:
            prev_data = json.load(f)
        print("Found " + str(len(prev_data)) + " entries already scrapped")
    except FileNotFoundError:
        prev_data = []
    except Exception as e:
        traceback.print_exc()
        prev_data = []
    out = prev_data + out
    # Sort data based on Dex number
    out.sort(key=lambda x:x["no"])
    with open(data_dir + "state.json","w") as f:
        json.dump(state,f)
    with open(data_dir + "main_data.json","w") as f:
        json.dump(out,f,indent=2)
    print("Saved " + str(count) + " entries ( + " + str(len(prev_data)) + " old entries) with " + str(len(not_scrapped)) + " entries skipped.\n")

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

valid = False

while not valid:
    print("\nWhat do you want to do?")
    print("---------------------------------")
    print("1. Start scraping data.")
    print("2. Refresh initial data.")
    if state:
        print("R. Resume from last scrapped data")
    if onErrorStop:
        print("S. Scraping setting : Stop when error occurs")
    else:
        print("S. Scraping setting : Ignore when error occurs")
    if exitWhenDone:
        print("EX. Scraping setting : Terminate when scraping finished")
    else:
        print("EX. Scraping setting : Do not terminate program when scraping finished")
    print("E. Exit")
    print("---------------------------------")
    sel = input("Your choice : ")
    if (sel == "1"):
        print("Scraping job started...!")
        Scrape(0)
        valid = exitWhenDone
    elif (sel == "2"):
        GetInitList()
    elif ((sel == "R" or sel == "r") and state):
        temp = []
        if state["notScrapped"]:
            print("Scrapping errored entries first... ")
            stop = False
            while state["notScrapped"] and not stop:
                current = state["notScrapped"].pop()
                try:
                    print("Scraping " + pokemons[current]["name"] + " (#" + str(pokemons[current]["no"]) + ")...")
                    temp.append(SingleScrape(current))
                    print(pokemons[current]["name"] + " (#" + str(pokemons[current]["no"]) + ") scrapped")
                except KeyboardInterrupt:
                    state["notScrapped"].insert(0,current)
                    break
                except:
                    traceback.print_exc()
                    print("Error in scraping " + pokemons[current]["name"] + " (#" + str(pokemons[current]["no"]) + "), will try later...")
                    state["notScrapped"].insert(0,current)
                    if onErrorStop:
                        stop = True
        print("Resuming...")
        Scrape(state["lastScrapped"],temp,state["notScrapped"])
        valid = exitWhenDone
    elif (sel == "S" or sel == "s"):
        onErrorStop = not onErrorStop
        print("Setting changed.")
    elif (sel == "EX" or sel == "ex" or sel == "Ex" or sel == "eX"):
        exitWhenDone = not exitWhenDone
        print("Setting changed.")
    elif (sel == "E" or sel == "e"):
        print("Buh bye...!")
        valid = True
    else:
        print("Input is not valid!")
