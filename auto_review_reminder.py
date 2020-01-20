from bud import *
import pandas as pd
import numpy as np
import time
import datetime as dt

# **** VERSION 1.0 16th January *****
# This implementation is semi-automated. Still requires a user to enter 'Y' to send a reminder.
# This of course can easily be removed. 
# Future work: identify reviews that are not yet ready for signatures (i.e. missing comment sections)
# or just remove complete activities from activity selection from bud site. Also, could change bud module altogether
# so that this script can just reference a local file, rather than repeatedly pull from the site.
# Could also read when the last review was sent, and only send another reminder if a certain delta t is met
# Currently waits 4 seconds on each page. Could perhaps speed up the whole script by using a more sophesticated
# method - however not every review has the same buttons, so waiting for one to appear will not do
# For a prettier log file, turn list into a dataframe and then save as csv to file
# ***********************************

# To access all learner reviews, use this login
user = 'info@decoded.com'
password = 'Letmein123'

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
remind_manager_btn_x = '//*[@id="mainContent"]/div/div/progress-reviews/div/progress-review/learner-page/div/div/section/progress-review-confirmation/section/div/div[2]/progress-review-signatures/bud-signatures/div/div/progress-review-employer-signature/signature/div/bud-signature/div/fieldset/div[2]/div[2]/button'

# Below is to check that indeed, a review is complete and not just actually incomplete
# Will require a bit of extra thought however, but this should be trackable with current powerBI capabiities
# learner_has_signed_x = '//*[@id="mainContent"]/div/div/progress-reviews/div/progress-review/learner-page/div/div/section/progress-review-confirmation/section/div/div[2]/progress-review-signatures/bud-signatures/div/div/progress-review-learner-signature/signature/div/bud-signature/div/fieldset/div[2]/div/strong'


# Will record all automated reminders sent 
temp_log = []

# For demonstration purposes, may not want to go through every learner
user_quits = False
print('\n\nType QUIT to exit when prompted for input.')


for learner in learner_info:

    learner_name = learner['name']
    learner_id = learner['learner_id']
    
    for review_id in learner['review_ids']:
        url = f'https://web.bud.co.uk/progress-reviews/{learner_id}/review/{review_id}/confirmation'
        bud_session.driver.get(url)
        
        # THIS MAY VARY FOR SLOWER COMPUTERS. IF RUNNING INTO TROUBLE EXTEND THIS. 
        time.sleep(4)
        
        # Try to remind learner first
        try:
            remind_sign_loc = bud_session.driver.find_element_by_xpath(remind_learner_btn_x)
            sign_q = input('Send reminder to learner? (Captial Y if so.)')
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
            sign_q = input('Send reminder to manager? (Captial Y if so.)')
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




