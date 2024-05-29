from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from .models import *
from werkzeug.utils import secure_filename
import os
from flask_login import login_required, current_user
from ._init_ import db

views = Blueprint('views', __name__)  # views can be changed
UPLOAD_IMG = "website/static/upload_image/"  # Path to the uploaded images
UPLOAD_FILES = "website/static/upload_file/"  # Path to the uploaded files


@views.route('/', defaults={'game_title': None})
@views.route('/<game_title>')
def home(game_title):
    # If the user is logged in, redirect to dashboard
    #if current_user.is_authenticated:
    #return redirect(url_for('views.dashboard'))

    if game_title:
        return redirect(url_for('views.gameinfo', game_title=game_title))

    # Fetch recently added games (assuming you're sorting by game ID)
    recently_added_games = Game.query.order_by(Game.id.desc()).limit(6).all()

    # Categorize games by genres
    all_games = Game.query.all()
    games_by_genre = {}
    for game in all_games:
        for genre in game.categories:
            if genre not in games_by_genre:
                games_by_genre[genre] = []
            games_by_genre[genre].append(game)

    return render_template("home.html",
                           recently_added_games=recently_added_games,
                           games_by_genre=games_by_genre,
                           user=current_user)


@views.route(
    '/gameinfo/<game_title>'
)  # this is a game info page that would show, donation etc. Will be Dynamically changing
def gameinfo(game_title):
    # Query the game based on the provided title
    game = Game.query.filter_by(title=game_title).first()

    # If the game is not found, handle the error
    if game is None:
        return render_template('error.html', message="Game not found")

    # Render the gameinfo.html template with the game information
    return render_template('gameinfo.html', game=game)


@views.route(
    '/dashboard', defaults={'game_title': None}
)  #Similar to Home but replace login and register with redirect to orders and logout
@views.route('/dashboard/<game_title>')
@login_required  # user needs to be login, otherwise redirect to login page
def dashboard(game_title):
    if game_title:
        return redirect(url_for('views.gameinfo', game_title=game_title))

    # Fetch recently added games (assuming you're sorting by game ID)
    recently_added_games = Game.query.order_by(Game.id.desc()).limit(6).all()

    # Categorize games by genres
    all_games = Game.query.all()
    games_by_genre = {}
    for game in all_games:
        for genre in game.categories:
            if genre not in games_by_genre:
                games_by_genre[genre] = []
                games_by_genre[genre].append(game)

    return render_template("home.html",
                           recently_added_games=recently_added_games,
                           games_by_genre=games_by_genre,
                           user=current_user)


@views.route(
    '/browse'
)  #List every single game, Do not include download here change to add to cart
def browse():
    # Query all games from the database
    games = Game.query.all()
    # Filter out games with None image paths
    games_with_images = [game for game in games if game.image is not None]
    return render_template("browse.html", games=games_with_images)


@login_required  # user needs to be login, otherwise redirect to login page
@views.route('/transaction')  #check each order
def transaction():
    return render_template("transaction.html")


@login_required  # user needs to be login, otherwise redirect to login page
@views.route(
    '/library')  #To download games from, listed similar to how it is in browse
def library():
    return render_template("library.html")


@login_required  # user needs to be login, otherwise redirect to login page
@views.route('/checkout', methods=[
    'GET', 'POST'
])  #fill out user details, payment details, etc and purchase games
def checkout():
    if request.method == 'POST':
        # Extract data from the form
        name = request.form.get('firstName')
        address = request.form.get('address')
        credit_card = request.form.get('creditCard')

        # Update the current user's customer information
        current_user.customer.name = name
        current_user.customer.address = address
        current_user.customer.credit_card = credit_card

        # Check if the current user has a cart
        if current_user.cart is None:
            flash('No games in cart', 'error')

        # Get the games from the user's cart
        games_in_cart = current_user.cart.games

        # Add each game in the cart to user.games
        for game in games_in_cart:
            current_user.games.append(game)

        # Get the games from the user's cart
        games_in_cart = current_user.cart.games

        # Create a new Order instance
        order = Orders(cart_id=current_user.cart.id,
                       user_id=current_user.id,
                       date_purchased=datetime.now(),
                       subtotal=current_user.cart.subtotal,
                       status=True)
        # add games from cart to order
        for game in current_user.cart.games:
            order.games.append(game)
        # Add the new Order instance to the session
        db.session.add(order)
        db.session.commit()
        # Clear the cart
        current_user.cart.games = []
        db.session.commit()

        return redirect(url_for('views.thank_you'))
    return render_template("checkout.html")


@views.route('/uploadgame', methods=['GET', 'POST'])
@login_required  # user needs to be login, otherwise redirect to login page
def uploadgame():
    if request.method == 'POST':
        # Extract data from the form
        title = request.form.get('game_title')
        developer_name = request.form.get('game_developer')
        genres = request.form.getlist('genre[]')
        price = float(request.form.get('game-price'))
        description = request.form.get('game_description')
        donation = request.form.get('game_donation')
        # Handle file uploads for game image and zip file
        game_image = request.files['game_image']
        game_zip = request.files['zip_file']

        # Store the file
        game_image_filename = secure_filename(game_image.filename)
        game_image_path = os.path.join(UPLOAD_IMG, game_image_filename)
        os.makedirs(os.path.dirname(game_image_path), exist_ok=True)
        game_image.save(game_image_path)

        game_zip_filename = secure_filename(game_zip.filename)
        game_zip_path = os.path.join(UPLOAD_FILES, game_zip_filename)
        os.makedirs(os.path.dirname(game_zip_path), exist_ok=True)
        game_zip.save(game_zip_path)

        # Query the Developer object based on the provided developer name
        developer = Developer.query.filter_by(devName=developer_name).first()
        if not developer:
            # Check if a Developer with the same email already exists
            existing_developer = Developer.query.filter_by(
                email=current_user.email).first()
            if existing_developer:
                # If a Developer with the same email already exists, use that Developer
                developer = existing_developer
            else:
                # If no Developer with the same email exists, create a new Developer
                developer = Developer(devName=developer_name,
                                      donation=donation,
                                      email=current_user.email,
                                      user_id=current_user.id)
                db.session.add(developer)
                db.session.commit()

        # Create a new Game object and save it to the database, appending genre
        new_game = Game(title=title,
                        developer_id=developer.id,
                        price=price,
                        description=description,
                        image=game_image_path,
                        data=game_zip_path)
        db.session.add(new_game)
        db.session.commit()
        for value in genres:
            category = Game_catalog.query.filter_by(category=value).first()
            if category:
                new_game.categories.append(
                    category
                )  # updates game_catalog_games table to link game to category
        db.session.commit()

        return redirect(
            url_for('views.home'))  # Redirect to the home page after upload

    return render_template("uploadgame.html")


@views.route('/cart', methods=['GET', 'POST'])  #checking the cart itself
@login_required  # user needs to be login, otherwise redirect to login page
def cart():
    # Check if the current user has a cart
    if current_user.cart is None:
        return render_template("cart.html", games=[])

    subtotal = current_user.cart.subtotal

    # Get the games in the current user's cart
    if request.method == 'POST':  # removes game from cart if method is POST
        game_id = request.form.get('game_id')
        game = Game.query.get(game_id)
        if game in current_user.cart.games:
            current_user.cart.games.remove(game)
            db.session.commit()
            games_in_cart = current_user.cart.games
            return render_template("cart.html", games=games_in_cart)

    games_in_cart = current_user.cart.games
    return render_template("cart.html", games=games_in_cart, subtotal=subtotal)


@views.route('/add_to_cart', methods=[
    'POST'
])  # add games to cart, for a seemless experience, using javascript to POST
@login_required  # user needs to be login, otherwise redirect to login page
def add_to_cart(
):  # this would provide functionality of adding games to cart, thinking of doing this without reloading the page
    game_id = request.form.get('game_id')

    # Check if the current user has a cart
    if current_user.cart is None:
        return jsonify({
            'status': 'failure',
            'message': 'User does not have a cart'
        })

    # Get the game object from the game ID
    game = Game.query.get(game_id)

    # Check if the game is not in the user's cart
    if game not in current_user.cart.games:
        # Add the game to the user's cart
        current_user.cart.games.append(game)
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': f'{game.title} added to cart'
        })
    else:
        return jsonify({
            'status': 'success',
            'message': f'{game.title} already in cart'
        })


@views.route('/add_to_cart_and_redirect', methods=['POST'])
@login_required
def add_to_cart_and_redirect():
    game_id = request.form.get('game_id')

    # Check if the current user has a cart
    if current_user.cart is None:
        return jsonify({
            'status': 'failure',
            'message': 'User does not have a cart'
        })

    # Get the game object from the game ID
    game = Game.query.get(game_id)

    # Check if the game is not in the user's cart
    if game not in current_user.cart.games:
        # Add the game to the user's cart
        current_user.cart.games.append(game)
        db.session.commit()
    return redirect(url_for('views.cart'))


@views.route('/thank-you')
@login_required
def thank_you():
    return render_template('thankyou.html')
