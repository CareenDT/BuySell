import datetime
import logging
import os

import requests
from flask import Flask, abort, jsonify, make_response, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_restful import Api
from requests import get, post

from data import db_session
from data.__all_models import User, Products
from forms.user import LoginForm, RegisterForm
from resources.chat_api import ChatListResource, ChatResource
from resources.product_api import ProductListResource, ProductResource
from forms.product import ProductForm

# logging.basicConfig(
#     filename="RuntimeOutput.log",
#     format='%(message)s',
#     encoding="utf-8",
# )

app = Flask(__name__)
api = Api(app)

app.config["SECRET_KEY"] = os.urandom(16).hex()
app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(days=365)

login_manager = LoginManager()
login_manager.init_app(app)

APP_NAME = "BuySellTemplate"

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
    return render_template("index.html", title="{APP_NAME}", products = response["products"])

@app.route("/product_list")
def products():
    response: dict = get(f"http://127.0.0.1:8080/api/product").json()
    return render_template("products.html", title="{APP_NAME} > Products", products = response["products"])

@app.route("/view_product/<int:product_id>")
def view_product(product_id):
    response: dict = get(f"http://127.0.0.1:8080/api/product/{product_id}").json()
    return render_template("view_product.html", title=f"{APP_NAME} > Product", product=response["product"])

@app.route("/profile")
def profile():
    return render_template("profile.html", title=f"{APP_NAME} > Profile({current_user.username})", user=current_user)

@app.route("/del_product/<int:product_id>", methods=["GET", "POST"])
@login_required
def del_product(product_id):
    response: dict = get(f"http://127.0.0.1:8080/api/product/{product_id}").json()
    product = response["product"]
    data = {
        "owner": product["owner"],
        "current_user_id": current_user.id
    }

    response = requests.delete(f"http://127.0.0.1:8080/api/product/{product_id}", json=data)

    if response.status_code == 200:
        return redirect("/product_list")
    return jsonify({"Error while delete the product": response.status_code})


@app.route("/sell_product", methods=['GET', 'POST'])
@login_required
def sell_product():
    form = ProductForm()

    if form.validate_on_submit():

        data = {
            "owner": current_user.id,
            "name": form.name.data,
            "description": form.description.data,
            "pricing": form.price.data
        }

        response = post("http://127.0.0.1:8080/api/product", json=data)

        if response.status_code == 200:
            return redirect("/product_list")
        else:
            return render_template("sell_product.html", title="Продать товар", form=form,
                                   message=f"Error while adding the product: {response.status_code}")

    return render_template("sell_product.html", title="{APP_NAME} > Sell", form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
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
    
    return render_template('register.html', title='{APP_NAME} > Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():

    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)

            return redirect("/")
        return render_template('login.html',
                               message="Invalid login information",
                               form=form)
    return render_template('login.html', title = f"{APP_NAME} > Login", form=form)

@app.route("/chat/<int:chat_id>")
@login_required
def chat(chat_id):

    first_response = get(f"http://127.0.0.1:8080/api/chat/{chat_id}")
    data = first_response.json()

    if first_response.status_code != 200:
        return first_response
    print(data)
    if current_user.id in [data["owner"], data["recipient"]]:
        return render_template("chat.html", title = f"{APP_NAME} > Chat", chat_id=chat_id, current_user=current_user)
    else:
        abort(403)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({"error":"NotFound"}), 404)

@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({"error":"Bad Request"}), 400)

@app.errorhandler(403)
def bad_request(error):
    return make_response(jsonify({"error":"Forbidden"}), 403)

def main():
    db_session.global_init("db/store.db")

    api.add_resource(ProductListResource, "/api/product")
    api.add_resource(ProductResource, "/api/product/<int:product_id>")

    api.add_resource(ChatResource, "/api/chat/<int:chat_id>")
    api.add_resource(ChatListResource, "/api/chat")

    app.run("127.0.0.1", 8080)

if __name__ == "__main__":
    main()
