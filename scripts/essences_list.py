import requests
import re
import datetime
from requests.sessions import Session
from concurrent.futures import ThreadPoolExecutor
from threading import Thread, local
from io import BytesIO
import zipfile
import xmltodict

requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning)

class Station:
    def __init__(self, id, name, brand):
        self.id = id
        self.name = name
        self.brand = brand

###
# Retrieve all IDS
###
url = "https://donnees.roulez-eco.fr/opendata/instantane"

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0"
}

print("Retrieving data from API")
r = requests.get(url, verify=False, headers=headers)

print("Generating ID list")
if r.status_code != 200:
    print(r.json())
    exit()

with zipfile.ZipFile(BytesIO(r.content)) as z:
    with z.open(z.namelist()[0]) as file:
        doc = xmltodict.parse(file)['pdv_liste']['pdv']

# Parse entry to store relevant data
all_ids = []
for station_data in doc:
    if not station_data['@id'] in all_ids:
        all_ids.append(station_data['@id'])

###
# Retrieve stations data
###
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:103.0) Gecko/20100101 Firefox/103.0",
    "Accept": "text/javascript, text/html, application/xml, text/xml, */*",
    "Accept-Language": "en,en-US;q=0.8,fr;q=0.5,fr-FR;q=0.3",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.prix-carburants.gouv.fr/",
    "Connection": "keep-alive",
    "Cookie": "atuserid=%7B%22name%22%3A%22atuserid%22%2C%22val%22%3A%22f5678982-6a58-46c0-89c9-63e38a6ad25d%22%2C%22options%22%3A%7B%22end%22%3A%222023-09-09T09%3A54%3A30.088Z%22%2C%22path%22%3A%22%2F%22%7D%7D; atauthority=%7B%22name%22%3A%22atauthority%22%2C%22val%22%3A%7B%22authority_name%22%3A%22cnil%22%2C%22visitor_mode%22%3A%22exempt%22%7D%2C%22options%22%3A%7B%22end%22%3A%222023-09-10T13%3A34%3A42.721Z%22%2C%22path%22%3A%22%2F%22%7D%7D; public=c02ace13a9c8223efa60bfa5eefe3aaf",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "no-cors",
    "Sec-Fetch-Site": "same-origin",
    "DNT": "1",
    "Sec-GPC": "1",
    "X-Requested-With": "XMLHttpRequest", "X-Prototype-Version": "1.7",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache"
}

baseurl = "https://www.prix-carburants.gouv.fr/map/recuperer_infos_pdv/"

thread_local = local()


def get_session() -> Session:
    if not hasattr(thread_local, 'session'):
        thread_local.session = requests.Session()
    return thread_local.session


total_done = 0
all_stations = []
errors = []


def get_station(id: str):
    global total_done
    id = id.strip()
    session = get_session()
    url = baseurl + id
    with session.get(url, headers=headers) as response:
        if response.status_code != 200:
            result = re.search(r"<title>.*<\/title>", response.text, re.DOTALL)
            values = re.sub('<.*?>', '', result.group(0))
            errors.append(f"{id}: {values}")
        else:
            total_done += 1
            result = re.search(r"<p>.*<\/p>", response.text, re.DOTALL)
            result = re.search(r"<strong>.*<\/strong>",
                               result.group(0), re.DOTALL)
            values = re.sub('<.*?>', '', result.group(0)).splitlines()

            # print(station.__dict__)
            all_stations.append(
                Station(id, values[0].strip(), values[1].strip()))


def get_all(stations: list) -> None:
    with ThreadPoolExecutor(max_workers=200) as executor:
        executor.map(get_station, stations)


start = datetime.datetime.now()
print("Retrieving station names")
get_all(all_ids)
with open('stations_lookup.csv', 'w') as csv:
    csv.writelines(
        f"\"{station.id}\";\"{station.name}\";\"{station.brand}\"\n" for station in all_stations)
with open("error.log", "w") as f_error:
    f_error.writelines(f"{err}\n" for err in errors)
end = datetime.datetime.now()
delta = end - start

print(f"{total_done}/{len(all_ids)} done in {delta}")
if len(errors) > 0:
    print("Read error.log")
