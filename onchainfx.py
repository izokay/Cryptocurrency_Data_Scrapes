import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import datetime


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
                column_names.append(th.get_text().replace('(', '').replace(')', '').replace(',', '').replace('-', ' '))

    # Safeguard on Column Titles
    if len(column_names) > 0 and len(column_names) != n_columns:
        raise Exception("Column titles do not match the number of columns")

    columns = column_names if len(column_names) > 0 else range(0, n_columns)
    df = pd.DataFrame(columns=columns,
                      index=range(0, n_rows))
    row_marker = 0
    for row in table.find_all('tr'):
        column_marker = 0
        columns = row.find_all('td')
        for column in columns:
            datas = column.find_all('span')
            if datas:
                for data in datas:
                    if 'sats' in data.get_text():
                        df.iat[row_marker, column_marker] = str((float(data.get_text().replace(' sats', ''))/100000000))
                    elif 'cents' in data.get_text():
                        df.iat[row_marker, column_marker] = str((float(data.get_text().replace(' cents', ''))/100))
                    else:
                        df.iat[row_marker, column_marker] = (data.get_text()).replace(',', '').replace(
                            '0no data', '-') \
                            .replace('0unknowable ?', '-').replace('%', '').replace('+', '').replace('cents', '').replace('$','') \
                            .replace('฿', '').replace('sats', '').replace('?', '').replace('yrs', '').replace('yr','').replace('no data', '-') \
                            .replace('unknowable', '-').replace('(', '').replace(')', '')
            else:
                if 'sats' in column.get_text():
                    df.iat[row_marker, column_marker] = str((float(column.get_text().replace(' sats', '')) / 100000000))
                elif 'cents' in column.get_text():
                    df.iat[row_marker, column_marker] = str((float(column.get_text().replace(' cents', '')) / 100))
                else:
                    df.iat[row_marker, column_marker] = (column.get_text()).replace(',', '').replace('0no data', '-') \
                        .replace('0unknowable ?', '-').replace('%', '').replace('+', '').replace('cents', '').replace('$', '') \
                        .replace('฿', '').replace('sats', '').replace('?', '').replace('yrs', '').replace('yr', '').replace('no data', '-') \
                        .replace('unknowable', '-').replace('(', '').replace(')', '')
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


errors = []

url = "https://onchainfx.com/v/7gQmrg"
browser = webdriver.Chrome(executable_path=r"chromedriver.exe")
browser.get(url)
table = WebDriverWait(browser, 100).until(
        EC.presence_of_element_located((By.ID, "dt_matrix"))
    )
html = browser.page_source
soup = BeautifulSoup(html, 'html.parser')
results = soup.find("table")
df = parse_html_table(results)
df = df.rename(index=str, columns={"Name": "symbol"})
date = (datetime.datetime.today().strftime('%Y-%m-%d'))
df.drop(df.columns[[0]], axis=1, inplace=True)
df.insert(0, "date", date)
df = df.rename(index=str, columns={"24hr Change vs USD": "Change vs USD 24hr"})
df = df.rename(index=str, columns={"24hr Change vs BTC": "Change vs USD BTC"})
df = df.rename(index=str, columns={"7 day Change vs USD": "Change vs USD 7 day"})
df = df.rename(index=str, columns={"30 day Change vs USD": "Change vs USD BTC 30 day"})
df = df.rename(index=str, columns={"90 day Change vs USD": "Change vs USD BTC 90 day"})
df = df.rename(index=str, columns={"1 year Change vs USD": "Change vs USD BTC 1 year"})
df = df.rename(index=str, columns={"24hr Vol": "Vol 24hr"})
df = df.rename(index=str, columns={"% down from ATH": "Percent down from ATH"})
df = df.rename(index=str, columns={"1 year Change vs USD": "Change vs USD BTC 1 year"})
df = df.rename(index=str, columns={"1 year Change vs USD": "Change vs USD BTC 1 year"})
df = df.rename(index=str, columns={"Supply % Issued": "Supply Percent Issued"})


print(df)
df.to_csv('./onchain/table.csv', index=False)

