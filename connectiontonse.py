import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import nse


nse.nse()
df, current_market_price = nse.convertintodataframe()
st.write(""" #My first App *""")
st.dataframe(df)
