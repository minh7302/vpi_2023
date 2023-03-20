import requests

form = {
    'username': 'superadmin',
    'password': 'abc123'
}
response = requests.post('http://127.0.0.1:8000/auth/token', data=form)
data = response.json()
print(data)
if 'access_token' in data:
    token = data['access_token']
    headers = {'Authorization': f'bearer {token}'}
    table_name = 'cal_curve_value'
    api_response = requests.get(f'http://127.0.0.1:8000/api/{table_name}', headers=headers).json()
else:
    print('Invalid username or password')

