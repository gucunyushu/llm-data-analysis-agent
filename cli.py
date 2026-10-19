"""命令行入口：python cli.py "你的问题" —— 快速调试，不依赖 Streamlit。"""
import sys

import agent


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "上季度哪个产品类别的利润最高？"
    print(f"问题：{q}\n")
    result = agent.answer(q)
    for i, s in enumerate(result["steps"], 1):
        print(f"--- 步骤 {i}: {s['tool']} ---")
        if s["tool"] == "run_sql":
            print(f"SQL:\n{s['args'].get('sql', '')}")
        print(f"返回（截断）:\n{s['result'][:800]}\n")
    print("=== 回答 ===")
    print(result["answer"])


if __name__ == "__main__":
    main()
