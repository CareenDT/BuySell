import datetime
import logging
import os

import requests
from flask import Flask, abort, jsonify, make_response, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_restful import Api
from requests import get, post

from data import db_session
from data.__all_models import User, Products, Chat
from forms.user import LoginForm, RegisterForm
from backend.resources.product_api import ProductListResource, ProductResource
from forms.product import ProductForm
from backend.sse_handler import sse_bp

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
    return render_template("index.html", title=f"{APP_NAME}", products = response["products"])

@app.route("/product_list")
def products():
    response: dict = get(f"http://127.0.0.1:8080/api/product").json()
    return render_template("products.html", title=f"{APP_NAME} > Products", products = response["products"])

@app.route("/view_product/<int:product_id>")
def view_product(product_id):
    response: dict = get(f"http://127.0.0.1:8080/api/product/{product_id}").json()
    delete_allowed = False

    try:
        if current_user.id == response["product"]["owner"]:
            delete_allowed = True
    except Exception as e:
        pass
    return render_template("view_product.html", title=f"{APP_NAME} > Product", product=response["product"], delete_allowed=delete_allowed)

@app.route("/profile")
@login_required
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
        return redirect("/")
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
            return redirect("/")
        else:
            return render_template("sell_product.html", title="Продать товар", form=form,
                                   message=f"Error while adding the product: {response.status_code}")

    return render_template("sell_product.html", title=f"{APP_NAME} > Sell", form=form)


@app.route("/messages", methods=['GET'])
@login_required
def messages():
    db_sess = db_session.create_session()

    chats = db_sess.query(Chat).filter(
        (Chat.owner == current_user.id) | (Chat.recipient == current_user.id)
    ).all()

    chat_list = []
    for chat in chats:
        if chat.owner == current_user.id:
            other_id = chat.recipient
        else:
            other_id = chat.owner
        other_user = db_sess.get(User, other_id)

        last_message = chat.contents[-1]["text"] if chat.contents else "Нет сообщений"

        chat_list.append({
            "chat_id": chat.id,
            "other_username": other_user.username,
            "last_message": last_message,
            "created_date": chat.created_date
        })

    db_sess.close()

    return render_template("messages.html", chats=chat_list)


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
    
    return render_template('register.html', title=f'{APP_NAME} > Register', form=form)

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

@app.route("/start_chat/<int:owner_id>/<int:product_id>")
@login_required
def start_chat(owner_id, product_id):
    if current_user.id == owner_id:
        return redirect("/")

    db_sess = db_session.create_session()

    chat = db_sess.query(Chat).filter(
        ((Chat.owner == current_user.id) & (Chat.recipient == owner_id)) |
        ((Chat.owner == owner_id) & (Chat.recipient == current_user.id))
    ).first()

    if not chat:

        chat = Chat(
            owner=current_user.id,
            recipient=owner_id
        )
        db_sess.add(chat)
        db_sess.commit()

    chat_id = chat.id
    db_sess.close()

    return redirect(f"/chat/{chat_id}")

@app.route("/chat/<int:chat_id>")
@login_required
def chat(chat_id):
    db_sess = db_session.create_session()
    chat = db_sess.get(Chat, chat_id)
    db_sess.close()
    
    if not chat:
        abort(404)
    
    if current_user.id not in [chat.owner, chat.recipient]:
        abort(403)
    
    return render_template("chat.html", title=f"{APP_NAME} > Chat", chat_id=chat_id, current_user=current_user)

@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/api/'):
        return make_response(jsonify({"error": "NotFound"}), 404)
    
    return render_template("error.html", title="404", error_code=404, message="Page not found"), 404


@app.errorhandler(400)
def bad_request(error):
    if request.path.startswith('/api/'):
        return make_response(jsonify({"error": "Bad Request"}), 400)
    
    return render_template("error.html", title="400", error_code=400, message="Bad Request"), 400

@app.errorhandler(403)
def forbidden(error):
    if request.path.startswith('/api/'):
        return make_response(jsonify({"error": "forbidden"}), 403)
    
    return render_template("error.html", title="403", error_code=403, message="Forbidden"), 403

def main():
    db_session.global_init("db/store.db")

    api.add_resource(ProductListResource, "/api/product")
    api.add_resource(ProductResource, "/api/product/<int:product_id>")

    app.register_blueprint(sse_bp)

    app.run("127.0.0.1", 8080)

if __name__ == "__main__":
    main()
