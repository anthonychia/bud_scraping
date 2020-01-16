from bud import *
import pandas as pd
import numpy as np
import time
import os, sys, inspect    
import datetime as dt


def load_savefile(filename):
    if os.path.isfile(filename):
        return pd.read_csv(filename)
    else:
        return pd.DataFrame(columns=['id','reminderDate'])
    

if __name__ == '__main__':
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
    df = pd.DataFrame.from_dict(data['items'], orient='columns')

    #Loading save file if one exists
    save_df = load_savefile('reminderList.csv')
    df = df.merge(save_df, on='id', how='left')
    df = df[df['reminderDate'].isna()]

    #Looping through each learner and each activity
    for learner_id in df['id']:
        #Getting learning plan for each learner
        data = bud_session.get_learning_plan(learner_id)
        learner_name = data['learner']['foreName']
        trainer_name = data['assessor']['foreName']

        #Filtering down the activities to ones that are overdue without submissions and not exempted
        activities = [[i['id'], i['name'], i['dueDate']] for i in data['activities'] if ~i['hasSubmissions'] & i['isOverdue'] & ~i['isExempt']]

        #Save progress to file
        save_df.loc[len(save_df)] = [learner_id, dt.datetime.today()]
        save_df.to_csv('reminderList.csv', index=False)

        #Looping through all activities
        for activity_id, activity_name, due_date in activities:
            #Ignore project, hackathon and data science in a day
            ignore_list = ['project', 'hackathon:', 'hackathon', 'science', 'review']
            if any(x in activity_name.lower() for x in ignore_list): 
                continue
            
            #Calculate the number of days activity is overdue
            overdue = dt.datetime.now() - dt.datetime.strptime((due_date[:24]).strip(), "%Y-%m-%dT%H:%M:%SZ")
            if due_date:
                if( overdue < dt.timedelta(days=28)): continue

            #Sending reminder message
            fopen = open('./messages/practice_workshop_reminder.txt','r')
            message = ''.join([line for line in fopen])
            message = message%(learner_name, overdue.days, trainer_name)
            bud_session.send_message(learner_id, activity_id, message)
            time.sleep(1+np.random.rand())

    #Remove save file if process is complete
    os.remove('reminderList.csv')
    bud_session.quit()
