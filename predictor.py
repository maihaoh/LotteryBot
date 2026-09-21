import sqlite3
from collections import Counter

# ============================================================
# Lottery Predictor
# Database: lottery.db
# Table: draws
# ============================================================

DB_FILE = "lottery.db"
RECENT_LIMIT = 50


# ============================================================
# Database
# ============================================================

def get_connection():
    return sqlite3.connect(DB_FILE)


def load_draws():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT issueNumber, number, colour, size
        FROM draws
        WHERE CAST(number AS INTEGER) BETWEEN 0 AND 9
        ORDER BY issueNumber ASC
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows


# ============================================================
# Basic statistics
# ============================================================

def percentage(count, total):
    if total == 0:
        return 0

    return count / total * 100


def count_numbers(rows):
    return Counter(int(row[1]) for row in rows)


def count_sizes(rows):
    return Counter(row[3] for row in rows)


def count_colours(rows):
    """
    颜色可能出现：
    red
    green
    red,violet
    green,violet

    如果包含 violet，则同时统计 violet。
    """

    counter = Counter()

    for row in rows:
        colour = str(row[2]).lower()

        for c in colour.split(","):
            c = c.strip()

            if c:
                counter[c] += 1

    return counter


# ============================================================
# Recent trend
# ============================================================

def get_recent(rows, limit=RECENT_LIMIT):
    return rows[-limit:]


def get_current_streak(rows, index):
    """
    从最新一期开始计算连续相同结果。
    """

    if not rows:
        return None, 0

    latest_value = rows[-1][index]
    streak = 0

    for row in reversed(rows):
        if row[index] == latest_value:
            streak += 1
        else:
            break

    return latest_value, streak


# ============================================================
# Number prediction
# ============================================================

def calculate_number_scores(rows):
    """
    综合评分：

    全历史频率 60%
    最近50期频率 40%
    """

    all_counter = count_numbers(rows)
    recent_rows = get_recent(rows)
    recent_counter = count_numbers(recent_rows)

    total_all = len(rows)
    total_recent = len(recent_rows)

    scores = {}

    for number in range(10):

        all_rate = percentage(
            all_counter[number],
            total_all
        )

        recent_rate = percentage(
            recent_counter[number],
            total_recent
        )

        score = (
            all_rate * 0.60
            +
            recent_rate * 0.40
        )

        scores[number] = {
            "score": score,
            "all_rate": all_rate,
            "recent_rate": recent_rate,
            "all_count": all_counter[number],
            "recent_count": recent_counter[number]
        }

    return scores


# ============================================================
# Hot / Cold numbers
# ============================================================

def get_hot_cold(rows):

    recent_rows = get_recent(rows)

    counter = count_numbers(recent_rows)

    hot = sorted(
        range(10),
        key=lambda n: counter[n],
        reverse=True
    )

    cold = sorted(
        range(10),
        key=lambda n: counter[n]
    )

    return hot, cold, counter


# ============================================================
# Size prediction
# ============================================================

def predict_size(rows):

    all_counter = count_sizes(rows)
    recent_counter = count_sizes(get_recent(rows))

    total_all = len(rows)
    total_recent = len(get_recent(rows))

    scores = {}

    for size in ["大", "小"]:

        all_rate = percentage(
            all_counter[size],
            total_all
        )

        recent_rate = percentage(
            recent_counter[size],
            total_recent
        )

        score = (
            all_rate * 0.60
            +
            recent_rate * 0.40
        )

        scores[size] = {
            "score": score,
            "all_rate": all_rate,
            "recent_rate": recent_rate
        }

    prediction = max(
        scores,
        key=lambda x: scores[x]["score"]
    )

    return prediction, scores


# ============================================================
# Colour prediction
# ============================================================

def predict_colour(rows):

    all_counter = count_colours(rows)
    recent_counter = count_colours(
        get_recent(rows)
    )

    total_all = len(rows)
    total_recent = len(get_recent(rows))

    scores = {}

    for colour in ["red", "green", "violet"]:

        all_rate = percentage(
            all_counter[colour],
            total_all
        )

        recent_rate = percentage(
            recent_counter[colour],
            total_recent
        )

        score = (
            all_rate * 0.60
            +
            recent_rate * 0.40
        )

        scores[colour] = {
            "score": score,
            "all_rate": all_rate,
            "recent_rate": recent_rate
        }

    prediction = max(
        scores,
        key=lambda x: scores[x]["score"]
    )

    return prediction, scores


# ============================================================
# Display helpers
# ============================================================

def print_number_analysis(rows):

    scores = calculate_number_scores(rows)

    ranking = sorted(
        scores.keys(),
        key=lambda n: scores[n]["score"],
        reverse=True
    )

    print()
    print("==================================================")
    print("数字综合评分")
    print("==================================================")

    print(
        "数字 | 综合 | 全历史 | 最近50期 | 全历史次数 | 最近次数"
    )

    print("-" * 65)

    for number in ranking:

        data = scores[number]

        print(
            f"{number:^4} | "
            f"{data['score']:>5.2f}% | "
            f"{data['all_rate']:>6.2f}% | "
            f"{data['recent_rate']:>8.2f}% | "
            f"{data['all_count']:>9} | "
            f"{data['recent_count']:>8}"
        )

    print()

    print("Top 3 数字：")

    for i, number in enumerate(ranking[:3], 1):

        data = scores[number]

        print(
            f"{i}. {number} "
            f"(综合 {data['score']:.2f}%)"
        )

    return ranking


def print_size_analysis(rows):

    prediction, scores = predict_size(rows)

    print()
    print("==================================================")
    print("大小分析")
    print("==================================================")

    for size in ["大", "小"]:

        data = scores[size]

        print(
            f"{size}: "
            f"综合 {data['score']:.2f}% | "
            f"历史 {data['all_rate']:.2f}% | "
            f"最近50期 {data['recent_rate']:.2f}%"
        )

    latest, streak = get_current_streak(rows, 3)

    print()
    print(
        f"当前连续：{latest} × {streak} 期"
    )

    print(
        f"下一期统计倾向：{prediction}"
    )

    return prediction


def print_colour_analysis(rows):

    prediction, scores = predict_colour(rows)

    print()
    print("==================================================")
    print("颜色分析")
    print("==================================================")

    for colour in ["red", "green", "violet"]:

        data = scores[colour]

        print(
            f"{colour:<6}: "
            f"综合 {data['score']:.2f}% | "
            f"历史 {data['all_rate']:.2f}% | "
            f"最近50期 {data['recent_rate']:.2f}%"
        )

    latest, streak = get_current_streak(rows, 2)

    print()
    print(
        f"当前颜色连续：{latest} × {streak} 期"
    )

    print(
        f"下一期统计倾向：{prediction}"
    )

    return prediction


# ============================================================
# Hot / Cold analysis
# ============================================================

def print_hot_cold(rows):

    hot, cold, counter = get_hot_cold(rows)

    print()
    print("==================================================")
    print("冷热号分析（最近50期）")
    print("==================================================")

    print(
        "🔥 热号：",
        " ".join(
            f"{n}({counter[n]})"
            for n in hot[:3]
        )
    )

    print(
        "❄️ 冷号：",
        " ".join(
            f"{n}({counter[n]})"
            for n in cold[:3]
        )
    )


# ============================================================
# Recent history
# ============================================================

def print_recent_history(rows):

    print()
    print("==================================================")
    print("最近开奖结果")
    print("==================================================")

    for row in reversed(rows[-10:]):

        issue, number, colour, size = row

        print(
            f"{issue} | "
            f"{number} | "
            f"{colour} | "
            f"{size}"
        )


# ============================================================
# Main prediction
# ============================================================

def main():

    rows = load_draws()

    if not rows:
        print("数据库没有有效开奖数据。")
        return

    print()
    print("==================================================")
    print("LOTTERY AI PREDICTOR")
    print("==================================================")

    print(f"数据库：{DB_FILE}")
    print(f"有效开奖数量：{len(rows)}")

    latest_issue = rows[-1][0]

    try:
        next_issue = str(int(latest_issue) + 1)
    except ValueError:
        next_issue = "下一期"

    print(f"最新期号：{latest_issue}")
    print(f"预测期号：{next_issue}")

    # --------------------------------------------------------
    # Number
    # --------------------------------------------------------

    ranking = print_number_analysis(rows)

    # --------------------------------------------------------
    # Size
    # --------------------------------------------------------

    size_prediction = print_size_analysis(rows)

    # --------------------------------------------------------
    # Colour
    # --------------------------------------------------------

    colour_prediction = print_colour_analysis(rows)

    # --------------------------------------------------------
    # Hot / Cold
    # --------------------------------------------------------

    print_hot_cold(rows)

    # --------------------------------------------------------
    # Recent history
    # --------------------------------------------------------

    print_recent_history(rows)

    # --------------------------------------------------------
    # Final prediction
    # --------------------------------------------------------

    top1 = ranking[0]
    top2 = ranking[1]
    top3 = ranking[2]

    top1_score = calculate_number_scores(rows)[top1]["score"]

    print()
    print("==================================================")
    print("🎯 下一期统计预测")
    print("==================================================")

    print(f"预测期号   : {next_issue}")
    print()
    print(f"数字 Top 1 : {top1}")
    print(f"数字 Top 2 : {top2}")
    print(f"数字 Top 3 : {top3}")
    print()
    print(f"大小       : {size_prediction}")
    print(f"颜色       : {colour_prediction}")
    print()
    print(f"数字综合分 : {top1_score:.2f}%")

    print()
    print("==================================================")
    print("⚠️ 注意")
    print("==================================================")
    print("以上是基于历史数据的统计模型，不代表开奖结果。")
    print("彩票开奖结果具有随机性，不能保证预测准确。")
    print("==================================================")


if __name__ == "__main__":
    main()