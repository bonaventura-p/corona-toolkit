
import requests
import time

def getJsonData(days_ago: int):
    '''days_ago is number of days ago'''
    # Make sure to replace variables with appropriate values
    receiving_function_url = 'https://europe-west1-syncvr-dev.cloudfunctions.net/api_private'

    # Set up metadata server request
    metadata_server_token_url = 'http://metadata/computeMetadata/v1/instance/service-accounts/default/identity?audience='

    token_request_url = metadata_server_token_url + receiving_function_url
    token_request_headers = {'Metadata-Flavor': 'Google'}

    end: int = int(time.time() ) *1000  # milliseconds
    start: int = end - (100 0 *6 0 *6 0 *24 * days_ago)  # milliseconds

    # Fetch the token
    token_response = requests.get(token_request_url, headers=token_request_headers)
    jwt = token_response.content.decode("utf-8")

    request_url = receiving_function_url + "/v1/results?start=" + str(start) + "&end=" + str(end)

    # Provide the token in the request to the receiving function
    receiving_function_headers = {'Authorization': f'bearer {jwt}'}
    function_response = requests.get(request_url, headers=receiving_function_headers)

    return function_response.json()