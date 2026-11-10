from flask import Flask, request, redirect, session, send_file
import os, hashlib, io, json
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "iraq-2026")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = 1800

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///army.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default="commander")
    unit_name = db.Column(db.String(100), default="")

class Unit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unit_name = db.Column(db.String(100), nullable=False)
    commander_name = db.Column(db.String(100), default="")
    owner = db.Column(db.String(50), default="")
    data_json = db.Column(db.Text, default="{}")
    def get_data(self):
        try:
            return json.loads(self.data_json)
        except:
            return {"persons": {"ضباط": {"muqarrar":0,"mawjood":0},"مراتب": {"muqarrar":0,"mawjood":0},"موظفين مدنيين": {"muqarrar":0,"mawjood":0}}, "weapons": {}, "ammunition": {}, "vehicles": {}}
    def set_data(self, data):
        self.data_json = json.dumps(data, ensure_ascii=False)

def hash_pw(p):
    return hashlib.sha256(p.encode()).hexdigest()
  def init_db():
    with app.app_context():
        db.create_all()
        if User.query.count() == 0:
            db.session.add(User(username="admin", password=hash_pw("1234"), role="admin", unit_name=""))
            db.session.add(User(username="ali", password=hash_pw("1111"), role="commander", unit_name="فوج الأول"))
            db.session.add(User(username="ahmed", password=hash_pw("2222"), role="commander", unit_name="فوج الثاني"))
            db.session.commit()
        if Unit.query.count() == 0:
            for name, owner in [("فوج الأول", "ali"), ("فوج الثاني", "ahmed")]:
                data = {"persons": {"ضباط": {"muqarrar": 20, "mawjood": 15},"مراتب": {"muqarrar": 200, "mawjood": 180},"موظفين مدنيين": {"muqarrar": 10, "mawjood": 8}}, "weapons": {}, "ammunition": {}, "vehicles": {}}
                u = Unit(unit_name=name, commander_name="آمر " + name, owner=owner)
                u.set_data(data)
                db.session.add(u)
            db.session.commit()

CSS = """
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:Arial;direction:rtl;text-align:right;background:#f2f2f2;margin:0;padding:10px}
.container{max-width:900px;margin:auto;background:white;padding:15px;border-radius:12px}
h2{color:#1F4E78;text-align:center}
input,select{width:100%;padding:12px;margin:6px 0;border:1px solid #ccc;border-radius:8px;font-size:16px;box-sizing:border-box}
button,.btn{display:block;width:100%;padding:13px;background:#1F4E78;color:white;border:none;border-radius:8px;font-size:17px;margin-top:10px;text-align:center;text-decoration:none}
.btn-green{background:green}.btn-orange{background:orange}.btn-red{background:#c0392b}.btn-gray{background:gray}
table{width:100%;border-collapse:collapse;margin-top:10px;font-size:14px}
th,td{border:1px solid #ddd;padding:8px;text-align:center}
th{background:#1F4E78;color:white}
.card{background:#eaf2f8;padding:12px;border-radius:10px;margin:10px 0}
.small{font-size:13px;color:#666;text-align:center}
</style>
"""
def header(t): return CSS + "<div class='container'><h2>" + t + "</h2>"
def footer(): return "</div>"
 @app.route("/", methods=["GET", "POST"])
def login():
    init_db()
    if request.method == "POST":
        u = request.form["username"]; p = hash_pw(request.form["password"])
        user = User.query.filter_by(username=u, password=p).first()
        if user:
            session["user"] = user.username; session["role"] = user.role; session["unit_name"] = user.unit_name
            session.permanent = True
            return redirect("/dashboard")
        return header("خطأ") + "<p>خطأ بالدخول</p><a class='btn' href='/'>رجوع</a>" + footer()
    html = header("نظام تعداد وحدات الجيش العراقي")
    html += "<form method='post'><label>اسم المستخدم</label><input name='username'><label>كلمة السر</label><input name='password' type='password'><button>دخول</button></form><p class='small'>admin / 1234<br>ali / 1111<br>ahmed / 2222</p>"
    return html + footer()

@app.route("/dashboard")
def dashboard():
    if "user" not in session: return redirect("/")
    init_db()
    if session["role"] == "admin":
        units = Unit.query.all()
    else:
        units = Unit.query.filter((Unit.unit_name == session["unit_name"]) | (Unit.owner == session["user"])).all()
    html = header("اهلا " + session["user"] + " - " + session["role"])
    html += "<p style='text-align:center'>عدد الوحدات: " + str(len(units)) + "</p>"
    if session["role"] == "admin":
        html += "<a class='btn btn-green' href='/add_unit'>+ اضافة وحدة</a><a class='btn btn-green' href='/add_user'>+ اضافة مستخدم</a><a class='btn btn-orange' href='/export'>تحميل Excel</a>"
    for u in units:
        d = u.get_data(); p = d["persons"]
        dm = p["ضباط"]["mawjood"]; dq = p["ضباط"]["muqarrar"]
        mm = p["مراتب"]["mawjood"]; mq = p["مراتب"]["muqarrar"]
        cm = p["موظفين مدنيين"]["mawjood"]; cq = p["موظفين مدنيين"]["muqarrar"]
        tot_m = dm+mm+cm; tot_q = dq+mq+cq
        jah = round(tot_m/tot_q*100,1) if tot_q else 0
        html += "<div class='card'><b>" + u.unit_name + "</b> - آمر: " + u.commander_name + "<br>ضباط: " + str(dm)+"/"+str(dq) + " | مراتب: " + str(mm)+"/"+str(mq) + " | مدنيين: " + str(cm)+"/"+str(cq) + "<br>المجموع: " + str(tot_m)+"/"+str(tot_q) + " - الجاهزية: " + str(jah) + "%<br><a class='btn' href='/unit/" + str(u.id) + "'>عرض وتعديل</a></div>"
    html += "<a class='btn btn-red' href='/logout'>خروج</a>"
    return html + footer() 
 @app.route("/unit/<int:uid>", methods=["GET", "POST"])
def unit_detail(uid):
    if "user" not in session: return redirect("/")
    u = Unit.query.get_or_404(uid)
    if request.method == "POST":
        d = u.get_data()
        def geti(k):
            try: return int(request.form.get(k, 0) or 0)
            except: return 0
        d["persons"]["ضباط"] = {"muqarrar": geti("dq"), "mawjood": geti("dm")}
        d["persons"]["مراتب"] = {"muqarrar": geti("mq"), "mawjood": geti("mm")}
        d["persons"]["موظفين مدنيين"] = {"muqarrar": geti("cq"), "mawjood": geti("cm")}
        d["weapons"] = {k: geti("w_" + k) for k in ["مسدس", "بندقية M16", "بندقية AK47", "رشاشة", "هاون", "قاذفة RPG"]}
        d["ammunition"] = {k: geti("a_" + k) for k in ["مسدس", "بندقية", "رشاشة", "هاون", "RPG"]}
        d["vehicles"] = {k: geti("v_" + k) for k in ["همر", "بيكب", "مدرعة", "شاحنة", "مصفح"]}
        u.set_data(d); db.session.commit()
        return redirect("/dashboard")
    d = u.get_data(); p = d["persons"]
    html = header("تعديل: " + u.unit_name)
    html += "<form method='post'>"
    html += "<h3>الاشخاص</h3>"
    for key, label in [("ضباط", "ضباط"), ("مراتب", "مراتب"), ("موظفين مدنيين", "موظفين مدنيين")]:
        html += "<label>" + label + " - المقرر</label><input name='" + ("dq" if key=="ضباط" else "mq" if key=="مراتب" else "cq") + "' type='number' value='" + str(p[key]["muqarrar"]) + "'>"
        html += "<label>" + label + " - الموجود</label><input name='" + ("dm" if key=="ضباط" else "mm" if key=="مراتب" else "cm") + "' type='number' value='" + str(p[key]["mawjood"]) + "'>"
    html += "<h3>الاسلحة</h3>"
    for k in ["مسدس", "بندقية M16", "بندقية AK47", "رشاشة", "هاون", "قاذفة RPG"]:
        html += "<label>" + k + "</label><input name='w_" + k + "' type='number' value='" + str(d["weapons"].get(k,0)) + "'>"
    html += "<h3>العتاد</h3>"
    for k in ["مسدس", "بندقية", "رشاشة", "هاون", "RPG"]:
        html += "<label>عتاد " + k + "</label><input name='a_" + k + "' type='number' value='" + str(d["ammunition"].get(k,0)) + "'>"
    html += "<h3>العجلات</h3>"
    for k in ["همر", "بيكب", "مدرعة", "شاحنة", "مصفح"]:
        html += "<label>" + k + "</label><input name='v_" + k + "' type='number' value='" + str(d["vehicles"].get(k,0)) + "'>"
    html += "<button>حفظ التغييرات</button></form><a class='btn btn-gray' href='/dashboard'>رجوع</a>"
    return html + footer()

@app.route("/add_unit", methods=["GET", "POST"])
def add_unit():
    if "user" not in session or session["role"] != "admin": return redirect("/")
    if request.method == "POST":
        u = Unit(unit_name=request.form["unit_name"], commander_name=request.form.get("commander",""), owner=request.form.get("owner",""))
        u.set_data({"persons": {"ضباط": {"muqarrar":0,"mawjood":0},"مراتب": {"muqarrar":0,"mawjood":0},"موظفين مدنيين": {"muqarrar":0,"mawjood":0}}, "weapons": {}, "ammunition": {}, "vehicles": {}})
        db.session.add(u); db.session.commit(); return redirect("/dashboard")
    html = header("اضافة وحدة")
    html += "<form method='post'><input name='unit_name' placeholder='اسم الوحدة' required><input name='commander' placeholder='اسم الآمر'><input name='owner' placeholder='اسم مستخدم الآمر'><button>اضافة</button></form>"
    return html + footer()
  @app.route("/add_user", methods=["GET", "POST"])
def add_user():
    if "user" not in session or session["role"] != "admin": return redirect("/")
    if request.method == "POST":
        if User.query.filter_by(username=request.form["username"]).first():
            return header("خطأ") + "<p>المستخدم موجود</p><a class='btn' href='/dashboard'>رجوع</a>" + footer()
        db.session.add(User(username=request.form["username"], password=hash_pw(request.form["password"]), role=request.form["role"], unit_name=request.form.get("unit_name","")))
        db.session.commit(); return redirect("/dashboard")
    html = header("اضافة مستخدم")
    html += "<form method='post'><input name='username' placeholder='اسم المستخدم' required><input name='password' placeholder='كلمة السر' required><input name='unit_name' placeholder='اسم الوحدة'><select name='role'><option value='commander'>آمر وحدة</option><option value='admin'>مدير</option></select><button>اضافة</button></form>"
    return html + footer()

@app.route("/logout")
def logout():
    session.clear(); return redirect("/")

@app.route("/export")
def export():
    if "user" not in session or session["role"] != "admin": return redirect("/")
    try:
        from openpyxl import Workbook
        wb = Workbook(); ws = wb.active; ws.title = "تعداد"
        ws.append(["الوحدة", "الآمر", "ضباط مقرر", "ضباط موجود", "مراتب مقرر", "مراتب موجود", "مدنيين مقرر", "مدنيين موجود", "المجموع مقرر", "المجموع موجود", "الجاهزية %"])
        for u in Unit.query.all():
            d = u.get_data(); p = d["persons"]
            dq = p["ضباط"]["muqarrar"]; dm = p["ضباط"]["mawjood"]; mq = p["مراتب"]["muqarrar"]; mm = p["مراتب"]["mawjood"]; cq = p["موظفين مدنيين"]["muqarrar"]; cm = p["موظفين مدنيين"]["mawjood"]
            tq = dq+mq+cq; tm = dm+mm+cm; jah = round(tm/tq*100,1) if tq else 0
            ws.append([u.unit_name, u.commander_name, dq, dm, mq, mm, cq, cm, tq, tm, jah])
        buf = io.BytesIO(); wb.save(buf); buf.seek(0)
        return send_file(buf, as_attachment=True, download_name="army.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        return str(e)
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
  
  
