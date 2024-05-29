from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import mysql.connector
from os import path
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
DB_NAME = "testInventory"

def create_app(): 
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'RANDOM TOP SECRET'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://root:chickenbox@localhost/{DB_NAME}'
    db.init_app(app)

    migrate = Migrate(app, db)

    from website.views import views
    from website.auth import auth

    app.config['LOGIN_VIEW'] = 'auth.login' 
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User, Game

    with app.app_context():
        db.create_all()

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    return app

def create_database(app):
    cnx = mysql.connector.connect
    if not path.exists('website/' + DB_NAME):
        db.create_all(app=app)
        print('Created Database!')