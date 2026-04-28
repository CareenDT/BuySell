from flask import Blueprint, Response, abort, stream_with_context, request, jsonify
import json
import datetime
from data import db_session
from data.chats import Chat
from flask_login import current_user, login_required
from sqlalchemy.orm.attributes import flag_modified
from backend.ChatStreamManager import stream_manager

sse_bp = Blueprint('sse', __name__)

@sse_bp.route('/chats', methods=['POST'])
@login_required
def create_chat():
    data = request.get_json()
    session = db_session.create_session()
    chat = Chat(
        owner=data['owner'],
        recipient=data['recipient'],
        contents=[]
    )
    session.add(chat)
    session.commit()
    return jsonify({'chat_id': chat.id})

@sse_bp.route('/chat/<int:chat_id>/stream')
@login_required
def chat_stream(chat_id):
    user = current_user

    if not user:
        return abort(403)
    
    def generate():
        session = db_session.create_session()
        chat = session.get(Chat, chat_id)
        
        if user.id not in [chat.owner, chat.recipient]:
            yield f"data: {json.dumps({'error': 'Access denied'})}\n\n"
            return
        
        if chat and chat.contents:
            for msg in chat.contents:
                yield f"data: {json.dumps(msg)}\n\n"
        session.close()
        
        queue = stream_manager.subscribe(chat_id)
        while True:
            msg = queue.get()
            yield f"data: {json.dumps(msg)}\n\n"
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@sse_bp.route('/chat/<int:chat_id>/send', methods=['POST'])
def send_message(chat_id):
    user = current_user
    if not user:
        return abort(403)
    
    session = db_session.create_session()
    chat = session.get(Chat, chat_id)
    
    if str(user) not in [str(chat.owner), str(chat.recipient)]:
        session.close()
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    new_message = {
        'text': data['text'],
        'timestamp': datetime.datetime.now().isoformat(),
        'sender': data['sender']
    }
    
    chat.contents.append(new_message)
    flag_modified(chat, 'contents')
    session.commit()
    
    stream_manager.publish(chat_id, new_message)
    session.close()
    
    return jsonify({'status': 'sent'})