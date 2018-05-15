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
    global pokemons
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
    meta_pic = (main_data.find("table",attrs={"class" : "roundy"}).find_all("table",attrs={"class" : "roundy"}))[1].find_all("a",attrs={"class" : "image"})
    forms_names = []
    if (len(meta_pic) > 1):
        try:
            for pic in meta_pic:
                temp = pic.findNext("small").contents[0]
                if temp not in forms_names:
                    forms_names.append(temp)
        except:
            forms_names.append(pokemons[index]["name"])
    else:
        forms_names.append(pokemons[index]["name"])
    forms_count = len(forms_names)

    # Extracts type data
    type = []
    meta_type = metadata[1].find_all("table")
    list_iter = 0
    for type_cell in meta_type[1:]:
        temp_type = type_cell.find_all("td")
        type.append([])
        for td in temp_type:
            type[list_iter].append(td.find("span").find("b").contents[0])
        list_iter = list_iter + 1
    # Cleans the list from garbage
    type = [x for x in type if x[0] != "Unknown"]

    # Extracts abilities
    meta_ability = metadata[2].find_all("td")
    ability = []
    for iter in range(0,forms_count):
        ability.append([])
    for td in meta_ability:
        if forms_count > 1:
            if (td.find("small") is None):
                span = td.find_all("span")
                for sp in span:
                    ability[0].append(sp.contents[0])
            elif ("Hidden Ability" in (td.find("small").contents)):
                ability[0].append(td.find("span").contents[0])
            else:
                try:
                    ability[forms_names.index(td.find("small").contents[0])].append(td.find("span").contents[0])
                except:
                    span = td.find_all("span")
                    for sp in span:
                        ability[0].append(sp.contents[0])
        else:
            span = td.find_all("span")
            for sp in span:
                ability[0].append(sp.contents[0])

    ability = [x for x in ability if x != []]
    for iter in range(0,len(ability)):
        ability[iter] = list(set(ability[iter]))
        try:
            ability[iter].remove("Cacophony")
            ability[iter].remove("*")
        except:
            pass

    # Extracts weight
    meta_w = metadata[7].find_all("tr")
    weight = []
    for tr in meta_w[0::2]:
        temp = tr.find_all("td")
        temp = (temp[1].contents[0])[1:-1]
        if (temp != "0 kg"):
            weight.append(temp)

    # Extracts when this Pokemon is introduced
    when_str = (main_data.find_all("table",attrs={"class" : "roundy"}))[23].find("th").find("small").contents[0]

    # Extracts base stats of this Pokemon
    stat_header = soup.find("span",attrs={"id" : "Stats"})
    if (stat_header is None):
        stat_header = soup.find("span",attrs={"id" : "Base_stats"})
    statuses = []
    stat_table = stat_header.findNext("table")
    for iter in range(0,forms_count):
        try:
            stat_elements = stat_table.find_all("tr")
            hp = ((stat_elements[2].find("table").find_all("th"))[1].contents[0])[1:-1]
            atk = ((stat_elements[4].find("table").find_all("th"))[1].contents[0])[1:-1]
            defn = ((stat_elements[6].find("table").find_all("th"))[1].contents[0])[1:-1]
            spatk = ((stat_elements[8].find("table").find_all("th"))[1].contents[0])[1:-1]
            spdef = ((stat_elements[10].find("table").find_all("th"))[1].contents[0])[1:-1]
            spe = ((stat_elements[12].find("table").find_all("th"))[1].contents[0])[1:-1]
            statuses.append({"hp" : hp, "atk" : atk, "def" : defn, "spatk" : spatk, "spdef" : spdef, "spe" : spe})
            stat_table = stat_elements[len(stat_elements) - 1].findNext("table")
        except:
            break

    print("Found : " + repr(forms_names))
    # Inserting results into out array. Forms are splitted into individual entries (list element)
    out = []
    for iter in range(0,forms_count):
        out.append({})
        # Pokemon Dex Number and it's name. Adds the real name if scrapped name doesn't contain the real name
        out[iter]["no"] = pokemons[index]["no"]
        out[iter]["name"] = forms_names[iter]
        if (pokemons[index]["name"] not in out[iter]["name"]):
            out[iter]["name"] = pokemons[index]["name"] + " (" + out[iter]["name"] + ")"
        # When this Pokemon is introduced. First element always introduced on <when_str>
        if (iter >= 1):
            if ("Mega" in out[iter]["name"]):
                out[iter]["made_in"] = "Generation VI"
            elif ("Alolan" in out[iter]["name"]):
                out[iter]["made_in"] = "Generation VII"
            else:
                out[iter]["made_in"] = when_str
        else:
            out[iter]["made_in"] = when_str
        # Pokemon type
        if (iter >= len(type)):
            out[iter]["type"] = type[len(type) - 1]
        else:
            out[iter]["type"] = type[iter]
        # Pokemon abilities
        if (iter >= len(ability)):
            out[iter]["ability"] = ability[len(ability) - 1]
        else:
            out[iter]["ability"] = ability[iter]
        # Pokemon weight
        if (iter >= len(weight)):
            out[iter]["weight"] = weight[len(weight) - 1]
        else:
            out[iter]["weight"] = weight[iter]
        # Pokemon status
        if (iter >= len(statuses)):
            out[iter]["stats"] = statuses[len(statuses) - 1]
        else:
            out[iter]["stats"] = statuses[iter]
    return out

def Scrape(i,initial = [],init_not_scrapped = []):
    global pokemons
    count = len(pokemons)
    out = initial
    out_count = len(out)
    out_real = out_count
    not_scrapped = init_not_scrapped
    curIndex = 0
    if (i < count):
        try:
            for now in range(i,count):
                try:
                    print("Scraping " + pokemons[now]["name"] + " (#" + str(pokemons[now]["no"]) + ")...")
                    temp = SingleScrape(now)
                    out_count = out_count + len(temp)
                    out_real = out_real + len(temp)
                    out = out + temp
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
                    if (out_count >= 50):
                        print("Saving currently scrapped entries to file...")
                        try:
                            with open(data_dir + "main_data.json","r") as f:
                                prev_data = json.load(f)
                        except FileNotFoundError:
                            prev_data = []
                        out =  prev_data + out
                        # Sort data based on Dex number
                        out.sort(key=lambda x:x["no"])
                        with open(data_dir + "main_data.json","w") as f:
                            json.dump(out,f,indent=2)
                            out = []
                            prev_data = []
                            out_count = 0
                        print("Saved, resuming scrapping...")
                    time.sleep(0.25)
        except KeyboardInterrupt:
            print("Ctrl-C pressed, stopping...")
            pass
    else:
        now = 807
    if ((now + 1) == count):
        now = now + 1
    print("\n")
    state = {}
    state["lastScrapped"] = now
    state["notScrapped"] = not_scrapped
    print("Saving unsaved entries...")
    if (out_count > 0):
        try:
            if (out[-1]["no"] == (count - 1)):
                state["lastScrapped"] = state["lastScrapped"] + 1
        except:
            pass
        try:
            with open(data_dir + "main_data.json","r") as f:
                prev_data = json.load(f)
        except FileNotFoundError:
            prev_data = []
        except Exception as e:
            traceback.print_exc()
            prev_data = []
        out = prev_data + out
        # Sort data based on Dex number
        out.sort(key=lambda x:x["no"])
        with open(data_dir + "main_data.json","w") as f:
            json.dump(out,f,indent=2)
    with open(data_dir + "state.json","w") as f:
        json.dump(state,f)
    print("Saved " + str(out_real) + " entries. " + str(len(not_scrapped)) + " entries skipped.\n")

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
                    temp = temp + SingleScrape(current)
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
