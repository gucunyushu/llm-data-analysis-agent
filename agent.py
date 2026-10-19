"""Agent 核心：带工具调用（function calling）的执行循环。"""
import json
import pandas as pd
from openai import OpenAI

import config
import db

SYSTEM_PROMPT = """你是一个数据分析助手。用户会用中文提问，你需要查询 SQLite 数据库后给出答案。

规则：
1. 数据库 schema 已放在系统提示里，直接根据它写 SQL；如不确定可调用 get_schema 重新确认。
2. 用 run_sql 执行查询，SQL 使用 SQLite 语法，只允许 SELECT / WITH 开头的只读查询。
3. 查询可能返回很多行时，用 GROUP BY 聚合或加 LIMIT（最多 50 行）。
4. SQL 报错时，根据错误信息修正后重试，最多重试 3 次。
5. 拿到结果后，用中文简洁作答：给出关键数字、结论，可补一句业务含义；金额保留 2 位小数。
6. 不要复述整张表，只讲与问题相关的结论。"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_schema",
            "description": "查看数据库的表结构、字段以及部分文本字段的示例取值",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_sql",
            "description": "对 SQLite 数据库执行一条只读 SELECT 查询，返回结果行",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "要执行的 SQL（仅允许 SELECT / WITH 开头）"}
                },
                "required": ["sql"],
            },
        },
    },
]


def _run_sql(sql):
    """执行 SQL，返回 (给 LLM 看的文本, 供前端展示的 DataFrame 或 None)。"""
    sql = (sql or "").strip()
    if not sql:
        return "错误：sql 参数为空", None
    head = sql.lstrip().upper()
    if not (head.startswith("SELECT") or head.startswith("WITH")):
        return "错误：只允许只读的 SELECT 查询", None
    try:
        cols, rows = db.run_query(sql)
        if not cols:
            return "查询成功，但没有返回数据。", None
        df = pd.DataFrame(rows, columns=cols)
        text = df.head(50).to_string(index=False)
        if len(df) > 50:
            text += f"\n（共 {len(df)} 行，已截断到前 50 行）"
        return text, df
    except Exception as e:
        return f"SQL 执行出错：{e}", None


def _call_tool(name, args):
    if name == "get_schema":
        return db.get_schema(), None
    if name == "run_sql":
        return _run_sql(args.get("sql", ""))
    return f"未知工具：{name}", None


def answer(question: str) -> dict:
    """执行 agent 循环，返回 {"answer": 最终回答, "steps": 工具调用记录, "data": 最后一张结果表}。"""
    config.check_config()
    client = OpenAI(api_key=config.API_KEY, base_url=config.BASE_URL)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + "\n\n当前数据库结构：\n" + db.get_schema()},
        {"role": "user", "content": question},
    ]

    steps = []
    last_df = None

    for _ in range(8):  # 最多 8 轮，防止死循环
        resp = client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            tools=TOOLS,
            temperature=0.1,
        )
        msg = resp.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            return {"answer": msg.content or "（未返回内容）", "steps": steps, "data": last_df}

        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            text, df = _call_tool(name, args)
            if df is not None:
                last_df = df
            steps.append({"tool": name, "args": args, "result": text})
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": text[:4000],  # 截断，防止超长结果撑爆上下文
            })

    return {"answer": "（达到最大轮数，仍未完成）", "steps": steps, "data": last_df}
