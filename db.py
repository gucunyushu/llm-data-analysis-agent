"""数据层：内置示例电商数据 → SQLite，提供 schema 描述与只读查询能力。"""
import os
import random
import sqlite3
from datetime import date, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "analytics.db")

CATEGORIES = ["手机", "电脑", "家电", "服饰", "美妆", "食品"]
REGIONS = ["华东", "华北", "华南", "西南", "东北"]


def _init_db():
    """首次运行时生成一套确定性的示例数据（固定随机种子，保证可复现）。"""
    random.seed(42)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript("""
        PRAGMA foreign_keys = ON;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS products;
        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL
        );
        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY,
            order_date TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            region TEXT NOT NULL,
            units_sold INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            cost REAL NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        );
    """)

    # 产品表：6 个类别 × 每个 4 个商品 = 24 个商品
    products = []
    pid = 1
    for cat in CATEGORIES:
        for i in range(1, 5):
            products.append((pid, f"{cat}-商品{i}", cat))
            pid += 1
    cur.executemany("INSERT INTO products VALUES (?, ?, ?)", products)

    # 订单表：过去 180 天，每天随机若干条
    start = date(2026, 4, 20)
    orders = []
    oid = 1
    for day in range(180):
        d = start + timedelta(days=day)
        for _ in range(random.randint(8, 15)):
            pid = random.randint(1, len(products))
            units = random.randint(1, 30)
            price = round(random.uniform(20, 5000), 2)
            cost = round(price * random.uniform(0.5, 0.8), 2)
            region = random.choice(REGIONS)
            orders.append((oid, d.isoformat(), pid, region, units, price, cost))
            oid += 1
    cur.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?)", orders)
    conn.commit()
    conn.close()


def get_connection():
    if not os.path.exists(DB_PATH):
        _init_db()
    return sqlite3.connect(DB_PATH)


def get_schema() -> str:
    """返回给 LLM 看的表结构描述 + 低基数文本字段的示例取值（帮助写对 WHERE 条件）。"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]

    parts = []
    for t in tables:
        cur.execute(f"PRAGMA table_info({t})")
        cols = cur.fetchall()
        col_desc = ", ".join(f"{c[1]} {c[2]}" for c in cols)
        parts.append(f"表 {t} ({col_desc})")

    for t in tables:
        cur.execute(f"PRAGMA table_info({t})")
        for c in cur.fetchall():
            cname, ctype = c[1], c[2]
            if ctype.upper() in ("TEXT", "VARCHAR", "CHAR"):
                cur.execute(f"SELECT COUNT(DISTINCT {cname}) FROM {t}")
                if cur.fetchone()[0] <= 15:
                    cur.execute(f"SELECT DISTINCT {cname} FROM {t} LIMIT 20")
                    vals = [str(r[0]) for r in cur.fetchall()]
                    parts.append(f"表 {t}.{cname} 示例取值: {', '.join(vals)}")
    conn.close()
    return "\n".join(parts)


def run_query(sql: str):
    """执行一条 SQL，返回 (列名列表, 行列表)。"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description] if cur.description else []
    conn.close()
    return cols, rows
