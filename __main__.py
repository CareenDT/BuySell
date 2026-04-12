import datetime
import os

from flask import Flask, jsonify, make_response, redirect, render_template, request, url_for
from flask_login import LoginManager, login_required, login_user, logout_user
from flask_restful import Api
from requests import get, post
from sqlalchemy.sql.functions import current_user

from data import db_session
from data.__all_models import User, Products
from forms.user import LoginForm, RegisterForm
from resources.product_api import ProductListResource, ProductResource

app = Flask(__name__)
api = Api(app)

app.config["SECRET_KEY"] = os.urandom(16).hex()
app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(days=1)

login_manager = LoginManager()
login_manager.init_app(app)

current_user = {
    "id" : None,
    "username" : None,
    "email" : None,
    "about" : None,
    "joined_date" : None,
    "hashed_password" : None
    }

@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(User,user_id)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")

@app.route("/index")
@app.route("/")
def index():
    response: dict = get(f"http://127.0.0.1:8080/api/product").json()
    return render_template("index.html", title="BuySellTemplate", products = response["products"])

@app.route("/product_list")
def products():
    response: dict = get(f"http://127.0.0.1:8080/api/product").json()
    return render_template("products.html", title="BuySellTemplate > Products", products = response["products"])

@app.route("/view_product/<int:product_id>")
def view_product(product_id):
    response: dict = get(f"http://127.0.0.1:8080/api/product/{product_id}").json()
    return render_template("view_product.html", title="Продукт", product = response["product"])

@app.route("/profile")
def profile():
    return render_template("profile.html", title=f"Профиль: {current_user['username']}", user=current_user)

@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Register',
                                   form=form,
                                   message="Passwords do not match")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Register',
                                   form=form,
                                   message="Username is not available")
        user = User(
            username=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()

        return redirect('/login')
    
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)

            current_user["username"] = user.username
            current_user["email"] = user.email
            current_user["about"] = user.about
            current_user["joined_date"] = user.joined_date
            current_user["hashed_password"] = user.hashed_password
            current_user["id"] = user.id

            return redirect("/")
        return render_template('login.html',
                               message="Invalid login information",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({"error":"NotFound"}), 404)

@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({"error":"BadRequest"}), 400)

def main():
    db_session.global_init("db/store.db")

    api.add_resource(ProductListResource, "/api/product")
    api.add_resource(ProductResource, "/api/product/<int:product_id>")

    app.run("127.0.0.1", 8080)

if __name__ == "__main__":
    main()
