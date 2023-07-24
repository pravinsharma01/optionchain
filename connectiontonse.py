import requests
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import streamlit as st

# Function to get current time
def currenttime():
    local_timezone = timedelta(hours=5, minutes=30)  # India timezone offset is UTC+5:30
    curr_time = datetime.utcnow() + local_timezone
    curr_time = curr_time.strftime("%H:%M:%S")
    return curr_time

# Function to get option chain data from NSE
def GetOCdatafromwebsite(url, headers):
    opdata = []
    current_expiry_data = []
    
    session = requests.Session()
    data = session.get(url, headers=headers).json()['records']['data']
    
    for i in data:
        for j, k in i.items():
            if j == 'CE' or j == 'PE':
                info = k
                info['instrumentType'] = j
                opdata.append(info)
                current_expiry_data.append(info['expiryDate'])
                
    current_expiry_data = list(set(current_expiry_data))  # list of expiries 
    df = pd.DataFrame(opdata)  # converting JSON into a dataframe
    
    current_market_price = df['underlyingValue'][0]

    return df, current_market_price

# Function to get organized data for current expiry
def Getdataorganised(Data):    
    newdf_oc = pd.DataFrame()

    # Organizing the data and changing the name of columns
    newdf_oc['Expiry'] = pd.to_datetime(Data['expiryDate'])
    current_expiry = newdf_oc['Expiry'].min()
    newdf_oc['Current_Expiry'] = (newdf_oc['Expiry'] == current_expiry)
    newdf_oc['CE/PE'] = Data['instrumentType'] 
    newdf_oc['strikePrice'] = Data['strikePrice']
    newdf_oc['OI'] = Data['openInterest']
    newdf_oc['Change in OI'] = Data['changeinOpenInterest']
    newdf_oc['Volume'] = Data['totalTradedVolume']
    newdf_oc['LTP'] = Data['lastPrice']

    # Making separate dataframes for calls and puts and combining them
    ceop = newdf_oc[(newdf_oc['CE/PE'] == 'CE') & (newdf_oc['Current_Expiry'] == True)]
    peop = newdf_oc[(newdf_oc['CE/PE'] == 'PE') & (newdf_oc['Current_Expiry'] == True)]
    finalOC = ceop.merge(peop, on='strikePrice', how='outer')

    # Deleting unnecessary columns
    finalOC = finalOC.drop(['Expiry_y', 'Current_Expiry_x', 'Current_Expiry_y'], axis=1)
    ceop = ceop.drop(['Expiry', 'Current_Expiry'], axis=1)
    peop = peop.drop(['Expiry', 'Current_Expiry'], axis=1)

    # Deleting rows with NaN values
    finalOC.dropna(inplace=True)
    ceop.dropna(inplace=True)
    peop.dropna(inplace=True)

    # Rearranging the columns as needed
    newcolumns = ['Expiry_x', 'CE/PE_x', 'Change in OI_x', 'OI_x', 'Volume_x', 'LTP_x',
                  'strikePrice', 'LTP_y', 'Volume_y', 'OI_y', 'Change in OI_y', 'CE/PE_y']
    finalOC = finalOC[newcolumns]
    # Renaming the columns
    finalOC.columns = ['Expiry_date', 'CE', 'Change in OI(CE)', 'OI(CE)', 'Volume(CE)', 'LTP(CE)',
                        'strikePrice', 'LTP(PE)', 'Volume(PE)', 'OI(PE)', 'Change in OI(PE)', 'PE']

    # Arranging the columns in the main dataframe
    finalOC = finalOC.sort_values(by='strikePrice', ascending=1)

    return finalOC, ceop, peop

# Function to get PCR calculation
def PCRcalulation(PCRD, count, finalOC):
    signal = 0
    curr_clock = currenttime()
    
    newdf = finalOC.copy()
    TotalPE = newdf['OI(PE)'].sum()
    TotalCE = newdf['OI(CE)'].sum()
    TotalOI = TotalPE - TotalCE
    PCR = TotalPE / TotalCE
    if TotalOI > 0:
        signal = 'Buy'
    if TotalOI < 0:
        signal = 'Sell'
    newrow = [curr_clock, TotalCE, TotalPE, TotalOI, PCR, signal]
    
    # Adding row to PCR dataframe
    PCRD.loc[len(PCRD.index)] = newrow
    return PCRD, count

# Function to display the Streamlit app
def main():
    st.title("Option Chain Data")
    st.write("Data obtained from NSE")

    # Replace the below code with Streamlit widgets for user interactions if required

    Data, current_market_price = GetOCdatafromwebsite(url, headers)
    curr_clock = currenttime()
    finalOC, ceop, peop = Getdataorganised(Data)

    st.header("Option Chain Data:")
    st.write(finalOC)

    st.header("Call Option Data:")
    st.write(ceop)

    st.header("Put Option Data:")
    st.write(peop)

if __name__ == '__main__':
    main()
