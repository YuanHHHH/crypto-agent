import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.price import get_crypto_price
from src.tools.analyzer import analyze_coin
from src.tools.llm_client import llm_client
import streamlit as st


st.set_page_config("Crypto Agent",layout="wide")

with st.sidebar:
    st.title("Crypto Agent")
    st.write("v0.3")
    st.write("AI 加密货币分析助手")
    st.markdown("[GitHub](https://github.com/YuanHHHH/crypto-agent)")
st.title("Crypto Agent")

coins = ["bitcoin", "ethereum", "solana", "dogecoin", "ripple", "cardano"]
coin_selected = st.selectbox("选择币种", coins)
custom_coin = st.text_input("或手动输入币种（留空则用上面的选择）")
coin = custom_coin.strip() if custom_coin.strip() else coin_selected
col1, col2 = st.columns(2)

with col1:
    if st.button("查询价格"):
        try:
            with st.spinner("正在查询价格..."):
                res = get_crypto_price(coin)
                st.write(res)
        except Exception as e:
            st.error(f"查询失败: {e}")

with col2:
    if st.button("AI 分析"):
        try:
            with st.spinner("AI 分析中，请稍候..."):
                prompt = analyze_coin(coin)
                st.markdown(llm_client(prompt))
        except Exception as e:
            st.error(f"分析失败: {e}")


