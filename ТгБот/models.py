import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.schema import ForeignKeyConstraint


Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = sq.Column(sq.Integer, primary_key=True)
    name = sq.Column(sq.String(50))
    last_login_time = sq.Column(sq.DateTime)

"""class WordsRus(Base):
    __tablename__ = 'word_rus'

    id = sq.Column(sq.Integer, primary_key=True)
    word = sq.Column(sq.String(35), nullable=False)

class WordsEn(Base):
    __tablename__ = 'word_en'

    id = sq.Column(sq.Integer, primary_key=True)
    word = sq.Column(sq.String(45))"""

class WordsRusEn(Base):
    __tablename__ = 'words_rus_en'

    word_rus = sq.Column(sq.String(35), nullable=False, primary_key=True)
    word_en = sq.Column(sq.String(45), nullable=False, primary_key=True)

    """rus = relationship(WordsRus, backref='word1')
    en = relationship(WordsEn, backref='word2')"""

class UserWord(Base):
    __tablename__ = 'user_word'

    id = sq.Column(sq.Integer, primary_key=True)
    id_user = sq.Column(sq.Integer, sq.ForeignKey('user.id'), nullable=False)
    word_rus = sq.Column(sq.String(35), nullable=False)
    word_en = sq.Column(sq.String(45), nullable=False)
    perc_of_memor = sq.Column(sq.Integer, default=0)
    date_of_addition = sq.Column(sq.DateTime)
    date_of_update = sq.Column(sq.DateTime)

    __table_args__ = (ForeignKeyConstraint([word_rus, word_en],
                                           [WordsRusEn.word_rus, WordsRusEn.word_en]),
                      {})



def create_table(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print('Таблицы созданы')
