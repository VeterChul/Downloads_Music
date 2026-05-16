from yandex_music import Client
from json import dump

def on_code(code):
    print(f'Откройте {code.verification_url} и введите код: {code.user_code}')


client = Client()
token = client.device_auth(on_code=on_code)

# Сохраните токен куда-нибудь (переменная окружения, файл, БД),
# чтобы не проходить авторизацию при каждом запуске.
print(f'access_token:  {token.access_token}')
print(f'refresh_token: {token.refresh_token}')
print(f'expires_in:    {token.expires_in}')

print("Сохранение в env.json")
with open("env.json", "w") as file:
    json_env = {
        "access_token":  token.access_token,
        "refresh_token": token.refresh_token, 
        "expires_in":    token.expires_in

    }
    dump(json_env, file) 
client.init()
