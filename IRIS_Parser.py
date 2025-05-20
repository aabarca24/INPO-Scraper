from bs4 import BeautifulSoup
import pandas as pd

def parse(soup):
	# Data list to contain all relevant information, to be transformed into DataFrame later on
    data = [] # To hold all values
    unique_keys = {} # To hold column headers, and repeating variables within documents

    """
    This section parses for information regarding Location, Date, Record ID, and Title
    """
    # Find Site/Location Name
    location_tag = soup.find('td', attrs={'width':'40%'})
    location = location_tag.find('b').text.strip()    # Title Variable
    data.append(['Location:', location])

    # Find date of report
    date_tag = soup.find_all('td', attrs={'width':'30%'})
    date = date_tag[0].find('b').text.strip()   # Date Variable
    data.append(['Date:', date])

    # Find Record Number
    id_tag = soup.find_all('td', attrs={'width':'30%'})
    id = id_tag[1].find('b').text.strip()    # Record# Variable
    data.append(['Record ID:', id])
    
    # Creating BS lists that hold tags specified. i.e. div_span_tags holds all <div> and <span> tags
    # in the HTML document

    Div = soup.find_all('div')
    div_span_tags = soup.find_all(['div', 'span'])
    div_tr_tags = soup.find_all(['div', 'tr'])
    div_tr_span_tags = soup.find_all(['div', 'tr', 'span'])
    span_tags = soup.find_all('span')
    bold_tags = soup.find_all('b')

    """
    This section uses the Div BS list for sections included in all INPO templates
    """

    # First entry in the Div list holds the title
    title = Div[0].text.strip()   # Extracts title from Div table
    data.append(['Title:', title])

    # Div[1] holds Status line, with Report Category and status
    status_line = Div[1].find('span')
    data.append(["Category:", status_line.contents[1].get_text() + status_line.contents[2].get_text()])
    data.append(["Report Status:", status_line.contents[5].get_text().strip() + ' - ' + status_line.contents[7].get_text().strip()])

    # Significance found on Div line 2 (3 not included)
    sig_line = Div[2].find_all('span')
    data.append([sig_line[0].get_text(), sig_line[1].get_text()])
 
    # Abstract
    Abstract = Div[find_first_occurrence(Div, 'Abstract:') + 1].text.strip()
    data.append(['Abstract:', Abstract])
    
    # Description
    Description = Div[find_first_occurrence(Div, 'Description:') + 1].text.strip()
    data.append(['Description:', Description])

    # Cause Summary
    cause_summary = Div[find_first_occurrence(Div, 'Cause Summary:') + 1].text.strip()
    data.append(['Cause Summary:', cause_summary])

    # Corrective Action Summary
    corr_action_summary = Div[find_first_occurrence(Div, 'Corrective Action Summary:') + 1].text.strip()
    data.append(['Corrective Action Summary:', corr_action_summary])

    """
    This section begins scanning through the reports for headers (<div>) and/or subcontents of those
    headers (<span> or <tr> fields)
    """

    # For Event Type section
    sec_begin = find_first_occurrence(div_span_tags, "Event Type:")
    sec_end = find_first_occurrence(div_span_tags, "Unit Consequence:")
    section_range = div_span_tags[sec_begin+1:sec_end]
    for row in section_range:
        row_text = row.get_text(separator=' ', strip=True)
        if '-' in row_text:
            text_before_dash, text_after_dash = row_text.split('-', 1)
            data.append(['ET ' + text_before_dash.strip() + ':', text_after_dash.strip()])

    # For Unit Consequence section
    sec_begin = find_first_occurrence(div_tr_tags, "Unit Consequence:")
    sec_end = find_first_occurrence(div_tr_tags, "Industrial Safety Consequence")
    section_range = div_tr_tags[sec_begin+1:sec_end]
    if(div_tr_tags[sec_begin+1].get_text != 'None'):
        for row in section_range:
            row_text = row.get_text(separator=' ', strip=True)
            if ':' in row_text:
                text_before_colon, text_after_colon = row_text.split(':', 1)
                data.append(['UC ' + text_before_colon.strip() + ':', text_after_colon.strip()])

    # For Industrial Safety Consequence section
    sec_begin = find_first_occurrence(div_span_tags, "Industrial Safety Consequence")
    sec_end = find_first_occurrence(div_span_tags, "Radiological Consequence")
    section_range = div_span_tags[sec_begin+1:sec_end]
    for tag in section_range:
        span_tag = tag.find_all('span')
        for span in span_tag:
            span_text = span.text.strip()
            if ':' in span_text:
                text_before_colon, text_after_colon = span_text.split(':', 1)
                data.append(['ISC ' + text_before_colon.strip() + ':', text_after_colon.strip()])

    # Beginning section of Fire Consequence Summary
    FCS_sec = find_first_occurrence(div_span_tags, "Fire Consequence Summary:")

    if(FCS_sec != None):
        FCS_flag = True
    else:
        FCS_flag = False
    
    # For Radiological Consequence section
    sec_begin = find_first_occurrence(div_span_tags, "Radiological Consequence:")
    sec_end = find_first_occurrence(div_span_tags, "MSPI")
    if(FCS_flag):
        sec_end = FCS_sec
    if (sec_end == None):
        sec_end = find_first_occurrence(div_span_tags, "Level of Investigation")

    section_range = div_span_tags[sec_begin+1:sec_end]
    for row in section_range:
        row_text = row.get_text(separator=' ', strip=True)
        if ':' in row_text:
            text_before_colon, text_after_colon = row_text.split(':', 1)
            key = 'RC ' + text_before_colon.strip()
            if key != 'RC Location' and key != 'RC Date':
                print(key)
                if key in unique_keys:
                    unique_keys[key] += 1
                else:
                    unique_keys[key] = 1

                unique_key = f"{key}({unique_keys[key]})"
                data.append([str(unique_key) + ':', text_after_colon.strip().replace("\n\t\t\t\t\t", "")])
                data.append(['RC Count:', unique_keys[key]])

    # For Fire Consequence Summary section
    if(FCS_flag):
        data.append(['Fire:', "Yes"])
        sec_begin = FCS_sec
        sec_end = find_first_occurrence(div_span_tags, "Level of Investigation")
        section_range = div_span_tags[sec_begin+1:sec_end]
        #if(div_span_tags[sec_begin+1].get_text != 'None'):
        for tag in section_range:
            
            if tag.name == 'span':

                row_text = tag.get_text(separator=' ', strip=True)
                #print("\n<span>\n" + row_text + "\n<span>\n")
            if  ':' in row_text:
                text_before_colon, text_after_colon = row_text.split(':', 1)
                if(text_after_colon == ''):
                    if(tag.find_next_sibling('span') != None):
                        data.append(['FC ' + text_before_colon.strip() + ':', tag.find_next_sibling('span').get_text()])
                else:
                    data.append(['FC ' + text_before_colon.strip() + ':', text_after_colon.strip()])
    else:
        data.append(['Fire:', "No"])          

        # MSPI Section Unnecessary

    # Level of Investigation tag
    level_of_inv = div_span_tags[find_first_occurrence(div_span_tags, "Level of Investigation")].text
    if ':' in level_of_inv:
        text_before_colon, text_after_colon = level_of_inv.split(':', 1)
        data.append([text_before_colon.strip() + ':', text_after_colon.strip()])

    ########### For Equipment Affected and Initiating Components Fields ###############

    EA_flag = False
    IC_flag = False

    # Beginning section of EA
    EA_sec = find_first_occurrence(div_tr_tags, "Equipment Affected:")

    # Beginning section of IC
    IC_sec = find_first_occurrence(div_tr_tags, "Initiating Components:")

    # Beginning section of OE
    OE_sec = find_first_occurrence(div_tr_tags, "Other Trend Codes:")

    if(EA_sec != None):
        EA_flag = True
    if(IC_sec != None):
        IC_flag = True

    if(EA_flag and IC_flag):
        if ((find_indexes(div_tr_span_tags, "Initiating Components:")[0] 
            - find_indexes(div_tr_span_tags, "Equipment Affected")[0]) == 1):
            EA_flag = False

    ########### For Equipment Affected Section ####################

    if EA_flag:
    # Set the variables to specify a range for the EA Section
        sec_begin = EA_sec
        if IC_flag:
            sec_end = IC_sec
        else:
            sec_end = OE_sec
        section_range = div_tr_tags[sec_begin+1:sec_end]

        # For Key Component
        key_idx = find_first_occurrence(span_tags, 'Key           Component:')
        if (key_idx != None):
            original_string = span_tags[key_idx].get_text()
            key_line = original_string.replace('\n', '')
            if ':' in key_line:
                text_before_colon, text_after_colon = key_line.split(':', 1)
                text_after_colon = text_after_colon.split(' - ', 1)[0]
                data.append(['EA ' + 'Key Component' + ':', text_after_colon.strip()])
        # End Key Component

        # For EA System
        system_idx = find_first_occurrence(div_span_tags, 'System:')
        equipment_idx = find_first_occurrence(div_span_tags, 'Equipment Affected:')
        while system_idx != None and system_idx < equipment_idx:
            next_system_idx = find_first_occurrence(div_span_tags[system_idx+1:], "System:")
            if next_system_idx == None:
                break
            
            system_idx += next_system_idx + 1

            if system_idx >= equipment_idx:
              break
        if (system_idx != None):
            system_line = div_span_tags[system_idx].get_text()
            if ':' in system_line:
                text_before_colon, text_after_colon = system_line.split(':', 1)
                #data.append(['EA_' + 'System' + ':', text_after_colon.strip()])
                data.append(['EA System', text_after_colon.strip()])
        # End EA System

        # For all other information
        for row in section_range:
            row_text = row.get_text(separator=' ', strip=True)
            if ':' in row_text:
                text_before_colon, text_after_colon = row_text.split(':', 1)
                data.append(['EA ' + text_before_colon.strip() + ':', text_after_colon.strip()])

    ########### For Initiating Components Section ####################
    
    if IC_flag:
    # For Supporting Component
        span_idx = find_first_occurrence(span_tags, 'Supporting    Component:')

        if (span_idx != None):
            original_string = span_tags[span_idx].get_text()
            span_line = original_string.replace('\n', '')
            if ':' in span_line:
                text_before_colon, text_after_colon = span_line.split(':', 1)
                text_after_colon = text_after_colon.split(' - ', 1)[0]
                data.append(['IC Supporting Component' + ':', text_after_colon.strip()])
        # End Supporting Component

        sec_begin = find_first_occurrence(div_tr_span_tags, "Initiating Components:")
        sec_end = find_first_occurrence(div_tr_span_tags, "Parts:")
        if(sec_end == None):
            sec_end = find_first_occurrence(div_tr_span_tags, "Cause:")
            if(sec_end == None):
                sec_end = find_first_occurrence(div_tr_span_tags, "Other Trend Codes:")
                
        section_range = div_tr_span_tags[sec_begin+1:sec_end]

        # For IC Key Component
        key_idx = find_first_occurrence(section_range, 'Key           Component:')
        if (key_idx != None):
            original_string = section_range[key_idx].get_text()
            key_line = original_string.replace('\n', '')
            if ':' in key_line:
                text_before_colon, text_after_colon = key_line.split(':', 1)
                text_after_colon = text_after_colon.split(' - ', 1)[0]
                #print(['IC_' + 'Key Component' + ':', text_after_colon.strip()])
                data.append(['IC Key Component' + ':', text_after_colon.strip()])
        # End Key Component

        # For IC Key System
        system_idx = find_first_occurrence(section_range, 'System:')
        if (system_idx != None):
            system_line = section_range[system_idx].get_text()
            if ':' in system_line:
                text_before_colon, text_after_colon = system_line.split(':', 1)
                data.append(['IC System' + ':', text_after_colon.strip()])
        # End IC System

        # Filter and print only the tr tags
        tr_tags = [tag for tag in section_range if tag.name == 'tr']

        for tr in tr_tags:
            row_text = tr.get_text(separator=' ', strip=True)
            if ':' in row_text:
                text_before_colon, text_after_colon = row_text.split(':', 1)
                data.append(['IC ' + text_before_colon.strip() + ':', text_after_colon.strip()])
    
    ### For Cause Elements ###

	# Print each found <span> element
    sec_begin = find_first_occurrence(div_span_tags, "Cause:")
    sec_end = find_first_occurrence(div_span_tags, "Other Trend Codes")
    section_range = div_span_tags[sec_begin:sec_end]
    #print(section_range)
    for i, span in enumerate(section_range):
        if(span.name == 'span' and span.get_text() == 'As-found Condition'):
            if i + 1 < len(section_range):
                data.append(['Cause:', section_range[i+1].get_text()])
                data.append(['Sub-Cause:', section_range[i+2].get_text()])

        if(span.name == 'span' and span.get_text() == 'Because of External Condition(s)'):
            if i + 1 < len(section_range):
                data.append(['External Condition:', section_range[i+1].get_text()])
                data.append(['Sub-Condition:', section_range[i+2].get_text()])

        if(span.name == 'span' and span.get_text() == 'Component / Equipment Specific Cause(s)'):
            if i + 1 < len(section_range):
                data.append(['Component / Equipment Specific Cause:', section_range[i+1].get_text()])
                data.append(['Sub-Specific Cause', section_range[i+2].get_text()])

        
    ### End Cause Parsing ### 

	# Create DataFrame ################################################################

    columns = [column for column, _ in data]  # Extracting the first elements as column names
    rows = [row for _, row in data]           # Extracting the second elements as values
    #Create a dictionary from the extracted values
    dataf = {columns[i]: [rows[i]] for i in range(len(columns))}
    #Convert the dictionary to a DataFrame
    df = pd.DataFrame(dataf)
    print(date)
    return(df)
  
def find_first_occurrence(elements, search_text):
    for index, tag in enumerate(elements):
        if search_text in tag.get_text():
            return index
    return None

def find_indexes(elements, search_text):
    indexes = []
    for index, tag in enumerate(elements):
        if search_text in tag.get_text():
            indexes.append(index)
    return indexes

def find_last_occurence(elements, search_text):
    rev = reversed(elements)
    for index, tag in enumerate(elements):
        if search_text in tag.get_text():
            idx = len(elements) - index - 1
            return idx
    return None