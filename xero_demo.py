import base64
import logging
import webbrowser
from os.path import abspath
from urllib.parse import quote, urlencode

import requests

CLIENT_ID = '180D6F4D20BC4E2883770FA478C5B8A0'
CLIENT_SECRET = 'j-8iO8-i8pDAcYvYgMOD4iQQtsm82sWcqpPfLyCXQDsK1GpF-qcLLB8W7qBvYQiqkIcCOpCwKi'
AUTH_SCOPES = 'offline_access accounting.transactions files files.read'
AUTH_STATE = 123
REDIRECT_URL = 'https://xero.com/'

logging.basicConfig(
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    level=logging.DEBUG,
)


def urlparams(*_, **kwargs):
    safe_args = {k: v for k, v in kwargs.items() if v is not None}
    if safe_args:
        return '?{}'.format(urlencode(safe_args, quote_via=quote))
    return ''


def build_auth_token():
    auth_str = bytes(f'{CLIENT_ID}:{CLIENT_SECRET}', 'utf-8')
    return base64.b64encode(auth_str).decode('utf-8')


def build_auth_url():
    auth_url = 'https://login.xero.com/identity/connect/authorize'
    params = urlparams(
        response_type='code',
        client_id=CLIENT_ID,
        redirect_uri=REDIRECT_URL,
        scope=AUTH_SCOPES,
        state=AUTH_STATE,
    )

    return f'{auth_url}{params}'


def xero_auth():
    auth_url = build_auth_url()
    webbrowser.open_new(auth_url)
    logging.info(f'auth url ==> {auth_url}')

    auth_res_url = input('What is the response URL? ')
    start_number = auth_res_url.find('code=') + len('code=')
    end_number = auth_res_url.find('&scope')
    auth_code = auth_res_url[start_number:end_number]
    logging.info(f'extracted auth code ==> {auth_code}')

    headers = {'Authorization': f'Basic {build_auth_token()}'}
    data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': REDIRECT_URL,
    }
    exchange_code_url = 'https://identity.xero.com/connect/token'
    response = requests.post(exchange_code_url, headers=headers, data=data)

    assert response.status_code == 200
    json_response = response.json()
    logging.info(f'authorization code response ==> {json_response}')

    return {
        'access_token': json_response['access_token'],
        'refresh_token': json_response['refresh_token'],
    }


def xero_tenants(access_token):
    connections_url = 'https://api.xero.com/connections'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    response = requests.get(connections_url, headers=headers)
    json_response = response.json()
    logging.info(f'list of organizations/tenants ==> {json_response}')

    assert len(json_response) > 0
    tenant = json_response[0]  # type: dict
    return tenant.get('tenantId', None)


def xero_upload_file(filename, token):
    access_token = token.get('access_token')

    tenant_id = xero_tenants(access_token)
    assert tenant_id is not None
    logging.info(f'tenant_id ==> {tenant_id}')

    post_url = 'https://api.xero.com/files.xro/1.0/Files'
    files = {'filename': open(filename, 'rb')}
    values = {'name': 'Xero2'}

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Xero-tenant-id': f'{tenant_id}',
        'Accept': 'application/json',
    }

    response = requests.post(post_url, headers=headers, files=files, data=values)

    assert response.status_code == 201
    logging.info(f'upload response ==> {response.json()}')


def start(event, context=None):
    logging.info(f'event is ==> {event}')
    logging.info(f'context is ==> {context}')

    token = xero_auth()
    logging.info(f'old auth token ==> {token}')

    filename = abspath('./Barnprinter2.png')
    xero_upload_file(filename, token)


if __name__ == "__main__":
    start(event='hello from fargate==>task==>container!')
