import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from datetime import datetime
from gspread_pandas import Spread, conf
from googleapiclient.discovery import build

options = Options()
options.headless = True
chromedriver_path = 'INSERT your chromedriver path here'
driver = webdriver.Chrome(executable_path=chromedriver_path, options=options)
r = driver.get('https://smartentry.org/status/gymmboxx')

#date and time of the day
dateandtime = datetime.now()
date_now = dateandtime.strftime('%d/%m/%Y')
time_now = dateandtime.strftime('%H:%M')

try:
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#outlets > div:nth-child(1)")))
    
    outlet_fixed_details = {'Bishan' : [50, 6000], 'Bedok Point' : [50, 7660], 'Century Square' : [50, 7500], 'JCube' : [50, 5385], 'Keat Hong' : [37, 4000], 'Kebun Baru' : [21, 2500]}
    
    outlet_details = []
    
    for outlet in driver.find_elements_by_class_name("box.col-lg-4.col-md-6.col-sm-12"):
        
        #extract location of gymmboxx
        Location = outlet.find_element_by_class_name("lead.mb-3").text
        
        #area of outlet
        area = outlet_fixed_details[Location][1]
       
        #Max capacity of outlet
        max_capacity = outlet_fixed_details[Location][0]
       
        #extract percentage capacity of outlets
        percentage = outlet.find_element_by_class_name("bar-fg").get_attribute('style')
        percentage = percentage[7:11].strip(' %;')
        
        #calculate current capacity
        capacity_number = round(int(percentage) * max_capacity / 100)
        
        #density of outlet
        try:
            density = area / capacity_number
        except ZeroDivisionError:
            density = 0

        #extract current number of people in queue
        queue = outlet.find_element_by_class_name("queue_length").text
        
        outlet_details.append({'Date' : date_now, 'Location': Location, 'Area(SQ.FT)' : area, 'Time' : time_now, 'Max Capacity': max_capacity, 'Current Capacity' : capacity_number, '% Capacity' : percentage, 'SQ.FT/pax' : density, 'Waiting List' : queue})
   
    df = pd.DataFrame(outlet_details, columns = ['Date', 'Location', 'Area(SQ.FT)', 'Time', 'Max Capacity', 'Current Capacity', '% Capacity', 'SQ.FT/pax', 'Waiting List'])
    
    print(df)

except Exception as e:
    driver.save_screenshot('INSERT path to save image')

driver.quit()

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