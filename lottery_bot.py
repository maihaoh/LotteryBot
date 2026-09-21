import time
import random
import hashlib
import json

import requests

from database import (
    create_database,
    save_draw,
    get_total_draws,
    get_unchecked_predictions,
    update_prediction_result
)

from predictor import main as run_prediction


API_URL = (
    "https://mzplayapi.com/api/webapi/"
    "GetNoaverageEmerdList"
)


REQUEST_TIMEOUT = 15


HEADERS = {

    "User-Agent":
        "Mozilla/5.0",

    "Content-Type":
        "application/json",

    "Origin":
        "https://mzplay0.com",

    "Referer":
        "https://mzplay0.com/"
}


# =========================================================
# Random
# =========================================================

def generate_random():

    return ''.join(
        random.choices(
            "0123456789abcdef",
            k=32
        )
    )


# =========================================================
# Signature
# =========================================================

def generate_signature(data):

    t = data.copy()

    t.pop(
        "signature",
        None
    )

    t.pop(
        "timestamp",
        None
    )


    sorted_data = {}


    for key in sorted(
        t.keys()
    ):

        value = t[key]


        if key in [
            "signature",
            "track",
            "xosoBettingData"
        ]:

            continue


        if (
            value is None
            or value == ""
        ):

            continue


        sorted_data[key] = value


    json_string = json.dumps(
        sorted_data,
        separators=(
            ",",
            ":"
        ),
        ensure_ascii=False
    )


    return hashlib.md5(
        json_string.encode(
            "utf-8"
        )
    ).hexdigest().upper()


# =========================================================
# 大小
# =========================================================

def get_size(number):

    number = int(number)

    if 0 <= number <= 4:
        return "小"

    return "大"


# =========================================================
# 颜色
# =========================================================

def get_colours(number):

    number = int(number)

    if number == 0:

        return [
            "red",
            "violet"
        ]

    if number == 5:

        return [
            "green",
            "violet"
        ]

    if number in [
        1,
        3,
        7,
        9
    ]:

        return [
            "green"
        ]

    if number in [
        2,
        4,
        6,
        8
    ]:

        return [
            "red"
        ]

    return []


# =========================================================
# 抓 API
# =========================================================

def collect_data():

    payload = {

        "pageSize":
            10,

        "pageNo":
            1,

        "typeId":
            30,

        "language":
            0
    }


    payload["random"] = (
        generate_random()
    )


    payload["signature"] = (
        generate_signature(
            payload
        )
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
        "API Status:",
        response.status_code
    )


    response.raise_for_status()


    data = response.json()


    if data.get("code") != 0:

        print(
            "❌ API 请求失败"
        )

        print(data)

        return 0


    draw_list = (
        data["data"]["list"]
    )


    new_count = 0


    for item in draw_list:

        issue = (
            item["issueNumber"]
        )

        number = int(
            item["number"]
        )


        # 使用我们自己的颜色规则
        colours = get_colours(
            number
        )


        colour_string = ",".join(
            colours
        )


        size = get_size(
            number
        )


        before = (
            get_total_draws()
        )


        save_draw(

            issue,

            number,

            colour_string,

            size
        )


        after = (
            get_total_draws()
        )


        if after > before:

            new_count += 1


            print(

                "🆕 新开奖:",

                issue,

                "| 数字:",
                number,

                "| 颜色:",
                colour_string,

                "| 大小:",
                size
            )


    return new_count


# =========================================================
# 结算上一轮预测
# =========================================================

def settle_predictions():

    predictions = (
        get_unchecked_predictions()
    )


    if not predictions:

        return


    # 从 database 读取所有开奖
    from database import get_all_draws

    draws = get_all_draws()


    draw_map = {

        str(row[0]):
            row

        for row in draws
    }


    for prediction in predictions:

        issue = str(
            prediction[0]
        )


        if issue not in draw_map:

            continue


        actual = (
            draw_map[issue]
        )


        actual_number = int(
            actual[1]
        )


        actual_size = (
            get_size(
                actual_number
            )
        )


        actual_colours = (
            get_colours(
                actual_number
            )
        )


        predicted_number = int(
            prediction[1]
        )


        predicted_size = (
            prediction[2]
        )


        predicted_colours = json.loads(
            prediction[3]
        )


        # -------------------------
        # 数字
        # -------------------------

        if (
            predicted_number
            ==
            actual_number
        ):

            number_result = "WIN"

        else:

            number_result = "LOSS"


        # -------------------------
        # 大小
        # -------------------------

        if (
            predicted_size
            ==
            actual_size
        ):

            size_result = "WIN"

        else:

            size_result = "LOSS"


        # -------------------------
        # 颜色
        # -------------------------
        #
        # 只要预测颜色和实际颜色
        # 有共同颜色，就算颜色 WIN
        #
        # 例如：
        # 预测 0 = 红+紫
        # 实际 2 = 红
        # → 颜色 WIN
        #
        # -------------------------

        if set(
            predicted_colours
        ).intersection(
            set(actual_colours)
        ):

            colour_result = "WIN"

        else:

            colour_result = "LOSS"


        update_prediction_result(

            issue,

            actual_number,

            actual_size,

            actual_colours,

            number_result,

            size_result,

            colour_result
        )


        print()

        print(
            "📊 结算:",
            issue
        )

        print(
            "数字:",
            predicted_number,
            "→",
            actual_number,
            number_result
        )

        print(
            "大小:",
            predicted_size,
            "→",
            actual_size,
            size_result
        )

        print(
            "颜色:",
            predicted_colours,
            "→",
            actual_colours,
            colour_result
        )


# =========================================================
# MAIN
# =========================================================

def main():

    create_database()


    print()
    print("=" * 60)
    print("LOTTERY AI BOT")
    print("=" * 60)


    print(
        "📡 抓取最新开奖..."
    )


    new_count = (
        collect_data()
    )


    print()

    print(
        "本次新增:",
        new_count
    )


    print(
        "数据库:",
        get_total_draws(),
        "期"
    )


    # 先结算已经开奖的预测
    print()

    print(
        "📊 检查上一轮预测..."
    )

    settle_predictions()


    # 再生成下一期预测
    print()

    print(
        "🤖 生成下一期预测..."
    )

    run_prediction()


    print()

    print("=" * 60)

    print(
        "✅ 本次任务完成"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()
