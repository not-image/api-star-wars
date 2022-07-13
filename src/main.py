"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
import requests
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Favorites, Item, Character, Planet
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)

# from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DB_CONNECTION_STRING")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False
app.config["JWT_SECRET_KEY"] = os.environ.get("FLASK_API_KEY")
jwt = JWTManager(app)

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)


# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code


# generate sitemap with all the endpoints
@app.route("/")
def sitemap():
    return generate_sitemap(app)


@app.route("/signup", methods=["POST"])
def handle_signup():
    body = request.json

    if (
        not body.get("username")
        or not body.get("email")
        or not body.get("password")
        or not body.get("planet")
    ):
        return jsonify({"response": "Incomplete information."}), 404
    else:
        user = User(
            username=body["username"],
            email=body["email"],
            password=body["password"],
            planet=body["planet"],
        )
        db.session.add(user)

        try:
            db.session.commit()
            return jsonify({"response": "Success"}), 201
        except Exception as error:
            db.session.rollback()
            return jsonify({"response": error.args}), 500


@app.route("/login", methods=["POST"])
def handle_login():
    body = request.json
    email = body.get("email", None)
    password = body.get("password", None)

    if email is None or password is None:
        return jsonify({"response": "Incomplete information."}), 404
    else:
        user = User.query.filter_by(email=email, password=password).one_or_none()

        if user is not None:
            token = create_access_token(identity=user.id)
            return jsonify(
                {
                    "response": {
                        "token": token,
                        "username": user.username,
                        "planet": user.planet,
                    }
                }
            )
        else:
            return jsonify({"response": "Incorrect email or password."}), 404


@app.route("/favorites", methods=["GET", "POST", "DELETE"])
@jwt_required()
def handle_favorites():
    current_user_id = get_jwt_identity()

    if request.method == "GET":
        all_favorites = Favorites.query.filter_by(user_id=current_user_id).all()
        all_favorites = list(map(lambda fav: fav.serialize(), all_favorites))

        pre_item_favorites = []

        for index, favorite in enumerate(all_favorites):
            item_favorite = Item.query.filter_by(
                id=all_favorites[index]["item"]
            ).one_or_none()
            pre_item_favorites.append(item_favorite)

        all_item_favorites = list(map(lambda fav: fav.serialize(), pre_item_favorites))
        return jsonify({"results": all_item_favorites}), 200

    if request.method == "POST":
        body = request.json
        item = body.get("item_id")

        is_favorited = Favorites.query.filter_by(
            items=item, user_id=current_user_id
        ).first()

        if is_favorited is not None:
            return ({"msg": "Duplicate entry."}), 500

        if not item:
            return jsonify({"msg": "Not found."}), 404
        else:
            favorite = Favorites(user_id=current_user_id, items=item)
            db.session.add(favorite)

            try:
                db.session.commit()
                return jsonify(favorite.serialize()), 201
            except Exception as error:
                db.session.rollback()
                return jsonify(error.args), 500

    if request.method == "DELETE":
        body = request.json
        item = body.get("item_id")

        is_favorited = Favorites.query.filter_by(
            items=item, user_id=current_user_id
        ).first()

        if is_favorited is not None and item:
            favorite_to_delete = is_favorited
            db.session.delete(favorite_to_delete)

            try:
                db.session.commit()
                return jsonify([]), 204
            except Exception as error:
                db.session.rollback()
                return jsonify(error.args), 500
        else:
            return jsonify({"msg": "Not found."}), 404


@app.route("/characters", methods=["GET"])
@app.route("/characters/<int:char_id>", methods=["GET"])
def handle_characters(char_id=None):
    if char_id is not None:
        character = Character.query.filter_by(character_id=char_id).one_or_none()

        if character is not None:
            return jsonify(character.serialize())
        else:
            return jsonify({"msg": "Not found."}), 404
    else:
        all_characters = Character.query.all()
        all_characters = list(map(lambda char: char.serialize(), all_characters))
        return jsonify({"results": all_characters}), 200

    return jsonify([]), 200


@app.route("/planets", methods=["GET"])
@app.route("/planets/<int:plan_id>", methods=["GET"])
def handle_planets(plan_id=None):
    if plan_id is not None:
        planet = Planet.query.filter_by(planet_id=plan_id).one_or_none()

        if planet is not None:
            return jsonify(planet.serialize())
        else:
            return jsonify({"msg": "Not found."}), 404
    else:
        all_planets = Planet.query.all()
        all_planets = list(map(lambda plan: plan.serialize(), all_planets))
        return jsonify({"results": all_planets}), 200

    return jsonify([]), 200


BASE_URL = "https://swapi.dev/api"


@app.route("/populate/characters", methods=["GET"])
def handle_populate_characters():
    response = requests.get(f"{BASE_URL}/{'people'}")
    body = response.json()

    all_characters = []
    for result in body["results"]:
        response = requests.get(result["url"])
        body = response.json()
        all_characters.append(body)

    all_instances = []
    for index, character in enumerate(all_characters):
        print(character, "character")
        instance = Character.create(character, index + 1)
        print(instance, "instance")
        all_instances.append(instance)

    return jsonify(list(map(lambda ins: ins.serialize(), all_instances))), 200


@app.route("/populate/planets", methods=["GET"])
def handle_populate_planets():
    response = requests.get(f"{BASE_URL}/{'planets'}")
    body = response.json()

    all_planets = []
    for result in body["results"]:
        response = requests.get(result["url"])
        body = response.json()
        all_planets.append(body)

    all_instances = []
    for index, planet in enumerate(all_planets):
        print(planet, "planet")
        instance = Planet.create(planet, index + 1)
        print(instance, "instance")
        all_instances.append(instance)

    return jsonify(list(map(lambda ins: ins.serialize(), all_instances))), 200


# this only runs if `$ python src/main.py` is executed
if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 8000))
    app.run(host="127.0.0.1", port=PORT, debug=False)
