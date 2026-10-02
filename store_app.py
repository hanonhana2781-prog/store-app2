import sqlite3
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

# إعداد قاعدة البيانات
def init_db():
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            barcode TEXT,
            category TEXT,
            buy_price REAL,
            sell_price REAL,
            qty INTEGER,
            min_limit INTEGER,
            supplier TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT,
            qty_sold INTEGER,
            total_price REAL,
            payment_method TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

# قالب HTML متجاوب وعصري للوحة التحكم
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>copy & write</title>
    <style>
        body { font-family: Tahoma, sans-serif; background: #f5f6fa; margin: 0; padding: 20px; }
        h1 { color: #2f3640; text-align: center; }
        .nav { text-align: center; margin-bottom: 20px; }
        .nav a { background: #7158e2; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 0 5px; font-weight: bold; }
        .nav a:hover { background: #3b3193; }
        .container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); max-width: 900px; margin: auto; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #dcdde1; padding: 10px; text-align: center; }
        th { background: #2f3640; color: white; }
        input, select { padding: 8px; margin: 5px; width: calc(50% - 20px); }
        button { background: #4cd137; color: white; border: none; padding: 10px 20px; font-weight: bold; border-radius: 5px; cursor: pointer; width: 100%; margin-top: 10px; }
        .shortage { background-color: #ffcccc !important; }
    </style>
</head>
<body>
    <h1> (copy & write )</h1>
    <div class="nav">
        <a href="/">📦 المخزون</a>
        <a href="/sales">🛒 المبيعات</a>
        <a href="/shortages">⚠️ النواقص</a>
        <a href="/reports">📊 التقارير</a>
    </div>
    <div class="container">
        {% if page == 'inventory' %}
            <h2>إضافة صنف جديد </h2>
            <form action="/add" method="POST">
                <input type="text" name="name" placeholder="اسم الصنف" required>
                <input type="text" name="barcode" placeholder="الباركود / الكود">
                <input type="text" name="category" placeholder="التصنيف">
                <input type="number" step="0.01" name="buy_price" placeholder="سعر الشراء" required>
                <input type="number" step="0.01" name="sell_price" placeholder="سعر البيع" required>
                <input type="number" name="qty" placeholder="الكمية الحالية" required>
                <input type="number" name="min_limit" placeholder="الحد الأدنى للمخزون" required>
                <input type="text" name="supplier" placeholder="المورد">
                <button type="submit">حفظ الصنف</button>
            </form>
            <hr>
            <h2>قائمة المخزون الحالي</h2>
            <table>
                <tr>
                    <th>المسلسل</th>
                    <th>اسم الصنف</th>
                    <th>الباركود</th>
                    <th>التصنيف</th>
                    <th>شراء</th>
                    <th>بيع</th>
                    <th>الكمية</th>
                    <th>الحد الأدنى</th>
                    <th>المورد</th>
                </tr>
                {% for item in items %}
                <tr class="{{ 'shortage' if item[6] <= item[7] else '' }}">
                    <td>{{ item[0] }}</td>
                    <td>{{ item[1] }}</td>
                    <td>{{ item[2] }}</td>
                    <td>{{ item[3] }}</td>
                    <td>{{ item[4] }}</td>
                    <td>{{ item[5] }}</td>
                    <td><b>{{ item[6] }}</b></td>
                    <td>{{ item[7] }}</td>
                    <td>{{ item[8] }}</td>
                </tr>
                {% endfor %}
            </table>

        {% elif page == 'sales' %}
            <h2>تسجيل عملية بيع جديدة</h2>
            <form action="/process_sale" method="POST">
                <input type="text" name="query" placeholder="اسم الصنف أو الباركود" style="width: 100%;" required>
                <input type="number" name="qty_sold" placeholder="الكمية المباعة" style="width: 100%;" required>
                <select name="payment_method" style="width: 100%; padding: 8px; margin: 5px 0;">
                    <option value="كاش">كاش</option>
                    <option value="فيزا">فيزا</option>
                    <option value="انستا  ">انستا</option>
                </select>
                <button type="submit" style="background: #e84118;">إتمام البيع وخصم المخزون</button>
            </form>

        {% elif page == 'shortages' %}
            <h2>⚠️ الأصناف الناقصة (وصلت للحد الأدنى"يعني مفيش كتير")</h2>
            <table>
                <tr>
                    <th>اسم الصنف</th>
                    <th>الكمية الحالية</th>
                    <th>الحد الأدنى</th>
                    <th>المورد</th>
                </tr>
                {% for item in items %}
                <tr class="shortage">
                    <td>{{ item[1] }}</td>
                    <td><b>{{ item[6] }}</b></td>
                    <td>{{ item[7] }}</td>
                    <td>{{ item[8] }}</td>
                </tr>
                {% endfor %}
            </table>

        {% elif page == 'reports' %}
            <h2>📊 التقارير المالية</h2>
            <p>📌 إجمالي قيمة المخزون (بسعر الشراء): <b>{{ inv_value }} جنيه</b></p>
            <p>💰 إجمالي المبيعات: <b>{{ total_sales }} جنيه</b></p>
            <p>🛒 إجمالي عدد القطع المباعة: <b>{{ total_qty_sold }} قطعة</b></p>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory")
    items = cursor.fetchall()
    conn.close()
    return render_template_string(HTML_TEMPLATE, page='inventory', items=items)

@app.route('/add', methods=['POST'])
def add_item():
    name = request.form['name']
    barcode = request.form['barcode']
    category = request.form['category']
    buy_price = float(request.form['buy_price'])
    sell_price = float(request.form['sell_price'])
    qty = int(request.form['qty'])
    min_limit = int(request.form['min_limit'])
    supplier = request.form['supplier']

    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO inventory (name, barcode, category, buy_price, sell_price, qty, min_limit, supplier) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                   (name, barcode, category, buy_price, sell_price, qty, min_limit, supplier))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/sales')
def sales_page():
    return render_template_string(HTML_TEMPLATE, page='sales')

@app.route('/process_sale', methods=['POST'])
def process_sale():
    query = request.form['query']
    qty_sold = int(request.form['qty_sold'])
    payment_method = request.form['payment_method']

    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, sell_price, qty FROM inventory WHERE name=? OR barcode=?", (query, query))
    item = cursor.fetchone()

    if item:
        item_id, name, sell_price, current_qty = item
        if current_qty >= qty_sold:
            new_qty = current_qty - qty_sold
            total_price = sell_price * qty_sold
            cursor.execute("UPDATE inventory SET qty=? WHERE id=?", (new_qty, item_id))
            cursor.execute("INSERT INTO sales (item_name, qty_sold, total_price, payment_method) VALUES (?, ?, ?, ?)", (name, qty_sold, total_price, payment_method))
            conn.commit()
    conn.close()
    return redirect(url_for('sales_page'))

@app.route('/shortages')
def shortages_page():
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory WHERE qty <= min_limit")
    items = cursor.fetchall()
    conn.close()
    return render_template_string(HTML_TEMPLATE, page='shortages', items=items)

@app.route('/reports')
def reports_page():
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(qty * buy_price) FROM inventory")
    inv_value = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(total_price), SUM(qty_sold) FROM sales")
    sales_data = cursor.fetchone()
    total_sales = sales_data[0] or 0
    total_qty_sold = sales_data[1] or 0
    conn.close()
    return render_template_string(HTML_TEMPLATE, page='reports', inv_value=inv_value, total_sales=total_sales, total_qty_sold=total_qty_sold)

import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)