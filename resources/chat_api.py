from flask import Flask, jsonify
import flask
from flask_restful import Api, Resource, abort, reqparse

from data import db_session
from data.chats import Chat

CODEC_MAP = {"id", "owner", "created_date", "contents"}

parser = reqparse.RequestParser()

parser.add_argument("owner")

def abort_if_chat_not_found(id):
    session = db_session.create_session()
    chat = session.query(Chat).get(id)
    if not chat:
        abort(404, message = flask.make_response(flask.jsonify({"error": f"Chat, indexed: {id} , are not found"}), 404))

class ChatResource(Resource):
    def get(self, chat_id):
        abort_if_chat_not_found(chat_id)

        session = db_session.create_session()
        chat = session.get(Chat, chat_id)

        return jsonify({'chat': chat.to_dict(
            only=CODEC_MAP)})
    
    def update(self, chat_id):
        abort_if_chat_not_found(chat_id)

        session = db_session.create_session()
        chat = session.get(Chat, chat_id)

        session.delete(chat)
        session.commit()

    def delete(self, chat_id):
        abort_if_chat_not_found(chat_id)

        session = db_session.create_session()
        chat = session.get(Chat, chat_id)

        session.delete(chat)
        session.commit()
        return jsonify({'success': 'OK'})
    
class ChatListResource(Resource):
    def get(self):
        session = db_session.create_session()

        chats = session.query(Chat).all()
        return jsonify(
            {
                "chats": [x.to_dict(only=CODEC_MAP) for x in chats]
            }
        )
    
    def post(self):
        if not flask.request.json:
            return flask.make_response(flask.jsonify({'error': 'Empty request'}), 400)
        elif not all(key in flask.request.json for key in ["owner", "recipient"]):
            return flask.make_response(flask.jsonify({'error': 'Bad request'}), 400)
        
        session = db_session.create_session()

        chat = Chat(
            owner = flask.request.json.get("owner", 0),
            recipient = flask.request.json.get("recipient", 0),
        )
        session.add(chat)
        session.commit()
        return jsonify({'id': chat.id})