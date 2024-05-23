"""Модуль, с классами состояний"""

from sqlalchemy.inspection import inspect
from telebot.handler_backends import State, StatesGroup
from telebot.storage.base_storage import StateContext, StateStorageBase

import work_db as db


class PgStateStorage(StateStorageBase):
    """Ксласс для работы с состоянием пользователя"""

    def __init__(self, session):
        super().__init__()
        self.session = session

    def get_state(self, chat_id, user_id):
        state = db.get_state(self.session, user_id)
        if state is None:
            return None
        return state.current_status

    def set_state(self, chat_id, user_id, state):
        if hasattr(state, "name"):
            state = state.name
        db.set_state(self.session, user_id, {'current_status': state})
        return True

    def get_interactive_data(self, chat_id, user_id):
        return StateContext(self, chat_id, user_id)

    def set_data(self, chat_id, user_id, key, value):
        """
        Set data for a user in a particular chat.
        """
        if db.get_state(self.session, user_id) is None:
            return False

        db.create_or_change_user(self.session, user_id, value)
        return True

    def get_data(self, chat_id, user_id):
        """
        Get data for a user in a particular chat.
        """
        full_state = db.get_state(self.session, user_id)
        if full_state:
            return {c.key: getattr(full_state, c.key)
                    for c in inspect(full_state).mapper.column_attrs}

        return {}

    def delete_state(self, chat_id, user_id):
        """
        Delete state for a particular user.
        """
        if db.get_state(self.session, user_id) is None:
            return False

        db.clear_state(self.session, user_id)
        return True

    def reset_data(self, chat_id, user_id):
        """
        Reset data for a particular user in a chat.
        """
        full_state = db.get_state(self.session, user_id)
        if full_state:
            full_state = {c.key: getattr(full_state, c.key)
                          for c in inspect(full_state).mapper.column_attrs}
            for key in full_state.keys():
                if full_state[key] != 'id':
                    full_state[key] = None
            db.set_state(self.session, user_id, full_state)
            return True
        return False

    def save(self, chat_id, user_id, data):
        full_state = db.get_state(self.session, user_id)
        if full_state:
            full_state = data

            db.set_state(self.session, user_id, full_state)
            return True


class UserStates(StatesGroup):
    """Класс описывает виды состояний пользователя."""
    enter_a_name = State()
    select_a_command = State()
    choose_a_translation = State()
    enter_a_new_word = State()
    enter_a_translation = State()
    enter_dell_word = State()
