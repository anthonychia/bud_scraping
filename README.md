# Bud Scraping via Selenium

### Module:
**bud.py** contains main class `Bud()` which can be used to facilitate automations on [Bud learning platform](https://web.bud.co.uk/).

To start using this module, you can simply import it into your Python script by including this line of code at the start:

```python
from bud import *
```

### Example scripts: 

**bud_scraping.py** - Scraping learner's data from Bud

**bud_reminder.py** - Sending reminders for overdue activities

**bud_notifications.py** *(WIP)* - Connecting Bud with Slack API

**bud_reviews.py** *(WIP)* - Getting progress reviews data for all learners

**bud_activities.py** - Gathering all information on activities 

**auto_review_reminder.py** - Automated learning review signature reminders

### Requirements:

1. Install required Python packages:

>Selenium - `pip install selenium`

2. Download `chromedriver` and put that into the same folder as `bud.py`. Chromedriver can be downloaded from this repo or it can be downloaded from [here](https://chromedriver.chromium.org/downloads)
