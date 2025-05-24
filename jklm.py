import requests


def create_room(token, name, public=False):
    endpoint = "https://jklm.fun/api/startRoom"
    data = {
        'creatorUserToken': token,
        'isPublic': public,
        'name': name,
        'gameId': 'bombparty'
    }

    try:
        response = requests.post(endpoint, json=data, timeout=5)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

    return response.json()["url"], response.json()["roomCode"]


def identify_server(code):
    endpoint = "https://jklm.fun/api/joinRoom"
    data = {
        'roomCode': code.upper()
    }

    try:
        response = requests.post(endpoint, json=data, timeout=5)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

    return response.json()["url"]
