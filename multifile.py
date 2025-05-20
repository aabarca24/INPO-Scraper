from bs4 import BeautifulSoup
import re
import IRIS_Parser
import pandas as pd
import io
# Set pandas display options
pd.set_option('display.max_rows', None)   # Show all rows
pd.set_option('display.max_columns', None)  # Show all columns

# Sample combined HTML
htmlexample = r"""
input HTML here
"""

# Define the start and end markers
start_marker = '<table width="100%" cellpadding="0" cellspacing="0">'
end_marker = '<div class="pagebreak"></div>'

# Split the combined HTML string into individual documents
parts = re.split(f'(?={re.escape(start_marker)})', htmlexample)

# List to store the individual HTML documents
htmllist = []

# Process each part
for part in parts:
    # Skip empty parts
    if not part.strip():
        continue
    
    # Determine if this is the last part or not
    if end_marker in part:
        # Split on end_marker to isolate the document content
        document_content = part.split(end_marker, 1)[0]
    else:
        # For the last document (without end_marker)
        document_content = part
    
    # Append the document content to the list
    htmllist.append(document_content)

data = []
for i, doc_html in enumerate(htmllist):
    soup = BeautifulSoup(doc_html, 'html.parser')
    if(i == 0):
        continue
    # Parsing
    print(f"Processing Document {i}")
    id_tag = soup.find_all('td', attrs={'width':'30%'})
    id = id_tag[1].find('b').text.strip()    # Record # Variable
    print(id)
    data.append(IRIS_Parser.parse(soup))


# Now you have data, and the existing csv file
# Dataframe A will be the existing, and Dataframe B will be the df pulled from this scrape
A = pd.read_csv(r'C:\Users\aabarca\Downloads\Sort Test.csv')
B = pd.concat(data, ignore_index=True)

# Ensure dates are in readable format to Sort later on
A['Date:'] = pd.to_datetime(A['Date:'], format='%m/%d/%Y %H:%M') # As read from Excel
B['Date:'] = pd.to_datetime(B['Date:'], format='%Y-%m-%d %I:%M %p') # As created from Parse

# Boolean for columns shared between new DF and existing DF
common_columns = A.columns.intersection(B.columns)
# Filter out columns in new DF that are not in existing DF
B_subset = B[common_columns]
# Combine both DF to add new DF information to existing DF
final_df = pd.concat([A, B_subset], ignore_index=True)
final_df = final_df.drop_duplicates(subset='Record ID:', keep='last')

# Sort new merged dataframe by Date
final_df = final_df.dropna(subset=['Date:'])
final_df.sort_values(by='Date:', inplace=True)
final_df.reset_index(drop=True, inplace=True)

# Remove Additional Columns created by re-indexing
final_df = final_df.loc[:, ~final_df.columns.str.contains('^Unnamed')]

# Export new dataframe into CSV file (or overwrite if name is the same)
final_df.to_csv('Sort Test.csv')