import requests, os
from typing import List


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
                  to_addresses: List[str] = None) -> bool:

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

        r: requests.Response = requests.post(
            "https://api.mailgun.net/v3/sandbox792aff55bc5f460fa9f60be2d659a9ce.mailgun.org/messages",
            auth=("api", self.__api_key__),
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

