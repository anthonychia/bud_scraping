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

#bud_session.quit()

#Get account information
data = bud_session.get_account_info()
account_id = data['id']
account_name = data['firstName']

#Get a list of active learners
data = bud_session.get_active_learners()
learner_list = pd.DataFrame.from_dict(data['items'], orient='columns')

#Get messages
number_messages = 5
data = bud_session.get_notifications()
latest_messages = data[:number_messages]
slack_message = ':email: :email: :email: *Your latest Bud messages* :email: :email: :email:\nHere are your %i latest messages on Bud. Unread messages are highlighted in *italic*! *Please also note that if you click on the activity links before logging into Bud first, you will be redirected to the login page. So please make sure you are already logged in before clicking on these links.*\n\n'%(number_messages)

for i in range(len(latest_messages)):
    message = latest_messages[i]
    time_sent = message['sent']
    time_sent = dt.datetime.strptime(time_sent, '%Y-%m-%dT%H:%M:%S.%fZ')
    learner_id = message['routeParameters']['learningPlanId']
    activity_id = message['routeParameters']['activityId']
    url = "https://web.bud.co.uk/learningportal/assessor/plan/"+learner_id+"/activity/"+activity_id+"/submissions/"
    #formatting slack message
    url = ' - <%s|activity link>\n'%(url)
    time_sent = '<!date^%i^{date_num} {time_secs}|%s UTC>'%(int(time_sent.timestamp()), str(time_sent))
    slack_message = slack_message + '%i. [%s] %s %s ```%s```\n\n'%(i+1, time_sent, message['substitutions']['learnerName'], url, message['substitutions']['content'][:100])

bud_session.quit()

#Connect to Slack API via token
slack_token = os.environ["SLACK_API_TOKEN"]
client = slack.WebClient(slack_token)

#Send message via Slack
channel = client.conversations_open(users='UK6UQECMS')
#client.chat_postMessage(channel=channel['channel']['id'],
#                        text=slack_message)

#Look for Bud channel
#bud_channel=None
#cursor=''
#while bud_channel is None:
#    channel_list = client.conversations_list(limit=1000, exclude_archived='true', types='private_channel,public_channel', cursor=cursor)
#    cursor = channel_list['response_metadata']['next_cursor']
#    for i in channel_list['channels']:
#        if i['name'] == 'ldn-bud': bud_channel = i['id'] 

#Get user list for Bud channel
#bud_user_list = client.channels_info(channel=bud_channel)
#bud_user_list = bud_user_list['channel']['members']
#users=[]
#for user in bud_user_list:
    #convo = client.conversations_open(users=user_id)
#    user_info = client.users_info(user=user)
#    user_info = user_info['user']['profile']
#    users.append(user_info)
#df = pd.DataFrame.from_dict(users, orient='columns')
