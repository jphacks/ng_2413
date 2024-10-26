from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from config import Config
from ng_2413.mealselect import app_mealselect



app = Flask(__name__)
app.register_blueprint(app_mealselect)

app.config.from_object(Config)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # ログインしていない場合にリダイレクトするページ


# データ ベースモデルのインポート
from models import User


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

        # 結果をJSONで返す
        return jsonify({
            'bmr': bmr,
            'tdee': tdee,
            'calorie_needs': calorie_needs,
            'protein_needs': protein_needs,
            'fat_needs': fat_needs,
            'carbon_needs': carbon_needs
        })
    return render_template('index.html')




# 以下ログイン関連のページ


# ログイン時にユーザ情報を取得
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ユーザ登録ルート
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# ログインルート
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html')

# ダッシュボードルート（ログイン必須）
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=current_user.username)

# ログアウトルート
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))














if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
