import getpass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.chrome.options import Options

import pandas as pd
import numpy as np
import pprint
import requests
import time
import json
import os, sys, inspect    
import datetime as dt

'''
Create class to get all local storage
'''
class LocalStorage:
    def __init__(self, driver) :
        self.driver = driver

    def __len__(self):
        return self.driver.execute_script("return window.localStorage.length;")

    def items(self) :
        return self.driver.execute_script( \
            "var ls = window.localStorage, items = {}; " \
            "for (var i = 0, k; i < ls.length; ++i) " \
            "  items[k = ls.key(i)] = ls.getItem(k); " \
            "return items; ")

    def keys(self) :
        return self.driver.execute_script( \
            "var ls = window.localStorage, keys = []; " \
            "for (var i = 0; i < ls.length; ++i) " \
            "  keys[i] = ls.key(i); " \
            "return keys; ")

    def get(self, key):
        return self.driver.execute_script("return window.localStorage.getItem(arguments[0]);", key)

    def set(self, key, value):
        self.driver.execute_script("window.localStorage.setItem(arguments[0], arguments[1]);", key, value)

    def has(self, key):
        return key in self.keys()

    def remove(self, key):
        self.driver.execute_script("window.localStorage.removeItem(arguments[0]);", key)

    def clear(self):
        self.driver.execute_script("window.localStorage.clear();")

    def __getitem__(self, key) :
        value = self.get(key)
        if value is None :
          raise KeyError(key)
        return value

    def __setitem__(self, key, value):
        self.set(key, value)

    def __contains__(self, key):
        return key in self.keys()

    def __iter__(self):
        return self.items().__iter__()

    def __repr__(self):
        return self.items().__str__()


if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
elif __file__:
    application_path = os.path.dirname(__file__)

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

#Getting login details and logging in through login page via selenium automation
chromedriver_path = resource_path("chromedriver")
chrome_options = Options()
#chrome_options.add_argument("--headless")
driver = webdriver.Chrome(chromedriver_path, options=chrome_options)
url='https://web.bud.co.uk/'
user = input('Bud username: ')
pas = getpass.getpass('Bud password: ')
driver.get(url)
wait = WebDriverWait(driver, 60)
username = wait.until(ec.visibility_of_element_located((By.NAME, "Username")))
#username = driver.find_element_by_name('username')
username.clear()
username.send_keys(user)
password = driver.find_element_by_name('Password')
password.clear()
password.send_keys(pas)
login = driver.find_element_by_xpath('//button')
login.click()
try:
    accept_cookies = wait.until(ec.visibility_of_element_located((By.XPATH, "//a[@class='optanon-allow-all']")))
    accept_cookies.click()
except:
    print('Login failed!')
    exit()

#Obtaining cookies after logged in
cookies = driver.get_cookies()
storage = LocalStorage(driver)

#Obtaining Bearer access token from local storage in Chrome browser
access_token = json.loads(storage.get('bud.user:https://auth.bud.co.uk/:bud'))
#print(access_token['access_token'])
#driver.quit()

#GET REQUESTS and saving responses 
s = requests.Session()
for cookie in cookies:
    s.cookies.set(cookie['name'], cookie['value'])
headers = {"accept":"application/json","authorization":"Bearer "+access_token["access_token"],"cache-control":"no-cache","content-type":"application/json","pragma":"no-cache"}
#response = s.get("https://live-portfolio-learning-api.bud.co.uk/learningplan/currentlylearning", headers = headers)
response = s.get("https://live-account-api.bud.co.uk/account/profile", headers=headers)
data = response.json()
account_id = data['id']
accountName = data['firstName']

#response = s.post("https://live-portfolio-learning-api.bud.co.uk/stats/summaries", headers=headers)
response = s.get("https://live-learnermanagement-api.bud.co.uk/learner-management/active"+"?pageSize=1000&statuses=1", headers=headers)
data = response.json()
#fullname = [i['learner']['foreName']+' '+i['learner']['surname'] for i in data[account_id]]
#id = [i['id'] for i in data[account_id]]
#df['name'] = df['learner'].apply(lambda x: x['fullName'])
main_df = pd.DataFrame.from_dict(data['items'], orient='columns')

#list_of_cohorts = df['programmeName'].unique()
#print("=====================================")
#print("        List of Cohorts")
#print("=====================================")
#for i in range(len(list_of_cohorts)):
#    print("%i: %s\n"%(i,list_of_cohorts[i]))

#selected_cohorts = [ list_of_cohorts[int(i)] for i in input("Selecting cohort(s) \n* you can select multiple cohorts by entering e.g \"1,2,3\" * \nPlease Enter Selection: ").split(",") ]
#selected_cohorts = list_of_cohorts
#print(selected_cohorts)

#df = df[df['programmeName'].isin(selected_cohorts)]
df = main_df[main_df['trainerName']=='Anthony Chia'] #Change this to the primary trainer's name

if os.path.isfile('reminderList.csv'):
    save_df = pd.read_csv('reminderList.csv')
    df = df.merge(save_df, on='id', how='left')
    df = df[df['reminderDate'].isna()]
else:
    save_df = pd.DataFrame(columns=['id','reminderDate'])

for id in df['id'][:5]:
    response = s.get("https://live-portfolio-learning-api.bud.co.uk/learningplan/"+id, headers=headers)
    data = response.json()
    learner = data['learner']['foreName']
    activities_df = pd.DataFrame(columns=['id','name','date','filename'])
    activities = [[i['id'],i['name'], i['dueDate']] for i in data['activities'] if ~i['hasSubmissions'] & i['isOverdue'] & ~i['isExempt']]
    save_df.loc[len(save_df)] = [id, dt.datetime.today()]
    save_df.to_csv('reminderList.csv', index=False)
    for activity_id, activity_name, dueDate in activities:
        overdue = dt.datetime.now() - dt.datetime.strptime((dueDate[:24]).strip(), "%Y-%m-%dT%H:%M:%SZ") 
        if dueDate:
            if( overdue < dt.timedelta(days=28)): continue
        if any(x in activity_name.lower() for x in ['project', 'hackathon:', 'hackathon', 'science']):
            continue
        url = "https://web.bud.co.uk/learningportal/assessor/plan/"+id+"/activity/"+activity_id+"/submissions/"
        driver.get(url)
        fopen = open('./messages/practice_workshop_reminder.txt','r')
        message = ''.join([line for line in fopen])
        message = message%(learner, overdue.days, accountName)
        submitButton = wait.until(ec.visibility_of_element_located((By.XPATH, "//input[@value='Submit work / message']")))
        submitButton.click()
        textArea = driver.find_element_by_xpath("//textarea")
        textArea.send_keys(message)
        submitButton = driver.find_element_by_xpath("//button[@type='submit']")
        #submitButton.click()
        time.sleep(1)

#driver.quit()
