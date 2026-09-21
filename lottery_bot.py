import time
import random
import hashlib
import json

import requests

from database import create_database, save_draw, get_total_draws
from predictor import main as run_prediction


API_URL = "https://mzplayapi.com/api/webapi/GetNoaverageEmerdList"

REQUEST_TIMEOUT = 15

COLLECT_INTERVAL = 30

HEADERS = {
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

        if key in [
            "signature",
            "track",
            "xosoBettingData"
        ]:
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

    payload = {
        "pageSize": 10,
        "pageNo": 1,
        "typeId": 30,
        "language": 0
    }

    payload["random"] = generate_random()

    payload["signature"] = generate_signature(
        payload
    )

    payload["timestamp"] = int(
        time.time()
    )

    try:

        response = requests.post(
            API_URL,
            headers=HEADERS,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )

        print(
            "API Status:",
            response.status_code
        )

        response.raise_for_status()

        data = response.json()

    except Exception as error:

        print()
        print("❌ API 请求失败:")
        print(error)

        return 0


    if data.get("code") != 0:

        print()
        print("❌ API 返回错误:")
        print(data)

        return 0


    draw_list = data["data"]["list"]

    new_count = 0

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

        if after > before:

            new_count += 1

            print(
                "🆕 新开奖:",
                issue,
                "| 数字:", number,
                "| 颜色:", colour,
                "| 大小:", size
            )


    print()
    print(
        "本次新增:",
        new_count
    )

    print(
        "数据库总数量:",
        get_total_draws()
    )

    return new_count


def main():

    create_database()

    print()
    print("=" * 60)
    print("LOTTERY REAL-TIME BOT")
    print("=" * 60)

    print(
        "⏱️ 自动抓取间隔:",
        COLLECT_INTERVAL,
        "秒"
    )

    print()

    while True:

        try:

            print()
            print("=" * 60)

            print(
                "开始检查最新开奖..."
            )

            new_count = collect_data()


            if new_count > 0:

                print()
                print(
                    "🎯 发现新开奖，开始重新预测..."
                )

                run_prediction()

            else:

                print()
                print(
                    "⏳ 暂无新开奖，等待下一次检查..."
                )


            print()
            print(
                f"⏱️ {COLLECT_INTERVAL} 秒后再次检查..."
            )

            time.sleep(
                COLLECT_INTERVAL
            )


        except KeyboardInterrupt:

            print()
            print(
                "🛑 Bot 已停止"
            )

            break


        except Exception as error:

            print()
            print(
                "❌ Bot 发生错误:"
            )

            print(error)

            print()
            print(
                "30 秒后重新尝试..."
            )

            time.sleep(
                COLLECT_INTERVAL
            )


if __name__ == "__main__":
    main()
