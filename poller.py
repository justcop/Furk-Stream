#! /usr/bin/env python3

import pickle
import json
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

poll = pickle.load(open("poll.pkl", 'rb'))

if ordered(data) == ordered(poll):
 print("no change")
else
 print("change")

f = open("poll.pkl","wb")
pickle.dump(poll,f)
f.close()
