"""
Option chain data by getting data from NSE and using flask for HTML display

"""
import requests
import pandas as pd
from bs4 import BeautifulSoup
import json

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
    data = session.get(url, headers = headers)
    soup = BeautifulSoup(data.content, "html.parser")
    txtfile = open("nsefile.txt", "w")
    txtfile.writelines(soup)
    txtfile.close()

    filename = open('nsefile.txt','r')
    dic = filename.read()
    outfile = open( "sample.json", "w")
    outfile.write(dic)
    outfile.close()
    return 
def convertintodataframe():
    opdata= []
    current_expiry_data = []

    # Opening JSON file
    with open('sample.json', 'r') as openfile:
        # Reading from json file
        json_object = json.load(openfile)
    
    for i in json_object['records']['data']:
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
