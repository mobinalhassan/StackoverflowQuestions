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
    # files = {'file': open(get_full_path("../../data/in_test_upload.pdf"), 'rb'),'Content-Type':'application/pdf','Name':'in_test_upload.pdf'}
    # files = {'file': open(get_full_path("../../data/in_test_upload.pdf"), 'rb')}
    pay_part = [{"Content-Disposition": 'form-data; name=Xero; filename=icon-small.png', "Content-Type": "image/png"}]
    # files = {'file': open(get_full_path("../../data/in_test_upload.pdf"), 'rb')}
    # files = {'file': open(get_full_path("../../data/Data Mining1.png"), 'rb')} 'Content-Disposition': 'form-data; name=in_test_upload.pdf; filename=in_test_upload.pdf',
    # files = {'file': ('in_test_upload.pdf', open(get_full_path("../../data/in_test_upload.pdf"), 'rb'), 'application/pdf', {})}
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

    # xero_output = open(get_full_path("../../data/up_loadxero_output.txt"), 'w')
    # xero_output.write(response.text)
    # xero_output.close()
    xero_output_json = open(get_full_path("../../data/upload_xero_output.json"), 'w')
    json.dump(response.text, xero_output_json, ensure_ascii=False, indent=4)
    xero_output_json.close()


import requests
import json
import base64


def encode(data: bytes):
    """
    Return base-64 encoded value of binary data.
    """
    return base64.b64encode(data)


def decode(data: str):
    """
    Return decoded value of a base-64 encoded string.
    """
    return base64.b64decode(data.encode())


def get_pdf_data(filename):
    """
    Open pdf file in binary mode,
    return a string encoded in base-64.
    """
    with open(filename, 'rb') as file:
        return encode(file.read())


def send_pdf_data(filename_list, encoded_pdf_data):
    data = {}
    # *Put whatever you want in data dict*
    # Create content dict.
    content = [dict([("name", filename), ("data", pdf_data)])
               for (filename, pdf_data) in zip(filename_list, encoded_pdf_data)]
    data["content"] = content
    token='eyJhbGciOiJSUzI1NiIsImtpZCI6IjFDQUY4RTY2NzcyRDZEQzAyOEQ2NzI2RkQwMjYxNTgxNTcwRUZDMTkiLCJ0eXAiOiJKV1QiLCJ4NXQiOiJISy1PWm5jdGJjQW8xbkp2MENZVmdWY09fQmsifQ.eyJuYmYiOjE2MTg1Nzk3NjQsImV4cCI6MTYxODU4MTU2NCwiaXNzIjoiaHR0cHM6Ly9pZGVudGl0eS54ZXJvLmNvbSIsImF1ZCI6Imh0dHBzOi8vaWRlbnRpdHkueGVyby5jb20vcmVzb3VyY2VzIiwiY2xpZW50X2lkIjoiMTgwRDZGNEQyMEJDNEUyODgzNzcwRkE0NzhDNUI4QTAiLCJzdWIiOiI0Mzg1ZTIxYjExMTQ1ZGIwYmIyMGVlOWZlYzE5NDM2NyIsImF1dGhfdGltZSI6MTYxODU3NzgzNiwieGVyb191c2VyaWQiOiI1ZjcwZTQzMy0yZjczLTQ1OGUtYWFhYy05OTYxNTNjZjUxYTYiLCJnbG9iYWxfc2Vzc2lvbl9pZCI6Ijc2NjY2NjE0NWI2NDRkYTA4N2RkMzMxYzQ4Y2U0Y2NhIiwianRpIjoiNzVlY2VkOTIxNmU0YjZjNTNiMDNmNmMxNTNlZWFmZWIiLCJhdXRoZW50aWNhdGlvbl9ldmVudF9pZCI6ImQxMTYzYWJhLTZiYjgtNGQ4Ny1iNWZmLTM2ZThlODVkMzlmYyIsInNjb3BlIjpbImVtYWlsIiwicHJvZmlsZSIsIm9wZW5pZCIsImFjY291bnRpbmcucmVwb3J0cy5yZWFkIiwiYWNjb3VudGluZy5hdHRhY2htZW50cy5yZWFkIiwiZmlsZXMiLCJwcm9qZWN0cyIsImFjY291bnRpbmcuc2V0dGluZ3MiLCJhY2NvdW50aW5nLnNldHRpbmdzLnJlYWQiLCJhY2NvdW50aW5nLmF0dGFjaG1lbnRzIiwiZmlsZXMucmVhZCIsImFjY291bnRpbmcudHJhbnNhY3Rpb25zIiwiYWNjb3VudGluZy5qb3VybmFscy5yZWFkIiwiYWNjb3VudGluZy50cmFuc2FjdGlvbnMucmVhZCIsImFzc2V0cyIsImFjY291bnRpbmcuY29udGFjdHMiLCJhY2NvdW50aW5nLmNvbnRhY3RzLnJlYWQiLCJvZmZsaW5lX2FjY2VzcyJdfQ.sV_4lhlp1iwjkLy_IdGFeE7E9JAWnSQQwrMDL5zo9fBuK55H0y6zKJXuieu433FtJk5olrg-wcIr-v5nirg4Nx1LK9C9QSKXifYJdwL_K805zQfa1xUjqZrOTjtWjQh6d1Ac_4D_rryGWMbjUQJxCdbgRDQkr5H2EX8jQ5av3-dBePh-z5hYUN_RgeyehyLtG52CQwvf_dPly3-u0lNR-AL-N7oysXTU281kK0NiOh0DpJRJlQLm_tJuzoxOORfh534mpUNA1HhoyEdbN01Zm-kAyHyACjcQ6LVyjiksD8mJC7-XpvXRy_jBAdn44JFTojkn2AdKriKj2hg_B8Zgkw'
    data = json.dumps(data)  # Convert it to json.
    requests.post("https://api.xero.com/files.xro/1.0//Files",
                  headers={
                      'Authorization': f'Bearer {token}',
                      'Xero-tenant-id': 'd2210681-283f-4bf7-8d82-b3fcba5643c1',
                      # 'Accept': 'application/json',
                      'Content-type': 'multipart/form-data; boundary=JLQPFBPUP0',
                      'Content-Length': '1068',
                      'User-Agent': 'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1866.237 Safari/537.36',
                      # "accept-encoding": "gzip, deflate, br"
                  },
                  data=data)


def main():
    filename_list = ["/home/mobin/PycharmProjects/s3toxero/data/in_test_upload.pdf",
                     "/home/mobin/PycharmProjects/s3toxero/data/in_test_upload_manual.pdf"]
    pdf_blob_data = [get_pdf_data(filename) for filename
                     in filename_list]
    send_pdf_data(filename_list=['in_test_upload.pdf','in_test_upload_manual.pdf'],encoded_pdf_data=pdf_blob_data)

main()

# def start(event, context):
#     logging.info(f'event is ==> {event}')
#     logging.info(f'context is ==>{context}')
#     old_tokens = xero_auth()
#     print(f'Old Auth Token ==>{old_tokens}')
#     XeroRefreshToken(old_tokens[1])
#     get_files_xero()
#     upload_file_xero()
#
#
# if __name__ == "__main__":
#     start(event='hello from fargate==>task==>container!', context=None)
