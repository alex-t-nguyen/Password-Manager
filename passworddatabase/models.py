from datetime import datetime
from passworddatabase import db, login_manager
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    services = db.relationship('Service', backref='owner', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False, default="")
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    password = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"User('{self.title}', '{self.date_created}')"
