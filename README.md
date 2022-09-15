# Essences

## Pre-Requisites
- [Maps+ for Splunk](https://splunkbase.splunk.com/app/3124/)


## Get the prices of the stations
The data is provided by the api https://donnees.roulez-eco.fr/opendata/instantane

When connecting to this API, a zip containing the data is downloaded. In this archive is a file in xml format.

In order to ingest the data into Splunk, we use a Python script that performs the following actions:  
- Connect to the API to download the zip file Unzip the archive
- Parsing the xml file to extract useful data Generating the data in json format

The script is launched by a `script` stanza in the inputs.conf and the data is put in an `essence` index

## Retrieve station names

In the data retrieved previously, there is no name and brand of the service stations.

To get them, we use the API https://www.prix-carburants.gouv.fr/map/recuperer_infos_pdv/{station_id}

The list of station IDs can be retrieved via the API https://donnees.roulez-eco.fr/opendata/instantane

Thanks to a Python script, we will query the 2 APIs in order to generate a lookup containing the information of the service stations.

To optimize the lookup generation, the Python script is multi-threaded.

### Execution

```bash
pip3 install -r requirements.txt
python3 essences_list.py
```

It will generate a file called `stations_lookup.csv` that can be upload into Splunk, either with Lookup Editor, or with the Essence app into the lookups folder.

## Useful SPL

### Get ID
```sql
index="essence" ville="PARIS" | lookup stations_lookup.csv id | table id, name, brand, address, cp, ville
```

### Price evolution by station ID
```sql
index="essence" id="111111111" | timechart values(price) by type cont=FALSE
```

### Check if there are errors executing essences.py
```sql
index="_internal" essences.py log_level!=INFO
```