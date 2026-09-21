import json
from datetime import datetime

from database import (
    get_all_draws,
    save_prediction,
    get_prediction_stats,
    get_latest_checked_prediction
)


OUTPUT_FILE = "prediction.json"


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
                /
                len(recent)
                *
                100
            )

            window_rates.append(
                rate
            )


        # 如果数据库还没有足够数据
        if not window_rates:

            recent = rows

            count = sum(
                1
                for row in recent
                if int(row[1]) == number
            )

            recent_average = (
                count
                /
                len(recent)
                *
                100
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
                /
                sum(weights)
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

            "recent_rate":
                recent_average,

            "all_count":
                all_count
        }


    return scores


# =========================================================
# 预测
# =========================================================

def generate_prediction(rows):

    scores = calculate_scores(
        rows
    )


    ranking = sorted(
        range(10),
        key=lambda n:
            scores[n]["score"],
        reverse=True
    )


    top1 = ranking[0]
    top2 = ranking[1]
    top3 = ranking[2]


    predicted_size = get_size(
        top1
    )


    predicted_colours = get_colours(
        top1
    )


    return (
        ranking,
        predicted_size,
        predicted_colours,
        scores
    )


# =========================================================
# 颜色文字
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
# 保存预测
# =========================================================

def main():

    rows = get_all_draws()


    if not rows:

        print(
            "❌ Database 没有开奖数据"
        )

        return


    (
        ranking,
        predicted_size,
        predicted_colours,
        scores
    ) = generate_prediction(
        rows
    )


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


    # 保存给 database
    save_prediction(
        next_issue,
        top1,
        predicted_size,
        predicted_colours
    )


    # 胜率
    stats = get_prediction_stats()


    # 上一期结果
    previous = (
        get_latest_checked_prediction()
    )


    previous_data = None


    if previous:

        previous_data = {

            "issue":
                previous[0],

            "predicted_number":
                previous[1],

            "predicted_size":
                previous[2],

            "predicted_colours":
                json.loads(
                    previous[3]
                ),

            "actual_number":
                previous[4],

            "actual_size":
                previous[5],

            "actual_colours":
                json.loads(
                    previous[6]
                ),

            "number_result":
                previous[7],

            "size_result":
                previous[8],

            "colour_result":
                previous[9]
        }


    # JSON
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


    print()
    print("=" * 60)
    print("🎯 LOTTERY AI")
    print("=" * 60)

    print(
        "数据库:",
        len(rows),
        "期"
    )

    print(
        "最新:",
        latest_issue,
        "→",
        latest_number
    )

    print()

    print(
        "下一期:",
        next_issue
    )

    print(
        "Top 1:",
        top1,
        f"({scores[top1]['score']:.2f}%)"
    )

    print(
        "Top 2:",
        top2,
        f"({scores[top2]['score']:.2f}%)"
    )

    print(
        "Top 3:",
        top3,
        f"({scores[top3]['score']:.2f}%)"
    )

    print()

    print(
        "大小:",
        predicted_size
    )

    print(
        "颜色:",
        ", ".join(
            colour_name(
                predicted_colours
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

    print("=" * 60)


if __name__ == "__main__":
    main()
