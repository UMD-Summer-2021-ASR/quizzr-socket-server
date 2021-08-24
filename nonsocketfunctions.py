import random
from firebase_admin import auth
import requests


def lobbycode_generator(size=6, chars='ABCDEFGHIJKLMNPQRSTUVWXYZ123456789'):
    return ''.join(random.choice(chars) for _ in range(size))


usernames = {}


def get_user(authtoken):
    decoded_token = auth.verify_id_token(authtoken)
    uid = decoded_token['uid']
    return {'uid': uid, 'username': usernames[uid]}


def cache_user(authtoken):
    decoded_token = auth.verify_id_token(authtoken)
    url = "http://localhost:5000/profile"
    header = {'Authorization': authtoken}
    uid = decoded_token['uid']
    profile = requests.get(url, headers=header).json()
    usernames[uid] = profile['username']