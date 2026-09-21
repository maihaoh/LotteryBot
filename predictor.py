import json
from datetime import datetime

from database import (
    get_all_draws,
    save_prediction,
    get_prediction_stats,
    get_latest_checked_prediction
)


OUTPUT_FILE = "prediction.json"
HTML_FILE = "index.html"


WINDOWS = [
    10,
    20,
    50,
    100
]


# =========================================================
# 数字 → 大小
# =========================================================

def get_size(number):

    number = int(number)

    if 0 <= number <= 4:
        return "小"

    return "大"


# =========================================================
# 数字 → 颜色
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

    if number in [1, 3, 7, 9]:
        return [
            "green"
        ]

    if number in [2, 4, 6, 8]:
        return [
            "red"
        ]

    return []


# =========================================================
# 统计数字
# =========================================================

def calculate_scores(rows):

    total = len(rows)

    if total == 0:
        return {}

    scores = {}

    for number in range(10):

        # 全历史
        all_count = sum(
            1
            for row in rows
            if int(row[1]) == number
        )

        all_rate = (
            all_count / total * 100
        )

        # 最近窗口
        window_rates = []

        for window in WINDOWS:

            if len(rows) < window:
                continue

            recent = rows[-window:]

            count = sum(
                1
                for row in recent
                if int(row[1]) == number
            )

            rate = (
                count
                / len(recent)
                * 100
            )

            window_rates.append(rate)

        # 数据不足时使用全部数据
        if not window_rates:

            recent = rows

            count = sum(
                1
                for row in recent
                if int(row[1]) == number
            )

            recent_average = (
                count
                / len(recent)
                * 100
            )

        else:

            # 越新的窗口权重越高
            weights = list(
                range(
                    1,
                    len(window_rates) + 1
                )
            )

            weighted_sum = sum(
                rate * weight
                for rate, weight
                in zip(
                    window_rates,
                    weights
                )
            )

            recent_average = (
                weighted_sum
                / sum(weights)
            )

        # 综合评分
        score = (
            all_rate * 0.35
            +
            recent_average * 0.65
        )

        scores[number] = {

            "score": score,

            "all_rate": all_rate,

            "recent_rate": recent_average,

            "all_count": all_count
        }

    return scores


# =========================================================
# 生成预测
# =========================================================

def generate_prediction(rows):

    scores = calculate_scores(rows)

    ranking = sorted(
        range(10),
        key=lambda n:
            scores[n]["score"],
        reverse=True
    )

    top1 = ranking[0]
    top2 = ranking[1]
    top3 = ranking[2]

    predicted_size = get_size(top1)

    predicted_colours = get_colours(top1)

    return (
        ranking,
        predicted_size,
        predicted_colours,
        scores
    )


# =========================================================
# 颜色显示
# =========================================================

def colour_name(colours):

    mapping = {

        "red":
            "🔴 红色",

        "green":
            "🟢 绿色",

        "violet":
            "🟣 紫色"
    }

    return [
        mapping[c]
        for c in colours
        if c in mapping
    ]


# =========================================================
# 创建网页数据
# =========================================================

def build_web_data():

    rows = get_all_draws()

    if not rows:
        return None

    (
        ranking,
        predicted_size,
        predicted_colours,
        scores
    ) = generate_prediction(rows)

    latest_issue = rows[-1][0]

    latest_number = int(
        rows[-1][1]
    )

    try:

        next_issue = str(
            int(latest_issue) + 1
        )

    except Exception:

        next_issue = "下一期"

    top1 = ranking[0]
    top2 = ranking[1]
    top3 = ranking[2]

    # 保存下一期预测
    save_prediction(
        next_issue,
        top1,
        predicted_size,
        predicted_colours
    )

    # 胜率
    stats = get_prediction_stats()

    # 上一期结果
    previous = get_latest_checked_prediction()

    previous_data = None

    if previous:

        try:

            predicted_colours_previous = json.loads(
                previous[3]
            )

        except Exception:

            predicted_colours_previous = []

        try:

            actual_colours_previous = json.loads(
                previous[6]
            )

        except Exception:

            actual_colours_previous = []

        previous_data = {

            "issue":
                previous[0],

            "predicted_number":
                previous[1],

            "predicted_size":
                previous[2],

            "predicted_colours":
                predicted_colours_previous,

            "actual_number":
                previous[4],

            "actual_size":
                previous[5],

            "actual_colours":
                actual_colours_previous,

            "number_result":
                previous[7],

            "size_result":
                previous[8],

            "colour_result":
                previous[9]
        }

    data = {

        "status":
            "ONLINE",

        "updated_at":
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

        "total_draws":
            len(rows),

        "latest": {

            "issue":
                latest_issue,

            "number":
                latest_number,

            "size":
                get_size(
                    latest_number
                ),

            "colours":
                get_colours(
                    latest_number
                )
        },

        "prediction": {

            "issue":
                next_issue,

            "top1":
                top1,

            "top2":
                top2,

            "top3":
                top3,

            "top1_score":
                round(
                    scores[top1]["score"],
                    2
                ),

            "size":
                predicted_size,

            "colours":
                predicted_colours
        },

        "previous_result":
            previous_data,

        "statistics":
            stats,

        "rules": {

            "size":
                "0-4 小 / 5-9 大",

            "colour":
                "0 红+紫 / 5 绿+紫 / 13579 绿 / 2468 红"
        },

        "disclaimer":
            "统计模型根据历史数据进行分析，开奖结果具有随机性，不能保证预测准确。"
    }

    return data


# =========================================================
# 保存 JSON 备用
# =========================================================

def save_json(data):

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )


# =========================================================
# 直接更新 index.html
# =========================================================

def update_html(data):

    try:

        with open(
            HTML_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            html = file.read()

    except FileNotFoundError:

        print(
            "❌ 找不到 index.html"
        )

        return False

    data_json = json.dumps(
        data,
        ensure_ascii=False,
        separators=(
            ",",
            ":"
        )
    )

    start_marker = (
        "const LOTTERY_DATA = "
    )

    end_marker = (
        ";\n"
    )

    start = html.find(
        start_marker
    )

    if start == -1:

        print(
            "❌ index.html 找不到 "
            "'const LOTTERY_DATA = '"
        )

        return False

    value_start = (
        start
        +
        len(start_marker)
    )

    end = html.find(
        end_marker,
        value_start
    )

    if end == -1:

        print(
            "❌ index.html 数据结束位置找不到"
        )

        return False

    new_html = (
        html[:value_start]
        +
        data_json
        +
        html[end:]
    )

    with open(
        HTML_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            new_html
        )

    print(
        "✅ index.html 已更新"
    )

    return True


# =========================================================
# MAIN
# =========================================================

def main():

    data = build_web_data()

    if not data:

        print(
            "❌ Database 没有开奖数据"
        )

        return

    # JSON 继续保留作为备用
    save_json(data)

    # 直接把最新数据写入网页
    update_html(data)

    latest = data["latest"]

    prediction = data["prediction"]

    stats = data["statistics"]

    print()
    print("=" * 60)
    print("🎯 LOTTERY AI")
    print("=" * 60)

    print(
        "数据库:",
        data["total_draws"],
        "期"
    )

    print(
        "最新:",
        latest["issue"],
        "→",
        latest["number"]
    )

    print()

    print(
        "下一期:",
        prediction["issue"]
    )

    print(
        "Top 1:",
        prediction["top1"],
        f"({prediction['top1_score']:.2f}%)"
    )

    print(
        "Top 2:",
        prediction["top2"]
    )

    print(
        "Top 3:",
        prediction["top3"]
    )

    print()

    print(
        "大小:",
        prediction["size"]
    )

    print(
        "颜色:",
        ", ".join(
            colour_name(
                prediction["colours"]
            )
        )
    )

    print()

    print("📊 胜率")

    print(
        "数字:",
        stats["number"]["rate"],
        "%"
    )

    print(
        "颜色:",
        stats["colour"]["rate"],
        "%"
    )

    print(
        "大小:",
        stats["size"]["rate"],
        "%"
    )

    print()

    print(
        "🌐 index.html 已直接写入最新数据"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()
