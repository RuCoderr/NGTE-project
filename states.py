from aiogram.fsm.state import StatesGroup, State


class Form(StatesGroup):
    name = State()
    age = State()
    passport = State()
    zarplata = State()
    banks = State()
    hobbies = State()


class ToCurator(StatesGroup):
    mess = State()


class AdminState(StatesGroup):
    newsletter = State()


class Letter(StatesGroup):
    idd = State()
    mess = State()


class Balance(StatesGroup):
    idd = State()
    mess = State()


class Status(StatesGroup):
    idd = State()
    mess = State()


