
import re
import os
import sys
import time
import json

current_script_path = os.path.abspath(__file__)
parent_directory = os.path.dirname(os.path.dirname(current_script_path))
sys.path.append(parent_directory)

from adminui import *

from tgu import TGU
from constans import TEMP_FOLDER, HD_LOGO_BASE64, LOGIN_IMAGE

app = AdminApp(upload_folder=TEMP_FOLDER)

tgu = TGU()
information = tgu.get_status()

table_columns = [
    {'title': 'CAN DATA', 'dataIndex': 'data'}
]

# 초기 데이터 생성
data = []
default_can_data = []
current_can_data = {}

def can_data_callback(msg):
    global current_can_data
    current_can_data['original'] = msg['original']
    current_can_data['parsing']  = msg['parsing']

tgu.get_can_data(can_data_callback)

def mock_table_data(input_value):
    global current_can_data
    return [{"data": json.dumps(current_can_data[input_value])}]

def on_page(query):
    value = query['formValues'].get('type')
    time.sleep(0.01)
    if value == 'original':
        print(mock_table_data(value))
        return TableResult(mock_table_data(value), 1, query['current_page'])
    elif value =='parsing':
        return TableResult(mock_table_data(value), 1, query['current_page'])

    return TableResult(default_can_data, 1, query['current_page'])

def on_reset():
    global current_can_data
    current_can_data = {}

@app.login()
def on_login(username, password):
    if username=='admin' and password=='1111':
        return LoggedInUser("Admin", auth=['user', 'admin'], avatar=LOGIN_IMAGE, redirect_to='/')
    if username=='user' and password=='1111':
        return LoggedInUser("User",  auth=['user'], avatar=LOGIN_IMAGE, redirect_to='/')
    else:
        return LoginFailed()
    
@app.page('/log_in_zone', 'Logged In', auth_needed='user')
def logged_in_page():
    return [
        Card('Logged In', [
            Header('You are logged in')
        ])
    ]

@app.page('/', 'Dashboard Page', auth_needed='user')
def detail_page():
    '''
    "protocol"     : self.__protocol,
    "src_ip"       : self.__src_ip,  
    "src_port"     : self.__src_port,
    "dst_ip"       : self.__dst_ip,
    "dst_port"     : self.__dst_port,
    "can_channel"  : self.__can_channel,
    "bustype"      : self.__bustype,
    "bitrate"      : self.__bitrate
    '''
    return [
        Card(content=[
            # Timer(on_fire=on_timer_fire, data='hello timer'),
            Header('TGU', 1),
            DetailGroup('Hardware Information', content=[
                DetailItem('Manufacturer', "HD-Hyundai"),
                DetailItem('TGU Ip', information['src_ip']),
                DetailItem('TGU Mac', "5C:31:3E:D4:9E:C9"),
            ], bordered=True, column=1, size='small'),
            DetailGroup('Software Information', content=[
                DetailItem('Library', "can-library"),
                DetailItem('SW Version', "0.0.2"),
                DetailItem('Protocol', information['protocol']),
                DetailItem('Src Ip',   information['src_ip']),
                DetailItem('Src Port', information['src_port']),
                DetailItem('Dst Ip',   information['dst_ip']),
                DetailItem('Dst Port', information['dst_port']),
            ], bordered=True, column=1, size='small'),
            DetailGroup('CAN Information', content=[
                DetailItem('CAN Channel', information['can_channel']),
                DetailItem('CAN Bustype', information['bustype']),
                DetailItem('CAN Bitrate',   information['bitrate']),
            ], bordered=True, column=1, size='small'),
            DetailGroup('Contact Person Information', content=[
                DetailItem('Company',  "Clobot"),
                DetailItem('Division', "Robot Platform Business Division"),
                DetailItem('Name',     "홍원의"),
                DetailItem('Title', "Project Manager"),
                DetailItem('Mobile', "010-3594-8244"),
                DetailItem('E-mail', "luigi@clobot.co.kr"),
            ], column=1),
        ])
    ]

@app.page('/upload', 'Upload File', auth_needed='user')
def upload_page():
    return [
        Card('Upload Form',
            content= [
            Header('DBC File Upload', 1),
            DetailGroup('Upload DBC rule', content=[
                DetailItem('File name',  "The file name must be written in numbers and English letters only."),
                DetailItem('File extension',  "The file extension is .dbc or .DBC."),
            ]),
            Upload(on_data=on_upload, type='File', multiple=True)
        ])
    ]
@app.page('/tgu', 'Tgu Data')
def table_page():
    return [
        Card(content = [
            DataTable("Example Table", columns=table_columns, 
                data = TableResult(default_can_data, 1), on_data=on_page,
                filter_form=FilterForm([
                    SelectBox('Type', data=['original', 'parsing'], placeholder="Select One"),
                ], submit_text='Refresh', reset_text='Type Clear'))
            ,Button('Data Reset', on_click=on_reset)
        ])
    ]

def on_upload(file):
    extension = file['file_name'].split('.')[-1].lower()
    
    if re.match("^[a-zA-Z0-9]+$", file['file_name'].split('.')[0]) is None:
        print("Invalid file name. File name should contain only letters and numbers.")
        return
    
    if extension != 'dbc':
        print("Invalid file extension. Only '.dbc' files are allowed.")
        return
    
    print("=== file name will be: ===")
    print(file['file_name'])
    print('=== the file is stored in: ===')
    print(app.uploaded_file_location(file))




if __name__ == '__main__':
    app.app_title  = '현대보령PG'
    app.app_logo   = HD_LOGO_BASE64
    app.copyright_text = ''
    # app.register_link={'Sign Up': '/signup'}
    # app.forget_password_link={'Forget Password': '/forget'}
    app.app_styles = {'nav_theme': 'dark', 'layout': 'sidemenu'}
    # app.app_favicon = ''
    app.footer_links = ''
    app.set_menu(
        [
            MenuItem('Dash Board',  '/',              icon="dashboard", auth_needed='user'),
            MenuItem('TGU Data',    '/tgu',           icon="dashboard", auth_needed='user'),
            MenuItem('FILE',        '/upload',        icon="file-exclamation", auth_needed='user'),
            # MenuItem('About',       '/about',         icon="info-circle", auth_needed='user')
        ]
    )
    app.run(host='0.0.0.0')