# 数据分析 Agent（Ask-Your-Data）

用自然语言问数据库，Agent 自动生成并执行 SQL、报错自纠错、给出结论。定位是「行动型 AI Agent」作品，适合放进简历。

## 架构
- `db.py`：SQLite 数据层（内置示例电商数据），提供 schema 描述与只读查询
- `agent.py`：核心执行循环 —— LLM 工具调用（`get_schema` / `run_sql`）+ 报错重试
- `app.py`：Streamlit 交互界面（推理步骤 + SQL + 结果表 + 自动图表 + 回答）
- `cli.py`：命令行入口，快速调试

## 快速开始
1. 安装依赖：`pip install -r requirements.txt`
2. 配置密钥：复制 `.env.example` 为 `.env`，填入 `LLM_API_KEY`
3. 命令行试跑：`python cli.py "上季度哪个产品类别的利润最高？"`
4. 打开界面：`streamlit run app.py`

## 切换模型后端
改 `.env` 三项即可（均为 OpenAI 兼容接口）：
- DeepSeek：`https://api.deepseek.com`，`deepseek-chat`
- 通义千问：`https://dashscope.aliyuncs.com/compatible-mode/v1`，`qwen-plus`
- 智谱 GLM：`https://open.bigmodel.cn/api/paas/v4`，`glm-4-plus`
