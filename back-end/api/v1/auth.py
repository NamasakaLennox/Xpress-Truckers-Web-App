#!/usr/bin/python3
"""
Defines requests for the drivers route
"""
from api.v1.views import app_views
from flask import jsonify, request, make_response
from functools import wraps
from hashlib import md5
from models import storage
from models.user import User
import datetime
import jwt

SECRET_KEY = 'thisissecret'


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'message' : 'Token is missing!'}), 401

        data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        users = storage.all(User).values()
        current_user = None
        for user in users:
            if user.id == data['id']:
                current_user = user

        if not current_user:
            return jsonify({'message' : 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated

@app_views.route('/login', strict_slashes=False, methods=['POST'])
def login():
    # auth = request.authorization

    # if not auth or not auth.username or not auth.password:
    #     return (make_response(
    #         'Could not verify', 401,
    #         {'WWW-Authenticate' : 'Basic realm="Login required!"'}))

    body = request.get_json()
    all_users = storage.all(User).values()
    user = None

    for item in all_users:
        if item.email == body.get("email"):
            user = item
            break

    if not user:
        return (make_response(jsonify({"error": "Invalid Username"}), 401,
            {'WWW-Authenticate' : 'Basic realm="Login required!"'}))

    print(user.password, body.get("password"))
    if user.check_password(body.get("password")):
        token = jwt.encode(
            {'id' : user.id,
             'exp' : datetime.datetime.utcnow() + datetime.timedelta(hours=24)
             }, SECRET_KEY, algorithm='HS256')

        response = jsonify({'token' : token,
                            "user": {
                                     "id": user.id,
                                     "first_name": user.first_name,
                                     "last_name": user.last_name,
                                     "email": user.email,
                                     "role": user.role,
                                     }})

        return  response, 200

    return (make_response(
        'Invalid Password', 401,
        {'WWW-Authenticate' : 'Basic realm="Login required!"'}))
