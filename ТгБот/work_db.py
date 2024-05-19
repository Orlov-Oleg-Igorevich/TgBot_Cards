import sqlalchemy as sq
from sqlalchemy.orm import sessionmaker
import models as md
from datetime import datetime

def connection_db(DBMS, user, password, host, db_name):
    DSN = f'{DBMS}://{user}:{password}@{host}/{db_name}'
    engine = sq.create_engine(DSN)
    Session = sessionmaker(bind=engine)
    session = Session()
    print('Подкючение получено')
    return engine, session

def create_table(engine):
    md.create_table(engine)


def completion(session):
    with open('base_word.txt', 'r', encoding='utf-8') as f:
        date = [md.WordsRusEn(word_rus = i.split('-')[-1].strip(), word_en = i.split('-')[0].strip()) for i in f.readlines()]
    session.add_all(date)
    session.commit()


def add_card(session, user, word, translate):
    pk = session.query(md.WordsRusEn).filter(md.WordsRusEn.word_rus == word
    and md.WordsRusEn.word_en == translate)
    if pk.all():
        pk1, pk2 = pk.all()
        session.add(md.UserWord(id_user = user, word_rus=pk1, word_en=pk2, 
        date_of_addition = datetime.now(), date_of_update = datetime.now()))
    else:
        session.add(md.WordsRusEn(word_rus = word, word_en = translate))
        session.commit()
        session.add(md.UserWord(id_user = user, word_rus= word, word_en=translate, 
        date_of_addition = datetime.now(), date_of_update = datetime.now()))
    session.commit()

def dell_word(session, user, word):
    session.query(md.UserWord).filter((md.UserWord.id_user == user) & (md.UserWord.word_en == word or md.UserWord.word_rus == word)).delete()
    session.commit()

def create_user(session, id, name):
    session.add(md.User(id = id, name = name, last_login_time=datetime.now()))
    for rus, en in session.query(md.WordsRusEn.word_rus,
    md.WordsRusEn.word_en).limit(20).all():
        session.add(md.UserWord(id_user = id, word_rus= rus, word_en=en, 
        date_of_addition = datetime.now(), date_of_update = datetime.now()))
    session.commit()