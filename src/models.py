from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Base(db.Model):
    __abstract__ = True
    created = db.Column(db.DateTime(timezone=True), default=db.func.now())


class User(Base):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=False, nullable=False)
    favorites = db.relationship("Favorites", backref="user", uselist=True)

    def __repr__(self):
        return "<User %r>" % self.id

    def serialize(self):
        return {
            "id": self.id,
            "email": self.email,
        }


class Favorites(Base):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    items = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=False)
    # character_id = db.Column(db.Integer, db.ForeignKey("character.id"))
    # planet_id = db.Column(db.Integer, db.ForeignKey("planet.id"))

    __table_args__ = (
        db.UniqueConstraint("user_id", "items", name="unique_user_favorites"),
    )


class Item(Base):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    favorites = db.relationship("Favorites", backref="item")

    __mapper_args__ = {"polymorphic_identity": "item", "polymorphic_on": type}


class Character(Item):
    id = db.Column(db.Integer, db.ForeignKey("item.id"), primary_key=True)
    height = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    mass = db.Column(db.Integer)
    birth_year = db.Column(db.Integer)
    eye_color = db.Column(db.String(20))
    skin_color = db.Column(db.String(20))
    # favorites = db.relationship("Favorites", backref="character", uselist=True)

    __mapper_args__ = {"polymorphic_identity": "characters"}


class Planet(Item):
    id = db.Column(db.Integer, db.ForeignKey("item.id"), primary_key=True)
    population = db.Column(db.Integer)
    terrain = db.Column(db.String(80))
    diameter = db.Column(db.Integer)
    climate = db.Column(db.String(20))
    gravity = db.Column(db.String(20))
    # favorites = db.relationship("Favorites", backref="planet", uselist=True)

    __mapper_args__ = {"polymorphic_identity": "planets"}
