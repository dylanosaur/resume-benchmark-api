from flask import jsonify, request, session
import jwt
import requests
from config import SUPABASE_JWT_SECRET
from models import Users, db

def get_user_info():
    print(request.headers)
    # Extract the token from the cookie
    if 'Auth' in request.headers:
        token = request.headers['Auth']
        print(token)
        # Decode the token to get the user data
        if token:
            print('decoding')
            try:
                decoded_token = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"], audience='authenticated')
                print('token', decoded_token)
                user_id = decoded_token['sub']
                email = decoded_token['email']
                print('user and email', user_id, email)
                # Attach the token as a header labeled "Auth"
                headers = {'Auth': token}
                matching_user = db.session.query(Users).filter(Users.supabase_id==user_id).first()
                if not matching_user:
                    new_user = Users(email=email, supabase_id=user_id)
                    db.session.add(new_user)
                    db.session.commit()

                matched_user = {'user_id': user_id, 'email': email}
                session['user'] = matched_user
                print('set session user', session['user'])
                return jsonify({'user_id': user_id, 'email': email}), 200, headers
            except Exception as ex:
                print(ex)
        else:
            return jsonify({'message': 'Unauthorized access'}), 401