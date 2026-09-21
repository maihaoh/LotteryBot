import requests
import hashlib
import json
import random
import time

from database import create_database, save_draw, get_total_draws


API_URL = "https://mzplayapi.com/api/webapi/GetNoaverageEmerdList"


headers = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
    "Origin": "https://mzplay0.com",
    "Referer": "https://mzplay0.com/"
}


def generate_random():
    return ''.join(
        random.choices(
            "0123456789abcdef",
            k=32
        )
    )


def generate_signature(data):

    t = data.copy()

    t.pop("signature", None)
    t.pop("timestamp", None)

    sorted_data = {}

    for key in sorted(t.keys()):

        value = t[key]

        if key in ["signature", "track", "xosoBettingData"]:
            continue

        if value is None or value == "":
            continue

        sorted_data[key] = value

    json_string = json.dumps(
        sorted_data,
        separators=(",", ":"),
        ensure_ascii=False
    )

    return hashlib.md5(
        json_string.encode("utf-8")
    ).hexdigest().upper()


def get_size(number):

    if 0 <= number <= 4:
        return "小"

    return "大"


def collect_data():

    # =========================
    # 自动生成 Payload
    # =========================

    payload = {
        "pageSize": 10,
        "pageNo": 1,
        "typeId": 30,
        "language": 0,
    }

    payload["random"] = generate_random()

    payload["signature"] = generate_signature(payload)

    payload["timestamp"] = int(time.time())


    # =========================
    # 请求 API
    # =========================

    response = requests.post(
        API_URL,
        headers=headers,
        json=payload,
        timeout=15
    )

    print("API Status:", response.status_code)

    data = response.json()


    # =========================
    # 检查 API
    # =========================

    if data.get("code") != 0:

        print("API 请求失败")

        print(data)

        return


    # =========================
    # 取得开奖列表
    # =========================

    draw_list = data["data"]["list"]

    new_count = 0


    # =========================
    # 保存数据库
    # =========================

    for item in draw_list:

        issue = item["issueNumber"]

        number = int(item["number"])

        colour = item["colour"]

        size = get_size(number)


        before = get_total_draws()

        save_draw(
            issue,
            number,
            colour,
            size
        )

        after = get_total_draws()


        # 新数据
        if after > before:

            new_count += 1

            print(
                "新增:",
                issue,
                "| 数字:", number,
                "| 颜色:", colour,
                "| 大小:", size
            )


    print()
    print("=" * 50)

    print("本次新增:", new_count)

    print("数据库总数量:", get_total_draws())

    print("=" * 50)


# =========================
# 主程序
# =========================

if __name__ == "__main__":

    create_database()

    collect_data()