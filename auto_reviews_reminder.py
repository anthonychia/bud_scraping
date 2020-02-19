from bud import *
import pandas as pd
import numpy as np
import time
import datetime as dt

# Log in to bud, pull data from all active learners
# Store their names and learner ids (NB != apprenticeid)
bud_session = Bud()
bud_session.login()
bud_session.create_request_session()
data = bud_session.get_active_learners()
learners = pd.DataFrame.from_dict(data['items'], orient='columns')
learner_ids = learners.id.tolist()
learner_names = learners.fullName.tolist()

# Create a list of dicts containing a learners name, learning id 
# and all their review ids
learner_info = []
for index, item in enumerate(learner_ids):
    learner_info.append({'name':learner_names[index], 'learner_id':item})

for index, learner in enumerate(learner_info):
    # Fancy loading bar for fun
    print(f'Loading data... {index+1}/{len(learner_info)} [{(int(index/10))*"="}>{int((len(learner_info)-index-1)/10)*"."}]',end='\r')
    data = (bud_session.get_reviews(learner['learner_id']))
    review_ids = []
    for review in data:
        review_ids.append(review['id'])
    learner['review_ids'] = review_ids

# NB: For this basic implementation, look at all reviews and just ignore ones that have been signed. 
# In the future, can just not take the complete review ids from bud.

# These are the paths for each kind of button
# Should bud change things, this will be the only bit of code in need of an update

remind_learner_btn_x = '//*[@id="mainContent"]/div/div/progress-reviews/div/progress-review/learner-page/div/div/section/progress-review-confirmation/section/div/div[2]/progress-review-signatures/bud-signatures/div/div/progress-review-learner-signature/signature/div/bud-signature/div/fieldset/div[2]/div[2]/button'
last_asked_learner = '//*[@id="mainContent"]/div[2]/div/progress-reviews/div/progress-review/learner-page/div/div/section/progress-review-confirmation/section/div/div[2]/progress-review-signatures/bud-signatures/div/div/progress-review-learner-signature/signature/div/bud-signature/div/fieldset/div[2]/div[3]'
remind_manager_btn_x = '//*[@id="mainContent"]/div/div/progress-reviews/div/progress-review/learner-page/div/div/section/progress-review-confirmation/section/div/div[2]/progress-review-signatures/bud-signatures/div/div/progress-review-employer-signature/signature/div/bud-signature/div/fieldset/div[2]/div[2]/button'
last_asked_manager = '//*[@id="mainContent"]/div[2]/div/progress-reviews/div/progress-review/learner-page/div/div/section/progress-review-confirmation/section/div/div[2]/progress-review-signatures/bud-signatures/div/div/progress-review-employer-signature/signature/div/bud-signature/div/fieldset/div[2]/div[3]'


# Below is to check that indeed, a review is complete and not just actually incomplete
# Will require a bit of extra thought however, but this should be trackable with current powerBI capabiities
# learner_has_signed_x = '//*[@id="mainContent"]/div/div/progress-reviews/div/progress-review/learner-page/div/div/section/progress-review-confirmation/section/div/div[2]/progress-review-signatures/bud-signatures/div/div/progress-review-learner-signature/signature/div/bud-signature/div/fieldset/div[2]/div/strong'

# Will record all automated reminders sent 
temp_log = []

# For demonstration purposes, may not want to go through every learner
user_quits = False
print('\n\nType QUIT to exit when prompted for input.')


for lindex,learner in enumerate(learner_info):
    
    
    print(f'Progress: {lindex+1}/{len(learner_info)}')
    learner_name = learner['name']
    learner_id = learner['learner_id']
    
    for review_id in learner['review_ids']:
        url = f'https://web.bud.co.uk/progress-reviews/{learner_id}/review/{review_id}/confirmation'
        bud_session.driver.get(url)


        # If uncommented, this is the 'switch' for full automation
        sign_q = 'Y'


        # THIS MAY VARY FOR SLOWER COMPUTERS. IF RUNNING INTO TROUBLE EXTEND THIS. 
        time.sleep(7)
        
        # Try to remind learner first
        try:
            remind_sign_loc = bud_session.driver.find_element_by_xpath(remind_learner_btn_x)
            
            # Get date of last request
            try:
                print(bud_session.driver.find_element_by_xpath(last_asked_learner).text)
                req_date = bud_session.driver.find_element_by_xpath(last_asked_learner).text
                req_date = req_date[18:].split(',')[0]
                date_obj = dt.datetime.strptime(req_date, '%d %b %Y')
                delta = date_obj - dt.datetime.now()
                if delta.days < -7:
                    print(f'Last reminder sent {delta.days} ago. Send reminder')
                else:
                    print(f'Last reminder sent {delta.days} ago.')
                    break
                
            except:
                print('Not yet requested')
            
            # Uncomment below to semi-automate process
            # sign_q = input('Send reminder to learner? (Captial Y if so.)')
            if sign_q == 'Y':
                remind_sign_loc.click()
                temp_log.append([str(dt.datetime.now()),learner_name,url,'Sent to learner'])
            elif sign_q == 'QUIT':
                user_quits = True
                break
            else:
                pass
        except:
            pass
            # print('No remind learner button found.')
                      
        # Try to remind manager next                 
        try:
            remind_sign_manager_loc = bud_session.driver.find_element_by_xpath(remind_manager_btn_x)
            
            try:
                print(bud_session.driver.find_element_by_xpath(last_asked_manager).text)
                req_date = bud_session.driver.find_element_by_xpath(last_asked_manager).text
                req_date = req_date[18:].split(',')[0]
                date_obj = dt.datetime.strptime(req_date, '%d %b %Y')
                delta = date_obj - dt.datetime.now()
                if delta.days < -7:
                    print(f'Last reminder sent {delta.days} ago. Send reminder')
                else:
                    print(f'Last reminder sent {delta.days} ago.')
                    break
            except:
                print('Not yet requested')

            # Uncomment below to semi-automate process
            # sign_q = input('Send reminder to manager? (Captial Y if so.)')
            if sign_q == 'Y':
                remind_sign_manager_loc.click()
                temp_log.append([str(dt.datetime.now()),learner_name,url,'Sent to manager'])
            elif sign_q == 'QUIT':
                user_quits = True
                break
        except:
            pass
            # print('No remind manager button found.')
        
        # Uncomment to slow process down.
        # next_q = input('Move on?')
    if user_quits:
        break
        
# End the session
bud_session.quit()

# Save log of all actions in this session
now = dt.datetime.now().strftime("%Y%m%d-%H:%M:%S")
print(now)
with open(f'./review_signature_logs/review_reminder_log_{now}.txt', 'w') as f:
    for item in temp_log:
        f.write("%s\n" % ",".join(item))



