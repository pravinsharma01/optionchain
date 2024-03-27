from optionchain_new import app, GetOCdatafromwebsite 


headers = {
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en,en-US;q=0.9,hi;q=0.8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
    }


#########################################################################################3
import asyncio
import aiohttp
from optionchain_new import app, GetOCdatafromwebsite 


async def read_proxies_from_file(filename):
    proxies = []
    with open(filename, 'r') as file:
        for line in file:
            proxy = line.strip()
            proxies.append(proxy)
    return proxies

async def rotate_proxies_and_send_requests(url, url1, proxies):
    for proxy in proxies:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, proxy=f'http://{proxy}', timeout=5) as response:
                    if response.status == 200:
                        print(f"Using Proxy: {proxy}, Status Code: {response.status}")
                        # If the request is successful, fetch data from the NSE India API
                        Data, current_market_price = await GetOCdatafromwebsite(url1, headers, Indices)
                        # Perform further processing with the fetched data
                        break  # Exit the loop if a successful response is received
        except Exception as e:
            print(f"Proxy: {proxy}, Error: {str(e)}")
            # If the request fails, try the next proxy


# Define your URL
Indices = ["NIFTY", "FINNIFTY", "BANKNIFTY", "MIDCPNIFTY"]

url = 'http://httpbin.org/ip'
url1 = "https://www.nseindia.com/api/option-chain-indices?symbol="+Indices[0]

# Read proxies from file
proxies = asyncio.run(read_proxies_from_file('proxylist.txt'))

# Call the function for rotating proxies and sending requests
rotate_proxies_and_send_requests(url, url1, proxies)


#########################################################################################3

app.run()

