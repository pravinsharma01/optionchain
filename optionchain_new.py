"""
Option chain data by getting data from NSE and using flask for HTML display

"""
import requests
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from flask import Flask, render_template, request, redirect, url_for
from flask import Flask, render_template_string

app = Flask(__name__)
ceop = {}
count = 0
listofsp = []
increase_decrease_df = pd.DataFrame()
columns =['Time', 'Total Call Writer','Total Put Writer', 'Difference','PCR', 'Signal']
PCRD = pd.DataFrame(columns = columns)
PCRDV = pd.DataFrame(columns = columns)
Indices = ["NIFTY", "FINNIFTY", "BANKNIFTY", "MIDCPNIFTY"]

url = "https://www.nseindia.com/api/option-chain-indices?symbol="+Indices[0]
usename = "pravin-9558824321"
headers = {
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en,en-US;q=0.9,hi;q=0.8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
    }


# this function is for current time___________________________________________
def currenttime():
    local_timezone = timedelta(hours=5, minutes=30)  # India timezone offset is UTC+5:30
    curr_time = datetime.utcnow() + local_timezone
    curr_time = curr_time.strftime("%H:%M:%S")
    return curr_time


#this function is to get ALL the live data from NSE_________________________________
def GetOCdatafromwebsite(url, headers, Indices):
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



#this function is to only Current Expriy Data_________________________________________
def Getdataorganised(Data):    
    newdf_oc = pd.DataFrame()

    #orgainsing the data and chaning the name of columns
    newdf_oc['Expiry'] = pd.to_datetime(Data ['expiryDate'])
    current_expriry = newdf_oc['Expiry'].min()
    newdf_oc['Current_Expiry'] = (newdf_oc['Expiry'] == current_expriry)
    newdf_oc ['CE/PE'] = Data['instrumentType'] 
    newdf_oc['strikePrice'] = Data['strikePrice']
    newdf_oc ['OI'] = Data['openInterest']
    newdf_oc['Change in OI'] = Data['changeinOpenInterest']
    newdf_oc['Volume'] = Data['totalTradedVolume']
    newdf_oc['LTP'] = Data['lastPrice']

    
    #making seperate dataframe of calls and put and combined data frame
    ceop = newdf_oc[(newdf_oc['CE/PE'] == 'CE') & (newdf_oc['Current_Expiry'] == True)]
    peop = newdf_oc[(newdf_oc['CE/PE'] == 'PE') & (newdf_oc['Current_Expiry'] == True)]
    finalOC = ceop.merge(peop, on = 'strikePrice', how = 'outer')
    

    #deleting the unnecessary columns
    finalOC = finalOC.drop(['Expiry_y', 'Current_Expiry_x', 'Current_Expiry_y'], axis = 1)
    ceop = ceop.drop(['Expiry', 'Current_Expiry'], axis = 1)
    peop = peop.drop(['Expiry', 'Current_Expiry'], axis = 1)

    #Deleting the zero values
    finalOC.dropna(inplace = True)
    ceop.dropna(inplace = True)
    peop.dropna(inplace = True)

    # rearranging the Columns as per needed
    newcolums = ['Expiry_x',
                 'Change in OI_x','Volume_x','OI_x', 'LTP_x',
                 'strikePrice',
                 'LTP_y', 'OI_y', 'Volume_y', 'Change in OI_y']
    finalOC = finalOC[newcolums]
    #naming the proper columns
    finalOC.columns = ['Expiry_date',
                       'Change in OI(CE)','Volume(CE)', 'OI(CE)', 'LTP(CE)',
                        'strikePrice',
                       'LTP(PE)',  'OI(PE)','Volume(PE)', 'Change in OI(PE)']



    # Sort the dataframe by strikePrice
    finalOC = finalOC.sort_values(by='strikePrice', ascending=True)

    return finalOC, ceop, peop


# This function is for Specific strike price only
def get_updateddata(finalOC, current_market_price, ceop, peop):
    listofsp = []
    
    # Getting the targeted stike prices
    for i in range(len(finalOC['strikePrice'])):
        difference = current_market_price - int(finalOC.iloc[i]['strikePrice'])
        if difference <= 100 and difference > 0:
            x = finalOC.iloc[i]['strikePrice']
            listofsp.append(x)
            
        elif difference >= -100 and difference < 0:
            x = finalOC.iloc[i]['strikePrice']
            listofsp.append(x)

    
    listofsp.sort(reverse=True)  # Sort the list in descending order


    # Getting the data of given strike price
    OCforuse = finalOC[finalOC['strikePrice'].isin(listofsp)]
    onlycalldata = ceop[ceop['strikePrice'].isin(listofsp)]
    onlyputdata = peop[peop['strikePrice'].isin(listofsp)]    
    
    # grouping the data for proper view__________________________
    OCforuse = OCforuse.groupby('strikePrice').tail(1)
    onlycalldata = onlycalldata.groupby('strikePrice').tail(1)
    onlyputdata = onlyputdata.groupby('strikePrice').tail(1)

    #deleting duplicate rows
    #OCforuse = OCforuse.to_duplicate()
    
    return OCforuse, onlyputdata, onlycalldata


# this function is only for calculation of new row for PCR. This will only give the Row for PCR
def PCRcalulation(PCRD, count):    
    signal = 0
    curr_clock = currenttime()
    
    #calling all the functions one by one
    Data, current_market_price = GetOCdatafromwebsite(url, headers, Indices)
    curr_clock = currenttime()
    finalOC, ceop, peop = Getdataorganised(Data)

    OCforuse,allputdata, allcalldata = get_updateddata(finalOC, current_market_price, ceop, peop)
    
    newdf = OCforuse.copy()
    TotalPE = newdf['OI(PE)'].sum()
    TotalCE = newdf['OI(CE)'].sum()
    TotalOI = TotalPE - TotalCE
    PCR = TotalPE/TotalCE
    if TotalOI > 0:
        signal = 'Buy'
    if TotalOI < 0:
        signal = 'Sell'
    newrow = [curr_clock, TotalCE, TotalPE, TotalOI, PCR, signal]

    # this code is very important and needed to add rows in PCR dataframe
    
    PCRD.loc[len(PCRD.index)] =  newrow # instead of 0 we need to write a i of for loop
    
    return PCRD, count
    

# Userdefied Strikeprice and range of strickeprice to get data
def selectaccmaxpain(maxpain, selectofsp, finalOC):
    listofsp = []
    y = 0
    # Getting the targeted stike prices
    for i in range(len(finalOC['strikePrice'])):
        if maxpain == int(finalOC.iloc[i]['strikePrice']):
            for x in range(selectofsp):
                y = y + 50
                a = y + maxpain
                listofsp.append (a)
                b =  maxpain - y
                listofsp.append (b)


    listofsp.append(maxpain)
    listofsp.sort(reverse=True)  # Sort the list in descending order

    # Getting the data of given strike price
    OCforuse = finalOC[finalOC['strikePrice'].isin(listofsp)]  
    
    # grouping the data for proper view__________________________
    OCforuse = OCforuse.groupby('strikePrice').tail(1)
    
    return OCforuse





#PCR of Maxpain strike price
def MaxpainPCRofOI(OCforuse, PCRD):    
    signal = 0
    curr_clock = currenttime()
    
    #calling all the functions one buy one
    newdf = OCforuse.copy()
    TotalPE = newdf['OI(PE)'].sum()
    TotalCE = newdf['OI(CE)'].sum()
    TotalOI = TotalPE - TotalCE
    PCR = TotalPE/TotalCE
    if TotalOI > 0:
        signal = 'Buy'
    if TotalOI < 0:
        signal = 'Sell'
    newrow = [curr_clock, TotalCE, TotalPE, TotalOI, PCR, signal]

    # this code is very important and needed to add rows in PCR dataframe
    
    PCRD.loc[len(PCRD.index)] =  newrow # instead of 0 we need to write a i of for loop
    
    return PCRD


#PCR of Maxpain strike price of Volume
def MaxpainPCRofvolume(OCforuse, PCRDV):    
    signal = 0
    curr_clock = currenttime()
    columns =['Time', 'Total Volume of Call Writer','Total Volume of Put Writer', 'Difference','PCR', 'Signal']
    #calling all the functions one buy one
    newdf = OCforuse.copy()
    TotalPE = newdf['Volume(PE)'].sum()
    TotalCE = newdf['Volume(CE)'].sum()
    TotalOI = TotalPE - TotalCE
    PCR = TotalPE/TotalCE
    if TotalOI > 0:
        signal = 'Buy'
    if TotalOI < 0:
        signal = 'Sell'
    newrow = [curr_clock, TotalCE, TotalPE, TotalOI, PCR, signal]

    # this code is very important and needed to add rows in PCR dataframe
    
    PCRDV.loc[len(PCRDV.index)] =  newrow # instead of 0 we need to write a i of for loop
    PCRDV.columns = columns
    
    return PCRDV


# giving need to code more in this program. This is for indicator which need to combine with PCR
def indicatordata(increase_decrease_df):        
    Data, current_market_price = GetOCdatafromwebsite(url, headers,Indices)
    finalOC, ceop, peop = Getdataorganised(Data)

    OCforuse, onlyputdata, onlycalldata = get_updateddata(finalOC, current_market_price, ceop, peop)
    
    # Create a new DataFrame indicating if Volume and OI are increasing or decreasing
    increase_decrease_df = OCforuse.copy()
    
    increase_decrease_df['strikePrice'] = finalOC['strikePrice']
    increase_decrease_df['Volume(CE)_Increase'] = finalOC['Volume(CE)'].diff().gt(0)
    increase_decrease_df['Volume(CE)_Decrease'] = finalOC['Volume(CE)'].diff().lt(0)
    increase_decrease_df['Volume(PE)_Increase'] = finalOC['Volume(PE)'].diff().gt(0)
    increase_decrease_df['Volume(PE)_Decrease'] = finalOC['Volume(PE)'].diff().lt(0)
    increase_decrease_df['OI(CE)_Increase'] = finalOC['OI(CE)'].diff().gt(0)
    increase_decrease_df['OI(CE)_Decrease'] = finalOC['OI(CE)'].diff().lt(0)
    increase_decrease_df['OI(PE)_Increase'] = finalOC['OI(PE)'].diff().gt(0)
    increase_decrease_df['OI(PE)_Decrease'] = finalOC['OI(PE)'].diff().lt(0)
    for i in range(len(increase_decrease_df)):
        if increase_decrease_df.iloc[i]['OI(CE)_Increase'] == True and increase_decrease_df.iloc [i]['Volume(CE)_Increase'] == True:
           increase_decrease_df['Analysis'] = 'Long Build-up'

        if increase_decrease_df.iloc[i]['OI(CE)_Decrease'] == True and increase_decrease_df.iloc [i]['Volume(CE)_Increase'] == True:
           increase_decrease_df['Analysis'] = 'Long Unwinding'

        if increase_decrease_df.iloc[i]['OI(CE)_Decrease'] == True and increase_decrease_df.iloc [i]['Volume(CE)_Decrease'] == True:
           increase_decrease_df['Analysis'] = 'Long Unwinding'

           

        if increase_decrease_df.iloc[i]['OI(PE)_Increase'] == True and increase_decrease_df.iloc[i]['Volume(PE)_Increase'] == True:
           increase_decrease_df['indicator'] = 'Shorts Buil-up'     
        if increase_decrease_df.iloc[i]['OI(PE)_Decrease'] == True and increase_decrease_df.iloc[i]['Volume(PE)_Increase'] == True:
           increase_decrease_df['indicator'] = 'Shorts Unwinding'
        if increase_decrease_df.iloc[i]['OI(PE)_Decrease'] == True and increase_decrease_df.iloc[i]['Volume(PE)_Decrease'] == True:
           increase_decrease_df['indicator'] = 'Shorts Unwinding'

        else:
           increase_decrease_df['indicator'] = 'No chages'
           increase_decrease_df['Analysis'] = 'No Changes'
    

    newcolums = ['Expiry_date', 'Analysis', 'Change in OI(CE)', 'OI(CE)', 'Volume(CE)',
       'LTP(CE)', 'strikePrice', 'LTP(PE)', 'Volume(PE)', 'OI(PE)',
       'Change in OI(PE)', 'indicator', 'Volume(CE)_Increase', 'Volume(CE)_Decrease',
       'Volume(PE)_Increase', 'Volume(PE)_Decrease', 'OI(CE)_Increase',
       'OI(CE)_Decrease', 'OI(PE)_Increase', 'OI(PE)_Decrease']
    
    increase_decrease_df = increase_decrease_df[newcolums]
    
    return increase_decrease_df



# highest value of OI and Volumne and its strike price
def highestvalue(finalOC):
    all_data_timewise = finalOC.copy()
    Maximum_oi_PE = all_data_timewise['OI(PE)'].max()
    Maximum_oi_CE = all_data_timewise['OI(CE)'].max()
    Maximum_volumne_CE = all_data_timewise['Volume(CE)'].max()
    Maximum_volumne_PE = all_data_timewise['Volume(PE)'].max()
    for i in range(len(all_data_timewise)):
            if Maximum_oi_PE == all_data_timewise['OI(PE)'][i]:
                sp_oi_pe = all_data_timewise['strikePrice'][i]
            if Maximum_oi_CE == all_data_timewise['OI(CE)'][i]:
                sp_oi_ce = all_data_timewise['strikePrice'][i]
            if Maximum_volumne_CE == all_data_timewise['Volume(CE)'][i]:
                sp_vol_ce = all_data_timewise['strikePrice'][i]
            if Maximum_volumne_PE == all_data_timewise['Volume(PE)'][i]:
                sp_vol_pe = all_data_timewise['strikePrice'][i]
    Dfhv = pd.DataFrame(columns = ['index','Highest Call value', 'Stikeprice','Highest Put Value', 'Stikeprice'])
    Dfhv.loc[len(Dfhv.index)] = ['OI', Maximum_oi_CE, sp_oi_ce, Maximum_oi_PE, sp_oi_pe]
    Dfhv.loc[len(Dfhv.index)] = ['volume', Maximum_volumne_CE, sp_vol_ce, Maximum_volumne_PE, sp_vol_pe]
    Dfhv = Dfhv.set_index('index')
    #highlight the maximum value in both the side
    Dfhv.style.highlight_max(subset = ['OI(CE)', 'Volume(CE)', 'Volume(PE)', 'OI(PE)'])
    
    return Dfhv


def style_dataframe(df1):
    df = df1.copy()
    def apply_style(val):
        try:
            
            max_values = df[['Volume(PE)', 'OI(PE)', 'Change in OI(PE)']].max().values
            if np.isin(val, max_values):
                return 'background-color: green'
            
            max_values = df[['Change in OI(CE)', 'OI(CE)', 'Volume(CE)']].max().values
            if np.isin(val, max_values):
                return 'background-color: red'


            signal = df.iloc[-1]['Signal']
            print (signal)
            if signal == 'Buy':
                return 'background-color: green'
            
            if signal == 'Sell':
                return 'background-color: red'
            
            if val in ['Long Build-up', 'Shorts Unwinding']:
                return 'background-color: green'
            
            if val in ['Long Unwinding', 'Shorts Buil-up']:
                return 'background-color: red'
            
            # Add more conditions as needed
        except KeyError:
            # Handle the case where the columns do not exist in the DataFrame
            return ''

    # Apply CSS styles to DataFrame
    styled_df = df.style.applymap(apply_style).format({
        'Change in OI(CE)': '{:,}'.format,
        'OI(CE)': '{:,}'.format,
        'Volume(CE)': '{:,}'.format,
        'LTP(CE)': '{:,.2f}'.format,
        'Volume(PE)': '{:,}'.format,
        'OI(PE)': '{:,}'.format,
        'Change in OI(PE)': '{:,}'.format,
        'LTP(PE)': '{:,.2f}'.format,
        'Total Call Writer' :'{:,}'.format,
        'Total Put Writer': '{:,}'.format,
        'Difference' : '{:,}'.format,
        'PCR': '{:,.2f}'.format
    })

    # Add borders and light gray background color for header cells
    styled_df.set_table_styles([
        {'selector': 'th', 'props': [('border', '1px solid #dddddd'), ('background-color', '#f9f9f9')]},
        {'selector': 'td', 'props': [('border', '1px solid #dddddd')]},
    ])
    return styled_df



###########################################################################################################################################################################
# all in one coustimseed
"""
Data, current_market_price = GetOCdatafromwebsite(url, headers)
curr_clock = currenttime()
finalOC, finalOC_styled, ceop, peop = Getdataorganised(Data)

all_data_timewise = pd.DataFrame()



def dataframeforchart(maxpain, selectofsp, finalOC):
    listofsp = []
    y = 0
    
    # Getting the targeted stike prices
    for i in range(len(finalOC['strikePrice'])):
        if maxpain == int(finalOC.iloc[i]['strikePrice']):
            for x in range(selectofsp):
                y = y + 50
                a = y + maxpain
                listofsp.append (a)
                b =  maxpain - y
                listofsp.append (b)

    listofsp.append(maxpain)
    listofsp.sort(reverse=True)  # Sort the list in descending order
    for i in range(len(listofsp)):
        if listofsp[0] in finalOC['strikePrice'].values:
            b = finalOC[finalOC['strikePrice'] == listofsp[0]]
            
            print (b['strikePrice'])

    #add row in new dataframe
    a = finalOC[finalOC['strikePrice'].isin(listofsp)]
    return

maxpain = 19500
selectofsp = 2
dataframeforchart( maxpain, selectofsp, finalOC)

"""

###############################################################################3
# Flask Code to display an HTML link
@app.route('/')
def index():
    df = indicatordata(increase_decrease_df)
    
    # Copy only the necessary columns
    columnstocopy = ['Expiry_date', 'Analysis', 'Change in OI(CE)', 'OI(CE)', 'Volume(CE)',
                     'LTP(CE)', 'strikePrice', 'LTP(PE)', 'Volume(PE)', 'OI(PE)',
                     'Change in OI(PE)', 'indicator']
    df1 = df[columnstocopy].copy()
    # Assuming df is your DataFrame
    # Apply styling to the DataFrame
    styled_df = style_dataframe(df1)
    
    # Convert the styled DataFrame to HTML
    styled_html = styled_df.to_html(classes='styled-table', escape=False)

    # Render the template with styled HTML
    return render_template('index.html', df1 = styled_html)

#return render_template('index.html', df1=html_table)

#return render_template ('index.html', df1 = df1.to_html())

@app.route('/TargetedstrikepricandPCR')
def TargetedstrikepricandPCR():
    count = 0
    while True:            
        #calling all the functions one buy one
        Data, current_market_price = GetOCdatafromwebsite(url, headers,Indices)
        curr_clock = currenttime()
        finalOC, ceop, peop = Getdataorganised(Data)
        OCforuse,allputdata, allcalldata = get_updateddata(finalOC, current_market_price, ceop, peop)
        new_df ,count = PCRcalulation(PCRD, count)
        df2 = new_df.sort_index(ascending = False)
        df1 = OCforuse

        styled_df1 = style_dataframe(df1)
        styled_df2 = style_dataframe(df2)
        

        # Convert the styled DataFrame to HTML
        styled_html1 = styled_df1.to_html(classes='styled-table', escape=False)
        styled_html2 = styled_df2.to_html(classes='styled-table', escape=False)
        
        
        return render_template ('TargetedstrikepricandPCR.html', df1 = styled_html1, df2 = styled_html2)

@app.route('/maxpain', methods = ['GET','POST'])
def maxpain():
    operation = "1"
    request_method = request.method
    maxpain = 0
    res=0
    if request.method == 'POST':       
        maxpain = int(request.form['Maxpain'])
        selectofsp = int(request.form['Price_range'])
        operation = request.form.get('mycheckbox')


        Data, current_market_price = GetOCdatafromwebsite(url, headers, Indices)
        curr_clock = currenttime()
        finalOC, ceop, peop = Getdataorganised(Data)

        if operation == "1":
            OCforuse = selectaccmaxpain(maxpain, selectofsp, finalOC)
        if operation == "2":
            OCforuse = selectaccmaxpain(maxpain, selectofsp, ceop)
        if operation == "3":
            OCforuse = selectaccmaxpain(maxpain, selectofsp, peop)
            
        df1 = OCforuse

    elif request.method == 'GET':
        maxpain = request.args.get('Maxpain', type=int)
        selectofsp = request.args.get('Price_range', type=int)
        operation = request.args.get('mycheckbox')

        Data, current_market_price = GetOCdatafromwebsite(url, headers, Indices)
        curr_clock = currenttime()
        finalOC, ceop, peop = Getdataorganised(Data)

        OCforuse = selectaccmaxpain(maxpain, selectofsp, finalOC)

        if operation == "1":
            OCforuse = selectaccmaxpain(maxpain, selectofsp, finalOC)
        if operation == "2":
            OCforuse = selectaccmaxpain(maxpain, selectofsp, ceop)
        if operation == "3":
            OCforuse = selectaccmaxpain(maxpain, selectofsp, peop)

        df1 = OCforuse
    OIPCR = MaxpainPCRofOI(OCforuse, PCRD)
    VolumePCR = MaxpainPCRofvolume(OCforuse, PCRDV)
    Dfhv = highestvalue(finalOC)
    df2 = OIPCR.sort_index(ascending = False)
    df3 = VolumePCR.sort_index(ascending = False)
    df4 = Dfhv

    
    styled_df1 = style_dataframe(df1)
    styled_df2 = style_dataframe(df2)
    styled_df3 = style_dataframe(df3)

    # Convert the styled DataFrame to HTML
    styled_html1 = styled_df1.to_html(classes='styled-table', escape=False)
    styled_html2 = styled_df2.to_html(classes='styled-table', escape=False)
    styled_html3 = styled_df3.to_html(classes='styled-table', escape=False)
    styled_html4 = df4.to_html(classes='dataframe-table', escape=False) # Ensure no formatting is applied


    # Render the template with styled HTML
    return render_template('maxpain.html', df1=styled_html1, df2=styled_html2, df3=styled_html3, df4=styled_html4)

#    return render_template ('maxpain.html', df1 = df1.to_html(), df2 = df2.to_html(), df3 = df3.to_html(), df4 = df4.to_html())


if __name__ == '__main__':
    app.run()
##############################################################################3

