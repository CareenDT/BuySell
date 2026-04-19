import datetime

from flask import Flask, jsonify
import flask
from flask_restful import Api, Resource, abort, reqparse
from sqlalchemy.orm.attributes import flag_modified

from data import db_session
from data.chats import Chat

CODEC_MAP = {"id", "owner", "created_date", "contents", "recipient"}

parser = reqparse.RequestParser()

parser.add_argument("owner")
parser.add_argument("recipient")
parser.add_argument("owner")
parser.add_argument("message")

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
    
    def patch(self, chat_id):
        abort_if_chat_not_found(chat_id)
        
        if not flask.request.json:
            return flask.make_response(flask.jsonify({'error': 'Empty request'}), 400)
        elif (not flask.request.json.get("message")) or not all(key in flask.request.json["message"] for key in ["text", "sender"]):
            return flask.make_response(flask.jsonify({'error': 'Bad request'}), 400)

        session = db_session.create_session()
        chat = session.get(Chat, chat_id)

        new_message_obj = {
            'text': flask.request.json['message'].get("text", "???"),
            'timestamp': datetime.datetime.now().isoformat(),
            'sender': flask.request.json['message'].get('sender', 'user')
        }

        chat.contents.append(new_message_obj)
        print(chat.contents)

        setattr(chat, "contents", chat.contents)

        flag_modified(chat, 'contents')

        session.commit()

        return jsonify({'success': 'OK', 'id': chat.id, 'contents': chat.contents})

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