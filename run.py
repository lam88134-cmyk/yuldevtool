import os
import random
import sqlite3
from functools import wraps
from flask import Flask, request, redirect, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'yuldevtool_bi_mat_2026'

ADMIN_USER = 'Yul2012'
ADMIN_PASS = 'lam2922012'
ADMIN_PIN = '752012'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SECRET_DIR = os.path.join('/tmp', 'secret')
DB_PATH = os.path.join(SECRET_DIR, 'data.db')
UPLOAD_DIR = os.path.join(BASE_DIR, 'static', 'uploads')
os.makedirs(SECRET_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_DIR

def get_db():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with get_db() as c:
        c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT DEFAULT 'user', balance REAL DEFAULT 0)")
        c.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT, name TEXT, result TEXT, price REAL, description TEXT, image TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS purchases (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, product_id INTEGER, price REAL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        c.execute("CREATE TABLE IF NOT EXISTS cards (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, amount REAL, telco TEXT, code TEXT, serial TEXT, status TEXT DEFAULT 'pending', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        c.execute("CREATE TABLE IF NOT EXISTS deposits (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, amount REAL, code TEXT, note TEXT, status TEXT DEFAULT 'pending', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        c.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
        
        try:
            c.execute("SELECT image FROM products LIMIT 1")
        except sqlite3.OperationalError:
            c.execute("ALTER TABLE products ADD COLUMN image TEXT")

        if not c.execute("SELECT * FROM users WHERE username=?", (ADMIN_USER,)).fetchone():
            c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, 'admin')", (ADMIN_USER, generate_password_hash(ADMIN_PASS)))
        
        if not c.execute("SELECT * FROM settings WHERE key='qr_image'").fetchone():
            c.execute("INSERT INTO settings (key, value) VALUES ('qr_image', 'default_qr.png')")

init_db()

# --- GIAO DIỆN CHUNG ---
BASE_TMPL = """
<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>YulDevTool - Shop MMO</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0;font-family:'Inter',sans-serif}
body{background:#0a0e17;color:#e2e8f0;display:flex;flex-direction:column;min-height:100vh}
.topbar{height:60px;background:#111827;display:flex;align-items:center;padding:0 20px;border-bottom:1px solid #1f2937;position:fixed;width:100%;z-index:100;gap:20px}
.topbar .logo{font-weight:700;color:#3b82f6;font-size:20px;text-transform:uppercase;letter-spacing:1px}
.topbar .search{flex:1;max-width:400px;background:#1f2937;border-radius:20px;padding:8px 16px;display:flex;align-items:center}
.topbar .search input{background:transparent;border:none;color:#fff;outline:none;width:100%;margin-left:8px}
.topbar .actions{display:flex;gap:12px;margin-left:auto;align-items:center}
.topbar .actions button{background:#1f2937;color:#cbd5e1;padding:8px 16px;border-radius:6px;font-size:13px;font-weight:500;border:none;cursor:pointer}
.topbar .actions button:hover{background:#374151}

.menu-toggle{display:none;font-size:24px;color:#fff;background:transparent;border:none;cursor:pointer;padding:0 10px 0 0}

.layout{display:flex;margin-top:60px;min-height:calc(100vh - 60px);width:100%}
.sidebar{width:240px;background:#111827;padding:20px 12px;border-right:1px solid #1f2937;position:fixed;left:0;top:60px;height:calc(100vh - 60px);overflow-y:auto;transition:transform 0.3s ease;z-index:99}
.sidebar h4{color:#64748b;font-size:12px;text-transform:uppercase;margin:16px 0 8px 12px;letter-spacing:1px}
.sidebar a{display:flex;align-items:center;color:#94a3b8;text-decoration:none;padding:10px 12px;border-radius:8px;font-size:14px;margin-bottom:4px;transition:0.2s}
.sidebar a:hover,.sidebar a.active{background:#1e3a8a;color:#60a5fa}

.overlay{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:98}

main{padding:24px;width:100%;max-width:1000px;flex:1}
main.with-sidebar{margin-left:240px;max-width:calc(1000px + 240px)}
main.auth-main{display:flex;justify-content:center;align-items:center;min-height:calc(100vh - 60px);padding:20px;max-width:100%;margin:0 auto}

.banner{background:linear-gradient(135deg, #1e1b4b, #0f172a);border:1px solid #312e81;border-radius:16px;padding:32px;margin-bottom:24px;position:relative;overflow:hidden}
.banner::before{content:'';position:absolute;top:-50%;right:-10%;width:300px;height:300px;background:#3b82f6;filter:blur(100px);opacity:0.2;border-radius:50%}
.banner h1{font-size:24px;color:#fff;margin-bottom:12px;position:relative;z-index:1}
.banner p{color:#94a3b8;font-size:14px;margin-bottom:20px;position:relative;z-index:1}
.banner-btns{display:flex;gap:12px;position:relative;z-index:1;flex-wrap:wrap}
.banner-btns a{background:#3b82f6;color:#fff;padding:10px 24px;border-radius:8px;text-decoration:none;font-weight:600;font-size:14px;transition:0.2s}
.banner-btns a.secondary{background:transparent;border:1px solid #3b82f6;color:#60a5fa}
.banner-btns a:hover{opacity:0.8}
h2{font-weight:600;margin-bottom:20px;color:#f8fafc;font-size:20px}
h3{font-weight:600;margin:24px 0 12px 0;color:#cbd5e1;font-size:16px}
.card{background:#111827;padding:20px;border-radius:12px;margin-bottom:16px;display:flex;flex-direction:column;gap:12px;border:1px solid #1f2937}
input,select,button,textarea{padding:12px;border-radius:8px;border:1px solid #374151;background:#1f2937;color:#fff;font-size:14px;outline:none;width:100%}
input:focus,select:focus{border-color:#3b82f6}
button{background:#3b82f6;cursor:pointer;border:none;font-weight:600;color:#fff;transition:0.2s}
button:hover{background:#2563eb}
table{width:100%;border-collapse:collapse;background:#111827;margin-bottom:24px;border-radius:12px;overflow:hidden;border:1px solid #1f2937}
th,td{padding:14px 16px;border-bottom:1px solid #1f2937;text-align:left;font-size:14px;vertical-align:middle;word-break:break-word}
th{background:#1e293b;color:#94a3b8;font-weight:600;font-size:13px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:16px}
.err{color:#ef4444;font-size:14px;background:#ef444422;padding:10px;border-radius:8px;border:1px solid #ef444444;margin-bottom:12px}.ok{color:#10b981}
.auth-box{width:100%;max-width:400px;background:#111827;padding:32px;border-radius:16px;border:1px solid #1f2937;box-shadow:0 10px 25px rgba(0,0,0,0.5);margin:0 auto}
.auth-box h2{text-align:center;margin-bottom:24px;color:#3b82f6;border:none}
.product-img{width:100%;height:150px;object-fit:cover;border-radius:8px;margin-bottom:12px;background:#1f2937}
.result-box{background:#1e293b;padding:10px 12px;border-radius:6px;color:#60a5fa;font-family:monospace;font-size:14px;white-space:pre-wrap;word-break:break-all;max-height:300px;overflow-y:auto;display:block;width:100%;position:relative}
.btn-copy{background:#10b981;color:#fff;border:none;padding:8px 16px;border-radius:4px;font-size:14px;cursor:pointer;margin-bottom:10px;width:100%;font-weight:bold;}
.btn-copy:hover{background:#059669}
.warning-box { background: #451a03; border: 1px solid #b45309; color: #fbbf24; padding: 15px; border-radius: 8px; margin-bottom: 16px; font-size: 14px; line-height: 1.5; }
.warning-box b { color: #f59e0b; }
.warning-box code { background: #000; color: #fbbf24; padding: 2px 6px; border-radius: 4px; font-weight: bold; }
.tabs { display: flex; gap: 10px; margin-bottom: 20px; border-bottom: 1px solid #1f2937; padding-bottom: 10px; }
.tabs a { padding: 10px 20px; text-decoration: none; color: #94a3b8; border-radius: 8px; font-weight: 600; }
.tabs a.active { background: #3b82f6; color: white; }

@media (max-width: 768px) {
    .topbar { padding: 0 15px; gap: 10px; }
    .topbar .search { display: none; }
    .menu-toggle { display: block; }
    .sidebar { transform: translateX(-100%); width: 250px; box-shadow: 2px 0 10px rgba(0,0,0,0.5); }
    .sidebar.open { transform: translateX(0); }
    .overlay.open { display: block; }
    main, main.with-sidebar { margin-left: 0; padding: 16px; max-width: 100%; }
    .banner { padding: 20px; }
    .banner h1 { font-size: 20px; }
    table, thead, tbody, th, td, tr { display: block; }
    thead tr { position: absolute; top: -9999px; left: -9999px; }
    tr { border: 1px solid #1f2937; margin-bottom: 12px; border-radius: 8px; background: #111827; }
    td { border: none; border-bottom: 1px solid #1f2937; position: relative; padding-left: 50%; padding-top: 12px; padding-bottom: 12px; text-align: right; }
    td:before { position: absolute; top: 12px; left: 16px; width: 45%; padding-right: 10px; white-space: nowrap; text-align: left; font-weight: 600; color: #94a3b8; content: attr(data-label); }
    td:last-child { border-bottom: 0; }
    .auth-box { padding: 24px; }
    .card { padding: 16px; }
}
</style>
</head>
<body>
<div class="topbar">
    {% if session.get('uid') %}
    <button class="menu-toggle" onclick="toggleMenu()">☰</button>
    {% endif %}
    <div class="logo">YulDevTool</div>
    <div class="search">
        <span style="color:#64748b">🔍</span>
        <input placeholder="Tìm kiếm...">
    </div>
    <div class="actions">
        {% if session.get('uid') %}
        <span style="color:#94a3b8;font-size:14px;display:flex;align-items:center;margin-right:8px">Chào, {{ session.get('uname') }}</span>
        <a href="/logout" style="text-decoration:none"><button style="background:#ef444422;color:#ef4444">Đăng xuất</button></a>
        {% else %}
        <a href="/login" style="text-decoration:none"><button>Đăng nhập</button></a>
        <a href="/register" style="text-decoration:none"><button style="background:#1f2937;color:#fff">Đăng ký</button></a>
        {% endif %}
    </div>
</div>

<div class="overlay" id="overlay" onclick="toggleMenu()"></div>

<div class="layout">
    {% if session.get('uid') %}
    <aside class="sidebar" id="sidebar">
        <h4>Danh mục chính</h4>
        <a href="/user">🏠 Trang chủ</a>
        <a href="/deposit">💰 Nạp tiền</a>
        <a href="/tools">🛠 Tool</a>
        <a href="/tuts">📚 Tut</a>
        <a href="/history">🧾 Lịch sử</a>
        {% if session.get('role')=='admin' %}
        <h4>Quản trị viên</h4>
        <a href="/admin" style="color:#60a5fa">⚙️ Quản lý hệ thống</a>
        <a href="/admin_users" style="color:#60a5fa">👥 Quản lý User</a>
        {% endif %}
    </aside>
    <main class="with-sidebar">{{ content|safe }}</main>
    {% else %}
    <main class="auth-main">{{ content|safe }}</main>
    {% endif %}
</div>

<script>
function toggleMenu() {
    document.getElementById('sidebar').classList.toggle('open');
    document.getElementById('overlay').classList.toggle('open');
}
// Ham copy chuan cho ca PC va Mobile
function copyText(btn, inputId) {
    var copyText = document.getElementById(inputId);
    copyText.select();
    copyText.setSelectionRange(0, 99999); 
    
    try {
        var successful = document.execCommand('copy');
        if (successful) {
            let oldText = btn.innerText;
            btn.innerText = "✅ Đã sao chép!";
            btn.style.background = "#059669";
            setTimeout(() => {
                btn.innerText = oldText;
                btn.style.background = "#10b981";
            }, 2000);
        } else {
            alert('Trình duyệt không hỗ trợ sao chép tự động!');
        }
    } catch (err) {
        alert('Lỗi khi sao chép!');
    }
}
function togglePassword(inputId, icon) {
    var x = document.getElementById(inputId);
    if (x.type === "password") { x.type = "text"; icon.innerText = "🙈"; } 
    else { x.type = "password"; icon.innerText = "👁️"; }
}
</script>
</body>
</html>
"""

def render_page(content):
    return render_template_string(BASE_TMPL, content=content)

def login_required(f):
    @wraps(f)
    def w(*a, **k):
        if 'uid' not in session: return redirect('/login')
        return f(*a, **k)
    return w

def admin_required(f):
    @wraps(f)
    def w(*a, **k):
        if session.get('role') != 'admin': return redirect('/login')
        if not session.get('admin_verified'): return redirect('/pin')
        return f(*a, **k)
    return w

# --- ROUTES AUTH ---
@app.route('/')
def index():
    if 'uid' in session:
        return redirect('/admin' if session.get('role') == 'admin' else '/user')
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form.get('u'), request.form.get('p')
        with get_db() as c:
            row = c.execute("SELECT * FROM users WHERE username=?", (u,)).fetchone()
        if row and check_password_hash(row['password'], p):
            session['uid'] = row['id']
            session['uname'] = row['username']
            session['role'] = row['role']
            if row['role'] == 'admin':
                session['admin_verified'] = False
                return redirect('/pin')
            return redirect('/user')
        return render_page("<div class='auth-box'><h2>Đăng nhập</h2><p class='err'>Sai tên hoặc mật khẩu!</p><form method='post' style='display:flex;flex-direction:column;gap:12px'><input name='u' placeholder='Tên đăng nhập' required><div style='position:relative'><input name='p' id='pwd_login' type='password' placeholder='Mật khẩu' required style='padding-right:40px'><span onclick=\"togglePassword('pwd_login', this)\" style='position:absolute;right:10px;top:12px;cursor:pointer'>👁️</span></div><button>Đăng nhập</button></form><p style='text-align:center;margin-top:16px;font-size:14px;color:#94a3b8'>Chưa có tài khoản? <a href='/register' style='color:#3b82f6;text-decoration:none'>Đăng ký ngay</a></p></div>")
    return render_page("<div class='auth-box'><h2>Đăng nhập</h2><form method='post' style='display:flex;flex-direction:column;gap:12px'><input name='u' placeholder='Tên đăng nhập' required><div style='position:relative'><input name='p' id='pwd_login' type='password' placeholder='Mật khẩu' required style='padding-right:40px'><span onclick=\"togglePassword('pwd_login', this)\" style='position:absolute;right:10px;top:12px;cursor:pointer'>👁️</span></div><button>Đăng nhập</button></form><p style='text-align:center;margin-top:16px;font-size:14px;color:#94a3b8'>Chưa có tài khoản? <a href='/register' style='color:#3b82f6;text-decoration:none'>Đăng ký ngay</a></p></div>")

@app.route('/pin', methods=['GET', 'POST'])
def pin():
    if session.get('role') != 'admin': return redirect('/login')
    if session.get('admin_verified'): return redirect('/admin')
    
    if request.method == 'POST':
        p = request.form.get('pin')
        if p == ADMIN_PIN:
            session['admin_verified'] = True
            return redirect('/admin')
        return render_page("<div class='auth-box'><h2>Xác thực Admin</h2><p class='err'>Mã PIN không đúng!</p><form method='post' style='display:flex;flex-direction:column;gap:12px'><input name='pin' type='password' placeholder='Nhập mã PIN' required><button>Xác nhận</button></form></div>")
    
    return render_page("<div class='auth-box'><h2>Xác thực Admin</h2><form method='post' style='display:flex;flex-direction:column;gap:12px'><input name='pin' type='password' placeholder='Nhập mã PIN' required><button>Xác nhận</button></form></div>")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u, p = request.form.get('u'), request.form.get('p')
        agree = request.form.get('agree')
        if not agree:
            return render_page("<div class='auth-box'><h2>Đăng ký</h2><p class='err'>Bạn phải đồng ý điều khoản!</p><form method='post' style='display:flex;flex-direction:column;gap:12px'><input name='u' placeholder='Tên đăng nhập' required><div style='position:relative'><input name='p' id='pwd_reg' type='password' placeholder='Mật khẩu' required style='padding-right:40px'><span onclick=\"togglePassword('pwd_reg', this)\" style='position:absolute;right:10px;top:12px;cursor:pointer'>👁️</span></div><label style='color:#94a3b8;font-size:13px;display:flex;align-items:center;gap:8px'><input type='checkbox' name='agree' style='width:auto;margin:0'> Đồng ý điều khoản</label><button>Đăng ký</button></form></div>")
        if u.lower() == ADMIN_USER.lower(): return "Tên này không được phép sử dụng."
        try:
            with get_db() as c:
                c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (u, generate_password_hash(p)))
            return redirect('/login')
        except:
            return render_page("<div class='auth-box'><h2>Đăng ký</h2><p class='err'>Tên đăng nhập đã tồn tại!</p><form method='post' style='display:flex;flex-direction:column;gap:12px'><input name='u' placeholder='Tên đăng nhập' required><div style='position:relative'><input name='p' id='pwd_reg' type='password' placeholder='Mật khẩu' required style='padding-right:40px'><span onclick=\"togglePassword('pwd_reg', this)\" style='position:absolute;right:10px;top:12px;cursor:pointer'>👁️</span></div><label style='color:#94a3b8;font-size:13px;display:flex;align-items:center;gap:8px'><input type='checkbox' name='agree' style='width:auto;margin:0'> Đồng ý điều khoản</label><button>Đăng ký</button></form></div>")
    return render_page("<div class='auth-box'><h2>Đăng ký</h2><form method='post' style='display:flex;flex-direction:column;gap:12px'><input name='u' placeholder='Tên đăng nhập' required><div style='position:relative'><input name='p' id='pwd_reg' type='password' placeholder='Mật khẩu' required style='padding-right:40px'><span onclick=\"togglePassword('pwd_reg', this)\" style='position:absolute;right:10px;top:12px;cursor:pointer'>👁️</span></div><label style='color:#94a3b8;font-size:13px;display:flex;align-items:center;gap:8px'><input type='checkbox' name='agree' style='width:auto;margin:0'> Đồng ý điều khoản</label><button>Đăng ký</button></form></div>")

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# --- ROUTES USER ---
@app.route('/user')
@login_required
def user_home():
    with get_db() as c:
        u = c.execute("SELECT * FROM users WHERE id=?", (session['uid'],)).fetchone()
        pmap = {p['id']: p for p in c.execute("SELECT * FROM products").fetchall()}
        purchases = c.execute("SELECT * FROM purchases WHERE user_id=?", (session['uid'],)).fetchall()
    
    balance_display = "Vô Hạn (∞)" if u['role'] == 'admin' else f"{u['balance']:,.0f} VNĐ"
    
    html = f"""
    <div class='banner'>
        <h1>Chào mừng {u['username']}!</h1>
        <p>Số dư hiện tại: <b style='color:#10b981; font-size:18px'>{balance_display}</b></p>
        <div class='banner-btns'>
            <a href='/deposit'>Nạp tiền ngay</a>
            <a href='/tools' class='secondary'>Khám phá Tool</a>
        </div>
    </div>
    """
    html += "<h2>Sản phẩm đã mua</h2>"
    if purchases:
        html += "<table><thead><tr><th style='width:30%'>Tên sản phẩm</th><th>Kết quả / Link tải</th></tr></thead><tbody>"
        for p in purchases:
            prod = pmap.get(p['product_id'])
            if prod: 
                input_id = f"res_{p['product_id']}"
                html += f"""
                <tr>
                    <td data-label='Tên sản phẩm'><b>{prod['name']}</b></td>
                    <td data-label='Kết quả'>
                        <textarea id='{input_id}' style='position:absolute;left:-9999px'>{prod['result']}</textarea>
                        <button class='btn-copy' onclick="copyText(this, '{input_id}')">Sao chép kết quả</button>
                        <div class='result-box'>{prod['result']}</div>
                    </td>
                </tr>
                """
        html += "</tbody></table>"
    else: html += "<p style='color:#64748b'>Bạn chưa mua sản phẩm nào.</p>"
    return render_page(html)

@app.route('/deposit', methods=['GET', 'POST'])
@login_required
def deposit():
    tab = request.args.get('tab', 'bank')
    
    with get_db() as c:
        qr_row = c.execute("SELECT value FROM settings WHERE key='qr_image'").fetchone()
        qr_image = qr_row['value'] if qr_row else 'default_qr.png'

    if request.method == 'POST':
        method = request.form.get('method')
        amount = float(request.form.get('amount', 0))
        
        if method == 'bank':
            code = str(random.randint(0, 999999)).zfill(6)
            note = f"NAP {code} {session['uname']}"
            with get_db() as c:
                c.execute("INSERT INTO deposits (user_id, amount, code, note) VALUES (?, ?, ?, ?)", (session['uid'], amount, code, note))
            
            qr = f"/static/uploads/{qr_image}" 
            
            html = f"""
            <h2>Nạp tiền qua Ngân hàng</h2>
            <div class='card' style='max-width:500px'>
                <div class='warning-box'>
                    <p><b>⚠️ LƯU Ý QUAN TRỌNG:</b></p>
                    <p>- Vui lòng chuyển khoản <b>ĐÚNG SỐ TIỀN: {amount:,.0f} VNĐ</b>.</p>
                    <p>- Ghi đúng nội dung: <b>{note}</b></p>
                    <p>- Sau khi chuyển khoản, nhắn Zalo: <b>0775531924</b> kèm <b>Mã ({code})</b> để duyệt.</p>
                </div>
                <div style='background:#1e293b;padding:16px;border-radius:8px;text-align:center;'>
                    <p style='color:#94a3b8;margin-bottom:8px'>Mã giao dịch:</p>
                    <p style='color:#3b82f6;font-size:24px;font-weight:bold;margin-bottom:16px'>{code}</p>
                    <img src='{qr}' style='max-width:100%;border-radius:8px;border:2px solid #3b82f6'>
                    <p style='margin-top:16px;'><a href='/user' style='color:#60a5fa;text-decoration:none'>Quay lại</a></p>
                </div>
            </div>
            """
            return render_page(html)
            
        elif method == 'card':
            telco = request.form.get('telco')
            code = request.form.get('code')
            serial = request.form.get('serial')
            
            with get_db() as c:
                c.execute("INSERT INTO cards (user_id, amount, telco, code, serial) VALUES (?, ?, ?, ?, ?)", 
                          (session['uid'], amount, telco, code, serial))
                
            html = f"""
            <h2>Gửi thẻ thành công!</h2>
            <div class='card' style='max-width:500px;text-align:center;'>
                <p style='color:#10b981;font-size:18px;font-weight:bold;margin-bottom:10px'>Đã gửi thẻ {telco.upper()} - {amount:,.0f}đ</p>
                <div class='warning-box'>
                    <p>Thẻ của bạn đang ở trạng thái <b>Chờ duyệt</b>.</p>
                    <p>Vui lòng chờ từ <b>30 phút đến 1 tiếng</b> để Admin kiểm tra và cộng tiền (sau khi trừ chiết khấu 20%).</p>
                </div>
                <p style='margin-top:20px;'><a href='/user' style='color:#fff;background:#3b82f6;padding:10px 20px;border-radius:8px;text-decoration:none'>Quay lại trang chủ</a></p>
            </div>
            """
            return render_page(html)
            
    html = f"""
    <h2>Nạp tiền</h2>
    <div class='tabs'>
        <a href='/deposit?tab=bank' class='{"active" if tab=="bank" else ""}'>Ngân hàng (QR)</a>
        <a href='/deposit?tab=card' class='{"active" if tab=="card" else ""}'>Thẻ cào</a>
    </div>
    """
    
    if tab == 'bank':
        html += """
        <form method='post' class='card' style='max-width:400px'>
            <input type='hidden' name='method' value='bank'>
            <label style='color:#94a3b8;font-size:14px;'>Số tiền muốn nạp (VNĐ):</label>
            <input name='amount' type='number' min='10000' placeholder='VD: 50000' required>
            <button style='margin-top:12px'>Tạo mã QR nạp tiền</button>
        </form>
        """
    else:
        html += """
        <form method='post' class='card' style='max-width:400px'>
            <input type='hidden' name='method' value='card'>
            <div class='warning-box' style='font-size:12px;padding:10px;'>
                <p><b>Lưu ý:</b> Thẻ cào sẽ bị trừ 20% chiết khấu. Thời gian duyệt từ 30 phút - 1 tiếng.</p>
            </div>
            <label style='color:#94a3b8;font-size:14px;'>Chọn nhà mạng:</label>
            <select name='telco'>
                <option value='viettel'>Viettel</option>
                <option value='mobifone'>Mobifone</option>
                <option value='vinaphone'>Vinaphone</option>
            </select>
            <label style='color:#94a3b8;font-size:14px;'>Chọn mệnh giá:</label>
            <select name='amount'>
                <option value='10000'>10.000đ</option>
                <option value='20000'>20.000đ</option>
                <option value='50000'>50.000đ</option>
                <option value='100000'>100.000đ</option>
                <option value='200000'>200.000đ</option>
                <option value='500000'>500.000đ</option>
            </select>
            <input name='code' placeholder='Nhập mã thẻ' required>
            <input name='serial' placeholder='Nhập số serial' required>
            <button style='margin-top:12px;background:#10b981;'>Gửi thẻ</button>
        </form>
        """
    return render_page(html)

@app.route('/history')
@login_required
def history():
    with get_db() as c:
        deposits = c.execute("SELECT * FROM deposits WHERE user_id=? ORDER BY id DESC", (session['uid'],)).fetchall()
        cards = c.execute("SELECT * FROM cards WHERE user_id=? ORDER BY id DESC", (session['uid'],)).fetchall()
        purchases = c.execute("SELECT p.*, pr.name FROM purchases p JOIN products pr ON p.product_id=pr.id WHERE p.user_id=? ORDER BY p.id DESC", (session['uid'],)).fetchall()
    
    html = "<h2>Lịch sử giao dịch</h2>"
    
    html += "<h3>Lịch sử mua hàng</h3>"
    if purchases:
        html += "<table><thead><tr><th>Sản phẩm</th><th>Giá</th><th>Thời gian</th></tr></thead><tbody>"
        for p in purchases:
            html += f"<tr><td data-label='Sản phẩm'>{p['name']}</td><td data-label='Giá'>{p['price']:,.0f}đ</td><td data-label='Thời gian'>{p['created_at']}</td></tr>"
        html += "</tbody></table>"
    else: html += "<p style='color:#64748b'>Chưa có giao dịch mua hàng.</p>"
    
    html += "<h3>Lịch sử nạp ngân hàng</h3>"
    if deposits:
        html += "<table><thead><tr><th>Mã GD</th><th>Số tiền</th><th>Trạng thái</th><th>Thời gian</th></tr></thead><tbody>"
        for d in deposits:
            status_color = "#10b981" if d['status']=='approved' else ("#ef4444" if d['status']=='rejected' else "#f59e0b")
            html += f"<tr><td data-label='Mã GD'>{d['code']}</td><td data-label='Số tiền'>{d['amount']:,.0f}đ</td><td data-label='Trạng thái' style='color:{status_color}'>{d['status']}</td><td data-label='Thời gian'>{d['created_at']}</td></tr>"
        html += "</tbody></table>"
    else: html += "<p style='color:#64748b'>Chưa có giao dịch nạp ngân hàng.</p>"
    
    html += "<h3>Lịch sử nạp thẻ cào</h3>"
    if cards:
        html += "<table><thead><tr><th>Nhà mạng</th><th>Mệnh giá</th><th>Trạng thái</th><th>Thời gian</th></tr></thead><tbody>"
        for c in cards:
            status_color = "#10b981" if c['status']=='success' else ("#ef4444" if c['status']=='rejected' else "#f59e0b")
            html += f"<tr><td data-label='Nhà mạng'>{c['telco'].upper()}</td><td data-label='Mệnh giá'>{c['amount']:,.0f}đ</td><td data-label='Trạng thái' style='color:{status_color}'>{c['status']}</td><td data-label='Thời gian'>{c['created_at']}</td></tr>"
        html += "</tbody></table>"
    else: html += "<p style='color:#64748b'>Chưa có giao dịch nạp thẻ cào.</p>"
    
    return render_page(html)

@app.route('/tools')
@app.route('/tuts')
@login_required
def show_products():
    kind = 'tool' if 'tools' in request.path else 'tut'
    with get_db() as c:
        items = c.execute("SELECT * FROM products WHERE kind=?", (kind,)).fetchall()
        u = c.execute("SELECT * FROM users WHERE id=?", (session['uid'],)).fetchone()
    
    balance = u['balance'] if u['role'] != 'admin' else 999999999
    
    html = f"<h2>Danh sách {kind.upper()}</h2><div class='grid'>"
    if not items: html += "<p style='color:#64748b'>Chưa có sản phẩm nào.</p>"
    
    for t in items:
        img_src = f"/static/uploads/{t['image']}" if t['image'] else "https://via.placeholder.com/300x150/1f2937/60a5fa?text=No+Image"
        
        if balance >= t['price']:
            btn_mua = f"""
            <form method='post' action='/buy/{t['id']}' style='flex:1;margin:0' onsubmit="return confirm('Bạn có chắc chắn muốn mua {t['name']} với giá {t['price']:,.0f} VNĐ?');">
                <button style='width:100%'>Mua ngay</button>
            </form>
            """
        else:
            btn_mua = f"""
            <a href='/product/{t['id']}' style='flex:1;text-decoration:none'>
                <button style='width:100%;background:#ef4444'>Mua ngay</button>
            </a>
            """
            
        html += f"""
        <div class='card' style='justify-content:space-between'>
            <img src='{img_src}' class='product-img'>
            <div>
                <h3 style='margin:0 0 8px 0;color:#60a5fa'>{t['name']}</h3>
                <p style='color:#94a3b8;font-size:13px;margin-bottom:12px'>{t['description']}</p>
            </div>
            <div style='display:flex;flex-direction:column;gap:8px;'>
                <p style='font-weight:700;color:#10b981;margin:0;font-size:16px'>{t['price']:,.0f} VNĐ</p>
                <div style='display:flex;gap:8px;'>
                    <a href='/product/{t['id']}' style='flex:1;text-decoration:none'><button style='background:#1f2937;color:#fff;width:100%'>Chi tiết</button></a>
                    {btn_mua}
                </div>
            </div>
        </div>
        """
    html += "</div>"
    return render_page(html)

@app.route('/product/<int:pid>')
@login_required
def product_detail(pid):
    with get_db() as c:
        p = c.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
        if not p: return redirect('/tools')
        purchased = c.execute("SELECT * FROM purchases WHERE user_id=? AND product_id=?", (session['uid'], pid)).fetchone()
        u = c.execute("SELECT * FROM users WHERE id=?", (session['uid'],)).fetchone()
    
    img_src = f"/static/uploads/{p['image']}" if p['image'] else "https://via.placeholder.com/600x400/1f2937/60a5fa?text=No+Image"
    
    html = f"""
    <div style='margin-bottom:20px;'>
        <a href='/{p['kind']}s' style='color:#60a5fa;text-decoration:none;font-size:14px;'>&larr; Quay lại danh sách</a>
    </div>
    <div class='card' style='flex-direction:row;gap:24px;flex-wrap:wrap;'>
        <div style='flex:1;min-width:300px;'>
            <img src='{img_src}' style='width:100%;border-radius:12px;object-fit:cover;border:1px solid #1f2937;'>
        </div>
        <div style='flex:1;min-width:300px;display:flex;flex-direction:column;gap:16px;'>
            <h1 style='color:#60a5fa;font-size:24px;margin:0;'>{p['name']}</h1>
            <div style='background:#1e293b;padding:16px;border-radius:8px;'>
                <p style='color:#94a3b8;font-size:13px;margin-bottom:4px;'>Giá bán:</p>
                <p style='color:#10b981;font-size:28px;font-weight:700;margin:0;'>{p['price']:,.0f} VNĐ</p>
            </div>
            <div>
                <h3 style='margin:0 0 8px 0;font-size:16px;'>Mô tả sản phẩm</h3>
                <p style='color:#cbd5e1;line-height:1.6;white-space:pre-wrap;'>{p['description']}</p>
            </div>
            <div style='background:#111827;border:1px solid #3b82f6;padding:12px;border-radius:8px;'>
                <p style='color:#60a5fa;font-size:14px;margin:0;font-weight:600;'>
                    📞 Hỗ trợ / Liên hệ Zalo: <span style='color:#10b981;'>0775531924</span>
                </p>
            </div>
    """
    
    if purchased:
        input_id = f"res_detail_{p['id']}"
        html += f"""
            <div style='margin-top:8px;'>
                <h3 style='margin:0 0 8px 0;font-size:16px;color:#10b981;'>Kết quả của bạn:</h3>
                <textarea id='{input_id}' style='position:absolute;left:-9999px'>{p['result']}</textarea>
                <button class='btn-copy' onclick="copyText(this, '{input_id}')">Sao chép kết quả</button>
                <div class='result-box'>{p['result']}</div>
            </div>
        """
    else:
        if u['balance'] >= p['price'] or u['role'] == 'admin':
            html += f"""
                <form method='post' action='/buy/{p['id']}' onsubmit="return confirm('Bạn có chắc chắn muốn mua {p['name']} với giá {p['price']:,.0f} VNĐ?');">
                    <button style='width:100%;padding:16px;font-size:16px;margin-top:8px;'>Mua ngay</button>
                </form>
            """
        else:
            html += f"""
                <div style='background:#7f1d1d;padding:20px;border-radius:8px;text-align:center;'>
                    <p style='color:#fca5a5;font-weight:bold;margin-bottom:16px;'>Bạn không đủ tiền để mua sản phẩm này!</p>
                    <div style='display:flex;gap:12px;justify-content:center;'>
                        <a href='/product/{p['id']}'><button style='background:#374151;color:#fff'>OK</button></a>
                        <a href='/deposit'><button style='background:#3b82f6;color:#fff'>Nạp tiền</button></a>
                    </div>
                </div>
            """
    html += "</div></div>"
    return render_page(html)

@app.route('/buy/<int:pid>', methods=['POST'])
@login_required
def buy(pid):
    with get_db() as c:
        p = c.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
        u = c.execute("SELECT * FROM users WHERE id=?", (session['uid'],)).fetchone()
        
        if u['role'] == 'admin' or u['balance'] >= p['price']:
            if u['role'] != 'admin':
                c.execute("UPDATE users SET balance = balance - ? WHERE id=?", (p['price'], u['id']))
            c.execute("INSERT INTO purchases (user_id, product_id, price) VALUES (?, ?, ?)", (u['id'], pid, p['price']))
            return redirect(f'/product/{pid}')
        else:
            return render_page(f"""
                <div class='auth-box'>
                    <h2 style='color:#ef4444;margin-bottom:16px'>Chưa đủ tiền</h2>
                    <p style='text-align:center;margin-bottom:20px;'>Tài khoản của bạn không đủ để mua sản phẩm này.</p>
                    <div style='display:flex;gap:12px;justify-content:center;'>
                        <a href='/product/{pid}'><button style='background:#374151;color:#fff;width:auto;padding:10px 20px'>OK</button></a>
                        <a href='/deposit'><button style='width:auto;padding:10px 20px'>Nạp tiền</button></a>
                    </div>
                </div>
            """)

# --- ROUTES ADMIN ---
@app.route('/admin', methods=['GET', 'POST'])
@admin_required
def admin_home():
    if request.method == 'POST':
        if 'qr_image' in request.files:
            image = request.files.get('qr_image')
            if image and image.filename != '':
                img_filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], img_filename))
                with get_db() as c:
                    c.execute("UPDATE settings SET value=? WHERE key='qr_image'", (img_filename,))
            return redirect('/admin')
            
        kind = request.form.get('kind')
        name = request.form.get('name', '')
        if not name.endswith(f".{kind}"):
            return redirect('/admin?err=name')
        image = request.files.get('image')
        img_filename = ''
        if image and image.filename != '':
            img_filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], img_filename))
        with get_db() as c:
            c.execute("INSERT INTO products (kind, name, price, description, result, image) VALUES (?, ?, ?, ?, ?, ?)",
                      (kind, name, float(request.form.get('price', 0)), request.form.get('desc'), request.form.get('result'), img_filename))
        return redirect('/admin')
    
    with get_db() as c:
        prods = c.execute("SELECT * FROM products").fetchall()
        deps = c.execute("SELECT d.*, u.username FROM deposits d JOIN users u ON u.id=d.user_id WHERE status='pending'").fetchall()
        cards = c.execute("SELECT c.*, u.username FROM cards c JOIN users u ON u.id=c.user_id WHERE status='pending'").fetchall()
        qr_row = c.execute("SELECT value FROM settings WHERE key='qr_image'").fetchone()
        current_qr = qr_row['value'] if qr_row else ''
    
    html = "<div>"
    html += "<h2>Quản lý hệ thống</h2>"
    
    html += f"""
    <h3>Cấu hình thanh toán (QR)</h3>
    <form method='post' class='card' enctype='multipart/form-data'>
        <p style='color:#94a3b8;font-size:14px;'>Ảnh QR hiện tại:</p>
        <img src='/static/uploads/{current_qr}' style='max-width:200px;border-radius:8px;border:1px solid #3b82f6;'>
        <label style='color:#94a3b8;font-size:13px;margin-top:8px;'>Thay đổi ảnh QR mới:</label>
        <input type='file' name='qr_image' accept='image/*' style='background:transparent;border:none;padding:0'>
        <button type='submit' style='margin-top:8px;background:#10b981;'>Cập nhật ảnh QR</button>
    </form>
    """
    
    if request.args.get('err') == 'name': 
        html += "<p class='err'>Lỗi: Tên phải kết thúc bằng .tool hoặc .tut</p>"
        
    html += """
    <h3>Thêm sản phẩm mới</h3>
    <form method='post' class='card' enctype='multipart/form-data'>
        <select name='kind'>
            <option value='tool'>Tool</option>
            <option value='tut'>Tut</option>
        </select>
        <input name='name' placeholder='Tên sản phẩm (VD: hack.tool)' required>
        <input name='price' type='number' placeholder='Giá tiền' required>
        <label style='color:#94a3b8;font-size:13px;margin-bottom:-8px;'>Ảnh sản phẩm:</label>
        <input type='file' name='image' accept='image/*' style='background:transparent;border:none;padding:0'>
        <textarea name='result' placeholder='Kết quả trả về' rows='3'></textarea>
        <input name='desc' placeholder='Mô tả'>
        <button type='submit'>Thêm sản phẩm</button>
    </form>
    """
    
    html += "<h3>Duyệt nạp Ngân hàng</h3>"
    if deps:
        html += "<table><thead><tr><th>ID</th><th>Người dùng</th><th>Số tiền</th><th>Nội dung CK</th><th>Hành động</th></tr></thead><tbody>"
        for d in deps:
            html += f"<tr><td data-label='ID'>{d['id']}</td><td data-label='Người dùng'>{d['username']}</td><td data-label='Số tiền'>{d['amount']:,.0f}đ</td><td data-label='Nội dung'>{d['note']}</td><td data-label='Hành động'><form method='post' action='/admin/dep/{d['id']}/ok'><button style='padding:6px 12px;font-size:12px'>Duyệt</button></form></td></tr>"
        html += "</tbody></table>"
    else:
        html += "<p class='ok'>Không có lệnh nạp nào đang chờ.</p>"
        
    html += "<h3>Duyệt thẻ cào</h3>"
    if cards:
        html += "<table><thead><tr><th>Nhà mạng</th><th>Mệnh giá</th><th>Mã thẻ</th><th>Serial</th><th>Người dùng</th><th>Hành động</th></tr></thead><tbody>"
        for c in cards:
            html += f"""
            <tr>
                <td data-label='Nhà mạng'>{c['telco'].upper()}</td>
                <td data-label='Mệnh giá'>{c['amount']:,.0f}đ</td>
                <td data-label='Mã thẻ'>{c['code']}</td>
                <td data-label='Serial'>{c['serial']}</td>
                <td data-label='Người dùng'>{c['username']}</td>
                <td data-label='Hành động'>
                    <form method='post' action='/admin/card/{c['id']}/ok' style='display:inline'>
                        <button style='padding:6px 12px;font-size:12px;background:#10b981'>Duyệt</button>
                    </form>
                    <form method='post' action='/admin/card/{c['id']}/reject' style='display:inline'>
                        <button style='padding:6px 12px;font-size:12px;background:#ef4444'>Từ chối</button>
                    </form>
                </td>
            </tr>
            """
        html += "</tbody></table>"
    else:
        html += "<p class='ok'>Không có thẻ cào nào đang chờ.</p>"
    
    html += "<h3>Quản lý sản phẩm</h3>"
    if prods:
        html += "<table><thead><tr><th>Ảnh</th><th>Tên sản phẩm</th><th>Giá</th><th>Hành động</th></tr></thead><tbody>"
        for p in prods:
            img_file = dict(p).get('image', '')
            img_src = f"/static/uploads/{img_file}" if img_file else ""
            img_tag = f"<img src='{img_src}' style='width:50px;height:50px;object-fit:cover;border-radius:4px'>" if img_src else "Không có"
            html += f"<tr><td data-label='Ảnh'>{img_tag}</td><td data-label='Tên'>{p['name']}</td><td data-label='Giá'>{p['price']:,.0f}đ</td><td data-label='Hành động'><form method='post' action='/admin/del/{p['id']}'><button style='padding:6px 12px;font-size:12px;background:#ef4444'>Xóa</button></form></td></tr>"
        html += "</tbody></table>"
    else:
        html += "<p>Chưa có sản phẩm nào.</p>"
    
    html += "</div>"
    return render_page(html)

@app.route('/admin/dep/<int:did>/ok', methods=['POST'])
@admin_required
def dep_ok(did):
    with get_db() as c:
        d = c.execute("SELECT * FROM deposits WHERE id=? AND status='pending'", (did,)).fetchone()
        if d:
            c.execute("UPDATE users SET balance = balance + ? WHERE id=?", (d['amount'], d['user_id']))
            c.execute("UPDATE deposits SET status='approved' WHERE id=?", (did,))
    return redirect('/admin')

@app.route('/admin/card/<int:cid>/<action>', methods=['POST'])
@admin_required
def card_action(cid, action):
    with get_db() as c:
        card = c.execute("SELECT * FROM cards WHERE id=? AND status='pending'", (cid,)).fetchone()
        if card:
            if action == 'ok':
                chiet_khau = 0.20
                thuc_nhan = card['amount'] * (1 - chiet_khau)
                c.execute("UPDATE users SET balance = balance + ? WHERE id=?", (thuc_nhan, card['user_id']))
                c.execute("UPDATE cards SET status='success' WHERE id=?", (cid,))
            elif action == 'reject':
                c.execute("UPDATE cards SET status='rejected' WHERE id=?", (cid,))
    return redirect('/admin')

@app.route('/admin/del/<int:pid>', methods=['POST'])
@admin_required
def del_prod(pid):
    with get_db() as c:
        p = c.execute("SELECT image FROM products WHERE id=?", (pid,)).fetchone()
        if p and dict(p).get('image'):
            img_path = os.path.join(app.config['UPLOAD_FOLDER'], p['image'])
            if os.path.exists(img_path):
                os.remove(img_path)
        c.execute("DELETE FROM products WHERE id=?", (pid,))
    return redirect('/admin')

# --- ROUTES QUAN LY USER ---
@app.route('/admin_users')
@admin_required
def admin_users():
    search = request.args.get('search', '')
    with get_db() as c:
        if search:
            users = c.execute("SELECT * FROM users WHERE username LIKE ? AND role='user'", ('%'+search+'%',)).fetchall()
        else:
            users = c.execute("SELECT * FROM users WHERE role='user'").fetchall()
    
    html = "<h2>Quản lý người dùng</h2>"
    
    html += f"""
    <form method='get' action='/admin_users' class='card' style='flex-direction:row;gap:12px;'>
        <input name='search' placeholder='Tìm tên người dùng...' value='{search}' style='flex:1'>
        <button type='submit' style='width:auto;padding:0 24px'>Tìm kiếm</button>
    </form>
    """
    
    if users:
        html += "<table><thead><tr><th>Tên đăng nhập</th><th>Số dư</th><th>Thao tác</th></tr></thead><tbody>"
        for u in users:
            html += f"""
            <tr>
                <td data-label='Tên'>{u['username']}</td>
                <td data-label='Số dư'>{u['balance']:,.0f}đ</td>
                <td data-label='Thao tác'>
                    <div style='display:flex;gap:8px;justify-content:flex-end'>
                        <form method='post' action='/admin/addmoney/{u['id']}' style='display:flex;gap:8px;margin:0'>
                            <input name='amt' type='number' placeholder='Nhập số tiền' style='padding:6px' required>
                            <button style='padding:6px 12px;font-size:12px;background:#10b981'>Cộng</button>
                        </form>
                        <form method='post' action='/admin/deluser/{u['id']}' style='margin:0' onsubmit="return confirm('Bạn có chắc muốn xóa user này?');">
                            <button style='padding:6px 12px;font-size:12px;background:#ef4444'>Xóa</button>
                        </form>
                    </div>
                </td>
            </tr>
            """
        html += "</tbody></table>"
    else:
        html += "<p style='color:#94a3b8'>Không tìm thấy người dùng nào.</p>"
        
    return render_page(html)

@app.route('/admin/addmoney/<int:uid>', methods=['POST'])
@admin_required
def add_money(uid):
    amt = float(request.form.get('amt', 0))
    with get_db() as c:
        c.execute("UPDATE users SET balance = balance + ? WHERE id=?", (amt, uid))
    return redirect('/admin_users')

@app.route('/admin/deluser/<int:uid>', methods=['POST'])
@admin_required
def del_user(uid):
    with get_db() as c:
        c.execute("DELETE FROM users WHERE id=?", (uid,))
        c.execute("DELETE FROM purchases WHERE user_id=?", (uid,))
        c.execute("DELETE FROM deposits WHERE user_id=?", (uid,))
        c.execute("DELETE FROM cards WHERE user_id=?", (uid,))
    return redirect('/admin_users')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
