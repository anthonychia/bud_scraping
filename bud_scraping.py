import getpass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.chrome.options import Options

import pandas as pd
import pprint
import requests
import time
import json
import os, sys, inspect    

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

chromedriver_path = resource_path("chromedriver")
chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(chromedriver_path, options=chrome_options)
url='https://web.bud.co.uk/'
user = input('Bud username: ')
pas = getpass.getpass('Bud password: ')
driver.get(url)
wait = WebDriverWait(driver, 10)
username = wait.until(ec.visibility_of_element_located((By.NAME, "username")))
#username = driver.find_element_by_name('username')
username.clear()
username.send_keys(user)
password = driver.find_element_by_name('password')
password.clear()
password.send_keys(pas)
login = driver.find_element_by_id('login')
login.click()
try:
    accept_cookies = wait.until(ec.visibility_of_element_located((By.XPATH, "//a[@class='optanon-allow-all']")))
    accept_cookies.click()
except:
    print('Login failed!')
    exit()
#time.sleep(5)
cookies = driver.get_cookies()
storage = LocalStorage(driver)
access_token = json.loads(storage.get('bud.user:https://auth.bud.co.uk/:bud'))
#print(access_token['access_token'])
driver.quit()

#for i in cookies:
#    print(i)

s = requests.Session()
for cookie in cookies:
    s.cookies.set(cookie['name'], cookie['value'])
headers = {"accept":"application/json","authorization":"Bearer "+access_token["access_token"],"cache-control":"no-cache","content-type":"application/json","pragma":"no-cache"}
#response = s.get("https://live-portfolio-learning-api.bud.co.uk/learningplan/currentlylearning", headers = headers)
response = s.get("https://live-account-api.bud.co.uk/account/profile", headers=headers)
data = response.json()
account_id = data['id']

response = s.post("https://live-portfolio-learning-api.bud.co.uk/stats/summaries", headers=headers, data='["%s"]'%(account_id))
data = response.json()
fullname = [i['learner']['foreName']+' '+i['learner']['surname'] for i in data[account_id]]
id = [i['id'] for i in data[account_id]]
#df['name'] = df['learner'].apply(lambda x: x['fullName'])
df = pd.DataFrame({'fullName':fullname, 'id':id})

def find_evidence_form(files):
    for file in files:
        if any(x in file['fileName'] for x in ['Evidence', 'evidence']):
            return file['fileName']

monthly_counts = pd.DataFrame()
for id in df['id']:
    response = s.get("https://live-portfolio-learning-api.bud.co.uk/learningplan/"+id, headers=headers)
    data = response.json()
    activities_df = pd.DataFrame(columns=['id','name','date','filename'])
    activities = [[i['id'],i['name']] for i in data['activities'] if i['dueDate']]
    for activity_id, activity_name in activities:
        response = s.get("https://live-portfolio-learning-api.bud.co.uk/learningplan/"+id+"/activity/"+activity_id, headers=headers)
        data = response.json()
        for i in data['submissions']:
            if (i['status'] == 3): # 0: no file , 2: marked as incomplete, 3: marked as complete
                submissionDate = i['submissionDate']
                fileName = find_evidence_form(i['files']) # search through files for evidence form in case of multiple file submission.
                activities_df.loc[len(activities_df)] = [activity_id, activity_name, submissionDate, fileName]
    activities_df['month'] = pd.to_datetime(activities_df['date']).dt.strftime('%m-%Y')
    if not activities_df.empty:
        activities_df.loc[activities_df['name'].str.lower().str.contains('call'),'type'] = 'Call'
        activities_df.loc[activities_df['name'].str.lower().str.contains('workshop|practice', regex=True),'type'] = 'Bud'
        activities_df.loc[activities_df['name'].str.lower().str.contains('project', regex=True),'type'] = 'Project'
        single_count = activities_df.groupby(['month','type']).size().to_frame().transpose()
    else:
        single_count = pd.DataFrame()
    single_count.columns = single_count.columns.map('_'.join)
    single_count['id'] = id
    monthly_counts = pd.concat([monthly_counts,single_count], sort=False)

monthly_counts = monthly_counts[sorted(monthly_counts.columns)]
df = df.set_index('id').join(monthly_counts.set_index('id'))
df = df.sort_values(by='fullName')
#df = df.drop(['activityStats', 'alertCounts', 'apprenticeId', 'employer', 'learner', 'programme', 'status'], axis=1)

print(df.head())
print(os.path.join(application_path,"tracker.csv"))
df.to_csv(os.path.join(application_path,"tracker.csv"))
    
#https://live-portfolio-learning-api.bud.co.uk/stats/summaries
#https://live-application-api.bud.co.uk/stats/summaries
#https://live-portfolio-learning-api.bud.co.uk/stats/summaries
#https://live-learnermanagement-api.bud.co.uk/stats/summaries

#learning-id vs leaner-id
#https://live-portfolio-learning-api.bud.co.uk/learningplan/currentlylearning
#https://live-portfolio-learning-api.bud.co.uk/learningplan/a40fd16e-1ac6-4797-a822-aa4c010a277d
#https://live-portfolio-learning-api.bud.co.uk/learningplan/a40fd16e-1ac6-4797-a822-aa4c010a277d/activity/7beede4d-d36e-5032-ab96-be52b9da81b9

#https://live-account-api.bud.co.uk/account/profile
