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

# 栄養バランスを計算する関数
def calculate_percentage_deviation(selected, target_kcal, target_protein, target_fat, target_carbo):
    total_kcal = selected["kcal"].sum()
    total_protein = selected["protein"].sum()
    total_fat = selected["fat"].sum()
    total_carbo = selected["carbo"].sum()

    # 各栄養素の目標からのずれを計算
    kcal_deviation = abs(target_kcal - total_kcal) / target_kcal if target_kcal > 0 else 0
    protein_deviation = abs(target_protein - total_protein) / target_protein if target_protein > 0 else 0
    fat_deviation = abs(target_fat - total_fat) / target_fat if target_fat > 0 else 0
    carbo_deviation = abs(target_carbo - total_carbo) / target_carbo if target_carbo > 0 else 0

    # 合計スコアを計算
    total_deviation = kcal_deviation + protein_deviation + fat_deviation + carbo_deviation
    return total_deviation

# 食事の種類ごとに献立を生成する関数
def generate_meal_plan(df, target_kcal, target_protein, target_fat, target_carbo):
    meal_types = ['朝食', '昼食', '夕食']
    meal_plans = {}
    selected_mains = []  # 選択したメイン料理を保持
    selected_subs = []   # 選択した副菜を保持

    for meal in meal_types:
        if meal == '朝食':
            # 朝食のためのフィルタリング
            main = df[(df['side'] == 0) & (df['morn'] == 1)]
            sub = df[(df['side'] == 1) & (df['morn'] == 1)]
            staple = df[(df['side'] == 2) & (df['morn'] == 1)]  # 主食のフィルタリング
        else:
            # 昼食・夕食のためのフィルタリング
            main = df[(df['side'] == 0) & (df['morn'].isin([1, 0]))]
            sub = df[(df['side'] == 1) & (df['morn'].isin([1, 0]))]
            staple = df[(df['side'] == 2) & (df['morn'].isin([1, 0]))]  # 主食のフィルタリング

        best_deviation = float('inf')
        best_plan = None

        # 主食を必ず選択する
        if not staple.empty:
            selected_staple = staple.sample(n=1)  # 主食をランダムに選択

            # 残っているメイン料理の中で最も良いものを選択する
            remaining_mains = main[~main['dish'].isin(selected_mains)]
            best_main_score = float('inf')
            best_main = None
            
            if not remaining_mains.empty:
                for r_main in range(1, 2):  # メインは1品
                    for combo_main in itertools.combinations(remaining_mains.index, r_main):
                        selected_main = remaining_mains.loc[list(combo_main)]
                        
                        # 副菜は1〜2品（かぶらないように選ぶ）
                        remaining_subs = sub[~sub['dish'].isin(selected_subs)]  # 選択済みの副菜を除外
                        for r_sub in range(1, 3):
                            if not remaining_subs.empty:  # 副菜が空でない場合
                                for combo_sub in itertools.combinations(remaining_subs.index, r_sub):
                                    selected_sub = remaining_subs.loc[list(combo_sub)]
                                    complete_selected = pd.concat([selected_main, selected_staple, selected_sub])

                                    deviation = calculate_percentage_deviation(complete_selected, target_kcal, target_protein, target_fat, target_carbo)

                                    if deviation < best_main_score:
                                        best_main_score = deviation
                                        best_main = selected_main
                                        best_sub = selected_sub

            if best_main is not None:
                selected_mains.append(best_main['dish'].values[0])  # 選択したメイン料理を記録
                selected_subs.extend(best_sub['dish'].values)  # 選択した副菜を記録
                best_plan = pd.concat([best_main, selected_staple, best_sub])

        meal_plans[meal] = best_plan

    return meal_plans

# ユーザーの1日あたりの目標摂取量
# 後でapp.pyにつなぎこむ必要があり
target_kcal = 2000
target_protein = 100
target_fat = 55
target_carbo = 272

# 最適な献立を生成
optimal_plan = generate_meal_plan(df, target_kcal, target_protein, target_fat, target_carbo)

# 結果を表示
total_kcal = 0
total_protein = 0
total_fat = 0
total_carbo = 0

for meal, plan in optimal_plan.items():
    if plan is not None and not plan.empty:
        print(f"{meal}の最適な献立:")
        print(plan[["dish", "kcal", "protein", "fat", "carbo"]])
        total_kcal += plan['kcal'].sum()
        total_protein += plan['protein'].sum()
        total_fat += plan['fat'].sum()
        total_carbo += plan['carbo'].sum()
        print(f"合計カロリー: {plan['kcal'].sum()} kcal")
        print(f"合計タンパク質: {plan['protein'].sum()} g")
        print(f"合計脂質: {plan['fat'].sum()} g")
        print(f"合計炭水化物: {plan['carbo'].sum()} g")
    else:
        print(f"{meal}の献立は見つかりませんでした。")
    print("----------")

# 1日の合計スコアを計算
total_score = calculate_percentage_deviation(pd.DataFrame({
    "kcal": [total_kcal],
    "protein": [total_protein],
    "fat": [total_fat],
    "carbo": [total_carbo]
}), target_kcal, target_protein, target_fat, target_carbo)

# 1日の合計を表示
print("1日の合計:")
print(f"合計カロリー: {total_kcal} kcal")
print(f"合計タンパク質: {total_protein} g")
print(f"合計脂質: {total_fat} g")
print(f"合計炭水化物: {total_carbo} g")
print(f"1日の合計スコア: {total_score}")
