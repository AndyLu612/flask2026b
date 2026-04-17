import os
import json
import requests
from bs4 import BeautifulSoup

from flask import Flask, render_template, request
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# ======================
# 🔥 Firebase（本地 + 雲端自動切換）
# ======================
db = None

firebase_config = os.environ.get("FIREBASE_CONFIG")

if not firebase_admin._apps:
    if firebase_config:
        # ☁️ Vercel / 雲端
        cred = credentials.Certificate(json.loads(firebase_config))
    else:
        # 💻 本地開發
        cred = credentials.Certificate("spider/serviceAccountKey.json")

    firebase_admin.initialize_app(cred)

db = firestore.client()


# ======================
# 🏠 首頁
# ======================
@app.route("/")
def index():
    homepage = "<h1>盧安毅Python網頁</h1>"
    homepage += "<a href=/mis>MIS</a><br>"
    homepage += "<a href=/today>顯示日期時間</a><br>"
    homepage += "<a href=/welcome?nick=andylu>傳送使用者暱稱</a><br>"
    homepage += "<a href=/account>網頁表單傳值</a><br>"
    homepage += "<a href=/about>安毅簡介網頁</a><br>"
    homepage += "<a href=/math3>次方與根號計算</a><br>"
    homepage += "<a href=/movie>讀取開眼電影即將上映影片，寫入Firestore</a><br>"
    homepage += "<a href=/searchQ>根據片名關鍵字查詢資料</a><br>"
    homepage += "<a href=/search_teacher>靜宜資管老師查詢</a><br>"
    homepage += "<a href=/course>子青老師本學期課程</a><br>"
    return homepage



# ======================
# 📚 MIS
# ======================
@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><br><a href=/>返回首頁</a>"


# ======================
# ⏰ 時間
# ======================
@app.route("/today")
def today():
    now = datetime.now()
    return render_template("today.html", datetime=str(now))


# ======================
# 👤 welcome
# ======================
@app.route("/welcome", methods=["GET"])
def welcome():
    user = request.values.get("nick")
    return render_template("welcome.html", name=user)


# ======================
# 📄 account
# ======================
@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        return "帳號：" + user + " 密碼：" + pwd
    else:
        return render_template("account.html")


# ======================
# ℹ️ about
# ======================
@app.route("/about")
def about():
    return render_template("about.html")


# ======================
# 🧮 math3
# ======================
@app.route("/math3", methods=["GET", "POST"])
def math3():
    result = None

    if request.method == "POST":
        x = float(request.form["x"])
        opt = request.form["opt"]

        if opt == "**":
            y = float(request.form["y"])
            result = x ** y

        elif opt == "root":
            y = float(request.form["y"])
            if y == 0:
                result = "數學不能開0次根"
            else:
                result = x ** (1 / y)

        else:
            result = "請輸入正確運算"

    return render_template("math3.html", result=result)


# ======================
# 🎬 movie（爬蟲 + Firebase）
# ======================
@app.route("/movie")
def movie():
    url = "http://www.atmovies.com.tw/movie/next/"
    res = requests.get(url)
    res.encoding = "utf-8"

    sp = BeautifulSoup(res.text, "html.parser")
    result = sp.select(".filmListAllX li")

    lastUpdate = sp.find("div", class_="smaller09").text[5:]

    for item in result:
        picture = item.find("img").get("src").replace(" ", "")
        title = item.find("div", class_="filmtitle").text

        movie_id = item.find("div", class_="filmtitle").find("a").get("href")
        movie_id = movie_id.replace("/", "").replace("movie", "")

        hyperlink = "http://www.atmovies.com.tw" + item.find("div", class_="filmtitle").find("a").get("href")

        show = item.find("div", class_="runtime").text
        show = show.replace("上映日期：", "").replace("片長：", "").replace("分", "")

        showDate = show[0:10]
        showLength = show[13:]

        doc = {
            "title": title,
            "picture": picture,
            "hyperlink": hyperlink,
            "showDate": showDate,
            "showLength": showLength,
            "lastUpdate": lastUpdate
        }

        db.collection("電影").document(movie_id).set(doc)

    return """
    爬蟲完成 + Firebase寫入完成，更新時間：""" + lastUpdate + """
    <br><br>
    <a href="/">返回首頁</a>
    """



# ======================
# 🎬 movie（根據片名關鍵字查詢資料）
# ======================
@app.route("/search")
def search():
    info = ""
    db = firestore.client()  
    docs = db.collection("電影").get() 
    for doc in docs:
        if "者" in doc.to_dict()["title"]:
            info += "片名：" + doc.to_dict()["title"] + "<br>" 
            info += "海報：" + doc.to_dict()["picture"] + "<br>"
            info += "影片介紹：" + doc.to_dict()["hyperlink"] + "<br>"
            info += "片長：" + doc.to_dict()["showLength"] + " 分鐘<br>" 
            info += "上映日期：" + doc.to_dict()["showDate"] + "<br><br>"           
    return info



# ======================
# 🎬 movie（根據片名關鍵字查詢資料）
# ======================
@app.route("/searchQ", methods=["POST", "GET"])
def searchQ():

    if request.method == "POST":
        MovieTitle = request.form["MovieTitle"]
        info = ""

        collection_ref = db.collection("電影")
        docs = collection_ref.order_by("showDate").get()

        for doc in docs:
            data = doc.to_dict()

            if MovieTitle in data["title"]:
                info += "片名：" + data["title"] + "<br>"
                info += "影片介紹：" + data["hyperlink"] + "<br>"
                info += "片長：" + data["showLength"] + " 分鐘<br>"
                info += "上映日期：" + data["showDate"] + "<br><br>"

        return info

    else:
        return render_template("input.html")


# ======================
# 🎓 teacher（美化查詢結果）
# ======================
@app.route("/search_teacher", methods=["GET", "POST"])
def search_teacher():

    if request.method == "GET":
        return render_template("teacher.html")

    keyword = request.form["keyword"]

    docs = db.collection("靜宜資管2026B").get()

    result_html = ""

    for doc in docs:
        data = doc.to_dict()

        if keyword in data["name"]:

            result_html += f"""
            <div style="
                border:1px solid #ccc;
                border-radius:10px;
                padding:15px;
                margin:10px 0;
                box-shadow:2px 2px 8px rgba(0,0,0,0.1);
                background:#f9f9f9;
            ">
                <h3>👨‍🏫 {data['name']}</h3>
                <p>🔬 研究室：{data.get('lab','無資料')}</p>
                <p>📧 信箱：{data.get('mail','無資料')}</p>
            </div>
            """

    if result_html == "":
        result_html = "<h3>查無資料 😢</h3>"

    return f"""
    <h2>靜宜資管老師查詢</h2>
    <p>查詢結果 (關鍵字: {keyword})</p>
    {result_html}
    <br>
    <a href='/'>返回首頁</a>
    """


# ======================
# 📚 course（爬蟲 + 課程查詢）
# ======================
@app.route("/course")
def course_drive():

    import requests
    from bs4 import BeautifulSoup

    url = "https://www1.pu.edu.tw/~tcyang/course.html"

    res = requests.get(url,verify=False)
    res.encoding = "utf-8"

    soup = BeautifulSoup(res.text, "html.parser")

    links = soup.find_all("a")

    info = "<h2>子青老師課程資料</h2>"

    seen = set()

    for a in links:
        href = a.get("href")

        if href and "drive.google.com" in href:

            text = a.text.strip()

            if text == "":
                text = a.parent.text.strip()

            # 去重
            if href not in seen:
                seen.add(href)

                info += f"""
                <div style="border:1px solid #ccc;
                            padding:10px;
                            margin:10px;
                            border-radius:8px;">
                    📘 課程：{text}<br>
                    🔗 連結：<a href="{href}" target="_blank">{href}</a>
                </div>
                """

    info += "<br><a href='/'>返回首頁</a>"

    return info


# ======================
# 🚀 run
# ======================
if __name__ == "__main__":
    app.run(debug=True)