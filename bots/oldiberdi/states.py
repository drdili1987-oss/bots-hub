from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    choosing_language = State()
    entering_name = State()
    entering_phone = State()


class AddDebt(StatesGroup):
    entering_recipient = State()
    entering_alias = State()
    choosing_currency = State()
    entering_amount = State()
    entering_description = State()
    entering_due_date = State()


class FinanceOperation(StatesGroup):
    choosing_person = State()
    entering_amount = State()


class AdminBroadcast(StatesGroup):
    entering_message = State()
    confirming = State()


class AddPersonalFinance(StatesGroup):
    entering_type = State()
    entering_amount = State()
    choosing_currency = State()
    choosing_category = State()
    entering_custom_category = State()
    entering_note = State()
    entering_date = State()


class EditPersonalFinance(StatesGroup):
    choosing_field = State()
    editing_amount = State()
    editing_category = State()
    editing_custom_category = State()
    editing_note = State()
    editing_date = State()


class PartialDebtPayment(StatesGroup):
    entering_amount = State()

