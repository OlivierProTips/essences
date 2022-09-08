from io import BytesIO
import json
import zipfile
import requests
import xmltodict

"""
Import stations data

Note:
xmltodict needs to be install (pip install) in Splunk Python path
pip install xmltodict -t /opt/splunk/lib/python3.7/site-packages/
"""

requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

class EssenceType:
    def __init__(self, name, price, update):
        self.name = name
        self.price = price
        self.update = update

class Station:
    def __init__(self, id, latitude, longitude, cp, address, ville):
        self.prices = []
        self.id = id
        self.latitude = latitude
        self.longitude = longitude
        self.cp = cp
        self.address = address
        self.ville = ville


url = "https://donnees.roulez-eco.fr/opendata/instantane"

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0"
}

r = requests.get(url, verify=False, headers=headers)

if r.status_code != 200:
    print(r.json())
    exit()

with zipfile.ZipFile(BytesIO(r.content)) as z:
    with z.open(z.namelist()[0]) as file:
        doc = xmltodict.parse(file)['pdv_liste']['pdv']

# Parse entry to store relevant data
all_stations = []
for station_data in doc:
    station = Station(station_data['@id'], station_data['@latitude'], station_data['@longitude'], station_data['@cp'], station_data['adresse'], station_data['ville'])
    if 'prix' in station_data and station_data['prix'] != None:
        if type(station_data['prix']) is list:
            for price_data in station_data['prix']:
                station.prices.append(EssenceType(price_data['@nom'], price_data['@valeur'], price_data['@maj']))
        else:
            station.prices.append(EssenceType(station_data['prix']['@nom'], station_data['prix']['@valeur'], station_data['prix']['@maj']))
    
    all_stations.append(station)

# Generate json events for Splunk
for s in all_stations:
    for t in s.prices:
        print(f'''{{
            "id": {json.dumps(s.id)},
            "latitude": {json.dumps(s.latitude)},
            "longitude": {json.dumps(s.longitude)},
            "cp": {json.dumps(s.cp)},
            "address": {json.dumps(s.address)},
            "ville": {json.dumps(s.ville)},
            "type": {json.dumps(t.name)},
            "price": {json.dumps(t.price)},
            "update": {json.dumps(t.update)}
        }}''')