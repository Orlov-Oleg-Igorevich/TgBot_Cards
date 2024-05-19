import requests

url = 'https://dictionary.yandex.net/api/v1/dicservice.json/lookup'
token = 'dict.1.1.20240314T141540Z.2a7491adbf23feab.05ee76e8a5962997854021d9d7068949844daa19'


def translate_word(word):
    params = {"key":token, "lang":"ru-en", "text":word}
    trans_word = requests.get(url, params=params).json()
    print(trans_word)
    return trans_word["def"][0]['tr'][0]["text"]


if __name__ == '__main__':
    word = 'машина'
    assert translate_word(word) == 'car'