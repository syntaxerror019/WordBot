import requests

class Discord:
    def __init__(self, url):
        self.url = url
        
    def send_message(self, message, name="User"):
        data = {
            "content": message,
            "username": name
        }

        requests.post(self.url, json=data)
