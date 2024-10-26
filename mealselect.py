import pandas as pd
import itertools

# UTF-8エンコーディングで読み込む
data_path = "./database/caloriecalculate.csv"
df = pd.read_csv(data_path, encoding='utf-8')

# 数値変換
df["kcal"] = pd.to_numeric(df["kcal"], errors='coerce')
df["protein"] = pd.to_numeric(df["protein"], errors='coerce')
df["fat"] = pd.to_numeric(df["fat"], errors='coerce')
df["carbo"] = pd.to_numeric(df["carbo"], errors='coerce')

# 欠損値を 0 に置き換え
df = df.fillna(0)

# ユーザーの1日あたりの目標摂取量

# 栄養バランスを計算する関数
def calculate_score(selected,target_kcal,target_protein,target_fat,target_carbo):
    total_kcal = selected["kcal"].sum()
    total_protein = selected["protein"].sum()
    total_fat = selected["fat"].sum()
    total_carbo = selected["carbo"].sum()

    score = (
        abs(target_kcal - total_kcal) +
        abs(target_protein - total_protein) +
        abs(target_fat - total_fat) +
        abs(target_carbo - total_carbo)
    )
    return score

# 1〜5品の組み合わせを生成
def generate_meal_plan(df):
    best_score = float('inf')
    best_plan = None

    for r in range(1, 6):
        for combo in itertools.combinations(df.index, r):
            selected = df.loc[list(combo)]
            score = calculate_score(selected)

            if score < best_score:
                best_score = score
                best_plan = selected

    return best_plan

# 最適な献立を生成
optimal_plan = generate_meal_plan(df)

# 結果を表示
print("最適な献立:")
print(optimal_plan[["dish", "kcal", "protein", "fat", "carbo"]])
print(f"合計カロリー: {optimal_plan['kcal'].sum()} kcal")
print(f"合計タンパク質: {optimal_plan['protein'].sum()} g")
print(f"合計脂質: {optimal_plan['fat'].sum()} g")
print(f"合計炭水化物: {optimal_plan['carbo'].sum()} g")
