from flask import Flask, render_template, request
from datetime import datetime
from flask import redirect
app = Flask(__name__)

@app.route("/")
def index():
    homepage = "<h1>盧安毅Python網頁</h1>"
    homepage += "<a href=/mis>MIS</a><br>"
    homepage += "<a href=/today>顯示日期時間</a><br>"
    homepage += "<a href=/welcome?nick=andylu>傳送使用者暱稱</a><br>"
    homepage += "<a href=/account>網頁表單傳值</a><br>"
    homepage += "<a href=/about>安毅簡介網頁</a><br>"
    homepage += "<a href=/math3>次方與根號計算</a><br>"
    return homepage


@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><br><a href=/>返回首頁</a>s"

@app.route("/today")
def today():
    now = datetime.now()
    return render_template("today.html", datetime = str(now))

@app.route("/welcome", methods=["GET"])
def welcome():
    user = request.values.get("nick")
    return render_template("welcome.html", name=user)

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        result = "您輸入的帳號是：" + user + "; 密碼為：" + pwd 
        return result
    else:
        return render_template("account.html")


@app.route("/about")
def about():
    return render_template("about.html")

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
                result = x ** (1/y)

        else:
            result = "請輸入正確運算"

    return render_template("math3.html", result=result)

if __name__ == "__main__":
    app.run()