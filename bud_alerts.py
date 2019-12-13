from bud import *
import pandas as pd
import numpy as np
import pprint
import requests
import time
import json
import os, sys, inspect    
import datetime as dt
import slack
import itertools

#Start a Bud session and getting necessary access token
bud_session = Bud()
bud_session.login()
bud_session.create_request_session()

#Get account information
data = bud_session.get_account_info()
account_id = data['id']
account_name = data['firstName']

#Get a list of active learners
data = bud_session.get_active_learners()
learner_list = pd.DataFrame.from_dict(data['items'], orient='columns')

trainer_list = ['fd310f9f-5816-4787-8db4-aa800101bb3a','d1a70d69-551f-4b8c-9189-aae000a8479e','d4154014-7179-41b2-8bf3-aa800100d4ca','787b6166-edc9-4609-9de2-aa5500a47df6','b616cb3c-92c0-49bc-a61d-aaee010124b6','67501d43-62cb-4a05-a726-aa6200af0fa1','31f5f193-e4d6-44c8-ab09-aae700a3e5e2','dada4e6c-afb2-4886-ba1a-aa290095c378','5dfaec26-b6fe-4123-adf0-aaf000e6144a','26c6f30f-46ea-4fc5-be08-aa4d00bc76fd','e4ec8c60-a7f2-4a59-a526-aaee010158fa','38413f21-bca7-4340-a910-aab200ef6e20','b33a9077-1952-42c5-8f31-aa2d00ebc815','9c9f795b-2795-4da0-8481-a9ff011c5447','770977fb-5188-4fee-8366-aa3100f29f38']

data = bud_session.get_learning_plans(str(trainer_list).replace("\n",','))
df = pd.DataFrame.from_dict(list(itertools.chain.from_iterable([data[i] for i in data.keys()])), orient='columns')
