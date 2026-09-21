import time
import random
import hashlib
import json
from datetime import datetime

import requests

from database import create_database, save_draw, get_total_draws
from predictor import main as run_prediction


# ============================================================
# SETTINGS
# ============================================================

API_URL = "https://mzplayapi.com/api/webapi/GetNoaverageEmerdList"

CHECK_INTERVAL = 10
REQUEST_TIMEOUT = 15
RETRY_DELAY = 10


HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
    "Origin": "https://mzplay0.com",
    "Referer": "https://mzplay0.com/"
}


# ============================================================
# RANDOM
# ============================================================

def generate_random():

    return ''.join(
        random.choices(
            "0123456789abcdef",
            k=32
        )
    )


# ============================================================
# SIGNATURE
# ============================================================

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


# ============================================================
# SIZE
# ============================================================

def get_size(number):

    if 0 <= number <= 4:
        return "小"

    return "大"


# ============================================================
# COLLECT DATA
# ============================================================

def collect_data():

    payload = {
        "pageSize": 10,
        "pageNo": 1,
        "typeId": 30,
        "language": 0,
    }

    payload["random"] = generate_random()

    payload["signature"] = generate_signature(
        payload
    )

    payload["timestamp"] = int(
        time.time()
    )

    response = requests.post(
        API_URL,
        headers=HEADERS,
        json=payload,
        timeout=REQUEST_TIMEOUT
    )

    print(
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
        f"API Status: {response.status_code}"
    )

    response.raise_for_status()

    data = response.json()

    if data.get("code") != 0:

        print("API 请求失败:")
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
                "新增:",
                issue,
                "| 数字:", number,
                "| 颜色:", colour,
                "| 大小:", size
            )

    return new_count


# ============================================================
# MAIN BOT
# ============================================================

def main():

    create_database()

    print()
    print("=" * 60)
    print("             LOTTERY BOT 24/7")
    print("=" * 60)
    print("API 自动抓取")
    print("SQLite 自动保存")
    print("新开奖自动预测")
    print("网络错误自动重试")
    print("=" * 60)
    print()

    last_total = get_total_draws()

    print(
        f"数据库当前数量: {last_total}"
    )

    print()
    print("Bot 已启动，等待新开奖...")
    print()

    while True:

        try:

            # ------------------------------------------------
            # 抓取数据
            # ------------------------------------------------

            new_count = collect_data()

            # ------------------------------------------------
            # 检查数据库
            # ------------------------------------------------

            current_total = get_total_draws()

            # ------------------------------------------------
            # 新开奖
            # ------------------------------------------------

            if current_total > last_total:

                print()
                print("=" * 60)
                print("🎉 发现新开奖")
                print("=" * 60)

                print(
                    f"新增: {current_total - last_total}"
                )

                print(
                    f"数据库总数量: {current_total}"
                )

                print("=" * 60)

                last_total = current_total

                # ------------------------------------------------
                # 自动预测
                # ------------------------------------------------

                print()
                print("正在分析下一期...")
                print()

                try:

                    run_prediction()

                except Exception as prediction_error:

                    print()
                    print("⚠️ Predictor 错误:")
                    print(prediction_error)

                print()
                print("=" * 60)
                print("⏳ 等待下一期开奖...")
                print("=" * 60)
                print()

            else:

                print(
                    f"[{datetime.now().strftime('%H:%M:%S')}] "
                    f"暂无新开奖"
                )

            # ------------------------------------------------
            # 等待
            # ------------------------------------------------

            time.sleep(CHECK_INTERVAL)

        except requests.exceptions.RequestException as error:

            print()
            print("=" * 60)
            print("⚠️ API / 网络错误")
            print("=" * 60)
            print(error)
            print(
                f"{RETRY_DELAY} 秒后自动重试..."
            )
            print("=" * 60)
            print()

            time.sleep(RETRY_DELAY)

        except Exception as error:

            print()
            print("=" * 60)
            print("⚠️ Bot 错误")
            print("=" * 60)
            print(error)
            print(
                f"{RETRY_DELAY} 秒后自动重试..."
            )
            print("=" * 60)
            print()

            time.sleep(RETRY_DELAY)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
