import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.price import get_crypto_price
import streamlit as st


st.set_page_config("Crypto Agent",layout="wide")
st.title("Crypto Agent")

coin = st.text_input("请输入你要查询的币种")
if st.button("查询"):
    try:
        with st.spinner("正在查询价格..."):
            res = get_crypto_price(coin)
            st.write(res)
    except Exception as e:
        st.error(e)
