from flask import Flask, jsonify
import flask
from flask_restful import Api, Resource, abort, reqparse

from data import db_session
from data.products import Products

CODEC_MAP = {"id", "owner", "name", "description", "pricing", "image", "created_date", "modified_date"}

parser = reqparse.RequestParser()

parser.add_argument("name")
parser.add_argument("description")
parser.add_argument("owner")
parser.add_argument("pricing")
parser.add_argument("image")

def abort_if_product_not_found(id):
    session = db_session.create_session()
    product = session.query(Products).get(id)
    if not product:
        abort(404, message = flask.make_response(flask.jsonify({"error": f"Products, indexed: {id} , are not found"}), 404))

class ProductResource(Resource):
    def get(self, product_id):
        abort_if_product_not_found(product_id)

        session = db_session.create_session()
        product = session.get(Products, product_id)
        
        result = jsonify({'product': product.to_dict(only=CODEC_MAP)})

        session.close()

        return result
    
    def update(self, product_id):
        abort_if_product_not_found(product_id)

        session = db_session.create_session()
        product = session.get(Products, product_id)

        session.delete(product)
        session.commit()

        session.close()

    def delete(self, product_id):
        if not flask.request.json:
            return flask.make_response(flask.jsonify({'error': 'Empty request'}), 400)
        elif not all(key in flask.request.json for key in ["owner", "current_user_id"]):
            return flask.make_response(flask.jsonify({'error': 'Bad request'}), 400)

        session = db_session.create_session()
        product = session.get(Products, product_id)

        data = {
            'owner': flask.request.json.get("owner", 0),
            'product_id': product.id,
            'current_user_id': flask.request.json.get("current_user_id", None),
        }

        if data["owner"] != data["current_user_id"]:
            return flask.make_response(flask.jsonify({'error': 'You are not the owner of this product'}), 403)

        session.delete(product)
        session.commit()

        session.close()

        return jsonify({'success': 'OK'})
    
class ProductListResource(Resource):
    def get(self):
        session = db_session.create_session()

        products = session.query(Products).all()

        result = jsonify({"products": [x.to_dict(only=CODEC_MAP) for x in products]})
        session.close()
        return result
    
    def post(self):
        if not flask.request.json:
            return flask.make_response(flask.jsonify({'error': 'Empty request'}), 400)
        elif not all(key in flask.request.json for key in ["owner", "pricing"]):
            return flask.make_response(flask.jsonify({'error': 'Bad request'}), 400)
        
        session = db_session.create_session()

        product = Products(
            owner = flask.request.json.get("owner", 0),
            name = flask.request.json.get("name", None),
            description = flask.request.json.get("description", None),
            pricing = flask.request.json.get("pricing", 0),
            image = flask.request.json.get("image", None)
        )
        session.add(product)

        result = jsonify({'id': product.id})

        session.commit()
        session.close()
        
        return result
