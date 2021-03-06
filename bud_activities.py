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

activities_df = pd.DataFrame()

for index, learner_id in enumerate(learner_list['id']):
    data = bud_session.get_learning_plan(learner_id)
    df = pd.DataFrame.from_dict(data['activities'], orient='columns')
    df['learner_plan_id'] = learner_id
    activities_df = activities_df.append(df)
    print(f'Loading data... {index+1}/{len(learner_list["id"])} [{(int(index/10))*"="}>{int((len(learner_list["id"])-index-1)/10)*"."}]', end='\r')


activities_df = learner_list.merge(activities_df, how='left', left_on='id', right_on='learner_plan_id')
activities_df.to_csv(dt.datetime.today().strftime(format="%Y%m%d")+'activities_list.csv', index=False)
