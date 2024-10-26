import pandas as pd
import itertools
from flask import Blueprint, render_template, g, request, Flask, jsonify, session

app_mealselect = Blueprint('app_mealselect', __name__)

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

# グローバル変数としてoptimal_plan_cacheを定義
optimal_plan = None

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
    selected_staples = []  # 選択した主食を保持

    for meal in meal_types:
        if meal == '朝食':
            portion_factor = (1/4, 1/4, 1/4)  # 朝食は1/4
        elif meal == '昼食':
            portion_factor = (3/8, 3/8, 3/8)  # 昼食は3/8
        else:
            portion_factor = (3/8, 3/8, 3/8)  # 夕食は3/8

        # 目標摂取量を計算
        meal_target_kcal = target_kcal * portion_factor[0]
        meal_target_protein = target_protein * portion_factor[1]
        meal_target_fat = target_fat * portion_factor[2]
        meal_target_carbo = target_carbo * portion_factor[2]

        # 各食事のフィルタリング
        main = df[(df['side'] == 0) & (df['morn'] == (1 if meal == '朝食' else 0))]
        sub = df[(df['side'] == 1) & (df['morn'] == (1 if meal == '朝食' else 0))]
        staple = df[(df['side'] == 2) & (df['morn'] == (1 if meal == '朝食' else 0))]

        best_deviation = float('inf')
        best_plan = None

        # 主食を必ず選択する
        if not staple.empty:
            # 残っている主食の中から選択
            remaining_staples = staple[~staple['dish'].isin(selected_staples)]
            if not remaining_staples.empty:
                selected_staple = remaining_staples.sample(n=1)  # 主食をランダムに選択
                selected_staples.append(selected_staple['dish'].values[0])  # 選択した主食を記録

                # 残っているメイン料理の中で最も良いものを選択する
                remaining_mains = main[~main['dish'].isin(selected_mains)]
                best_main_score = float('inf')
                best_main = None
                
                if not remaining_mains.empty:
                    for r_main in range(1, 2):  # メインは1品
                        for combo_main in itertools.combinations(remaining_mains.index, r_main):
                            selected_main = remaining_mains.loc[list(combo_main)]
                            
                            # 副菜は1〜2品（かぶらないように選ぶ）
                            remaining_subs = sub[~sub['dish'].isin(selected_subs)]
                            for r_sub in range(1, 3):
                                if not remaining_subs.empty:  # 副菜が空でない場合
                                    for combo_sub in itertools.combinations(remaining_subs.index, r_sub):
                                        selected_sub = remaining_subs.loc[list(combo_sub)]
                                        complete_selected = pd.concat([selected_main, selected_staple, selected_sub])

                                        deviation = calculate_percentage_deviation(complete_selected, meal_target_kcal, meal_target_protein, meal_target_fat, meal_target_carbo)

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

@app_mealselect.route('/form/recipe', methods=['GET'])
def recipe_list():
    # UTF-8エンコーディングで読み込む
    global optimal_plan
    if optimal_plan is None:
        # データの読み込みと最適な献立の生成
        data_path = "./database/caloriecalculate.csv"
        df = pd.read_csv(data_path, encoding='utf-8')

        optimal_plan = generate_meal_plan(df, session.get('calorie_needs', None),
            session.get('protein_needs', None),
            session.get('fat_needs', None),
            session.get('carbon_needs', None))
        
        print(session.get('calorie_needs', None))
    
    # メニュー一覧をHTMLで表示
    return render_template('recipe.html', menus=optimal_plan)


@app_mealselect.route('/form/recipe/breakfast', methods=['GET'])
def recipe_breakfast():
    global optimal_plan
    if optimal_plan is None:
        # データの読み込みと最適な献立の生成
        data_path = "./database/caloriecalculate.csv"
        df = pd.read_csv(data_path, encoding='utf-8')

        optimal_plan = generate_meal_plan(df, 2000, 100, 55, 272)
        # 朝食の献立を生成
        optimal_plan = generate_meal_plan(df, 2000, 100, 55, 272)
    breakfast_plan = optimal_plan.get('朝食')

    # HTMLに朝食の詳細（料理名と栄養素）を渡す
    return render_template('breakfast.html', meal_plan=breakfast_plan)

@app_mealselect.route('/form/recipe/lunch', methods=['GET'])
def recipe_lunch():
    global optimal_plan
    if optimal_plan is None:
        # データの読み込みと最適な献立の生成
        data_path = "./database/caloriecalculate.csv"
        df = pd.read_csv(data_path, encoding='utf-8')

        optimal_plan = generate_meal_plan(df, 2000, 100, 55, 272)
        # 朝食の献立を生成
        optimal_plan = generate_meal_plan(df, 2000, 100, 55, 272)
    lunch_plan = optimal_plan.get('昼食')

    # HTMLに昼食の詳細（料理名と栄養素）を渡す
    return render_template('lunch.html', meal_plan=lunch_plan)

@app_mealselect.route('/form/recipe/dinner', methods=['GET'])
def recipe_dinner():
    global optimal_plan
    if optimal_plan is None:
        # データの読み込みと最適な献立の生成
        data_path = "./database/caloriecalculate.csv"
        df = pd.read_csv(data_path, encoding='utf-8')

        optimal_plan = generate_meal_plan(df, 2000, 100, 55, 272)
        # 朝食の献立を生成
        optimal_plan = generate_meal_plan(df, 2000, 100, 55, 272)
    dinner_plan = optimal_plan.get('夕食')

    # HTMLに夕食の詳細（料理名と栄養素）を渡す
    return render_template('dinner.html', meal_plan=dinner_plan)


@app_mealselect.route('/form/recipe/nutrition', methods=['GET'])
def recipe_summary():
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

    # 各献立の栄養素合計を計算
    total_kcal = df['kcal'].sum()
    total_protein = df['protein'].sum()
    total_fat = df['fat'].sum()
    total_carbo = df['carbo'].sum()

    total_nutrition = {
        "total_kcal": total_kcal,
        "total_protein": total_protein,
        "total_fat": total_fat,
        "total_carbo": total_carbo
    }

    # 合計をHTMLに表示
    return render_template('nutrition.html', total=total_nutrition)