#IRIS Report Scraping Tool v 2.0
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import IRIS_Parser

"""
User Inputs:
Excel list of links: 
    User should apply filters on IRIS export a list of links to a csv file using the IRIS 
    database export tool.  This file should be fed into this script.  
Output File name: name of output csv file generated 
Chromedrive location:
    User must have the selenium chrome driver extension installed with the appropriate path specified. 
Python libraries required:
    Selenium, html2text, and BeautifulSoup (bs4) are used to parse the reports.
    Pandas and numpy are used to format results. 
Flags:
    User should specify desired output fields by setting the appropriate flags to "True"
"""

###### User Input Block ######
input_filename = r'C:\Users\aabarca\OneDrive - MPR Associates\Documents\MPR Coding\Test VENV\.venv\INPO\experience-grid-results-20240618-043749.csv'
chrome_driver_loc = r'C:\Users\aabarca\chromedriver.exe'
output_filename = 'new_iris_scrape(0823).csv'

Post_Process_Results = True
# This flag removes the INPO ID Number from the component field and buckets the systems into ~EIIS naming conventions.
# Initiating_System_Flag and Initiating_Key_Component_Flag must both be True

###### End User Input Block ######

# Read list of links and create resulting dataframe
df = pd.read_csv(input_filename)
links = df['Report URL']
number_of_links = len(links)
print(number_of_links)
newdf = df[['Exp ID','Location']].copy()

# Define Function to Get Report Text
def get_page_text(current_link, chrome_driver_loc):   

    webdriver_established = False
    while not webdriver_established:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.add_argument('--headless=new')
        driver = webdriver.Chrome(options=chrome_options)
        webdriver_established = True

    driver.get('https://iris.inpo.org/report_api/experience/OutputReport/485864')
    time.sleep(0.75)
    try:    
        login_button = driver.find_element("id","submit-generic-button")
        login_button.click()
        not_yet_clicked = False
    except:
        print('login button not found')
        not_yet_clicked = True
    driver.get(current_link)
    time.sleep(1)
    page_source = driver.page_source
    bs = BeautifulSoup(page_source, 'html.parser')
    time.sleep(0.5)
    driver.quit()
    return bs, not_yet_clicked


data = []
try:
    for i in range(number_of_links):
        try:
            # Open Link and gather information into beautiful soup and text objects
            print('link number:', i)
            link = links[i]
            not_yet_clicked = True
            bs, not_yet_clicked = get_page_text(link, chrome_driver_loc)
            retry = 0
            while not_yet_clicked: #page_text, unsplit_page_text,
                bs, not_yet_clicked = get_page_text(link, chrome_driver_loc)
                retry += 1
                print('retry', retry)
            data.append(IRIS_Parser.parse(bs))
        except KeyboardInterrupt:
            print("\nProcess interrupted by user. Exiting...")
            break
        except Exception as e:
            print("An error occurred: {e}")
            print(f"Error occurred at link: {i}")
            continue
finally:
    resulttest = pd.concat(data, ignore_index=True)
    resulttest.to_csv(output_filename)

