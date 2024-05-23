"""Модуль для работы с API Яндекса"""

import requests

URL = 'https://dictionary.yandex.net/api/v1/dicservice.json/lookup'
TOKEN = 'dict.1.1.20240314T141540Z.2a7491adbf23feab.05ee76e8a5962997854021d9d7068949844daa19'

def translate_word(word, language):
    """Функция возвращает перевод слова по заданному языку"""
    params = {"key":TOKEN, "lang":language, "text":word}
    trans_word = requests.get(URL, params=params, timeout=10).json()
    if trans_word["def"]:
        return trans_word["def"][0]['tr'][0]["text"]
    return None



if __name__ == '__main__':
    WORD_RUS = 'машина'
    print(translate_word(WORD_RUS, "ru-en"))
