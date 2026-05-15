import datetime
import os
import uuid

import requests
from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_restful import Api
from requests import get, post
from werkzeug.utils import secure_filename

from data import db_session
from data.__all_models import User, Products, Chat, Order
from forms.user import LoginForm, RegisterForm
from backend.resources.product_api import ProductListResource, ProductResource
from forms.product import ProductForm, ProductSearchForm
from backend.chat_handler import chatHandler_bp
from backend.cart_handler import cartHandler_bp
from decimal import Decimal
from forms.sort import SortForm
from i18n import normalize_lang, translate
from flask_mail import Mail
from data.email_utils import send_verification_email, save_verification_code, verify_code
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
api = Api(app)

app.config["SECRET_KEY"] = os.urandom(16).hex()
app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(days=365)
app.config["UPLOAD_FOLDER"] = os.path.join("static", "product", "images")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message_category = "warning"

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = int(os.getenv("MAIL_PORT"))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'buysell22867@gmail.com'
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] = 'buysell22867@gmail.com'

mail = Mail()
mail.init_app(app)

APP_NAME = "BuySell"


def localize_product_form(form, lang_code: str) -> None:
    form.name.label.text = translate(lang_code, "sell.name")
    form.description.label.text = translate(lang_code, "sell.desc")
    form.price.label.text = translate(lang_code, "sell.price")
    form.image.label.text = translate(lang_code, "sell.image")
    form.submit.label.text = translate(lang_code, "sell.submit")


def localize_product_search_form(form, lang_code: str) -> None:
    form.search.label.text = translate(lang_code, "search.label")
    form.submit.label.text = translate(lang_code, "search.submit")


def localize_login_form(form, lang_code: str) -> None:
    form.email.label.text = translate(lang_code, "login.email_field")
    form.password.label.text = translate(lang_code, "login.password_field")
    form.remember_me.label.text = translate(lang_code, "login.remember")
    form.submit.label.text = translate(lang_code, "login.submit_btn")


def localize_register_form(form, lang_code: str) -> None:
    form.name.label.text = translate(lang_code, "register.name_field")
    form.password.label.text = translate(lang_code, "register.password_field")
    form.password_again.label.text = translate(
        lang_code, "register.password_again_field"
    )
    form.email.label.text = translate(lang_code, "register.email_field")
    form.about.label.text = translate(lang_code, "register.about_field")
    form.submit.label.text = translate(lang_code, "register.submit_btn")


@app.before_request
def sync_ui_prefs():
    session.setdefault("lang", "ru")
    session.setdefault("theme", "dark")
    session.permanent = True
    login_manager.login_message = translate(session["lang"], "flash.login_required")


@app.context_processor
def inject_ui():
    lang = session.get("lang", "ru")
    theme = session.get("theme", "dark")
    return {
        "t": lambda key: translate(lang, key),
        "ui_lang": lang,
        "ui_theme": theme,
    }


@app.route("/set_language/<code>")
def set_language(code):
    session["lang"] = normalize_lang(code)
    session.permanent = True
    return redirect(request.referrer or url_for("index"))


@app.route("/set_theme/<name>")
def set_theme_route(name):
    session["theme"] = name if name in ("dark", "light") else "dark"
    session.permanent = True
    return redirect(request.referrer or url_for("index"))


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings_page():
    lc = session.get("lang", "ru")
    if request.method == "POST":
        session["lang"] = normalize_lang(request.form.get("lang", lc))
        th = request.form.get("theme", "dark")
        session["theme"] = th if th in ("dark", "light") else "dark"
        session.permanent = True
        return redirect(url_for("settings_page"))
    return render_template(
        "settings.html",
        title=f"{APP_NAME} > {translate(lc, 'settings.title')}",
    )


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(User, user_id)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

@app.route("/index", methods=["GET", "POST"])
@app.route("/", methods=["GET", "POST"])
def index():
    if current_user.is_authenticated:
        return redirect("/home_page")
    pic_list = [url_for('static', filename='index/images/1.jpg'),
                           url_for('static', filename='index/images/2.jpg'),
                           url_for('static', filename='index/images/3.jpg'),
                           ]
    return render_template(
        "index.html",
        title=f'{APP_NAME}', pic_list=pic_list,
    )

@app.route("/home_page", methods=["GET", "POST"])
def home_page():
    response: dict = get(f"http://127.0.0.1:8080/api/product").json()
    form = SortForm()
    products = response["products"]
    if form.validate_on_submit():
        choice = form.sort_type.data
        if choice == 'price_asc':
            products.sort(key=lambda p: p["pricing"], reverse=False)
        elif choice == 'price_desc':
            products.sort(key=lambda p: p["pricing"], reverse=True)
        elif choice == 'newest':
            products.sort(key=lambda p: p["created_date"], reverse=True)
    print(products)
    return render_template("home_page.html", title=f"{APP_NAME} > home_page", products=products, form=form)

@app.route("/product_list")
def products():
    response: dict = get(f"http://127.0.0.1:8080/api/product").json()
    lc = session.get("lang", "ru")
    return render_template(
        "products.html",
        title=f'{APP_NAME} > {translate(lc, "nav.products")}',
        products=response["products"],
    )


@app.route("/products", methods=["GET", "POST"])
def product_search():
    form = ProductSearchForm()
    localize_product_search_form(form, session.get("lang", "ru"))
    if form.validate_on_submit():
        return redirect(f"/search/{form.search.data}")
    return render_template(
        "product_search.html",
        title=f'{APP_NAME} > {translate(session.get("lang", "ru"), "nav.search")}',
        form=form,
    )


@app.route("/search/<search>")
def search(search):
    get(f"http://127.0.0.1:8080/api/product").json()

    db_sess = db_session.create_session()

    products = db_sess.query(Products).filter(Products.name.ilike(f"%{search}%")).all()

    lc = session.get("lang", "ru")
    return render_template(
        "after_search_page.html",
        title=f'{APP_NAME} > {translate(lc, "after_search.results")}',
        products=products,
    )


@app.route("/view_product/<int:product_id>")
def view_product(product_id):
    response = get(f"http://127.0.0.1:8080/api/product/{product_id}")
    data = response.json()
    delete_allowed = False

    if not data.get("product"):
        abort(404)

    try:
        if current_user.id == data["product"]["owner"]:
            delete_allowed = True
    except Exception:
        pass

    product = data["product"]
    pid = product["id"]
    in_cart = False
    cart_quantity = 0
    try:
        if current_user.is_authenticated:
            sess = db_session.create_session()
            u = sess.get(User, current_user.id)
            if u and u.cart_contents:
                for row in u.cart_contents:
                    if int(row.get("product_id", -1)) == int(pid):
                        in_cart = True
                        cart_quantity += int(row.get("quantity") or 0)
            sess.close()
    except Exception:
        pass

    if cart_quantity <= 0 and in_cart:
        cart_quantity = 1

    if response.status_code == 200:
        return render_template(
            "view_product.html",
            title=f'{product.get("name", APP_NAME)} — {APP_NAME}',
            product=product,
            delete_allowed=delete_allowed,
            in_cart=in_cart,
            cart_quantity=cart_quantity,
        )
    return abort(response.status_code)


@app.route("/profile")
@login_required
def profile():
    lc = session.get("lang", "ru")

    db_sess = db_session.create_session()

    products = db_sess.query(Products).filter(Products.owner == current_user.id).all()
    products_len = len(products)

    return render_template("profile.html",
                           title=f'{APP_NAME} > {translate(lc, "nav.profile")} ({current_user.username})',
                           user=current_user,
                           products=products,
                           products_len=products_len,
                           )


@app.route("/del_product/<int:product_id>", methods=["GET", "POST"])
@login_required
def del_product(product_id):
    response: dict = get(f"http://127.0.0.1:8080/api/product/{product_id}").json()

    if not response.get("product"):
        abort(404)

    product = response["product"]

    data = {
        "owner": product["owner"],
        "current_user_id": current_user.id
    }

    response = requests.delete(f"http://127.0.0.1:8080/api/product/{product_id}", json=data)

    if response.status_code == 200:
        return redirect("/")
    return jsonify({"Error while deleting the product": response.status_code})


def save_image(file):
    if not file or not file.filename:
        return None

    upload_folder = app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)

    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1]
    unique_filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(upload_folder, unique_filename)

    file.save(filepath)

    return os.path.join("static", "product", "images", unique_filename)


@app.route("/sell_product", methods=["GET", "POST"])
@login_required
def sell_product():
    lc = session.get("lang", "ru")
    form = ProductForm()
    localize_product_form(form, lc)

    if form.validate_on_submit():
        image_path = None
        if form.image.data:
            image_path = save_image(form.image.data)

        data = {
            "owner": current_user.id,
            "name": form.name.data,
            "description": form.description.data,
            "pricing": form.price.data,
            "image": image_path
        }

        response = post("http://127.0.0.1:8080/api/product", json=data)

        if response.status_code == 200:
            return redirect("/")
        else:
            msg = f"{translate(lc, 'sell.error_add')} {response.status_code}"
            return render_template(
                "sell_product.html",
                title=f"{APP_NAME} > {translate(lc, 'nav.sell')}",
                form=form,
                message=msg,
            )

    return render_template(
        "sell_product.html",
        title=f"{APP_NAME} > {translate(lc, 'nav.sell')}",
        form=form,
    )


@app.route("/messages", methods=["GET"])
@login_required
def messages():
    db_sess = db_session.create_session()

    chats = db_sess.query(Chat).filter(
        (Chat.owner == current_user.id) | (Chat.recipient == current_user.id)
    ).all()

    chat_list = []
    for chat in chats:
        try:
            if chat.owner == current_user.id:
                other_id = chat.recipient
            else:
                other_id = chat.owner
            other_user = db_sess.get(User, other_id)

            last_message = chat.contents[-1]["text"] if chat.contents else None

            chat_list.append({
                "chat_id": chat.id,
                "other_username": other_user.username,
                "last_message": last_message,
                "created_date": chat.created_date
            })
        except Exception:
            pass

    db_sess.close()

    lc = session.get("lang", "ru")
    return render_template(
        "messages.html",
        chats=chat_list,
        title=f'{APP_NAME} > {translate(lc, "messages.title")}',
    )


@app.route('/register', methods=['GET', 'POST'])
def register():
    lc = session.get("lang", "ru")
    form = RegisterForm()
    localize_register_form(form, lc)
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template(
                "register.html",
                title=f'{APP_NAME} > {translate(lc, "register.title")}',
                form=form,
                message=translate(lc, "register.msg_mismatch"),
            )
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            db_sess.close()
            return render_template(
                "register.html",
                title=f'{APP_NAME} > {translate(lc, "register.title")}',
                form=form,
                message=translate(lc, "register.msg_busy"),
            )
        user = User(
            username=form.name.data,
            email=form.email.data,
            about=form.about.data,
            cart_contents=[],
            confirmed=False,
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()

        code = save_verification_code(user, db_sess)
        db_sess.close()

        send_verification_email(app, form.email.data, code)

        session['pending_verification_email'] = form.email.data
        return redirect('/verify_email')

    return render_template(
        "register.html",
        title=f'{APP_NAME} > {translate(lc, "register.title")}',
        form=form,
    )


@app.route('/verify_email', methods=['GET', 'POST'])
def verify_email_page():
    email = session.get('pending_verification_email')

    if not email:
        return redirect('/register')

    if request.method == 'POST':
        code = request.form.get('code', '').strip()

        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == email).first()

        if not user:
            db_sess.close()
            session.pop('pending_verification_email', None)
            return redirect('/register')

        is_valid, msg = verify_code(user, code)

        if is_valid:
            user.confirmed = True
            user.email_verification_code = None
            user.email_verification_expires = None
            db_sess.commit()

            user_id = user.id
            db_sess.close()

            session.pop('pending_verification_email', None)

            new_db_sess = db_session.create_session()
            fresh_user = new_db_sess.query(User).filter(User.id == user_id).first()
            login_user(fresh_user)
            new_db_sess.close()

            return redirect('/home_page')
        else:
            db_sess.close()
            return render_template(
                'verify_email.html',
                email=email,
                message=msg,
                message_type='danger'
            )

    return render_template('verify_email.html', email=email)

@app.route('/resend_code')
def resend_code():
    email = session.get('pending_verification_email')

    if not email:
        return redirect('/register')

    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.email == email).first()

    if not user:
        db_sess.close()
        session.pop('pending_verification_email', None)
        return redirect('/register')

    if user.confirmed:
        db_sess.close()
        session.pop('pending_verification_email', None)
        return redirect('/login')
    
    code = save_verification_code(user, db_sess)
    db_sess.close()


    try:
        send_verification_email(app, email, code)
    except Exception:
        return redirect('/verify_email')
    return redirect('/verify_email')


@app.route('/login', methods=['GET', 'POST'])
def login():
    lc = session.get("lang", "ru")
    form = LoginForm()
    localize_login_form(form, lc)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)

            return redirect("/")
        db_sess.close()
        return render_template(
            "login.html",
            message=translate(lc, "login.invalid"),
            form=form,
            title=f'{APP_NAME} > {translate(lc, "login.title")}',
        )
    return render_template(
        "login.html",
        title=f'{APP_NAME} > {translate(lc, "login.title")}',
        form=form,
    )


@app.route("/checkout")
@login_required
def checkout():

    cart = []
    try:
        cart = current_user.cart_contents or []
    except Exception:
        cart = []

    cart_items = []
    subtotal = Decimal("0.00")

    for item in cart:
        try:
            product_id = int(item.get("product_id"))
            quantity = int(item.get("quantity", 0))
        except Exception:
            continue

        if quantity <= 0:
            continue

        product_response = get(f"http://127.0.0.1:8080/api/product/{product_id}")
        if product_response.status_code != 200:
            continue

        product_data = product_response.json().get("product")
        if not product_data:
            continue

        pricing = product_data.get("pricing", 0) or 0

        try:
            pricing_dec = Decimal(str(pricing))
        except Exception:
            pricing_dec = Decimal("0.00")

        line_total = pricing_dec * quantity
        subtotal += line_total

        cart_items.append({
            "product_id": product_id,
            "product_name": product_data.get("name"),
            "quantity": quantity,
            "pricing": pricing_dec,
            "line_total": line_total,
            "name": product_data.get("name")
        })



    return render_template(
        "checkout.html",
        title=f"{APP_NAME} > Checkout",
        cart_items=cart_items,
        subtotal=subtotal
    )

@app.route("/orders")
@login_required
def orders_page():
    db_sess = db_session.create_session()
    try:
        raw_orders = db_sess.query(Order).filter(

            (Order.buyer_id == current_user.id) | (Order.seller_id == current_user.id)
        ).all()

        lc_orders = []
        for o in raw_orders:
            try:
                product_name = str(o.product_id)

            except Exception:
                product_name = str(o.product_id)

            status_display = o.status
            if o.seller_id == current_user.id and o.status == "pending":
                status_display = "to_fulfill"

            lc_orders.append(
                {
                    "id": o.id,
                    "product_id": o.product_id,
                    "product_name": product_name,
                    "quantity": o.quantity,
                    "amount": o.amount,
                    "status_display": status_display,
                    "transaction_id": o.transaction_id,
                }
            )
    finally:
        db_sess.close()

    return render_template("orders.html", orders=lc_orders, title=f"{APP_NAME} > Orders")


@app.route("/balance")
@login_required
def balance():
    try:
        db_sess = db_session.create_session()
        user_obj = db_sess.get(User, current_user.id)
        current_wallet = getattr(user_obj, "wallet_balance", None)
        db_sess.close()
    except Exception:
        current_wallet = None

    return render_template(
        "balance.html",
        title=f"{APP_NAME} > Balance",
        payment_method="wallet",
        transaction_id="-",
        paid_amount=Decimal("0.00"),
        balance_demo=Decimal("0.00"),
        wallet_balance=current_wallet,
    )


@app.route("/add_funds")
@login_required
def add_funds():
    return render_template("add_funds.html", title=f"{APP_NAME} > Add Funds")


@app.route("/add_funds/confirm", methods=["POST"])
@login_required
def add_funds_confirm():
    amount_raw = request.form.get("amount", "0")
    try:
        amount = Decimal(str(amount_raw))
    except Exception:
        amount = Decimal("0.00")

    if amount <= 0:
        return render_template(
            "balance.html",
            title=f"{APP_NAME} > Balance",
            payment_method="wallet",
            transaction_id="-",
            paid_amount=Decimal("0.00"),
            balance_demo=Decimal("0.00"),
            wallet_balance=getattr(current_user, "wallet_balance", None),
        )

    transaction_id = str(uuid.uuid4())

    try:
        db_sess = db_session.create_session()
        user_obj = db_sess.get(User, current_user.id)
        current_balance = Decimal(str(getattr(user_obj, "wallet_balance", 0.0) or 0.0))
        user_obj.wallet_balance = float(current_balance + amount)
        db_sess.commit()
        updated_balance = getattr(user_obj, "wallet_balance", None)
        db_sess.close()
    except Exception:
        updated_balance = getattr(current_user, "wallet_balance", None)

    return render_template(
        "balance.html",
        title=f"{APP_NAME} > Balance",
        payment_method="wallet",
        transaction_id=transaction_id,
        paid_amount=amount,
        balance_demo=amount,
        wallet_balance=updated_balance,
    )


@app.route("/orders/confirm", methods=["POST"])
@login_required
def order_confirm():
    order_id_raw = request.form.get("order_id")
    if not order_id_raw:
        return redirect("/orders")

    try:
        order_id = int(order_id_raw)
    except Exception:
        return redirect("/orders")

    db_sess = db_session.create_session()
    try:
        o = db_sess.get(Order, order_id)
        if not o:
            return redirect("/orders")

        if o.buyer_id != current_user.id and o.seller_id != current_user.id:
            return redirect("/orders")

        is_buyer = o.buyer_id == current_user.id
        is_seller = o.seller_id == current_user.id
        if o.status == "pending":
            if is_buyer:
                o.status = "pending_buyer"
            elif is_seller:
                o.status = "to_fulfill"
        elif o.status == "pending_buyer" and is_seller:
            o.status = "fulfilled"
        elif o.status == "to_fulfill" and is_buyer:
            o.status = "fulfilled"

        db_sess.commit()
    finally:
        db_sess.close()

    return redirect("/orders")


@app.route("/checkout/confirm", methods=["POST"])
@login_required
def checkout_confirm():
    cart = current_user.cart_contents or []

    subtotal = Decimal("0.00")
    for item in cart:
        try:
            product_id = int(item.get("product_id"))
            quantity = int(item.get("quantity", 0))
        except Exception:
            continue
        if quantity <= 0:
            continue

        product_resp = get(f"http://127.0.0.1:8080/api/product/{product_id}")
        if product_resp.status_code != 200:
            continue

        product_data = product_resp.json().get("product")
        if not product_data:
            continue

        pricing = product_data.get("pricing", 0) or 0
        try:
            pricing_dec = Decimal(str(pricing))
        except Exception:
            pricing_dec = Decimal("0.00")

        subtotal += pricing_dec * quantity

    payment_method = request.form.get("payment_method", "card")

    transaction_id = str(uuid.uuid4())


    if payment_method == "wallet":
        try:
            db_sess = db_session.create_session()
            user_obj = db_sess.get(User, current_user.id)
            current_balance = Decimal(str(getattr(user_obj, "wallet_balance", 0.0) or 0.0))
            db_sess.close()
        except Exception:
            current_balance = Decimal("0.0")

        if current_balance < subtotal:
            return render_template(

            "balance.html",
            title=f"{APP_NAME} > Balance",
            payment_method=payment_method,
            transaction_id=transaction_id,
            paid_amount=subtotal,
            balance_demo=Decimal("0.0"),
            wallet_balance=current_balance,
        )



        try:
            db_sess = db_session.create_session()
            user_obj = db_sess.get(User, current_user.id)

            current_balance = Decimal(str(getattr(user_obj, "wallet_balance", 0.0) or 0.0))

            new_balance = current_balance - subtotal
            if new_balance < 0:
                new_balance = Decimal("0.0")
            user_obj.wallet_balance = float(new_balance)
            cart_snapshot = list(current_user.cart_contents or [])

            created_any = False
            for item in cart_snapshot:
                try:
                    product_id = int(item.get("product_id"))
                    quantity = int(item.get("quantity", 0))
                except Exception:
                    continue

                if quantity <= 0:
                    continue

                product_resp = get(f"http://127.0.0.1:8080/api/product/{product_id}")
                if product_resp.status_code != 200:
                    continue

                product_data = product_resp.json().get("product")
                if not product_data:
                    continue

                seller_id = product_data.get("owner")
                if seller_id is None:
                    continue

                pricing = product_data.get("pricing", 0) or 0
                try:
                    pricing_dec = Decimal(str(pricing))
                except Exception:
                    pricing_dec = Decimal("0.00")

                line_amount = float(pricing_dec * quantity)


                order = Order(
                    buyer_id=current_user.id,
                    seller_id=int(seller_id),


                    product_id=product_id,
                    quantity=quantity,
                    amount=line_amount,
                    status="pending",

                    transaction_id=transaction_id,
                    payment_method=payment_method,
                )
                db_sess.add(order)
                created_any = True


            if created_any:

                user_obj.cart_contents = []

            db_sess.commit()


            updated_balance = getattr(user_obj, "wallet_balance", None)
            db_sess.close()
        except Exception:
            updated_balance = None

        return render_template(
            "balance.html",
            title=f"{APP_NAME} > Balance",
            paid_amount=subtotal,
            transaction_id=transaction_id,
            payment_method=payment_method,
            balance_demo=subtotal,
            wallet_balance=updated_balance
        )
    else:
        return make_response(jsonify({"error": "unimplemented"}))


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


@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/api/'):
        return make_response(jsonify({"error": "NotFound"}), 404)

    lc = session.get("lang", "ru")
    msg = translate(lc, "error.page_not_found")
    return render_template("error.html", title="404", error_code=404, message=msg), 404


@app.errorhandler(400)
def bad_request(error):
    if request.path.startswith('/api/'):
        return make_response(jsonify({"error": "Bad Request"}), 400)

    lc = session.get("lang", "ru")
    msg = translate(lc, "error.bad_request")
    return render_template("error.html", title="400", error_code=400, message=msg), 400


@app.errorhandler(403)
def forbidden(error):
    if request.path.startswith('/api/'):
        return make_response(jsonify({"error": "forbidden"}), 403)

    lc = session.get("lang", "ru")
    msg = translate(lc, "error.forbidden")
    return render_template("error.html", title="403", error_code=403, message=msg), 403


def main():
    db_session.global_init("db/store.db")

    api.add_resource(ProductListResource, "/api/product")
    api.add_resource(ProductResource, "/api/product/<int:product_id>")

    app.register_blueprint(chatHandler_bp)
    app.register_blueprint(cartHandler_bp)

    app.run("127.0.0.1", 8080)

if __name__ == "__main__":
    main()