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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SECRET_DIR = os.path.join(BASE_DIR, 'secret')
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
        c.execute("CREATE TABLE IF NOT EXISTS purchases (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, product_id INTEGER, price REAL)")
        c.execute("CREATE TABLE IF NOT EXISTS deposits (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, amount REAL, code TEXT, note TEXT, status TEXT DEFAULT 'pending')")
        
        try:
            c.execute("SELECT image FROM products LIMIT 1")
        except sqlite3.OperationalError:
            c.execute("ALTER TABLE products ADD COLUMN image TEXT")

        if not c.execute("SELECT * FROM users WHERE username=?", (ADMIN_USER,)).fetchone():
            c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, 'admin')", (ADMIN_USER, generate_password_hash(ADMIN_PASS)))

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
.topbar .actions{display:flex;gap:12px;margin-left:auto}
.topbar .actions button{background:#1f2937;color:#cbd5e1;padding:8px 16px;border-radius:6px;font-size:13px;font-weight:500;border:none;cursor:pointer}
.topbar .actions button:hover{background:#374151}
.layout{display:flex;margin-top:60px;min-height:calc(100vh - 60px);width:100%}
.sidebar{width:240px;background:#111827;padding:20px 12px;border-right:1px solid #1f2937;position:fixed;left:0;top:60px;height:calc(100vh - 60px);overflow-y:auto}
.sidebar h4{color:#64748b;font-size:12px;text-transform:uppercase;margin:16px 0 8px 12px;letter-spacing:1px}
.sidebar a{display:flex;align-items:center;color:#94a3b8;text-decoration:none;padding:10px 12px;border-radius:8px;font-size:14px;margin-bottom:4px;transition:0.2s}
.sidebar a:hover,.sidebar a.active{background:#1e3a8a;color:#60a5fa}
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

.result-box{background:#1e293b;padding:10px 12px;border-radius:6px;color:#60a5fa;font-family:monospace;font-size:13px;white-space:pre-wrap;word-break:break-all;max-height:200px;overflow-y:auto;display:block;width:100%;position:relative}
.btn-copy{background:#10b981;color:#fff;border:none;padding:4px 10px;border-radius:4px;font-size:12px;cursor:pointer;margin-top:6px;width:auto;float:right}
.btn-copy:hover{background:#059669}

@media (max-width: 768px) {
    .topbar .search { display: none; }
    .topbar { justify-content: space-between; }
    .sidebar { display: none; }
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
}
</style>
</head>
<body>
<div class="topbar">
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

<div class="layout">
    {% if session.get('uid') %}
    <aside class="sidebar">
        <h4>Danh mục chính</h4>
        <a href="/user">🏠 Trang chủ</a>
        <a href="/deposit">💰 Nạp tiền</a>
        <a href="/tools">🛠 Tool</a>
        <a href="/tuts">📚 Tut</a>
        {% if session.get('role')=='admin' %}
        <h4>Quản trị viên</h4>
        <a href="/admin" style="color:#60a5fa">⚙️ Quản lý hệ thống</a>
        {% endif %}
    </aside>
    <main class="with-sidebar">{{ content|safe }}</main>
    {% else %}
    <main class="auth-main">{{ content|safe }}</main>
    {% endif %}
</div>

<script>
function copyText(btn, text) {
    navigator.clipboard.writeText(text).then(() => {
        let oldText = btn.innerText;
        btn.innerText = "Đã chép!";
        btn.style.background = "#2563eb";
        setTimeout(() => {
            btn.innerText = oldText;
            btn.style.background = "#10b981";
        }, 2000);
    }).catch(err => { alert("Lỗi khi sao chép!"); });
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
            return redirect('/admin' if row['role']=='admin' else '/user')
        return render_page("<div class='auth-box'><h2>Đăng nhập</h2><p class='err'>Sai tên hoặc mật khẩu!</p><form method='post' style='display:flex;flex-direction:column;gap:12px'><input name='u' placeholder='Tên đăng nhập' required><input name='p' type='password' placeholder='Mật khẩu' required><button>Đăng nhập</button></form><p style='text-align:center;margin-top:16px;font-size:14px;color:#94a3b8'>Chưa có tài khoản? <a href='/register' style='color:#3b82f6;text-decoration:none'>Đăng ký ngay</a></p></div>")
    return render_page("<div class='auth-box'><h2>Đăng nhập</h2><form method='post' style='display:flex;flex-direction:column;gap:12px'><input name='u' placeholder='Tên đăng nhập' required><input name='p' type='password' placeholder='Mật khẩu' required><button>Đăng nhập</button></form><p style='text-align:center;margin-top:16px;font-size:14px;color:#94a3b8'>Chưa có tài khoản? <a href='/register' style='color:#3b82f6;text-decoration:none'>Đăng ký ngay</a></p></div>")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u, p = request.form.get('u'), request.form.get('p')
        if u.lower() == ADMIN_USER.lower(): return "Tên này không được phép sử dụng."
        try:
            with get_db() as c:
                c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (u, generate_password_hash(p)))
            return redirect('/login')
        except:
            return render_page("<div class='auth-box'><h2>Đăng ký</h2><p class='err'>Tên đăng nhập đã tồn tại!</p><form method='post' style='display:flex;flex-direction:column;gap:12px'><input name='u' placeholder='Tên đăng nhập' required><input name='p' type='password' placeholder='Mật khẩu' required><button>Đăng ký</button></form><p style='text-align:center;margin-top:16px;font-size:14px;color:#94a3b8'>Đã có tài khoản? <a href='/login' style='color:#3b82f6;text-decoration:none'>Đăng nhập</a></p></div>")
    return render_page("<div class='auth-box'><h2>Đăng ký</h2><form method='post' style='display:flex;flex-direction:column;gap:12px'><input name='u' placeholder='Tên đăng nhập' required><input name='p' type='password' placeholder='Mật khẩu' required><button>Đăng ký</button></form><p style='text-align:center;margin-top:16px;font-size:14px;color:#94a3b8'>Đã có tài khoản? <a href='/login' style='color:#3b82f6;text-decoration:none'>Đăng nhập</a></p></div>")

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
        html += "<table><thead><tr><th>Tên</th><th>Giá</th><th>Kết quả / Link tải</th></tr></thead><tbody>"
        for p in purchases:
            prod = pmap.get(p['product_id'])
            if prod: 
                result_text = prod['result'].replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n').replace('\r', '')
                html += f"""
                <tr>
                    <td data-label='Tên'><b>{prod['name']}</b></td>
                    <td data-label='Giá'>{p['price']:,.0f}đ</td>
                    <td data-label='Kết quả'>
                        <div class='result-box'>
                            {prod['result']}
                            <button class='btn-copy' onclick="copyText(this, '{result_text}')">Sao chép</button>
                        </div>
                    </td>
                </tr>
                """
        html += "</tbody></table>"
    else: html += "<p style='color:#64748b'>Bạn chưa mua sản phẩm nào.</p>"
    return render_page(html)

@app.route('/deposit', methods=['GET', 'POST'])
@login_required
def deposit():
    if request.method == 'POST':
        amount = float(request.form.get('amount', 0))
        code = str(random.randint(0, 999999)).zfill(6)
        note = f"NAP {code} {session['uname']}"
        with get_db() as c:
            c.execute("INSERT INTO deposits (user_id, amount, code, note) VALUES (?, ?, ?, ?)", (session['uid'], amount, code, note))
        qr = f"https://img.vietqr.io/image/970422-0000000000-compact2.png?amount={int(amount)}&addInfo={note}"
        return render_page(f"<h2>Nạp tiền</h2><div class='card' style='max-width:400px'><p>Mã giao dịch: <b style='color:#3b82f6;font-size:20px'>{code}</b></p><p>Nội dung CK: <code style='background:#1e293b;padding:4px 8px;border-radius:4px'>{note}</code></p><img src='{qr}' style='max-width:100%;border-radius:8px;margin-top:12px'> <a href='/user' style='text-align:center;margin-top:12px;color:#60a5fa;text-decoration:none'>Quay lại</a></div>")
    return render_page("<h2>Nạp tiền</h2><form method='post' class='card' style='max-width:400px'><label>Số tiền muốn nạp (VNĐ):</label><input name='amount' type='number' min='10000' placeholder='VD: 50000' required><button style='margin-top:12px'>Tạo mã QR</button></form>")

@app.route('/tools')
@app.route('/tuts')
@login_required
def show_products():
    kind = 'tool' if 'tools' in request.path else 'tut'
    with get_db() as c:
        items = c.execute("SELECT * FROM products WHERE kind=?", (kind,)).fetchall()
    html = f"<h2>Danh sách {kind.upper()}</h2><div class='grid'>"
    if not items: html += "<p style='color:#64748b'>Chưa có sản phẩm nào.</p>"
    for t in items:
        img_src = f"/static/uploads/{t['image']}" if t['image'] else "https://via.placeholder.com/300x150/1f2937/60a5fa?text=No+Image"
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
                    <form method='post' action='/buy/{t['id']}' style='flex:1;margin:0'><button style='width:100%'>Mua ngay</button></form>
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
        if not p:
            return redirect('/tools')
        
        # Kiem tra xem user da mua san pham nay chua
        purchased = c.execute("SELECT * FROM purchases WHERE user_id=? AND product_id=?", (session['uid'], pid)).fetchone()
    
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
        result_text = p['result'].replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n').replace('\r', '')
        html += f"""
            <div style='margin-top:8px;'>
                <h3 style='margin:0 0 8px 0;font-size:16px;color:#10b981;'>Kết quả của bạn:</h3>
                <div class='result-box'>
                    {p['result']}
                    <button class='btn-copy' onclick="copyText(this, '{result_text}')">Sao chép</button>
                </div>
            </div>
        """
    else:
        html += f"""
            <form method='post' action='/buy/{p['id']}'>
                <button style='width:100%;padding:16px;font-size:16px;margin-top:8px;'>Mua ngay</button>
            </form>
        """
        
    html += """
        </div>
    </div>
    """
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

# --- ROUTES ADMIN ---
@app.route('/admin', methods=['GET', 'POST'])
@admin_required
def admin_home():
    if request.method == 'POST':
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
        users = c.execute("SELECT * FROM users WHERE role='user'").fetchall()
        prods = c.execute("SELECT * FROM products").fetchall()
        deps = c.execute("SELECT d.*, u.username FROM deposits d JOIN users u ON u.id=d.user_id WHERE status='pending'").fetchall()
    
    html = "<div>"
    html += "<h2>Bảng điều khiển quản trị</h2>"
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
    
    html += "<h3>Duyệt nạp tiền</h3>"
    if deps:
        html += "<table><thead><tr><th>ID</th><th>Người dùng</th><th>Số tiền</th><th>Nội dung CK</th><th>Hành động</th></tr></thead><tbody>"
        for d in deps:
            html += f"<tr><td data-label='ID'>{d['id']}</td><td data-label='Người dùng'>{d['username']}</td><td data-label='Số tiền'>{d['amount']:,.0f}đ</td><td data-label='Nội dung'>{d['note']}</td><td data-label='Hành động'><form method='post' action='/admin/dep/{d['id']}/ok'><button style='padding:6px 12px;font-size:12px'>Duyệt</button></form></td></tr>"
        html += "</tbody></table>"
    else:
        html += "<p class='ok'>Không có lệnh nạp nào đang chờ.</p>"
    
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
    
    html += "<h3>Quản lý người dùng</h3>"
    if users:
        html += "<table><thead><tr><th>Tên đăng nhập</th><th>Số dư</th><th>Cộng tiền</th></tr></thead><tbody>"
        for u in users:
            html += f"<tr><td data-label='Tên'>{u['username']}</td><td data-label='Số dư'>{u['balance']:,.0f}đ</td><td data-label='Cộng tiền'><form method='post' action='/admin/addmoney/{u['id']}' style='display:flex;gap:8px;margin:0'><input name='amt' type='number' placeholder='Nhập số tiền' style='padding:6px' required><button style='padding:6px 12px;font-size:12px'>Cộng</button></form></td></tr>"
        html += "</tbody></table>"
    else:
        html += "<p>Chưa có người dùng nào.</p>"
    
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

@app.route('/admin/addmoney/<int:uid>', methods=['POST'])
@admin_required
def add_money(uid):
    amt = float(request.form.get('amt', 0))
    with get_db() as c:
        c.execute("UPDATE users SET balance = balance + ? WHERE id=?", (amt, uid))
    return redirect('/admin')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))