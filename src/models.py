from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Base(db.Model):
    __abstract__ = True
    created = db.Column(db.DateTime(timezone=True), default=db.func.now())


class User(Base):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=False, nullable=False)
    planet = db.Column(db.String(25), nullable=False)
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

    def serialize(self):
        return {"item": self.items}


class Item(Base):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    favorites = db.relationship("Favorites", backref="item")

    __table_args__ = (db.UniqueConstraint("name", "type", name="unique_items"),)

    __mapper_args__ = {"polymorphic_identity": "item", "polymorphic_on": type}


class Character(Item):
    id = db.Column(db.Integer, db.ForeignKey("item.id"), primary_key=True)
    uid = db.Column(db.Integer)
    height = db.Column(db.String(150))
    gender = db.Column(db.String(150))
    mass = db.Column(db.String(150))
    birth_year = db.Column(db.String(150))
    skin_color = db.Column(db.String(150))

    __mapper_args__ = {"polymorphic_identity": "characters"}

    def __init__(self, **kwargs):
        for (key, value) in kwargs.items():
            if hasattr(self, key):
                attr_type = getattr(self.__class__, key).type
                try:
                    attr_type.python_type(value)
                    setattr(self, key, value)
                except Exception as error:
                    print(f"Ignore all other attributes: {error}")

    @classmethod
    def create(cls, data, index):
        instance = cls(**data, uid=index)
        if isinstance(instance, cls):
            db.session.add(instance)
            try:
                db.session.commit()
                print(f"Instance {instance.name} created.")
                return instance
            except Exception as error:
                db.session.rollback()
                print(error.args)
        else:
            print("Something happened. Couldn't create Character instance.")
            return None

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "uid": self.uid,
            "type": self.type,
            "height": self.height,
            "gender": self.gender,
            "mass": self.mass,
            "birth_year": self.birth_year,
            "skin_color": self.skin_color,
        }


class Planet(Item):
    id = db.Column(db.Integer, db.ForeignKey("item.id"), primary_key=True)
    uid = db.Column(db.Integer)
    population = db.Column(db.String(150))
    terrain = db.Column(db.String(150))
    diameter = db.Column(db.String(150))
    climate = db.Column(db.String(150))
    gravity = db.Column(db.String(150))

    __mapper_args__ = {"polymorphic_identity": "planets"}

    def __init__(self, **kwargs):
        for (key, value) in kwargs.items():
            if hasattr(self, key):
                attr_type = getattr(self.__class__, key).type
                try:
                    attr_type.python_type(value)
                    setattr(self, key, value)
                except Exception as error:
                    print(f"Ignore all other attributes: {error}")

    @classmethod
    def create(cls, data, index):
        instance = cls(**data, uid=index)
        if isinstance(instance, cls):
            db.session.add(instance)
            try:
                db.session.commit()
                print(f"Instance {instance.name} created.")
                return instance
            except Exception as error:
                db.session.rollback()
                print(error.args)
        else:
            print("Something happened. Couldn't create Planet instance.")
            return None

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "uid": self.uid,
            "type": self.type,
            "population": self.population,
            "terrain": self.terrain,
            "diameter": self.diameter,
            "climate": self.climate,
            "gravity": self.gravity,
        }
