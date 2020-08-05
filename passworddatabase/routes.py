import os
from os import abort
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request
from passworddatabase import app, db, bcrypt
from passworddatabase.forms import RegistrationForm, LoginForm, UpdateAccountForm, PasswordForm
from passworddatabase.models import User, Service
from flask_login import login_user, current_user, logout_user, login_required

from hashlib import sha256

db.create_all()  # Create table in database


# Home page
@app.route("/")
@app.route("/home")
def home():
    num_passwords = sidebar_num_passwords()
    num_password_duplicates = sidebar_num_pass_duplicates()
    if current_user.is_authenticated:
        first_password = Service.query.filter_by(owner=current_user).first()
        if first_password is not None:
            page = request.args.get('page', 1, type=int)
            service_pass = Service.query.order_by(Service.date_created.desc()).paginate(page=page, per_page=5)
            return render_template('home.html', posts=service_pass, num_passwords=num_passwords, num_password_duplicates=num_password_duplicates, user=current_user.username)
    return render_template('home.html', posts=None, num_passwords=num_passwords, num_password_duplicates=num_password_duplicates, user=None)


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    form = UpdateAccountForm()
    if form.submit.data and form.validate():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Account has been updated', 'success')
        return redirect(url_for('account'))
    # if form.delete.data and form.validate():
    # delete_account(current_user.id)
    # return redirect(url_for('home'))

    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form=form)


@app.route("/passwords/new", methods=['GET', 'POST'])
@login_required
def new_password():
    form = PasswordForm()

    if form.validate_on_submit():
        # Generate password for service
        user = User.query.filter_by(email=current_user.email).first()
        secret_key = get_hex_key(user.password, form.title.data)
        service_pass = create_password(user.password, form.title.data, secret_key)

        # Save service's password to database
        password = Service(title=form.title.data, content=form.content.data, owner=current_user, password=service_pass)
        db.session.add(password)
        db.session.commit()
        flash('Password has been saved.', 'success')
        return redirect(url_for('home'))
    return render_template('create_password.html', title='New Password', form=form)


@app.route("/password/<int:password_id>")
def password_item(password_id):
    service_data = Service.query.get_or_404(password_id)
    return render_template('password_item.html', title=service_data.title, service=service_data)


@app.route("/password/<int:password_id>/delete", methods=['POST'])
@login_required
def delete_password(password_id):
    password = Service.query.get_or_404(password_id)
    if password.owner != current_user:
        abort(403)
    db.session.delete(password)
    db.session.commit()
    flash(f'Password for {password.title} has been deleted.', 'success')
    return redirect(url_for('home'))


@app.route("/account/<int:user_id>/delete", methods=['POST'])
@login_required
def delete_account(user_id):
    user = User.query.get_or_404(user_id)
    if user != current_user:
        abort(403)

    services = Service.query.filter_by(owner=current_user).all()
    for user_pass in services:
        db.session.delete(user_pass)

    user = User.query.filter_by(id=user_id).first()
    db.session.delete(user)
    db.session.commit()

    flash(f'Account has been deleted.', 'success')
    return redirect(url_for('home'))


@app.route("/read_me")
def read_me():
    return render_template('read_me.html', title='READ ME')


def sidebar_num_passwords():
    if current_user.is_authenticated:
        password_list_size = Service.query.filter_by(owner=current_user).count()
        return password_list_size
    else:
        return 0


def sidebar_num_pass_duplicates():
    num_duplicates = 0
    if current_user.is_authenticated:
        service_list = Service.query.filter_by(owner=current_user).all()
        set_of_services = set()
        for service in service_list:
            if service.password in set_of_services:
                num_duplicates += 1
            else:
                set_of_services.add(service.password)
    return num_duplicates


# Password Generation Functions
def create_password(admin_pass, service_name, pass_key):
    return sha256(admin_pass.encode('utf-8') + service_name.encode('utf-8') + pass_key.encode('utf-8')).hexdigest()[:15]


def get_hex_key(admin_pass, service_name):
    return sha256(admin_pass.encode('utf-8') + service_name.encode('utf-8')).hexdigest()
