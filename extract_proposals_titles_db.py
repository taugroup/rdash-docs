from fast_autocomplete import AutoComplete
import pandas as pd
import os
import json

db = {}


df = pd.read_csv('./Output/nih_proposals_cleaned.csv')

n = len(df['Opportunity Number'])
for i in range(n):
    title = df['Title'][i].split()
    db[' '.join(title)] = {'pid' : df['Opportunity Number'][i], 'agency': 'nih'}
    db[' '.join(title[1:])] = {'pid' : df['Opportunity Number'][i], 'agency': 'nih'}
    db[' '.join(title[2:])] = {'pid' : df['Opportunity Number'][i], 'agency': 'nih'}
    db[' '.join(title[3:])] = {'pid' : df['Opportunity Number'][i], 'agency': 'nih'}

df = pd.read_csv('./Output/nsf_proposals_cleaned.csv')

n = len(df['Opportunity Number'])
for i in range(n):
    title = df['Title'][i].split()
    db[' '.join(title)] = {'pid' : df['Opportunity Number'][i], 'agency': 'nsf'}
    db[' '.join(title[1:])] = {'pid' : df['Opportunity Number'][i], 'agency': 'nsf'}
    db[' '.join(title[2:])] = {'pid' : df['Opportunity Number'][i], 'agency': 'nsf'}
    db[' '.join(title[3:])] = {'pid' : df['Opportunity Number'][i], 'agency': 'nsf'}



json_object = json.dumps(db, indent=4)

with open("Output/proposals_titles_db.json", "w") as outfile:
    outfile.write(json_object)

# with open('Output/proposals_titles_db.json', 'r') as f:
#      db = json.load(f)

# To predict something use:
# autocomplete = AutoComplete(words=db)
# suggestions = autocomplete.search(word='Chemical', max_cost=10, size=10)







