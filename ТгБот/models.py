"""Модуль с описанием моделей таблиц и связей между ними"""

import sqlalchemy as sq
from sqlalchemy.orm import declarative_base
from sqlalchemy.schema import ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import ARRAY


Base = declarative_base()

class User(Base):
    """Модель таблицы пользователя"""
    __tablename__ = 'user'

    id = sq.Column(sq.BigInteger, primary_key=True)
    name = sq.Column(sq.String(50))
    current_status = sq.Column(sq.String(50))
    target_word = sq.Column(sq.String(50))
    translate_word = sq.Column(sq.String(50))
    language = sq.Column(sq.String(2))
    memor_word = sq.Column(sq.Integer)

    other_words = sq.Column(ARRAY(sq.String(50)))

    last_login_time = sq.Column(sq.DateTime)


class WordsRusEn(Base):
    """Модель таблицы для пар слов вида (ru-en)"""
    __tablename__ = 'words_rus_en'

    word_rus = sq.Column(sq.String(35), nullable=False, primary_key=True)
    word_en = sq.Column(sq.String(45), nullable=False, primary_key=True)

class UserWord(Base):
    """Модель таблицы, которая реализует связи многие ко многим между таблицами User и WordsRusEn"""
    __tablename__ = 'user_word'

    id = sq.Column(sq.Integer, primary_key=True)
    id_user = sq.Column(sq.BigInteger, sq.ForeignKey('user.id'), nullable=False)
    word_rus = sq.Column(sq.String(35), nullable=False)
    word_en = sq.Column(sq.String(45), nullable=False)
    perc_of_memor = sq.Column(sq.Integer, default=0)
    date_of_addition = sq.Column(sq.DateTime)
    date_of_update = sq.Column(sq.DateTime)

    __table_args__ = (ForeignKeyConstraint([word_rus, word_en],
                                           [WordsRusEn.word_rus, WordsRusEn.word_en]),
                      {})



def create_table(engine):
    """Функция, создающая таблицы в бд"""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print('Таблицы созданы')
