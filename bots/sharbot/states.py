from aiogram.fsm.state import State, StatesGroup


class YangiZakaz(StatesGroup):
    magazin_kodi = State()
    sana = State()
    manzil = State()
    arka_metr = State()
    logotip_menu = State()
    logotip_soni = State()
    sharchi_tanlash = State()


class BajarildiForm(StatesGroup):
    metr = State()
    logotip = State()
    uzoqmi = State()
    km = State()
    rasm = State()


class TolovForm(StatesGroup):
    worker_id = State()
    summa = State()


class AddSharchiForm(StatesGroup):
    tg_id = State()
    ism = State()


class OylikHisobotForm(StatesGroup):
    oy = State()


class XodimPhotoForm(StatesGroup):
    arka_photo = State()
    logo_photo = State()


class XodimBajarildiForm(StatesGroup):
    metr = State()
    logotip = State()
    uzoqmi = State()
    km = State()


class AdminQarzForm(StatesGroup):
    summa = State()
    izoh = State()


class EditOrderForm(StatesGroup):
    order_id = State()
    field = State()
    waiting_for_value = State()
    waiting_for_sharchi = State()


class AdminEditExecutionForm(StatesGroup):
    execution_id = State()
    field = State()
    waiting_for_value = State()


class EditWorkerPricesForm(StatesGroup):
    arka = State()
    logotip = State()
    km = State()
