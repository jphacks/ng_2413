# config.py
import os

class Config:
    SECRET_KEY = 'your_secret_key'  # セッションのセキュリティキー
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'  # SQLiteを使用
    SQLALCHEMY_TRACK_MODIFICATIONS = False
