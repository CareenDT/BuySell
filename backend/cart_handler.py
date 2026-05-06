from flask import Blueprint, Response, abort, render_template, stream_with_context, request, jsonify
import json
from data import db_session
from data.users import User
from flask_login import current_user, login_required
from sqlalchemy.orm.attributes import flag_modified
from backend.stream_manager import StreamManager

stream_manager = StreamManager()

cartHandler_bp = Blueprint('cart_bp', __name__)

@cartHandler_bp.route('/cart')
@login_required
def cart_page():
    return render_template('cart.html')

@cartHandler_bp.route('/cart/stream')
@login_required
def cart_stream():
    user = current_user
    user_id = user.id

    if not user:
        return abort(403)
    
    def generate():
        session = db_session.create_session()
        userData = session.get(User, user_id)
        
        if userData and userData.cart_contents:
            yield f"data: {json.dumps({'type': 'initial', 'cart': userData.cart_contents})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'initial', 'cart': []})}\n\n"
        session.close()
        
        queue = stream_manager.subscribe(user_id)
        while True:
            msg = queue.get()
            yield f"data: {json.dumps({'item': msg})}\n\n"
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@cartHandler_bp.route('/cart/add', methods=['POST'])
@login_required
def add_product():
    user = current_user
    user_id = user.id

    session = db_session.create_session()
    user_obj = session.get(User, user_id)

    data = request.get_json()
    product_id = int(data['product_id'])
    quantity_to_add = int(data['quantity'])

    cart = list(user_obj.cart_contents)
    merged_by_product = {}
    for item in cart:
        pid = int(item.get('product_id'))
        qty = int(item.get('quantity', 0))
        merged_by_product[pid] = merged_by_product.get(pid, 0) + qty

    merged_by_product[product_id] = merged_by_product.get(product_id, 0) + quantity_to_add

    user_obj.cart_contents = [{'product_id': pid, 'quantity': qty} for pid, qty in merged_by_product.items()]

    flag_modified(user_obj, 'cart_contents')
    session.commit()

    stream_manager.publish(user_id, {'type': 'add', 'product_id': product_id, 'quantity': quantity_to_add})
    session.close()

    return jsonify({'status': 'added'})

@cartHandler_bp.route('/cart/update', methods=['POST'])
@login_required
def update_cart_item():
    user = current_user
    user_id = user.id

    session = db_session.create_session()
    user_obj = session.get(User, user_id)

    data = request.get_json()
    print(data)
    product_id = int(data['product_id'])
    quantity = int(data['quantity'])

    cart = list(user_obj.cart_contents)
    merged_by_product = {}
    for item in cart:
        pid = int(item.get('product_id'))
        qty = int(item.get('quantity', 0))
        merged_by_product[pid] = merged_by_product.get(pid, 0) + qty

    merged_by_product[product_id] = quantity

    user_obj.cart_contents = [{'product_id': pid, 'quantity': qty} for pid, qty in merged_by_product.items()]

    flag_modified(user_obj, 'cart_contents')
    session.commit()
    session.close()

    stream_manager.publish(user_id, {'type': 'update', 'product_id': product_id})
    return jsonify({'status': 'updated'})

@login_required
@cartHandler_bp.route('/cart/get_contents', methods=['GET'])
def get_cart_contents():
    user = current_user
    user_id = user.id

    session = db_session.create_session()
    user_obj = session.get(User, user_id)
    return jsonify(user_obj.cart_contents)

@cartHandler_bp.route('/cart/remove', methods=['POST'])
@login_required
def remove_cart_item():
    user = current_user
    user_id = user.id
    
    session = db_session.create_session()
    user_obj = session.get(User, user_id)
    
    data = request.get_json()
    product_id = int(data['product_id'])
    
    user_obj.cart_contents = [item for item in user_obj.cart_contents if item['product_id'] != product_id]
    flag_modified(user_obj, 'cart_contents')
    session.commit()
    session.close()
    
    stream_manager.publish(user_id, {'type': 'remove', 'product_id': product_id})
    
    return jsonify({'status': 'removed'})

