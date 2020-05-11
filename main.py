# [cloud function daily corona update ] "

from helpers.aggregation import daily_overview

import firebase_admin

admin = firebase_admin.initialize_app()

def cloud_function_daily_aggregation(event, context):
    '''TRIGGER IS PUB/SUB MESSAGE WITH DAILY SCHEDULE'''
    print("Generating daily aggregation!")
    daily_overview()



## 1. automatically triggered by pubsub

## 2. reading data from firestore dictionary




## 3. creating template

## 4. sending email

## 2-3-4 for all devices (with different emails!!)

