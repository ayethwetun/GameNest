from flask import Blueprint, render_template, request, jsonify, redirect, session, url_for, flash
import mysql.connector
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from .models import User, Customer, Cart
from ._init_ import db

auth = Blueprint('auth', __name__) # auth can be changed

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Authenticating the user
        email = request.form.get('email')
        password = request.form.get('password')
        # check database for user with the email
        user = User.query.filter_by(email=email).first()
        if user: # if found user with the email, check the password
            if check_password_hash(user.password, password): #if correct
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else: 
                flash('Incorrect password, try again.', category='error')

        else:
            flash('Email does not exist.', category='error')
    return render_template("login.html", boolean=True)

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('views.home'))

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('firstName')
        password = request.form.get('password1')
        dob = request.form.get('dob')
        account_balance = 0.0

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater or equal to 4 characters.', category='error')
        elif dob is None:
            flash('Please enter a valid date of birth.', category='error')
        elif len(password) < 5: 
          flash('Password must be greater or equal to 5 characters.', category='error')
        elif password is None:
          flash('Please enter your password.', category='error')
        else:
            #create user instance
            new_user = User(email=email, password=generate_password_hash(password, method='pbkdf2:sha256'))

            #add user instance to the session
            db.session.add(new_user)
            db.session.commit()
            #create a new cart for user
            new_cart = Cart(user_id=new_user.id)
            db.session.add(new_cart)
            db.session.commit()
            # Create Customer instance linked to the new User
            customer = Customer(name=name, dob=dob, account_balance=account_balance, user_id=new_user.id, email=email)
            #add customer instance to the session
            db.session.add(customer)
            db.session.commit()
            #redirect to the login page
            flash('Account created successfully', category='success')
            return redirect(url_for('auth.login'))

    return render_template("sign_up.html")
