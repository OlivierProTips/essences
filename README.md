# Essences

## Pre-Requisites
- [Maps+ for Splunk](https://splunkbase.splunk.com/app/3124/)

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