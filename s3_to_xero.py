import logging
from os.path import basename

from src.scripts.utils import *
import json
import requests
import webbrowser
import base64

os.makedirs(get_full_path("../../data/"), exist_ok=True)
client_id = '180D6F4D20BC4E2883770FA478C5B8A0'
client_secret = 'j-8iO8-i8pDAcYvYgMOD4iQQtsm82sWcqpPfLyCXQDsK1GpF'
redirect_url = 'https://xero.com/'
scope = 'offline_access accounting.transactions files files.read'
# scope = 'files'
b64_id_secret = base64.b64encode(bytes(client_id + ':' + client_secret, 'utf-8')).decode('utf-8')


def xero_auth():
    # Step1. Send a user to authorize your app
    auth_url = ('''https://login.xero.com/identity/connect/authorize?''' +
                '''response_type=code''' +
                '''&client_id=''' + client_id +
                '''&redirect_uri=''' + redirect_url +
                '''&scope=''' + scope +
                '''&state=123''')
    webbrowser.open_new(auth_url)

    # Step2. Users are redirected back to you with a code
    auth_res_url = input('What is the response URL? ')
    start_number = auth_res_url.find('code=') + len('code=')
    end_number = auth_res_url.find('&scope')
    auth_code = auth_res_url[start_number:end_number]
    print(f'Extracted Auth code ==> {auth_code}')
    print('\n')

    # Step3. Exchange the code
    exchange_code_url = 'https://identity.xero.com/connect/token'
    response = requests.post(exchange_code_url,
                             headers={
                                 'Authorization': 'Basic ' + b64_id_secret
                             },
                             data={
                                 'grant_type': 'authorization_code',
                                 'code': auth_code,
                                 'redirect_uri': redirect_url
                             })
    json_response = response.json()
    print(f'Authorization Code response ==> {json_response}')
    print('\n')
    # Step4. Receive your tokens
    return [json_response['access_token'], json_response['refresh_token']]


# Step5. Check the full set of tenants you've been authorized to access
def XeroTenants(access_token):
    connections_url = 'https://api.xero.com/connections'
    response = requests.get(connections_url,
                            headers={
                                'Authorization': 'Bearer ' + access_token,
                                'Content-Type': 'application/json'
                            })
    json_response = response.json()
    print(f'List of Organizations/tenants ==> {json_response}')
    print('\n')
    json_dict = None
    for tenants in json_response:
        json_dict = tenants
    return json_dict['tenantId']


# Step6.1 Refreshing access tokens
def XeroRefreshToken(refresh_token):
    token_refresh_url = 'https://identity.xero.com/connect/token'
    response = requests.post(token_refresh_url,
                             headers={
                                 'Authorization': 'Basic ' + b64_id_secret,
                                 'Content-Type': 'application/x-www-form-urlencoded'
                             },
                             data={
                                 'grant_type': 'refresh_token',
                                 'refresh_token': refresh_token
                             })
    json_response = response.json()
    print(f'Refreshed token ==> {json_response}')
    print('\n')

    new_refresh_token = json_response['refresh_token']

    rt_file = open(get_full_path("../../data/refresh_token.txt"), 'w')
    rt_file.write(new_refresh_token)
    rt_file.close()

    return [json_response['access_token'], json_response['refresh_token']]


# Step6.2 Call the API to get Files list
def get_files_xero():
    old_refresh_token = open(get_full_path("../../data/refresh_token.txt"), 'r').read()
    new_tokens = XeroRefreshToken(old_refresh_token)
    xero_tenant_id = XeroTenants(new_tokens[0])

    get_url = 'https://api.xero.com/files.xro/1.0/Files/'
    response = requests.get(get_url,
                            headers={
                                'Authorization': 'Bearer ' + new_tokens[0],
                                'Xero-tenant-id': xero_tenant_id,
                                'Accept': 'application/json'
                            })
    json_response = response.json()
    print(f'List of files in FilesAPI ==>{json_response}')
    print('\n')

    xero_output_json = open(get_full_path("../../data/xero_output.json"), 'w')
    json.dump(response.text, xero_output_json)
    xero_output_json.close()


# I'm having problem here in uploading files
def upload_file_xero():
    old_refresh_token = open(get_full_path("../../data/refresh_token.txt"), 'r').read()
    new_tokens = XeroRefreshToken(old_refresh_token)
    print(f'New Token Dict ==> {new_tokens}')
    xero_tenant_id = XeroTenants(new_tokens[0])
    print(f'xero_tenant_id ==> {xero_tenant_id}')
    # post_url = 'https://api.xero.com/files.xro/1.0/Files/'
    post_url = 'https://api.xero.com/files.xro/1.0//Files'
    pay_part = [{"Content-Disposition": 'form-data; name=Xero; filename=icon-small.png', "Content-Type": "image/png"}]
    # I'm here
    # I need to all payload in the request with content type=application/pdf
    '''----------[RANDOM_STRING_BOUNDARY]
Content-Disposition: form-data; name="4223a011.pdf"; filename="4223a011.pdf"
Content-Type: application/pdf

{RAW_FILE_CONTENT}
----------[RANDOM_STRING_BOUNDARY]--'''
    datad = {'Content-Disposition': 'form-data; name=in_test_upload.pdf; filename=in_test_upload.pdf',
             'Content-type': 'application/pdf; boundary=JLQPFBPUP0'
             }
    with open(get_full_path("../../data/in_test_upload.pdf"), 'rb') as f:
        contents = f.read()
        files = {'file': contents}

        response = requests.post(post_url,
                                 headers={
                                     'Authorization': 'Bearer ' + new_tokens[0],
                                     'Xero-tenant-id': xero_tenant_id,
                                     # 'Accept': 'application/json',
                                     'Content-type': 'multipart/form-data; boundary=JLQPFBPUP0',
                                     'Content-Length': '1068',
                                     'User-Agent': 'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1866.237 Safari/537.36',
                                     # "accept-encoding": "gzip, deflate, br"
                                 },
                                 files=files,
                                 data=datad
                                 )
        json_response = response.json()
        print(f'Uploading Responsoe ==> {json_response}')
        print(f'Uploading Responsoe ==> {response}')
        from requests_toolbelt import MultipartEncoder

        fields = {
            'Content-type': 'multipart/form-data'
        }

        m = MultipartEncoder(fields, boundary='JLQPFBPUP0')
        head = {'Authorization': 'Bearer ' + new_tokens[0],
                'Xero-tenant-id': xero_tenant_id,
                'Content-Type': m.content_type,
                'Content-Length': '1068'
                }
        second_response = requests.post(post_url, headers=head, files=files)

        print(f'Second Uploading Responsoe ==> {second_response}')

    xero_output_json = open(get_full_path("../../data/upload_xero_output.json"), 'w')
    json.dump(response.text, xero_output_json, ensure_ascii=False, indent=4)
    xero_output_json.close()


def start(event, context):
    logging.info(f'event is ==> {event}')
    logging.info(f'context is ==>{context}')
    old_tokens = xero_auth()
    print(f'Old Auth Token ==>{old_tokens}')
    XeroRefreshToken(old_tokens[1])
    get_files_xero()
    upload_file_xero()


if __name__ == "__main__":
    start(event='hello from fargate==>task==>container!', context=None)
