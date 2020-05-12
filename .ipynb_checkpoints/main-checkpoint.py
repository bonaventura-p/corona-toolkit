# [cloud function daily corona update ] "

from helpers.aggregators import daily_overview

import firebase_admin

admin = firebase_admin.initialize_app()

def cloud_function_daily_corona_update(event, context):
    '''TRIGGER IS PUB/SUB MESSAGE WITH DAILY SCHEDULE'''
    print("Generating daily aggregation!")
    daily_overview()



## 1. automatically triggered by pubsub

## deploy as cloud function, remember to add api key and sender as environment variables



