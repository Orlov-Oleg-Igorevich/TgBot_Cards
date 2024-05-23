"""Главный программный модуль"""

import re
import random

from telebot import types, TeleBot, custom_filters

from states import PgStateStorage, UserStates
from yandex import translate_word
from connection_file import DBMS, USER, PASSWORD, HOST, DB_NAME, TOKEN
import work_db as db




engine, session = db.connection_db(DBMS, USER, PASSWORD, HOST, DB_NAME)
state_storage = PgStateStorage(session)
bot = TeleBot(TOKEN, state_storage=state_storage)

def show_target(word_ru, word_en):
    """Принимает два слова и возвращает строку с их красивым отображением"""
    return f"{word_ru} -> {word_en}"

def show_hint(*lines):
    """Функция принимает список из строк и возвращает одну 
    строку с переносами для более красивого отображения"""
    return '\n'.join(lines)

class Command:
    """Атрибуты класса - это команды, которые может ввести пользователь"""
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово🔙'
    NEXT = 'Дальше ⏭'
    WORKOUT = 'Режим тренировки 💪'
    CANCEL = "/cancel"


###начало диалога, регистрация пользователя
@bot.message_handler(commands=['start'])
def start_message(message):
    """Функция-обработчик команды '/start'. Приветствует пользователя и запрашивает у него имя."""
    bot.reply_to(message, 'Привет 👋')
    bot.send_message(message.chat.id,
    "Меня зовут Гоша. Я тг бот для изучения английского языка. Давай познакомимся. Как твоё имя?")
    db.create_or_change_user(session, message.from_user.id, {})
    bot.set_state(message.from_user.id, UserStates.enter_a_name, message.chat.id)


@bot.message_handler(state=UserStates.enter_a_name)
def create_user(message):
    """Функция принимает имя пользователя, заносит его в бд и высылает приветственное сообщение."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(*buttons(5))
    name = message.text
    if len(name) <= 50:
        db.create_or_change_user(session, message.from_user.id, {'name': name})
        bot.send_message(message.chat.id, f'''{name}, отлично!
Профиль создан. Теперь ты можешь практиковаться в английском языке и расширять свой словарный запас. 
Тренировки можно проходить в удобном для себя темпе.
На начальном этапе у тебя есть базовый набор, состоящий из 20 слов.
Но тренажёр - это конструктор, поэтому необходимо собрать свою собственную базу для обучения. Для этого воспрользуйся инструментами:
\nдобавить слово ➕,
\nудалить слово 🔙.
\nНу что, начнём ⬇️''', reply_markup=markup)
        bot.set_state(message.from_user.id, UserStates.select_a_command)
    else:
        bot.send_message(message.chat_id, '''Ой-ой. Я не могу запомнить такое длинное имя.
Попробуй его немного сократить, а затем отправь ещё раз)''')

@bot.message_handler(commands=['cancel'])
def create_again(message):
    """Функция-обработчик команды '/cancel'. Возвращает пользователя к этапу регистрации."""
    bot.send_message(message.chat.id, ' Ну что же, начнём заново. Как тебя зовут?')
    bot.set_state(message.from_user.id, UserStates.enter_a_name)


### блок для добавления карточки
@bot.message_handler(state=UserStates.select_a_command,
func=lambda message: message.text == Command.ADD_WORD)
def add_command(message):
    """Функция-обработчик команды 'Добавить слово ➕'.
    Запршивает у пользователя слово на добавление в бд."""
    bot.send_message(message.chat.id, "Какое слово хотите изучить?")
    bot.set_state(message.from_user.id, UserStates.enter_a_new_word)

@bot.message_handler(state=UserStates.enter_a_new_word)
def add_verification(message):
    """Принимает новое слово на добавление в бд. Запрашивает перевод."""
    word = message.text.lower()
    if re.match(r"^[а-яА-Я]*$", word) or re.match(r"^[a-zA-Z]*$", word):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton('Хочу доверить перевод слова вам')
        markup.add(item1)
        bot.send_message(message.chat.id,
        f"Введите перевод для слова '{word}'.", reply_markup=markup)
        bot.set_state(message.from_user.id, UserStates.enter_a_translation)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['target_word'] = word
            data['language'] = 'ru' if re.match(r'^[а-яА-Я]', word) else 'en'

    else:
        bot.send_message(message.chat.id,
        f'''Извините, но я не могу распознать слово '{word}'. Пожалуйста, проверьте его на корректность. 
При вводе можно использовать только буквы английского или русского алфавитов без каких-либо специальных символов''', reply_markup=buttons(2))
        bot.set_state(message.from_user.id, UserStates.select_a_command)

@bot.message_handler(state=UserStates.enter_a_translation)
def add(message):
    """Функция принимает перевод слова и заносит пару слов в бд"""
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        language = data['language']
        word = data['target_word']
    ans = message.text.lower()
    if ans == 'хочу доверить перевод слова вам':
        ans = translate_word(word, 'ru-en') if language == 'ru' else translate_word(word, 'en-ru')
        if ans is None:
            bot.send_message(message.chat.id,
    f'''Извините, но не было найдено перевода для слова: "{word}".
Проверте, что оно было введено корректно, и попробуйте ещё раз. Вы также можете ввести перевод самостоятельно''',
    reply_markup=buttons(2))
        else:
            if language != 'ru':
                word, ans = ans, word
            status = db.add_card(session, message.from_user.id, word, ans)
            if status:
                rows = db.count_rows(session, message.from_user.id)
                bot.send_message(message.chat.id,
        f'''Пара слов "{word}-{ans}" была успешно добавлена в ваш словарь.
        Слов в вашем словаре: {rows}''', reply_markup=buttons(2))
            else:
                bot.send_message(message.chat.id,
        f'Пара слов "{word}-{ans}" уже есть в вашем словаре', reply_markup=buttons(2))
    else:
        if re.match(r"^[а-яА-Я]*$", ans) or re.fullmatch(r"^[a-zA-Z]*$", ans):
            lan = 'ru' if re.match(r'^[а-яА-Я]', ans) else 'en'
            if lan != language:
                if language != 'ru':
                    word, ans = ans, word
                status = db.add_card(session, message.from_user.id, word, ans)
                if status:
                    rows = db.count_rows(session, message.from_user.id)
                    bot.send_message(message.chat.id,
        f'''Пара слов "{word}-{ans}" была успешно добавлена в ваш словарь.
        Слов в вашем словаре: {rows}''', reply_markup=buttons(2))
                else:
                    bot.send_message(message.chat.id,
        f'Пара слов "{word}-{ans}" уже есть в вашем словаре', reply_markup=buttons(2))
            else:
                bot.send_message(message.chat.id,
            f'''Извините, но слова из пары "{word}-{ans}" введены на одинаковых языках. 
Добавление такой пары слов в ваш словарь невозможно.
Пожалуйста, проверьте корректность введённых данных и попробуйде проделать операцию ещё раз''', 
                reply_markup=buttons(2))
        else:
            bot.send_message(message.chat.id,
            f'''Извините, но я не могу распознать слово '{ans}'. Пожалуйста, проверьте его на корректность.
При вводе можно использовать только буквы английского или русского алфавитов без каких-либо специальных символов''',
            reply_markup=buttons(2))
    bot.set_state(message.from_user.id, UserStates.select_a_command)


### блок для удаления карточки
@bot.message_handler(state=UserStates.select_a_command,
func=lambda message: message.text == Command.DELETE_WORD)
def dell_command(message):
    """Функция-обработчик команды 'Удалить слово🔙'. Запрашивает у пользователя слово на удаление."""
    bot.send_message(message.chat.id,
    'Введите слово, которое хотите удалить(на русском или английском)')
    bot.set_state(message.from_user.id, UserStates.enter_dell_word)

@bot.message_handler(state=UserStates.enter_dell_word)
def dell_word(message):
    """Функция принимает слово и удаляет его из бд"""
    ans = message.text.lower()
    res = db.dell_word(session, message.from_user.id, ans)
    if res:
        bot.send_message(message.chat.id,
        f'Слово "{ans}" было успешно удалено из вашего словаря', reply_markup=buttons(2))
    else:
        bot.send_message(message.chat.id,
        f'Слово "{ans}" не было найдено в вашем словаре', reply_markup=buttons(2))
    bot.set_state(message.from_user.id, UserStates.select_a_command)

### режим тренировки
@bot.message_handler(state=UserStates.select_a_command,
func=lambda message: message.text in {Command.WORKOUT, Command.NEXT})
def workout_command(message):
    """Функция-обработчик команд 'Дальше ⏭' и 'Режим тренировки 💪'.
    Берёт из бд 4 слова и выдаёт и выдаёт их пользователю."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    words = db.get_set_words(session, message.from_user.id)
    if words:
        random_word = random.choice(words)
        target_word = random_word[0]
        translate_word = random_word[1]
        memor_word = random_word[2]
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['target_word'] = target_word
            data['translate_word'] = translate_word
            data['memor_word'] = memor_word
            data['other_words'] = [i[1] for i in words]
        random.shuffle(words)
        buttoms = [types.KeyboardButton(i[1]) for i in words]
        markup.add(*buttoms[:2], row_width=2)
        markup.add(*buttoms[2:], row_width=2)
        markup.add(*buttons(3))
        greeting = f"Выбери перевод слова: {target_word}"
        bot.send_message(message.chat.id, greeting, reply_markup=markup)
        bot.set_state(message.from_user.id, UserStates.choose_a_translation, message.chat.id)
    else:
        bot.send_message(message.chat.id, f'''Извините, но для режима тренировки в вашем словаре должно быть не менее 4 слов.
Советуем воспользоваться командой "{Command.ADD_WORD}", чтобы добавить слова.''', reply_markup=markup)
        bot.set_state(message.from_user.id, UserStates.select_a_command, message.chat.id)

@bot.message_handler(state=UserStates.choose_a_translation,
func=lambda message: True, content_types=['text'])
def message_reply(message):
    """Функция принимает ответ от пользователя и выводит результат(правильно/неправильно)"""
    text = message.text
    markup = types.ReplyKeyboardMarkup(row_width=2)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        target_word = data['target_word']
        translate_word = data['translate_word']
        other_words = data['other_words']
        memor_word = data['memor_word']
    if text == translate_word:
        hint = show_target(target_word, translate_word)
        hint_text = ["Отлично!❤", hint]
        markup = buttons(4)
        hint = show_hint(*hint_text)
        if memor_word < 100:
            memor_word += 1
        db.save_memor(session, message.from_user.id, memor_word, translate_word)
        bot.set_state(message.from_user.id, UserStates.select_a_command, message.chat.id)
    else:
        for i, word in enumerate(other_words):
            if word == text:
                other_words[i] = text + '❌'
                break
        buttoms = []
        buttoms = [types.KeyboardButton(i) for i in other_words]
        markup.add(*buttoms)
        hint = show_hint("Допущена ошибка!",
        f"Попробуй ещё раз вспомнить слово {data['target_word']}")
        if memor_word > 0:
            memor_word -= 1
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['memor_word'] = memor_word
            data['other_words'] = other_words
    bot.send_message(message.chat.id, hint, reply_markup=markup)

bot.add_custom_filter(custom_filters.StateFilter(bot))


def buttons(flag):
    """Функция, генерирующая тг клавиатуру"""
    if flag == 1:
        but = []
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        next_btn = types.KeyboardButton(Command.NEXT)
        add_word_btn = types.KeyboardButton(Command.ADD_WORD)
        delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
        wrk = types.KeyboardButton(Command.WORKOUT)
        but.extend([next_btn, add_word_btn, delete_word_btn, wrk])
        markup.add(*but)
        return markup
    if flag == 2:
        but = []
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        add_word_btn = types.KeyboardButton(Command.ADD_WORD)
        delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
        wrk = types.KeyboardButton(Command.WORKOUT)
        but.extend([add_word_btn, delete_word_btn, wrk])
        markup.add(*but)
        return markup
    if flag == 3:
        but = []
        add_word_btn = types.KeyboardButton(Command.ADD_WORD)
        delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
        next_btn = types.KeyboardButton(Command.NEXT)
        but.extend([next_btn, add_word_btn, delete_word_btn])
        return but
    if flag == 4:
        but = []
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        next_btn = types.KeyboardButton(Command.NEXT)
        add_word_btn = types.KeyboardButton(Command.ADD_WORD)
        delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
        but.extend([next_btn, add_word_btn, delete_word_btn])
        markup.add(*but)
        return markup
    but = []
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
    wrk = types.KeyboardButton(Command.WORKOUT)
    canc = types.KeyboardButton(Command.CANCEL)
    but.extend([add_word_btn, delete_word_btn, wrk, canc])
    return but

if __name__ == '__main__':
    print('Bot is running!')
    db.create_table(engine)
    db.completion(session)
    bot.polling()
