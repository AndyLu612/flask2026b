import requests
import json

city = input("請輸入縣市：")
city = city.replace("台", "臺")

token = "rdec-key-123-45678-011121314"

url = (
    "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"
    "?Authorization=" + token +
    "&format=JSON&locationName=" + city
)

Data = requests.get(url)
data = json.loads(Data.text)

locations = data["records"]["location"]

if len(locations) == 0:
    print("查無資料，請確認縣市名稱（例：臺中市）")
else:
    weather = locations[0]["weatherElement"][0]["time"][0]["parameter"]["parameterName"]
    rain = locations[0]["weatherElement"][1]["time"][0]["parameter"]["parameterName"]

    print(weather + "，降雨機率：" + rain + "%")