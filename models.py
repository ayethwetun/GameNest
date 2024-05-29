from ._init_ import db 
from flask_login import UserMixin
from sqlalchemy.sql import func, insert
from datetime import datetime
# Association table, games user owns, many to many relationship
User_games = db.Table('user_games',
    db.Column('userid', db.Integer, db.ForeignKey('user.id')),
    db.Column('gameid', db.Integer, db.ForeignKey('game.id'))
)

Cart_Games = db.Table('cart_games',
    db.Column('cartid', db.Integer, db.ForeignKey('cart.id')),
    db.Column('gameid', db.Integer, db.ForeignKey('game.id'))
)

game_catalog_games = db.Table('game_catalog_games',
    db.Column('game_id', db.Integer, db.ForeignKey('game.id'), primary_key=True),
    db.Column('game_catalog_id', db.Integer, db.ForeignKey('game_catalog.id'), primary_key=True)
)

orders_games = db.Table('orders_games',
    db.Column('order_id', db.Integer, db.ForeignKey('orders.id'), primary_key=True),
    db.Column('game_id', db.Integer, db.ForeignKey('game.id'), primary_key=True)
)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    games = db.relationship('Game', secondary=Cart_Games, backref=db.backref('game_carts', lazy=True))

    @property
    def subtotal(self):
        return sum(game.price for game in self.games) or 0.0


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150))
    data = db.Column(db.String(10000))
    categories = db.relationship('Game_catalog', secondary=game_catalog_games, backref=db.backref('game', lazy=True))
    developer_id = db.Column(db.Integer, db.ForeignKey('developer.id'))
    developer = db.relationship('Developer', backref='developer_games')
    price = db.Column(db.Float)
    image = db.Column(db.String(500)) #contains path to image file
    description = db.Column(db.String(500))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    games = db.relationship('Game', secondary=User_games, backref=db.backref('game_user', lazy=True))
    customer = db.relationship('Customer', backref='customer_user', uselist=False, foreign_keys='Customer.user_id')
    cart = db.relationship('Cart', backref='user', uselist=False)


class Game_catalog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(150), unique=True)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    dob = db.Column(db.String(150), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    address = db.Column(db.String(150))
    email = db.Column(db.String(150), db.ForeignKey('user.email'), nullable=False)
    credit_card = db.Column(db.String(16))
    account_balance = db.Column(db.Float)
    user = db.relationship('User', backref=db.backref('user_customer', uselist=False), foreign_keys=[user_id])

class Developer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    devName = db.Column(db.String(150), unique=True)
    donation = db.Column(db.String(500)) #links like patreon, paypal, etc
    email = db.Column(db.String(150), db.ForeignKey('user.email'), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('user_developer', uselist=False), foreign_keys=[user_id])
    games = db.relationship('Game', backref='game_developer', lazy=True)
    #uploads = db.relationship('Game', backref='developer', lazy=True) probably not needed

class Orders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'))
    cart = db.relationship('Cart', backref='orders')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='orders')
    date_purchased = db.Column(db.DateTime, default=datetime.utcnow)
    subtotal = db.Column(db.Float)
    status = db.Column(db.Boolean, default=False) #if they have buyed the game or not
    games = db.relationship('Game', secondary=orders_games, backref='orders')
    games = db.relationship('Game', secondary=orders_games, backref='orders')


