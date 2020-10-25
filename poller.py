#! /usr/bin/env python3

import pickle
import json
import requests
import os
from configs import furk_api

base_url = 'https://www.furk.net/api/ping?api_key={}'
data = (requests.get(base_url.format(furk_api))).json()

try:
 poll = pickle.load(open("poll.pkl", 'rb'))
except:
 open("poll.pkl","wb")
 poll = ""

print(str(data) + "/n" + str(poll))


if data == poll:
 print("true")
else:
 print("false")

f = open("poll.pkl","wb")
pickle.dump((poll),f)
f.close()
