import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.price import get_crypto_price
from src.tools.analyzer import analyze_coin
from src.tools.llm_client import llm_client
from src.tools.market import get_market_overview,get_coin_market
import streamlit as st


st.set_page_config("Crypto Agent",layout="wide")

with st.sidebar:
    st.title("Crypto Agent")
    st.write("v0.3")
    st.write("AI 加密货币分析助手")
    st.markdown("[GitHub](https://github.com/YuanHHHH/crypto-agent)")
st.title("Crypto Agent")

#「实时分析」|「市场概览」
tab1, tab2 = st.tabs(["实时分析","市场概览"])
with tab1:
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

with tab2:
    try:
        with st.spinner("加载市场数据..."):

            st.subheader("全球市场概览")
            overview = get_market_overview()
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("总市值 (USD)", f"${overview['total_market_cap_usd']:,.0f}")
            with m2:
                st.metric("BTC 市占率", f"{overview['btc_dominance']:.1f}%")
            with m3:
                st.metric("24h 市值变化", f"{overview['market_cap_change_24h']:.2f}%", delta=f"{overview['market_cap_change_24h']:.2f}%")

            st.subheader("单币种详情")
            coin_selected = st.selectbox("选择币种查看详情", coins, key="detail_coin")
            detail = get_coin_market(coin_selected)
            d1, d2 = st.columns(2)
            with d1:
                st.metric("24h 涨跌", f"{detail['price_change_24h']}",delta=f"{detail['price_change_24h']:.2f}")
                st.metric("市值", f"${detail['market_cap']:,.0f}")
            with d2:
                st.metric("24h 最高", f"${detail['high_24h']}")
                st.metric("24h 最低", f"${detail['low_24h']}")
                st.metric("历史最高 (ATH)", f"${detail['ath']}")
                with st.expander("查看更多数据"):
                    st.write(f"总成交量: ${detail.get('total_volume', 'N/A'):,.0f}")
    except Exception as e:
        st.error(f"市场数据加载失败: {e}")
