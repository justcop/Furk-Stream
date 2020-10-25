#! /usr/bin/env python3

import pickle
import json
import requests
from configs import furk_api

def ordered(obj):
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(ordered(x) for x in obj)
    else:
        return obj

base_url = 'https://www.furk.net/api/ping&api_key={}'
data = (requests.get(base_url.format(furk_api))).json()

try:
 poll = pickle.load(open("poll.pkl", 'rb'))

g = ordered(data)
print("g")

f = open("poll.pkl","wb")
pickle.dump(poll,f)
f.close()
