from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.chrome.options import Options
import requests
import json
import getpass
import os

class LocalStorage:
    '''
    
    Create class to get all local storage
    
    '''

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

def resource_path(relative_path):
    """ 

    Get absolute path to resource, works for dev and for PyInstaller 
    
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class Bud:
    def __init__(self):
        #Getting login details and logging in through login page via selenium automation
        self.chromedriver_path = resource_path("chromedriver")
        self.chrome_options = Options()
        #chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(self.chromedriver_path, options=self.chrome_options)
        
    def login(self):
        self.url='https://web.bud.co.uk/'
        self.driver.get(self.url)
        self.wait = WebDriverWait(self.driver, 60)
        self.get_login_details()
        self.username_field = self.wait.until(ec.visibility_of_element_located((By.NAME, "Username")))
        self.password_field = self.driver.find_element_by_name('Password')
        self.username_field.clear()
        self.username_field.send_keys(self.user)
        self.password_field.clear()
        self.password_field.send_keys(self.pas)
        self.login_button = self.driver.find_element_by_xpath('//button')
        self.login_button.click()
        self.accept_cookies()
        self.access_token = self.get_token()
        self.cookies = self.get_cookies()
        self.headers = {"accept":"application/json",
                        "authorization":"Bearer "+self.access_token["access_token"],
                        "cache-control":"no-cache",
                        "content-type":"application/json",
                        "pragma":"no-cache",
                        'Connection':'close'}
        
    def accept_cookies(self):
        try:
            self.cookies_button = self.wait.until(ec.visibility_of_element_located((By.XPATH, "//a[@class='optanon-allow-all']")))
            self.cookies_button.click()
        except:
            print('Login failed!')
            self.driver.quit()
            exit()

    def get_login_details(self):
        try:
            self.user = os.environ['BUD_USER']
            self.pas = os.environ['BUD_PASS']
        except:
            self.user = input('Bud username: ')
            self.pas = getpass.getpass('Bud password: ')

    def get_token(self):
        #Obtaining Bearer access token from local storage in Chrome browser
        self.storage = LocalStorage(self.driver)
        return json.loads(self.storage.get('bud.user:https://auth.bud.co.uk/:bud'))

    def get_cookies(self):
        #Obtaining cookies after logged in
        return self.driver.get_cookies()

    def create_request_session(self):
        self.s = requests.Session()
        #Attaching cookies to the request session
        for cookie in self.cookies:
            self.s.cookies.set(cookie['name'], cookie['value'])
    
    def get_account_info(self):
        return self.s.get("https://live-account-api.bud.co.uk/account/profile", headers=self.headers).json()

    def get_active_learners(self):
        return self.s.get("https://live-learnermanagement-api.bud.co.uk/learner-management/active"+"?pageSize=1000&statuses=1", headers=self.headers).json()

    def get_learning_plans(self, trainer_id):
        return self.s.post("https://live-portfolio-learning-api.bud.co.uk/stats/summaries", headers=self.headers, data=trainer_id).json()

    def get_learning_plan(self, learner_id):
        return self.s.get("https://live-portfolio-learning-api.bud.co.uk/learningplan/"+learner_id, headers=self.headers).json()
    
    def send_message(self, learner_id, activity_id, message):
        self.driver.get("https://web.bud.co.uk/learningportal/assessor/plan/"+learner_id+"/activity/"+activity_id+"/submissions/")
        self.submit_button = self.wait.until(ec.visibility_of_element_located((By.XPATH, "//input[@value='Submit work / message']")))
        self.submit_button.click()
        self.textarea = self.driver.find_element_by_xpath("//textarea")
        self.textarea.send_keys(message)
        self.submit_button = self.driver.find_element_by_xpath("//button[@type='submit']")
        self.submit_button.click()    

    def quit(self):
        self.driver.quit()
