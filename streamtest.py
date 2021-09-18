import requests

HANDSHAKE = "Lt`cw%Y9sg*bJ_~KZ#;|rbfI)nx[r5"
STREAM_URL = 'http://localhost:61075'

qids = ['1NRBBvNshd-cccFSZGzUe6cqMxsAd9V5P']

def get_token(qid):
    payload = {'handshake': HANDSHAKE, 'qid': qid}
    response = requests.post(STREAM_URL,data=payload).json()
    print(response)