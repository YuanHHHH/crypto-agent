"""
Crypto Agent Streamlit 前端入口
启动方式: streamlit run src/app.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.utils.exceptions import APIError,InvalidCoinError
from src.tools.price import get_crypto_price,load_price_history
from src.tools.analyzer import analyze_coin
from src.tools.market import get_market_overview,get_coin_market
from src.agent.agent_runner import AgentRunner
from src.agent.langchain_agent import langchain_agent_run
import streamlit as st
from src.utils.config import HISTORY_FILE
from dotenv import load_dotenv

load_dotenv()


st.set_page_config("Crypto Agent",layout="wide")
agent = AgentRunner()
with st.sidebar:
    st.title("Crypto Agent")
    st.write("v0.3")
    st.write("AI 加密货币分析助手")
    st.markdown("[GitHub](https://github.com/YuanHHHH/crypto-agent)")
    mode_choice = st.radio("开发者模式：",["开发模式","正常模式"])

st.title("Crypto Agent")

#「实时分析」|「市场概览」
tab1, tab2, tab3 = st.tabs(["实时分析","市场概览","历史记录"])
with tab1:
    coins = ["bitcoin", "ethereum", "solana", "dogecoin", "ripple", "cardano"]

    if "coin_index" not in st.session_state:
        st.session_state.coin_index = 0
    coin_selected = st.selectbox("选择币种", coins,index=st.session_state.coin_index)
    custom_coin = st.text_input("或手动输入币种（留空则用上面的选择）")
    coin = custom_coin.strip() if custom_coin.strip() else coin_selected
    agent_text = st.text_input("若要点击Agent模式，请在此输入要询问的问题")
    col1, col2, col3, col4 = st.columns(3)

    with col1:
        if st.button("查询价格"):
            try:
                with st.spinner("正在查询价格..."):
                    res = get_crypto_price(coin)
                    if coin in coins:
                        st.session_state.coin_index = coins.index(coin)
                st.toast(f"{coin} 价格查询完成")
                st.write(res)
            except InvalidCoinError as e:
                st.error("币种不存在，请检查输入")
                if mode_choice == "开发模式":
                    st.exception(e)
            except APIError as e:
                st.error("CoinGecko API 请求失败，请稍后重试")
                if mode_choice == "开发模式":
                    st.exception(e)
            except Exception as e:
                st.error(f"未知错误: {e}")
                if mode_choice == "开发模式":
                    st.exception(e)

    with col2:
        if st.button("AI 分析"):
            try:
                with st.spinner("AI 分析中，请稍候..."):
                    res = analyze_coin(coin)
                    st.markdown(res)
                    st.success(f"分析成功：{coin}")
            except InvalidCoinError as e:
                st.error("币种不存在，请检查输入")
                if mode_choice == "开发模式":
                    st.exception(e)
            except APIError as e:
                st.error("API 请求失败，请稍后重试")
                if mode_choice == "开发模式":
                    st.exception(e)
            except Exception as e:
                st.error(f"AI 分析失败: {e}")
    with col3:
        if st.button("Agent模式:手写版"):
            if not agent_text.strip():
                st.warning("请先在上方输入框输入你的问题")
            else:
                try:
                    with st.spinner("Agent分析中，请稍候..."):
                        answer,step_log = agent.run(agent_text)
                        for step_info in step_log:
                            step_num = step_info.get("step","?")
                            step_type = step_info.get("type","?")
                            with st.expander(f"步骤{step_num}：{step_type}"):
                                if step_info.get("thought"):
                                    st.markdown(f"**💭 Thought:** {step_info['thought']}")
                                if step_type == "action":
                                    st.markdown(f"**🔧 Action:** `{step_info['action']}`")
                                    st.markdown(f"**📥 Action Input:** `{step_info['action_input']}`")
                                    st.markdown(f"**📤 Observation:** {step_info.get('observation', '')}")
                                elif step_type == "final_answer":
                                    st.markdown(f"**✅ Final Answer:** {step_info['final_answer']}")
                                elif step_type == "no_parsed":
                                    st.markdown(f"**⚠️ Raw Text:** {step_info.get('raw_text', '')}")
                                elif step_type == "error":
                                    st.markdown(f"**❌ Error:** {step_info.get('observation', '')}")

                        st.markdown("---")
                        st.markdown("### 最终答案")
                        st.markdown(answer)
                        st.success("Agent分析成功")
                except Exception as e:
                    st.error(f"AI 分析失败: {e}")
    with col4:
        if st.button("Agent模式:langchain版"):
            if not agent_text.strip():
                st.warning("请先在上方输入框输入你的问题")
            else:
                try:
                    with st.spinner("Agent分析中，请稍候..."):
                        answer,step_log = agent.run(agent_text)
                        for step_info in step_log:
                            step_num = step_info.get("step","?")
                            step_type = step_info.get("type","?")
                            with st.expander(f"步骤{step_num}：{step_type}"):
                                if step_info.get("thought"):
                                    st.markdown(f"**💭 Thought:** {step_info['thought']}")
                                if step_type == "action":
                                    st.markdown(f"**🔧 Action:** `{step_info['action']}`")
                                    st.markdown(f"**📥 Action Input:** `{step_info['action_input']}`")
                                    st.markdown(f"**📤 Observation:** {step_info.get('observation', '')}")
                                elif step_type == "final_answer":
                                    st.markdown(f"**✅ Final Answer:** {step_info['final_answer']}")
                                elif step_type == "no_parsed":
                                    st.markdown(f"**⚠️ Raw Text:** {step_info.get('raw_text', '')}")
                                elif step_type == "error":
                                    st.markdown(f"**❌ Error:** {step_info.get('observation', '')}")

                        st.markdown("---")
                        st.markdown("### 最终答案")
                        st.markdown(answer)
                        st.success("Agent分析成功")
                except Exception as e:
                    st.error(f"AI 分析失败: {e}")


with tab2:
    try:
        with st.spinner("加载市场数据..."):

            st.subheader("全球市场概览")
            try:
                overview = get_market_overview()
            except APIError as e:
                st.error("API 请求失败")
                if mode_choice == "开发模式":
                    st.exception(e)
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("总市值 (USD)", f"${overview['total_market_cap_usd']:,.0f}")
            with m2:
                st.metric("BTC 市占率", f"{overview['btc_dominance']:.1f}%")
            with m3:
                st.metric("24h 市值变化", f"{overview['market_cap_change_24h']:.2f}%", delta=f"{overview['market_cap_change_24h']:.2f}%")

            st.subheader("单币种详情")
            coin_selected = st.selectbox("选择币种查看详情", coins, key="detail_coin")
            try:
                detail = get_coin_market(coin_selected)
            except InvalidCoinError as e:
                st.error("币种不存在")
                if mode_choice == "开发模式":
                    st.exception(e)
            except APIError as e:
                st.error("API 请求失败")
                if mode_choice == "开发模式":
                    st.exception(e)

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


with tab3:
    st.subheader("历史查询记录")
    history_coin_selected = st.selectbox("选择币种", ["全部记录"]+coins,key="history_coins")
    history_custom_coin = st.text_input("或手动输入币种（留空则用上面的选择）",key="history_custom_coin")
    history_coin = history_custom_coin.strip() if history_custom_coin.strip() else history_coin_selected
    limit = st.number_input("显示条数", min_value=1, max_value=100, value=20,key = "history_limit")

    try:
        with st.spinner("查找历史中"):
            records = load_price_history(HISTORY_FILE)
            if history_coin != "全部记录":
                filtered = [record for record in records if record.get("symbol") == history_coin]
            else:
                filtered = records
            filtered = filtered[:limit]

            if filtered:
                st.dataframe(filtered)
                st.write(f"共 {len(filtered)} 条记录")
            else:
                st.warning("没有找到相关记录")
    except Exception as e:
        st.error(f"加载历史记录失败: {e}")
