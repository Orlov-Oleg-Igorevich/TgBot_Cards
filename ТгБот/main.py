from telebot import types, TeleBot
from yandex import translate_word
import work_db as wb
from telebot.handler_backends import State, StatesGroup
import random
import models as md


token = '7047239962:AAEmpbIxf2RlZLzAb1hvZ2MgNwj4Xrv3PnA'
bot = TeleBot(token)

def show_target(data):
    return f"{data['target_word']} -> {data['translate_word']}"

def show_hint(*lines):
    return '\n'.join(lines)

class Command:
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово🔙'
    NEXT = 'Дальше ⏭'
    WORKOUT = 'Режим тренировки 💪'

class MyStates(StatesGroup):
    target_word = State()
    translate_word = State()
    another_words = State()


###начало диалога, регистрация пользователя
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.reply_to(message, 'Привет 👋')
    sent_msg = bot.send_message(message.chat.id, " Меня зовут Гоша. Я тг бот для изучения английского языка. Давай познакомимся. Как твоё имя?")
    bot.register_next_step_handler(sent_msg, create_user)

def create_user(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard = types.KeyboardButton('/Start_my_training')
    markup.add(keyboard)
    name = message.text
    wb.create_user(session, message.from_user.id, name)
    bot.send_message(message.chat.id, '''Отлично! Твой профиль создан. Теперь ты можете практиковаться в английском языке и расширять свой словарный запас. 
\nТренировки можно проходить в удобном для себя темпе.
\nНа начальном этапе у тебя есть базовый набор, состоящий из 20 слов.
\nНо у тебя есть возможность использовать тренажёр, как конструктор, и собирать свою собственную базу для обучения. Для этого воспрользуйся инструментами:
\n\nдобавить слово ➕,
\nудалить слово 🔙.
\nНу что, начнём ⬇️''', reply_markup=markup)

@bot.message_handler(commands=['Start_my_training'])
def button_message(message):
    bot.send_message(message.chat.id, 'Что надо?', reply_markup=buttons(1))


### Блок для добавления карточки
@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_command(message):
    sent_msg = bot.send_message(message.chat.id, "Какое слово хотите изучить(введите слово на русском языке)?")
    bot.register_next_step_handler(sent_msg, add_verification)

def add_verification(message):
    word = message.text.lower()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton('Хочу доверить перевод слова вам')
    markup.add(item1)
    sent_msg = bot.send_message(message.chat.id,
    f"Введите перевод для слова '{word}'.", reply_markup=markup)
    bot.register_next_step_handler(sent_msg, add, word)

def add(message, word):
    ans = message.text.lower()
    if ans == 'хочу доверить перевод слова вам':
        ans = translate_word(word).lower()
        wb.add_card(session, message.from_user.id, word, ans)
    else:
        wb.add_card(session, message.from_user.id, word, ans)
    bot.send_message(message.chat.id,
    f'Пара слов "{word}-{ans}" была успешно добавлена в ваш словарь', reply_markup=buttons(1))


### блок для удаления карточки
@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def dell_command(message):
    sent_message = bot.send_message(message.chat.id, 'Введите слово, которое хотите удалить')
    bot.register_next_step_handler(sent_message, dell_word)

def dell_word(message):
    ans = message.text.lower()
    wb.dell_word(session, message.from_user.id, ans)
    bot.send_message(message.chat.id,
    f'Слово "{ans}" было успешно удалено из вашего словаря', reply_markup=buttons(1))


## занимаемся дальше
@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_command(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        random_word = random.choice(data['all_words'])
        data['all_words'].remove(random_word)
        target_word = random_word[0]
        translate_word = random_word[1]
        learn_words = data['learned_words'] + data['all_words']
        random.shuffle(learn_words)
        buttoms = [types.KeyboardButton(i[1]) for i in learn_words[:3]]
        buttoms.append(types.KeyboardButton(translate_word))
        random.shuffle(buttoms)
        markup.add(*buttoms[:2], row_width=2)
        markup.add(*buttoms[2:], row_width=2)
        markup.add(*buttons(3))
        greeting = f"Выбери перевод слова: {target_word}"
        bot.send_message(message.chat.id, greeting, reply_markup=markup)
        bot.set_state(message.from_user.id, MyStates.translate_word, message.chat.id)
        data['target_word'] = target_word
        data['translate_word'] = translate_word
        data['another_words'] = learn_words[:3]
        data['learned_words'].append(random_word)


### режим трени
@bot.message_handler(func=lambda message: message.text == Command.WORKOUT)
def workout_command(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    words = []
    for rus, en in session.query(md.UserWord.word_rus, md.UserWord.word_en).filter(md.UserWord.id_user == message.chat.id).order_by(
        md.UserWord.date_of_update.desc()).limit(8).all():
        words.append((rus, en))
    random_word = random.choice(words)
    words.remove(random_word)
    target_word = random_word[0]
    translate_word = random_word[1]
    random.shuffle(words)
    buttoms = [types.KeyboardButton(i[1]) for i in words[:3]]
    buttoms.append(translate_word)
    markup.add(*buttoms[:2], row_width=2)
    markup.add(*buttoms[2:], row_width=2)
    markup.add(*buttons(3))
    greeting = f"Выбери перевод слова: {target_word}"
    bot.send_message(message.chat.id, greeting, reply_markup=markup)
    bot.set_state(message.from_user.id, MyStates.translate_word, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['target_word'] = target_word
        data['translate_word'] = translate_word
        data['another_words'] = words[:3]
        data['all_words'] = words
        data['learned_words'] = [random_word]

@bot.message_handler(func=lambda message: True, content_types=['text'])
def message_reply(message):
    text = message.text
    markup = types.ReplyKeyboardMarkup(row_width=2)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        translate_word = data['translate_word']
        if text == translate_word:
            hint = show_target(data)
            hint_text = ["Отлично!❤", hint]
            markup = buttons(4)
            hint = show_hint(*hint_text)
        else:
            for btn in range(len(data['another_words'])):
                if data['another_words'][btn][1] == text:
                    data['another_words'][btn] = (data['another_words'][btn][0], text + '❌')
                    break
            buttoms = []
            buttoms = [types.KeyboardButton(i[1]) for i in data['another_words']]
            buttoms.append(types.KeyboardButton(translate_word))
            markup.add(*buttoms)
            hint = show_hint("Допущена ошибка!", f"Попробуй ещё раз вспомнить слово {data['target_word']}")
            data['all_words'].append(data['learned_words'].pop(-1))

    bot.send_message(message.chat.id, hint, reply_markup=markup)


    

def buttons(flag):
    if flag == 1:
        buttons = []
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        next_btn = types.KeyboardButton(Command.NEXT)
        add_word_btn = types.KeyboardButton(Command.ADD_WORD)
        delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
        wrk = types.KeyboardButton(Command.WORKOUT)
        buttons.extend([next_btn, add_word_btn, delete_word_btn, wrk])
        markup.add(*buttons)
        return markup
    if flag == 2:
        buttons = []
        next_btn = types.KeyboardButton(Command.NEXT)
        add_word_btn = types.KeyboardButton(Command.ADD_WORD)
        delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
        wrk = types.KeyboardButton(Command.WORKOUT)
        buttons.extend([next_btn, add_word_btn, delete_word_btn, wrk])
        return buttons
    if flag == 3:
        buttons = []
        add_word_btn = types.KeyboardButton(Command.ADD_WORD)
        delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
        next_btn = types.KeyboardButton(Command.NEXT)
        buttons.extend([next_btn, add_word_btn, delete_word_btn])
        return buttons
    if flag == 4:
        buttons = []
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        next_btn = types.KeyboardButton(Command.NEXT)
        add_word_btn = types.KeyboardButton(Command.ADD_WORD)
        delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
        buttons.extend([next_btn, add_word_btn, delete_word_btn])
        markup.add(*buttons)
        return markup

if __name__ == '__main__':
    print('Bot is running!')
    DBMS = 'postgresql'
    user = 'postgres'
    password = 'izvara32'
    host = 'localhost:5432'
    db_name = 'englishcard'
    global session
    engine, session = wb.connection_db(DBMS, user, password, host, db_name)
    wb.create_table(engine)
    wb.completion(session)
    bot.polling()