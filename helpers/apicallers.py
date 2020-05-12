import requests, os
from typing import List
import time

def getJsonData(days_ago: int):
    '''days_ago is number of days ago'''


    # PRODUCTION URL 
    receiving_function_url = 'https://europe-west1-optimum-time-233909.cloudfunctions.net/api_private'

    # Set up metadata server request
    metadata_server_token_url = 'http://metadata/computeMetadata/v1/instance/service-accounts/default/identity?audience='

    token_request_url = metadata_server_token_url + receiving_function_url
    token_request_headers = {'Metadata-Flavor': 'Google'}

    end: int = int(time.time() ) *1000  # milliseconds
    start: int = end - (1000 *60 *60 *24 * days_ago)  # milliseconds

    # Fetch the token
    token_response = requests.get(token_request_url, headers=token_request_headers)
    jwt = token_response.content.decode("utf-8")

    request_url = receiving_function_url + "/v1/results?start=" + str(start) + "&end=" + str(end)

    # Provide the token in the request to the receiving function
    receiving_function_headers = {'Authorization': f'bearer {jwt}'}
    function_response = requests.get(request_url, headers=receiving_function_headers)

    return function_response.json()



class MailgunClient:

    def __init__(self, api_key: str = None):
        if api_key is None:
            try:
                self.__api_key__ = os.environ["MAILGUN_API_KEY"]
            except:
                self.__api_key__ = ""
        else:
            self.__api_key__ = api_key

    def send_mail(self,
                  subject: str,
                  text: str,
                  html: str,
                  from_address: str = None,
                  to_addresses: List[str] = None,
                  attachment: str= None,
                  path: str = None) -> bool:

        if from_address is None:
            try:
                from_address = os.environ["FROM_ADDRESS"]
            except:
                return
        to: str = ""
        if to_addresses is None:
            try:
                to = os.environ["TO_ADDRESSES"]
            except:
                return
        else:
             to = ",".join(to_addresses)

        if attachment is None:
            print('No attachments')
        else: 
            if path is None:
                attached_file=("attachment", (attachment, open(attachment, "rb").read()))
            else:
                attached_file=("attachment", (attachment, open(path+attachment, "rb").read()))

        r: requests.Response = requests.post(
            "https://api.eu.mailgun.net/v3/mg.syncvr.tech/messages",
            auth=("api", self.__api_key__),
            files = [attached_file],
            data={
                "from": from_address,
                "to": to,
                "subject": subject,
                "text": text,
                "html": html
            }
        )

        if r.status_code >= 200 and r.status_code < 300:
            return True
        else:
            return False




