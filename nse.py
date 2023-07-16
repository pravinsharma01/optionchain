"""
Option chain data by getting data from NSE and using flask for HTML display

"""
import requests
import pandas as pd

def nse():

    url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
    headers = {
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en,en-US;q=0.9,hi;q=0.8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
        }
    opdata= []
    current_expiry_data = []
        
    session = requests.Session()
    data = session.get(url, headers = headers).json()['records']['data']
    for i in data:
        for j,k in i.items():
            if j == 'CE' or j == 'PE':
                info = k
                info ['instrumentType'] = j
                opdata.append(info)
                current_expiry_data.append(info['expiryDate'])
                
    current_expiry_data= list(set(current_expiry_data)) # list of expries 
    df = pd.DataFrame(opdata) # converting Jason into dataframe
        
    current_market_price = df['underlyingValue'][0]
    return df, current_market_price
