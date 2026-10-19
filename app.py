"""Streamlit 界面：提问 → 展示 agent 的推理步骤、SQL、结果表、自动图表与最终回答。"""
import pandas as pd
import streamlit as st

import agent
import config
import db

st.set_page_config(page_title="数据分析 Agent", page_icon="📊", layout="wide")
st.title("📊 自然语言数据分析 Agent")


def _render_chart(data):
    """简单启发式：结果有 ≥2 列且含数值列时，自动画柱状图 / 折线图。"""
    if data.shape[1] < 2:
        return
    numeric = data.select_dtypes(include="number").columns.tolist()
    if not numeric:
        return
    x, y = data.columns[0], numeric[-1]
    sub = data[[x, y]].copy()
    parsed = pd.to_datetime(sub[x], errors="coerce")
    if parsed.notna().mean() > 0.8 and sub.shape[0] > 1:
        sub[x] = parsed
        st.line_chart(sub.set_index(x))
    elif sub.shape[0] <= 30:
        st.bar_chart(sub.set_index(x)[y])


with st.sidebar:
    st.header("配置")
    st.write(f"模型：`{config.MODEL}`")
    st.write(f"接口：`{config.BASE_URL}`")
    st.caption("改 .env 里的 LLM_BASE_URL / LLM_MODEL 可切换 DeepSeek / Qwen / GLM")
    if st.button("查看数据库结构"):
        st.code(db.get_schema())

question = st.text_input(
    "用中文提问，例如：", placeholder="上季度哪个产品类别的利润最高？各区域的销售额排名？"
)

if st.button("开始分析") and question:
    try:
        with st.spinner("Agent 分析中…"):
            result = agent.answer(question)
    except Exception as e:
        st.error(f"出错了：{e}")
        st.stop()

    st.subheader("📝 回答")
    st.write(result["answer"])

    if result["steps"]:
        st.subheader("🔍 推理过程")
        for i, s in enumerate(result["steps"], 1):
            with st.expander(f"步骤 {i}：调用工具 {s['tool']}"):
                if s["tool"] == "run_sql":
                    st.code(s["args"].get("sql", ""), language="sql")
                else:
                    st.code(str(s["args"]))
                st.caption("返回：")
                st.code(s["result"][:1500])

    data = result.get("data")
    if data is not None and not data.empty:
        st.subheader("📈 结果数据")
        st.dataframe(data)
        _render_chart(data)
