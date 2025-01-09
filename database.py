from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()  # 不绑定 app，仅定义 SQLAlchemy 实例