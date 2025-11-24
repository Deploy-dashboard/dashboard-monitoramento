import requests

class Client:
    def __init__(self):
        self.base_url = 'http://10.0.10.22:41112/'

    def login(self, username:str, password:str) -> bool:
        self.logged = False

        payload = {'username': username, 'password': password}
        headers = {'Content-Type': 'application/json'}

        url = self.base_url + 'gw/login/auth/login'
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        if response.status_code == 200:
            token = response.json().get('token')

            self.headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }

            self.logged = True

        return self.logged
    
