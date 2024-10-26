from flask import Flask, render_template, request

app = Flask(__name__)

# BMR計算関数
def calculate_bmr(weight, height, age, gender):
    if gender == 'male':
        bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    elif gender == 'female':
        bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
    return bmr

# TDEE計算関数
def calculate_tdee(bmr, activity_level):
    return bmr * activity_level

# 筋肉増加に必要なカロリーを計算
def calculate_calorie_needs(tdee, goal='muscle_gain', surplus=300):
    if goal == 'muscle_gain':
        return tdee + surplus
    elif goal == 'maintain':
        return tdee
    elif goal == 'fat_loss':
        return tdee - surplus
    else:
        return tdee
    
    # 筋肉増加に必要なタンパク質
def calculate_protein_needs(weight):
    protein = 2.0 * weight
    return protein

def calculate_fat_needs(tdee,goal):
    fat = calculate_calorie_needs(tdee,goal) * (25/100)/9
    return fat

def calculate_carbon_needs(tdee,goal,weight):
    carbon = (calculate_calorie_needs(tdee,goal)-calculate_protein_needs(weight)*4-calculate_fat_needs(tdee,goal)*9)/4
    return carbon

@app.route('/', methods=['GET'])
def start():
    return render_template('start.html')

@app.route('/form', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        weight = float(request.form['weight'])
        height = float(request.form['height'])
        age = int(request.form['age'])
        gender = request.form['gender']
        activity_level = float(request.form['activity_level'])
        goal = request.form['goal']

        # BMRの計算
        bmr = calculate_bmr(weight, height, age, gender)
        # TDEEの計算
        tdee = calculate_tdee(bmr, activity_level)
        # 筋肉増加に必要な1日のカロリーの計算
        calorie_needs = calculate_calorie_needs(tdee, goal)
        # 筋肉増加に必要なタンパク質の計算
        protein_needs = calculate_protein_needs(weight)
        # 筋肉増加に必要な脂質の計算
        fat_needs = calculate_fat_needs(tdee,goal)
        # 筋肉増加に必要な炭水化物の計算
        carbon_needs = calculate_carbon_needs(tdee,goal,weight)

        return render_template('result.html', bmr=bmr, tdee=tdee, calorie_needs=calorie_needs,protein_needs=protein_needs,fat_needs=fat_needs,carbon_needs=carbon_needs)

    return render_template('index.html')



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)