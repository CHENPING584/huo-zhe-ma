from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import datetime
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # 用于会话加密

# 授权码
AUTHORIZATION_CODE = "LYY996"

# 数据库配置
DATABASE = "sign_in.db"

# 初始化数据库
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # 创建用户表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 创建签到记录表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sign_records (
        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        sign_date TEXT NOT NULL,
        sign_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        consecutive_missed INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    ''')
    
    conn.commit()
    conn.close()

# 检查用户是否已签到
def is_signed_in_today(user_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    today = datetime.date.today().strftime("%Y-%m-%d")
    cursor.execute("SELECT * FROM sign_records WHERE user_id = ? AND sign_date = ?", (user_id, today))
    result = cursor.fetchone()
    
    conn.close()
    return result is not None

# 获取连续签到天数
def get_consecutive_days(user_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # 获取最近的签到记录
    cursor.execute("SELECT sign_date FROM sign_records WHERE user_id = ? ORDER BY sign_date DESC", (user_id,))
    records = cursor.fetchall()
    
    if not records:
        return 0
    
    consecutive = 0
    today = datetime.date.today()
    
    for record in records:
        sign_date = datetime.datetime.strptime(record[0], "%Y-%m-%d").date()
        expected_date = today - datetime.timedelta(days=consecutive)
        
        if sign_date == expected_date:
            consecutive += 1
        else:
            break
    
    conn.close()
    return consecutive

# 获取最长连续签到天数
def get_longest_streak(user_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # 获取所有签到日期，按日期排序
    cursor.execute("SELECT sign_date FROM sign_records WHERE user_id = ? ORDER BY sign_date", (user_id,))
    records = cursor.fetchall()
    
    if not records:
        return 0
    
    longest_streak = 1
    current_streak = 1
    
    for i in range(1, len(records)):
        prev_date = datetime.datetime.strptime(records[i-1][0], "%Y-%m-%d").date()
        curr_date = datetime.datetime.strptime(records[i][0], "%Y-%m-%d").date()
        
        if (curr_date - prev_date).days == 1:
            current_streak += 1
            longest_streak = max(longest_streak, current_streak)
        else:
            current_streak = 1
    
    conn.close()
    return longest_streak

# 授权码验证页面
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        code = request.form.get("code")
        if code == AUTHORIZATION_CODE:
            session["authorized"] = True
            return redirect(url_for("home"))
        else:
            return render_template("login.html", error="授权码错误")
    return render_template("login.html")

# 主页面
@app.route("/home", methods=["GET", "POST"])
def home():
    if not session.get("authorized"):
        return redirect(url_for("login"))
    
    # 检查用户是否已登录
    user_id = session.get("user_id")
    username = session.get("username", "")
    email = session.get("email", "")
    
    consecutive_days = 0
    longest_streak = 0
    signed_in_today = False
    
    if user_id:
        consecutive_days = get_consecutive_days(user_id)
        longest_streak = get_longest_streak(user_id)
        signed_in_today = is_signed_in_today(user_id)
    
    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "save_user":
            # 保存用户信息
            username = request.form.get("username")
            email = request.form.get("email")
            
            if not username or not email:
                return render_template("home.html", username=username, email=email, error="用户名和邮箱不能为空")
            
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            
            # 检查用户是否已存在
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                # 更新用户信息
                cursor.execute("UPDATE users SET email = ? WHERE user_id = ?", (email, existing_user[0]))
                user_id = existing_user[0]
            else:
                # 添加新用户
                cursor.execute("INSERT INTO users (username, email) VALUES (?, ?)", (username, email))
                user_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            
            # 更新会话
            session["user_id"] = user_id
            session["username"] = username
            session["email"] = email
            
            # 刷新数据
            consecutive_days = get_consecutive_days(user_id)
            longest_streak = get_longest_streak(user_id)
            signed_in_today = is_signed_in_today(user_id)
            
            return render_template("home.html", username=username, email=email, consecutive_days=consecutive_days, longest_streak=longest_streak, signed_in_today=signed_in_today, success="用户信息已保存")
        
        elif action == "sign_in":
            # 执行签到
            if not user_id:
                return render_template("home.html", username=username, email=email, error="请先保存用户信息")
            
            if signed_in_today:
                return render_template("home.html", username=username, email=email, consecutive_days=consecutive_days, longest_streak=longest_streak, signed_in_today=signed_in_today, error="您今日已签到")
            
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            
            # 添加签到记录
            today = datetime.date.today().strftime("%Y-%m-%d")
            cursor.execute("INSERT INTO sign_records (user_id, sign_date) VALUES (?, ?)", (user_id, today))
            
            conn.commit()
            conn.close()
            
            # 刷新数据
            consecutive_days = get_consecutive_days(user_id)
            longest_streak = get_longest_streak(user_id)
            signed_in_today = True
            
            return render_template("home.html", username=username, email=email, consecutive_days=consecutive_days, longest_streak=longest_streak, signed_in_today=signed_in_today, success="签到成功")
    
    return render_template("home.html", username=username, email=email, consecutive_days=consecutive_days, longest_streak=longest_streak, signed_in_today=signed_in_today)

# 退出登录
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    init_db()
    # 生产环境配置
    import os
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(host=host, port=port, debug=debug)