import streamlit as st
import requests
import pandas as pd
import nse

df, current_market_price = nse.convertintodataframe()
st.write(""" #My first App *""")
st.dataframe(df)
