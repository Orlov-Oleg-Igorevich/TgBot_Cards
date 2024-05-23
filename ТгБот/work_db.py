"""Модуль по работе с бд"""

from datetime import datetime
import sqlalchemy as sq
from sqlalchemy.orm import sessionmaker

import models as md


def connection_db(dbms, user, password, host, db_name):
    """Установка соединения с бд"""
    dsn = f'{dbms}://{user}:{password}@{host}/{db_name}'
    engine = sq.create_engine(dsn)
    Session = sessionmaker(bind=engine)
    session = Session()
    print('Подкючение получено')
    return engine, session

def create_table(engine):
    """Вызов функции по созданию таблиц"""
    md.create_table(engine)


def completion(session):
    """Добавление пользователю базового набора слов"""
    with open('base_word.txt', 'r', encoding='utf-8') as f:
        date = [md.WordsRusEn(word_rus = i.split('-')[-1].strip(),
                word_en = i.split('-')[0].strip()) for i in f.readlines()]
    session.add_all(date)
    session.commit()


def add_card(session, user, word, translate):
    """Добавление нового слова пользователю"""
    have = session.query(md.UserWord).filter(md.UserWord.id_user == user,
            md.UserWord.word_rus==word, md.UserWord.word_en==translate).first()
    if have:
        return None
    pk = session.query(md.WordsRusEn).get((word, translate))
    if pk:
        pk1, pk2 = pk.all()
        session.add(md.UserWord(id_user = user, word_rus=pk1, word_en=pk2,
        date_of_addition = datetime.now(), date_of_update = datetime.now()))
    else:
        session.add(md.WordsRusEn(word_rus = word, word_en = translate))
        session.commit()
        session.add(md.UserWord(id_user = user, word_rus= word, word_en=translate,
        date_of_addition = datetime.now(), date_of_update = datetime.now()))
    session.commit()
    return True

def dell_word(session, user, word):
    "Удаление слова из словаря пользователя"
    subq = session.query(md.UserWord).filter((md.UserWord.id_user == user) &
    ((md.UserWord.word_en == word) | (md.UserWord.word_rus == word)))
    if subq.first():
        subq.delete()
        session.commit()
        return True
    return None

def create_or_change_user(session, user_id, data):
    """Создание и изменение данных пользователя"""
    subq = session.query(md.User).get(user_id)
    if subq is None:
        session.add(md.User(id = user_id, last_login_time=datetime.now()))
        for rus, en in session.query(md.WordsRusEn.word_rus,
        md.WordsRusEn.word_en).limit(20).all():
            session.add(md.UserWord(id_user = user_id, word_rus= rus, word_en=en,
            date_of_addition = datetime.now(), date_of_update = datetime.now()))
    else:
        session.query(md.User).filter(md.User.id == user_id).update(data)
    session.commit()


def get_state(session, user_id):
    """Возвращает состояние пользователя"""
    state = session.query(md.User).get(user_id)
    return state

def set_state(session, user_id, data):
    """Изменяет состояние пользователя"""
    session.query(md.User).filter(md.User.id == user_id).update(data)
    session.commit()

def clear_state(session, user_id):
    """Очищает состояние пользователя"""
    session.query(md.User).filter(md.User.id == user_id).update({'current_status': None})

def get_set_words(session, user_id):
    """Возвращает набор из 4-х слов"""
    words = []
    quer = session.query(md.UserWord.word_rus, md.UserWord.word_en,
    md.UserWord.perc_of_memor).filter(md.UserWord.id_user ==
    user_id).order_by(md.UserWord.perc_of_memor,
    md.UserWord.date_of_update).limit(4).all()
    if len(quer) >= 4:
        for rus, en, proc in quer:
            words.append((rus, en, proc))
        return words
    return None

def save_memor(session, user_id, memor, translate_word):
    """Изменяет процент запоминания слова"""
    session.query(md.UserWord).filter((md.UserWord.id_user == user_id) &
    (md.UserWord.word_en == translate_word)).update({'perc_of_memor': memor,
                                            'date_of_update': datetime.now()})

def count_rows(session, user_id):
    """Возвращает количество изучаемых пользователем слов"""
    return session.query(md.UserWord).filter(md.UserWord.id_user == user_id).count()
