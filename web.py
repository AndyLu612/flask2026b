import os
import json
import requests
from bs4 import BeautifulSoup

from flask import Flask, render_template, request, make_response, jsonify
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
    homepage += "<a href=/road>台中市十大肇事路口</a><br>"
    homepage += "<a href=/weather>天氣查詢系統</a><br>"
    homepage += "<a href=/rate>本週新片進DB</a><br>"
    homepage += "<a href=/webhook3>查詢資料庫中該級的電影片名</a><br>"
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
        picture = item.find("img").get("src").strip()

        # 🔥 完整修正圖片網址（最重要）
        if picture.startswith("//"):
            picture = "https:" + picture
        elif picture.startswith("/"):
            picture = "http://www.atmovies.com.tw" + picture
        elif not picture.startswith("http"):
            picture = "http://www.atmovies.com.tw/" + picture

        title = item.find("div", class_="filmtitle").text.strip()

        movie_id = item.find("div", class_="filmtitle").find("a").get("href")
        movie_id = movie_id.replace("/", "").replace("movie", "")

        hyperlink = "http://www.atmovies.com.tw" + item.find("div", class_="filmtitle").find("a").get("href")

        show = item.find("div", class_="runtime").text
        show = show.replace("上映日期：", "").replace("片長：", "").replace("分", "")

        showDate = show[0:10]
        showLength = show[13:] if len(show) > 13 else "未知"

        doc = {
            "title": title,
            "picture": picture,
            "hyperlink": hyperlink,
            "showDate": showDate,
            "showLength": showLength,
            "lastUpdate": lastUpdate
        }

        db.collection("電影").document(movie_id).set(doc)

    return "<h2>爬蟲完成</h2><a href='/'>返回首頁</a>"




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
        info = f"<h2>查詢結果（關鍵字：{MovieTitle}）</h2>"

        docs = db.collection("電影").order_by("showDate").get()

        found = False

        for doc in docs:
            data = doc.to_dict()

            if MovieTitle in data["title"]:
                found = True

                pic = data["picture"]

                # 🔥 再保險修一次圖片
                if pic.startswith("//"):
                    pic = "https:" + pic
                elif pic.startswith("/"):
                    pic = "http://www.atmovies.com.tw" + pic

                info += f"""
                <div style="
                    border:1px solid #ccc;
                    border-radius:10px;
                    padding:15px;
                    margin:15px 0;
                    box-shadow:2px 2px 8px rgba(0,0,0,0.1);
                    background:#f9f9f9;
                ">
                    <h3>{data['title']}</h3>

                    <img src="{pic}" width="200"><br><br>

                    <a href="{data['hyperlink']}" target="_blank">點我看介紹</a><br>
                    片長：{data['showLength']} 分鐘<br>
                    上映日期：{data['showDate']}
                </div>
                """

        if not found:
            info += "<h3>查無資料</h3>"

        info += "<br><a href='/'>返回首頁</a>"

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
        result_html = "<h3>查無資料</h3>"

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


@app.route("/road", methods=["GET", "POST"])
def road():

    Result = ""

    url = "https://datacenter.taichung.gov.tw/swagger/OpenData/a1b899c0-511f-4e3d-b22b-814982a97e41"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    JsonData = []


    for i in range(5):
        try:
            Data = requests.get(url, headers=headers, timeout=10)
            Data.raise_for_status()
            JsonData = Data.json()
            break
        except Exception:
            import time
            time.sleep(2)


    if not JsonData:
        return """
        <h2>台中市十大肇事路口查詢</h2>
        <p>政府OpenData目前無回應，請稍後再試</p>
        <a href='/'>返回首頁</a>
        """


    if request.method == "POST":

        Road = request.form["Road"]

        # 🔍 查單一
        if Road.strip() != "":

            for item in JsonData:
                if Road in item["路口名稱"]:
                    Result += (
                        item["路口名稱"] +
                        "：發生" +
                        item["總件數"] +
                        "件，主因是" +
                        item["主要肇因"] +
                        "<br><br>"
                    )

            if Result == "":
                Result = "抱歉，查無相關資料！"

        # 📋 查全部
        else:

            Result = "<h3>📊 全部資料（前10筆）</h3>"

            for i, item in enumerate(JsonData[:10]):
                Result += (
                    str(i+1) + ". " +
                    item["路口名稱"] +
                    "：發生" +
                    item["總件數"] +
                    "件，主因：" +
                    item["主要肇因"] +
                    "<br>"
                )


    webpage = """
    <h2>台中市十大肇事路口查詢</h2>

    <form method="post">
        請輸入路名（不輸入＝查全部）：
        <input type="text" name="Road">
        <input type="submit" value="查詢">
    </form>

    <hr>
    """

    webpage += Result
    webpage += "<br><br><a href='/'>返回首頁</a>"

    return webpage


@app.route("/weather", methods=["GET", "POST"])
def weather():

    result = ""

    if request.method == "POST":

        city = request.form.get("city", "").strip()

        if city == "":
            result = "請輸入縣市（例：臺中市）"

        else:

            city = city.replace("台", "臺")

            token = "rdec-key-123-45678-011121314"

            url = (
                "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"
                "?Authorization=" + token +
                "&format=JSON&locationName=" + city
            )

            try:
                data = requests.get(url, timeout=10)
                json_data = data.json()

                locations = json_data["records"]["location"]

                if len(locations) == 0:
                    result = "查無資料，請輸入正確縣市（例：臺中市）"
                else:
                    weather = locations[0]["weatherElement"][0]["time"][0]["parameter"]["parameterName"]
                    rain = locations[0]["weatherElement"][1]["time"][0]["parameter"]["parameterName"]

                    result = f"""
                    <h3>查詢結果：{city}</h3>
                    <p>天氣：{weather}</p>
                    <p>降雨機率：{rain}%</p>
                    """

            except Exception as e:
                result = "查詢失敗：" + str(e)

    return f"""
    <h2>🌤 天氣查詢系統</h2>

    <form method="post">
        輸入縣市：
        <input type="text" name="city" placeholder="例：臺中市">
        <input type="submit" value="查詢">
    </form>

    <hr>

    {result}

    <br><br>
    <a href='/'>返回首頁</a>
    """


# ======================
# 本週新片進DB
# ======================
@app.route("/rate")
def rate():
    #本週新片
    url = "https://www.atmovies.com.tw/movie/new/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    lastUpdate = sp.find(class_="smaller09").text[5:]
    print(lastUpdate)
    print()

    result=sp.select(".filmList")

    for x in result:
        title = x.find("a").text
        introduce = x.find("p").text

        movie_id = x.find("a").get("href").replace("/", "").replace("movie", "")
        hyperlink = "http://www.atmovies.com.tw/movie/" + movie_id
        picture = "https://www.atmovies.com.tw/photo101/" + movie_id + "/pm_" + movie_id + ".jpg"

        r = x.find(class_="runtime").find("img")
        rate = ""
        if r != None:
            rr = r.get("src").replace("/images/cer_", "").replace(".gif", "")
            if rr == "G":
                rate = "普遍級"
            elif rr == "P":
                rate = "保護級"
            elif rr == "F2":
                rate = "輔12級"
            elif rr == "F5":
                rate = "輔15級"
            else:
                rate = "限制級"

        t = x.find(class_="runtime").text

        t1 = t.find("片長")
        t2 = t.find("分")
        showLength = t[t1+3:t2]

        t1 = t.find("上映日期")
        t2 = t.find("上映廳數")
        showDate = t[t1+5:t2-8]

        doc = {
            "title": title,
            "introduce": introduce,
            "picture": picture,
            "hyperlink": hyperlink,
            "showDate": showDate,
            "showLength": int(showLength),
            "rate": rate,
            "lastUpdate": lastUpdate
        }

        db = firestore.client()
        doc_ref = db.collection("本週新片含分級").document(movie_id)
        doc_ref.set(doc)
    return "本週新片已爬蟲及存檔完畢，網站最近更新日期為：" + lastUpdate


# ======================
# 清理字串（避免查不到）
# ======================
def clean(text):
    return str(text).strip().replace(" ", "").replace("\n", "").replace("\r", "")

# ======================
# Webhook
# ======================
@app.route("/webhook3", methods=["POST"])
def webhook():

    req = request.get_json(force=True)

    action = req.get("queryResult", {}).get("action", "")

    info = "查無資料"

    if action == "rateChoice":

        # Dialogflow 傳來的值
        rate = req["queryResult"]["parameters"].get("rate", "")

        print("USER RATE:", repr(rate))

        db = firestore.client()

        docs = db.collection("電影含分級").stream()

        result = ""

        for doc in docs:

            data = doc.to_dict()

            db_rate = data.get("rate", "")

            print("DB RATE:", repr(db_rate))

            # ======================
            # 核心比對（已修好）
            # ======================
            if clean(rate) == clean(db_rate):

                result += "片名：" + data.get("title", "") + "\n"
                result += "簡介：" + data.get("introduce", "") + "\n"
                result += "上映：" + str(data.get("showDate", "")) + "\n"
                result += "片長：" + str(data.get("showLength", "")) + " 分鐘\n"
                result += "連結：" + data.get("hyperlink", "") + "\n\n"

        if result == "":
            result = "沒有符合條件的電影"

        info = "您選擇的電影分級：" + rate + "\n\n" + result

    return jsonify({
        "fulfillmentText": info
    })


# ======================
# 🚀 run
# ======================
if __name__ == "__main__":
    app.run(debug=True)