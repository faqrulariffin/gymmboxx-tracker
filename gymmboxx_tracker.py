import pandas as pd
import requests
from datetime import datetime
from gspread_pandas import Spread, conf
from googleapiclient.discovery import build

#date and time of the day
dateandtime = datetime.now()
date_now = dateandtime.strftime('%d/%m/%Y')
time_now = dateandtime.strftime('%H:%M')

url = "https://smartentry.org/status/api/metrics/gymmboxx"
headers = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'Connection': 'keep-alive',
    'Host': 'smartentry.org',
    'Referer': 'https://smartentry.org/status/gymmboxx',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest'
}

response = requests.get(url, headers=headers)
response_dict = response.json()

outlet_fixed_details = {'Bishan' : 6000, 'Bedok Point' : 7660, 'Century Square' : 7500, 'JCube' : 5385, 'Keat Hong' : 4000, 'Kebun Baru' : 2500, 'Canberra': 5000}
outlets = response_dict['outlets']
outlet_details = []

for outlet in outlets:
    outletName = outlet['name']
    outletQueue = outlet['queue_length']
    outletOccupancy = outlet['occupancy']
    outletLimit = outlet['occupancy_limit']
    outletPercentage = round(outletOccupancy/outletLimit * 100)
    outletArea = outlet_fixed_details[outletName]
    try:
        density = round(outletArea / outletOccupancy, 2)
    except ZeroDivisionError:
        density = 0
    outlet_details.append({'Date' : date_now, 'Location': outletName, 'Area(SQ.FT)' : outletArea, 'Time' : time_now, 'Max Capacity': outletLimit, 'Current Capacity' : outletOccupancy, '% Capacity' : outletPercentage, 'SQ.FT/pax' : density, 'Waiting List' : outletQueue})
   
df = pd.DataFrame(outlet_details, columns = ['Date', 'Location', 'Area(SQ.FT)', 'Time', 'Max Capacity', 'Current Capacity', '% Capacity', 'SQ.FT/pax', 'Waiting List'])

service = build('drive', 'v3', credentials = conf.get_creds())
files = service.files().list(
    q = "'INSERT folder_id here' in parents and mimeType != 'application/vnd.google-apps.folder'", 
    fields = 'files(name)').execute()

files_dict = files['files']
print(files_dict)

i = 0
for i in range(len(files_dict)):
    list1 = files_dict[i].values()
    str1 = ''.join(list1)
    if str1 == date_now:
        match = 'y'
        break
    else:
        i += 1
        match = 'n'

if match == 'n':
    file_id = 'INSERT template file id here'
    copied_file = {'name' : date_now}
    service.files().copy(fileId = file_id, body = copied_file).execute()

today_tracker_file = Spread(date_now, sheet = 'INSERT sheet name here')
today_tracker_df = today_tracker_file.sheet_to_df()
today_tracker_list = [today_tracker_df.columns.values.tolist()]
today_tracker_list.extend(today_tracker_df.values.tolist())

start_row = len(today_tracker_list) + 1
spread = Spread(date_now)
sheet_name = 'INSERT sheet name here'
start_cell = (start_row, 1)

spread.open_sheet(sheet_name)
spread.df_to_sheet(df, index = False, headers = False, sheet = sheet_name, start = start_cell, replace = False)