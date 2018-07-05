import requests
import pandas as pd
from bs4 import BeautifulSoup
import json
import datetime
import os


def parse_html_table(table):
    n_columns = 0
    n_rows = 0
    column_names = []

    # Find number of rows and columns
    # we also find the column titles if we can
    for row in table.find_all('tr'):

        # Determine the number of rows in the table
        td_tags = row.find_all('td')
        if len(td_tags) > 0:
            n_rows += 1
            if n_columns == 0:
                # Set the number of columns for our table
                n_columns = len(td_tags)

        # Handle column names if we find them
        th_tags = row.find_all('th')
        if len(th_tags) > 0 and len(column_names) == 0:
            for th in th_tags:
                column_names.append(th.get_text())

    columns = column_names if len(column_names) > 0 else range(0, n_columns)
    df = pd.DataFrame(columns=columns,
                      index=range(0, n_rows))
    row_marker = 0
    for row in table.find_all('tr'):
        column_marker = 0
        columns = row.find_all('td')
        for column in columns:
            df.iat[row_marker, column_marker] = (column.get_text()).replace(',', '')
            column_marker += 1
        if len(columns) > 0:
            row_marker += 1

    # Convert to float if possible
    for col in df:
        try:
            df[col] = df[col].astype(float)
        except ValueError:
            pass
    return df


# The response from this request will return ticker data for all coins on coinmarketcap.
ticker_data = requests.get("https://api.coinmarketcap.com/v1/ticker/?limit=0")

# Parse the ticker_data so it can be used as a normal dictionary.
parsed_ticker_data = json.loads(ticker_data.content)

# Put all ids and symbols into arrays for later use.
ids = []
symbols = []
for x in range(0, len(parsed_ticker_data)):
    ids.append(parsed_ticker_data[x]['id'])
    symbols.append(str(parsed_ticker_data[x]['symbol']))

# We will put the csv files in a directory called "coinmarketcap_historical_data".
# For the first time running the script this directory may not exist.
directory = 'coinmarketcap_historical_data'
if not os.path.exists(directory):
    os.makedirs(directory)

# Some coins on coinmarketcap do not have historical data, so we will add them to an array to verify this later.
errors = []

# In this loop we will get the historical data for all coins until today's date.
# After that, format it for the marketplace and put it into CSV files.
date = (datetime.datetime.today().strftime('%Y%m%d'))
for i in range(0, len(ids)):
    print('Processing coin {} of {}.'.format(i + 1, len(ids)))
    # This page contains the table with a coin's historical data.
    url = "https://coinmarketcap.com/currencies/" + str(ids[i]) + "/historical-data/?start=20130428&end=" + str(date)
    # Get the raw html from the url above and parse for the table containing historical data.
    response = requests.get(url)
    html = BeautifulSoup(response.text, 'html.parser')
    html_table = html.find("table")

    try:
        # Function parse_html_table creates a pandas dataframe from the html table.
        df = parse_html_table(html_table)
        # Format a symbol and date columns to fit marketplace requirements.
        df.insert(1, "symbol", symbols[i])
        df['Date'] = pd.to_datetime(df['Date']).apply(lambda x: x.strftime('%Y-%m-%d'))
        df = df.rename(index=str, columns={"Date": "date"})
        df['date'] = pd.to_datetime(df['date'])
        # Write dataframe to CSV file.
        df.to_csv(str(directory + '/' + ids[i]) + '.csv', index=False)
    except:
        errors.append(ids[i])

print('Writing to CSV files complete. Errors on {}.'.format(errors))
