import datetime

from flask import Flask, render_template, request, url_for
from flask_restful import Api
from requests import get, post
from data import db_session
from data import __all_models
from resources.product_api import ProductListResource, ProductResource

app = Flask(__name__)
api = Api(app)

@app.route("/index")
@app.route("/")
def index():
    response: dict = get(f"http://127.0.0.1:8080/api/product").json()
    return render_template("index.html", title="BuySellTemplate", products = response["products"])

@app.route("/product_list")
def products():
    response: dict = get(f"http://127.0.0.1:8080/api/product").json()
    return render_template("products.html", title="BuySellTemplate > Products", products = response["products"])

def main():
    db_session.global_init("db/store.db")

    api.add_resource(ProductListResource, "/api/product")
    api.add_resource(ProductResource, "/api/product/<int:product_id>")

    app.run("127.0.0.1", 8080)

if __name__ == "__main__":
    main()
