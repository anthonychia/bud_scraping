from bud import *
import pandas as pd
import numpy as np
import pprint
import requests
import time
import json
import os, sys, inspect    
import datetime as dt

#Getting login details and logging in through login page via selenium automation
bud_session = Bud()
bud_session.login()
bud_session.create_request_session()

#GET REQUESTS and saving responses 
s = requests.Session()
for cookie in cookies:
    s.cookies.set(cookie['name'], cookie['value'])
headers = {"accept":"application/json","authorization":"Bearer "+access_token["access_token"],"cache-control":"no-cache","content-type":"application/json","pragma":"no-cache"}
#response = s.get("https://live-portfolio-learning-api.bud.co.uk/learningplan/currentlylearning", headers = headers)
response = s.get("https://live-account-api.bud.co.uk/account/profile", headers=headers)
data = response.json()
account_id = data['id']

#response = s.post("https://live-portfolio-learning-api.bud.co.uk/stats/summaries", headers=headers)
response = s.get("https://live-learnermanagement-api.bud.co.uk/learner-management/active"+"?pageSize=1000&statuses=1", headers=headers)
data = response.json()
#fullname = [i['learner']['foreName']+' '+i['learner']['surname'] for i in data[account_id]]
#id = [i['id'] for i in data[account_id]]
#df['name'] = df['learner'].apply(lambda x: x['fullName'])
df = pd.DataFrame.from_dict(data['items'], orient='columns')

def find_evidence_form(files):
    for file in files:
        if any(x in file['fileName'] for x in ['Evidence', 'evidence']):
            return file['fileName']

monthly_counts = pd.DataFrame()

list_of_cohorts = df['programmeName'].unique()
print("=====================================")
print("        List of Cohorts")
print("=====================================")
for i in range(len(list_of_cohorts)):
    print("%i: %s\n"%(i,list_of_cohorts[i]))

selected_cohorts = [ list_of_cohorts[int(i)] for i in input("Selecting cohort(s) \n* you can select multiple cohorts by entering e.g \"1,2,3\" * \nPlease Enter Selection: ").split(",") ]
#selected_cohorts = list_of_cohorts
print(selected_cohorts)

df = df[df['programmeName'].isin(selected_cohorts)]

days=60
    
for id in df['id']:
    response = s.get("https://live-portfolio-learning-api.bud.co.uk/learningplan/"+id, headers=headers)
    data = response.json()
    time.sleep(np.random.rand()*0.5)
    activities_df = pd.DataFrame(columns=['id','name','date','filename'])
    activities = [[i['id'],i['name'],i['dateOfLastLearnerAction'], i['dueDate']] for i in data['activities'] if i['hasSubmissions']]
    for activity_id, activity_name,lastActionDate,dueDate in activities:
        if lastActionDate:
            if(dt.datetime.now() - dt.datetime.strptime((lastActionDate[:24]).strip(), "%Y-%m-%dT%H:%M:%S.%f") > dt.timedelta(days=days)): continue   #only count activities in the last 60 days
        else:
            if(dt.datetime.now() - dt.datetime.strptime((dueDate[:24]).strip(), "%Y-%m-%dT%H:%M:%SZ") > dt.timedelta(days=days)): continue   #only count activities in the last 60 days
        response = s.get("https://live-portfolio-learning-api.bud.co.uk/learningplan/"+id+"/activity/"+activity_id, headers=headers)
        data = response.json()
        for i in data['submissions']:
            if i['status'] >= 1: # 0: no file , 1: file submitted, 2: marked as incomplete, 3: marked as complete
                submissionDate = i['submissionDate']
                fileName = find_evidence_form(i['files']) # search through files for evidence form in case of multiple file submission.
        activities_df.loc[len(activities_df)] = [activity_id, activity_name, submissionDate, fileName]
                

    #Counting reviews
    response = s.get("https://live-portfolio-learning-api.bud.co.uk/progress-review/all/"+id, headers=headers)
    data = response.json()
    for review in data:
        if review['dateStarted']:
            if(dt.datetime.now() - dt.datetime.strptime((review['schedule']['reviewDate'][:24]).strip(), "%Y-%m-%dT%H:%M:%SZ") > dt.timedelta(days=days)): continue 
            reviewDate = review['schedule']['reviewDate']
            fileName = 'None'
            activityName = review['name']
            activityId = review['id']
            activities_df.loc[len(activities_df)] = [activityId, activityName, reviewDate, fileName]

    activities_df['month'] = pd.to_datetime(activities_df['date']).dt.strftime('%m-%Y')
    if not activities_df.empty:
        activities_df.loc[activities_df['name'].str.lower().str.contains('call|review', regex=True),'type'] = 'Call'
        #activities_df.loc[activities_df['name'].str.lower().str.contains('review'),'type'] = 'Review'
        activities_df.loc[activities_df['name'].str.lower().str.contains('workshop|practice|project', regex=True),'type'] = 'Bud'
        #activities_df.loc[activities_df['name'].str.lower().str.contains('project', regex=True),'type'] = 'Project'
        single_count = activities_df.groupby(['month','type']).size().to_frame().transpose()
    else:
        single_count = pd.DataFrame()
    single_count.columns = single_count.columns.map('_'.join)
    single_count['id'] = id
    monthly_counts = pd.concat([monthly_counts,single_count], sort=False)
    
monthly_counts = monthly_counts[sorted(monthly_counts.columns)]
df = df.set_index('id').join(monthly_counts.set_index('id'))
df = df.sort_values(by=['trainerName','fullName'], ascending=[False,True])
df = df.drop(['status','programmeName','programmeType','apprenticeId',
              'active', 'secondaryTrainerNames', 'expectedEndDate', 
              'learnerReferenceNumber', 'location', 'alertCounts'], 
             axis=1)

