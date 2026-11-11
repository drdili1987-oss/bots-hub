from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import re
from datetime import datetime, date
import database as db
import keyboards as kb
from states import (
    YangiZakaz,
    AddSharchiForm,
    TolovForm,
    OylikHisobotForm,
    AdminQarzForm,
    AdminEditExecutionForm,
    EditOrderForm
)
from config import ADMIN_ID, ARKA_NARXI_METR, LOGOTIP_NARXI_DONA, TRANSPORT_NARXI_KM

router = Router()


def is_admin(message_or_call) -> bool:
    return message_or_call.from_user.id == ADMIN_ID


# ---------------- BEKOR QILISH / BOSH MENYU ----------------

@router.message(F.text.in_({"❌ Bosh menyu", "Bosh menyu"}), F.from_user.id == ADMIN_ID)
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Bosh menyuga qaytildi.",
        reply_markup=kb.admin_menu_kb(),
    )


# ---------------- START ----------------

@router.message(CommandStart(), F.from_user.id == ADMIN_ID)
async def cmd_start_admin(message: Message):
    await message.answer(
        "Assalomu alaykum, Admin!\nQuyidagi menyudan foydalaning:",
        reply_markup=kb.admin_menu_kb(),
    )


# ---------------- SHARCHI QO'SHISH ----------------

@router.message(F.text == "➕ Sharchi qo'shish", F.from_user.id == ADMIN_ID)
async def add_sharchi_start(message: Message, state: FSMContext):
    await message.answer(
        "Sharchining Telegram ID raqamini yuboring (masalan @userinfobot orqali bilib oling):",
        reply_markup=kb.cancel_kb()
    )
    await state.set_state(AddSharchiForm.tg_id)


@router.message(AddSharchiForm.tg_id, F.from_user.id == ADMIN_ID)
async def add_sharchi_tgid(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("Iltimos, faqat raqam yuboring.")
        return
    await state.update_data(tg_id=int(message.text.strip()))
    await message.answer("Endi sharchining ismini yozing:", reply_markup=kb.cancel_kb())
    await state.set_state(AddSharchiForm.ism)


@router.message(AddSharchiForm.ism, F.from_user.id == ADMIN_ID)
async def add_sharchi_ism(message: Message, state: FSMContext):
    data = await state.get_data()
    await db.add_worker(data["tg_id"], message.text.strip())
    await message.answer(
        f"✅ Sharchi qo'shildi: {message.text.strip()} (ID: {data['tg_id']})\n"
        f"Sharchi botga /start yozib, o'z panelini ochishi mumkin.",
        reply_markup=kb.admin_menu_kb(),
    )
    await state.clear()


# ---------------- YANGI ZAKAZ ----------------

@router.message(F.text == "🆕 Yangi zakaz", F.from_user.id == ADMIN_ID)
async def yangi_zakaz_start(message: Message, state: FSMContext):
    await message.answer("Magazin kodini kiriting:", reply_markup=kb.cancel_kb())
    await state.set_state(YangiZakaz.magazin_kodi)


@router.message(YangiZakaz.magazin_kodi, F.from_user.id == ADMIN_ID)
async def zakaz_magazin(message: Message, state: FSMContext):
    await state.update_data(magazin_kodi=message.text.strip())
    await message.answer("Sanani kiriting (masalan 15.07.2026):", reply_markup=kb.cancel_kb())
    await state.set_state(YangiZakaz.sana)


@router.message(YangiZakaz.sana, F.from_user.id == ADMIN_ID)
async def zakaz_sana(message: Message, state: FSMContext):
    await state.update_data(sana=message.text.strip())
    await message.answer("Lokatsiya (manzil) havolasini yuboring:", reply_markup=kb.cancel_kb())
    await state.set_state(YangiZakaz.manzil)


@router.message(YangiZakaz.manzil, F.from_user.id == ADMIN_ID)
async def zakaz_manzil(message: Message, state: FSMContext):
    await state.update_data(manzil=message.text.strip())
    await message.answer("Taxminiy arka o'lchamini kiriting (metrda, masalan 15 yoki 0):", reply_markup=kb.cancel_kb())
    await state.set_state(YangiZakaz.arka_metr)


@router.message(YangiZakaz.arka_metr, F.from_user.id == ADMIN_ID)
async def zakaz_arka_metr(message: Message, state: FSMContext):
    text = message.text.strip().replace(",", ".")
    try:
        arka_metr = float(text)
    except ValueError:
        await message.answer("Iltimos, faqat raqam kiriting (masalan 12.5 yoki 0):")
        return
    await state.update_data(arka_metr=arka_metr)
    # Initialize logo counts
    await state.update_data(qizil=0, oq=0, orange=0, sariq=0)
    await send_logo_menu(message, state)


async def send_logo_menu(message: Message, state: FSMContext):
    data = await state.get_data()
    qizil = data.get("qizil", 0)
    oq = data.get("oq", 0)
    orange = data.get("orange", 0)
    sariq = data.get("sariq", 0)
    
    text = (
        "Logotip sharlar sonini kiriting:\n\n"
        f"🔴 Qizil: {qizil} dona\n"
        f"⚪ Oq: {oq} dona\n"
        f"🟠 Orange: {orange} dona\n"
        f"🟡 Sariq: {sariq} dona\n\n"
        "Rang tugmasini bosib sonini kiriting, tugatgach 'Keyingi' tugmasini bosing:"
    )
    await message.answer(text, reply_markup=kb.logotip_colors_kb())
    await state.set_state(YangiZakaz.logotip_menu)


@router.callback_query(YangiZakaz.logotip_menu, F.data.startswith("logo_color_"))
async def logo_color_callback(call: CallbackQuery, state: FSMContext):
    color = call.data.split("_")[2]
    if color == "done":
        workers = await db.list_active_workers()
        if not workers:
            await call.message.answer(
                "Hozircha sharchilar ro'yxati bo'sh. Avval '➕ Sharchi qo'shish' orqali sharchi qo'shing.",
                reply_markup=kb.admin_menu_kb(),
            )
            await state.clear()
            await call.answer()
            return
        
        await call.message.answer("Zakazni qaysi sharchiga yuboramiz?", reply_markup=kb.workers_inline_kb(workers))
        await state.set_state(YangiZakaz.sharchi_tanlash)
        await call.answer()
        return
    
    await state.update_data(current_color=color)
    color_names = {"qizil": "Qizil", "oq": "Oq", "orange": "Orange", "sariq": "Sariq"}
    await call.message.answer(f"Nechta {color_names.get(color, color)} logotip shar kerak?", reply_markup=kb.cancel_kb())
    await state.set_state(YangiZakaz.logotip_soni)
    await call.answer()


@router.message(YangiZakaz.logotip_soni, F.from_user.id == ADMIN_ID)
async def logo_quantity_handler(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text.isdigit():
        await message.answer("Iltimos, faqat musbat butun son kiriting:")
        return
    
    data = await state.get_data()
    color = data.get("current_color")
    await state.update_data({color: int(text)})
    await send_logo_menu(message, state)


@router.callback_query(YangiZakaz.sharchi_tanlash, F.data.startswith("tanla_"))
async def zakaz_sharchi_tanlash(call: CallbackQuery, state: FSMContext):
    worker_id = int(call.data.split("_")[1])
    data = await state.get_data()

    order_id = await db.create_order(
        data["magazin_kodi"],
        data["sana"],
        data["manzil"],
        data.get("qizil", 0),
        data.get("oq", 0),
        data.get("orange", 0),
        data.get("sariq", 0),
        data.get("arka_metr", 0.0),
        worker_id
    )

    worker = await db.get_worker_by_id(worker_id)
    text = (
        f"🆕 Yangi zakaz #{order_id}\n"
        f"🏪 Magazin: {data['magazin_kodi']}\n"
        f"📅 Sana: {data['sana']}\n"
        f"📍 Manzil: {data['manzil']}\n"
        f"📐 Taxminiy arka: {data.get('arka_metr', 0)} metr\n"
        f"🔴 Qizil logotip: {data.get('qizil', 0)} dona\n"
        f"⚪ Oq logotip: {data.get('oq', 0)} dona\n"
        f"🟠 Orange logotip: {data.get('orange', 0)} dona\n"
        f"🟡 Sariq logotip: {data.get('sariq', 0)} dona"
    )
    await call.bot.send_message(worker["tg_id"], text, reply_markup=kb.qabul_rad_kb(order_id), disable_notification=False)

    # Notify xodim
    from config import XODIM_ID
    text_xodim = (
        f"🔔 **Yangi buyurtma yaratildi!**\n\n"
        f"🏪 Magazin: {data['magazin_kodi']}\n"
        f"📅 Sana: {data['sana']}\n"
        f"📍 Manzil: {data['manzil']}\n"
        f"📐 Taxminiy arka: {data.get('arka_metr', 0)} metr\n"
        f"🔴 Qizil logotip: {data.get('qizil', 0)} dona\n"
        f"⚪ Oq logotip: {data.get('oq', 0)} dona\n"
        f"🟠 Orange logotip: {data.get('orange', 0)} dona\n"
        f"🟡 Sariq logotip: {data.get('sariq', 0)} dona\n"
        f"👤 Sharchi: {worker['ism']}"
    )
    try:
        await call.bot.send_message(XODIM_ID, text_xodim, disable_notification=False)
    except Exception:
        pass

    await call.message.edit_text(f"✅ Zakaz #{order_id} {worker['ism']} ga yuborildi.")
    await state.clear()
    await call.answer()


# ---------------- ZAKAZNI TAHRIRLASH ----------------


@router.callback_query(F.data.startswith("editord_"))
async def edit_order_callback(call: CallbackQuery, state: FSMContext):
    if not is_admin(call):
        return
    action = call.data.replace("editord_", "")
    if action == "done":
        await call.message.delete()
        await call.message.answer("Tahrirlash yakunlandi.", reply_markup=kb.admin_menu_kb())
        return
    
    # action is like {order_id}_{field} e.g. "7_magazin_kodi"
    parts = action.split("_", 1)
    if len(parts) != 2:
        return
    order_id = int(parts[0])
    field = parts[1]
    
    await state.update_data(order_id=order_id, field=field)
    
    if field == "sharchi":
        workers = await db.list_active_workers()
        if not workers:
            await call.message.answer("Sharchilar topilmadi.")
            return
        await call.message.answer("Zakazni qaysi sharchiga o'tqazamiz?", reply_markup=kb.workers_inline_kb(workers))
        await state.set_state(EditOrderForm.waiting_for_sharchi)
        await call.answer()
        return

    field_names = {
        "magazin_kodi": "Magazin kodi",
        "sana": "Sana",
        "manzil": "Manzil",
        "arka_metr": "Arka metr",
        "qizil": "Qizil logotip",
        "oq": "Oq logotip",
        "orange": "Orange logotip",
        "sariq": "Sariq logotip"
    }
    await call.message.answer(f"Yangi '{field_names.get(field, field)}' qiymatini yuboring:", reply_markup=kb.cancel_kb())
    await state.set_state(EditOrderForm.waiting_for_value)
    await call.answer()

@router.message(EditOrderForm.waiting_for_value, F.from_user.id == ADMIN_ID)
async def edit_order_value(message: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("order_id")
    field = data.get("field")
    val = message.text.strip()
    
    if field == "arka_metr":
        try:
            val = float(val.replace(",", "."))
        except ValueError:
            await message.answer("Iltimos, raqam kiriting (masalan 10.5).")
            return
    elif field in ["qizil", "oq", "orange", "sariq"]:
        if not val.isdigit():
            await message.answer("Iltimos, butun son kiriting.")
            return
        val = int(val)
        
    await db.update_order_field(order_id, field, val)
    await message.answer(f"✅ O'zgartirildi.")
    
    order = await db.get_order(order_id)
    text_info = (
        f"Zakaz #{order['id']} ma'lumotlari:\n"
        f"Magazin: {order['magazin_kodi']}\n"
        f"Sana: {order['sana']}\n"
        f"Manzil: {order['manzil']}\n"
        f"Arka metr: {order['arka_metr']}\n"
        f"Qizil: {order['qizil']}, Oq: {order['oq']}, Orange: {order['orange']}, Sariq: {order['sariq']}\n"
        f"Holat: {order['status']}\n\n"
        "Yana qaysi qismini o'zgartirmoqchisiz?"
    )
    await message.answer(text_info, reply_markup=kb.edit_order_inline_kb(order_id))
    await state.clear()

@router.callback_query(EditOrderForm.waiting_for_sharchi, F.data.startswith("tanla_"), F.from_user.id == ADMIN_ID)
async def edit_order_worker(call: CallbackQuery, state: FSMContext):
    new_worker_id = int(call.data.split("_")[1])
    data = await state.get_data()
    order_id = data.get("order_id")
    
    await db.update_order_field(order_id, "worker_id", new_worker_id)
    await call.message.delete()
    await call.message.answer("✅ Zakaz yangi sharchiga muvaffaqiyatli o'tqazildi.")
    
    order = await db.get_order(order_id)
    worker = await db.get_worker_by_id(new_worker_id)
    wname = worker["ism"] if worker else "Noma'lum"
    
    text_info = (
        f"Zakaz #{order['id']} ma'lumotlari:\n"
        f"Magazin: {order['magazin_kodi']}\n"
        f"Sana: {order['sana']}\n"
        f"Manzil: {order['manzil']}\n"
        f"Arka metr: {order['arka_metr']}\n"
        f"Qizil: {order['qizil']}, Oq: {order['oq']}, Orange: {order['orange']}, Sariq: {order['sariq']}\n"
        f"Sharchi: {wname}\n"
    )
    await call.message.answer(text_info, reply_markup=kb.edit_order_inline_kb(order_id))
    
    # Notify new worker
    text_worker = (
        f"🔔 Sizga yangi zakaz o'tkazildi!\n\n"
        f"Zakaz raqami: #{order['id']}\n"
        f"🏪 Magazin: {order['magazin_kodi']}\n"
        f"📅 Sana: {order['sana']}\n"
        f"📍 Manzil: {order['manzil']}\n\n"
        f"🎈 Logotiplar:\n"
    )
    if order["qizil"] > 0: text_worker += f"- Qizil: {order['qizil']} dona\n"
    if order["oq"] > 0: text_worker += f"- Oq: {order['oq']} dona\n"
    if order["orange"] > 0: text_worker += f"- Orange: {order['orange']} dona\n"
    if order["sariq"] > 0: text_worker += f"- Sariq: {order['sariq']} dona\n"
    text_worker += f"\n📏 Arka: {order['arka_metr']} metr"

    try:
        if worker and worker["tg_id"]:
            await call.bot.send_message(worker["tg_id"], text_worker, disable_notification=False)
    except Exception:
        pass

    await state.clear()
    await call.answer()


# ---------------- BUYURTMALAR RO'YXATI (admin) ----------------

@router.message(F.text == "📋 Buyurtmalar", F.from_user.id == ADMIN_ID)
async def list_orders(message: Message):
    # Faqat bajarilmagan (faol) buyurtmalarni olish
    orders = await db.get_orders_by_statuses(['yuborilgan', 'qabul_qilingan'])
    if not orders:
        await message.answer("Hozircha faol buyurtmalar yo'q.")
        return
        
    def parse_order_date(o):
        sana_str = o.get("sana", "").strip()
        sana_str = re.sub(r'[\s\-/]+', '.', sana_str)
        parsed_date = None
        for fmt in ("%d.%m.%Y", "%d.%m.%y", "%Y.%m.%d", "%d.%m"):
            try:
                if fmt == "%d.%m":
                    parsed_date = datetime.strptime(sana_str, fmt).date().replace(year=date.today().year)
                else:
                    parsed_date = datetime.strptime(sana_str, fmt).date()
                break
            except ValueError:
                continue
        if parsed_date is None:
            parts = [int(p) for p in re.findall(r'\d+', sana_str)]
            if len(parts) == 3:
                if parts[0] > 1000:
                    parsed_date = date(parts[0], parts[1], parts[2])
                else:
                    year = parts[2]
                    parsed_date = date(year + 2000 if year < 100 else year, parts[1], parts[0])
            elif len(parts) == 2:
                parsed_date = date(date.today().year, parts[1], parts[0])
            else:
                parsed_date = date.min # Xato bo'lsa eng oxiriga / boshiga o'tadi
        return parsed_date or date.min

    # Sort in descending order (kelajakdagi uzoqroq sanalar tepada, yaqin sanalar pastda chiqishi uchun)
    orders.sort(key=parse_order_date, reverse=True)

    await message.answer(
        "Tahrirlash yoki ko'rish uchun buyurtmani tanlang:",
        reply_markup=kb.admin_orders_kb(orders)
    )


@router.callback_query(F.data.startswith("adminord_"))
async def admin_order_detail(call: CallbackQuery, state: FSMContext):
    if not is_admin(call):
        return
    order_id = int(call.data.split("_")[1])
    order = await db.get_order(order_id)
    if not order:
        await call.answer("Buyurtma topilmadi.", show_alert=True)
        return
    
    worker = await db.get_worker_by_id(order["worker_id"])
    wname = worker["ism"] if worker else "?"
    
    await state.update_data(order_id=order_id)
    text_info = (
        f"Zakaz #{order['id']} ma'lumotlari:\n"
        f"Magazin: {order['magazin_kodi']}\n"
        f"Sana: {order['sana']}\n"
        f"Manzil: {order['manzil']}\n"
        f"Arka metr: {order['arka_metr']}\n"
        f"Qizil: {order['qizil']}, Oq: {order['oq']}, Orange: {order['orange']}, Sariq: {order['sariq']}\n"
        f"Sharchi: {wname}\n"
        f"Holat: {order['status']}\n\n"
        "Qaysi qismini o'zgartirmoqchisiz?"
    )
    await call.message.edit_text(text_info, reply_markup=kb.edit_order_inline_kb(order_id))
    await state.set_state(None)
    await call.answer()


# ---------------- ISHNI TASDIQLASH ----------------

@router.callback_query(F.data.startswith("tasdiqlash_"))
async def tasdiqlash_callback(call: CallbackQuery):
    if not is_admin(call):
        await call.answer("Bu tugma faqat admin uchun.", show_alert=True)
        return

    execution_id = int(call.data.split("_")[1])
    execution = await db.get_execution(execution_id)
    order = await db.get_order(execution["order_id"])

    await db.confirm_execution(execution_id)
    await db.set_order_status(order["id"], "tasdiqlangan")
    await db.create_debt(order["worker_id"], order["id"], execution["summa"])

    worker = await db.get_worker_by_id(order["worker_id"])

    if call.message.caption:
        await call.message.edit_caption(
            caption=call.message.caption + "\n\n✅ TASDIQLANDI. Qarz hisobotga qo'shildi."
        )
    else:
        await call.message.edit_text(
            call.message.text + "\n\n✅ TASDIQLANDI. Qarz hisobotga qo'shildi."
        )
    await call.bot.send_message(
        worker["tg_id"],
        f"✅ #{order['id']} zakaz bo'yicha ishingiz tasdiqlandi.\n"
        f"Sizga {execution['summa']:,.0f} so'm qarz yozildi.".replace(",", " "),
    )
    await call.answer("Tasdiqlandi")


@router.callback_query(F.data.startswith("adminexecedit_"))
async def admin_exec_edit_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call):
        await call.answer()
        return
    execution_id = int(call.data.split("_")[1])
    await call.message.answer(
        "Nimani tahrirlamoqchisiz?",
        reply_markup=kb.admin_edit_execution_kb(execution_id)
    )
    await call.answer()

@router.callback_query(F.data.startswith("execedit_"))
async def admin_exec_edit_field(call: CallbackQuery, state: FSMContext):
    if not is_admin(call):
        await call.answer()
        return
    parts = call.data.split("_")
    execution_id = int(parts[1])
    field = parts[2]
    
    if field == "send":
        # Xodimga qayta jo'natish
        execution = await db.get_execution(execution_id)
        order = await db.get_order(execution['order_id'])
        worker = await db.get_worker_by_id(order['worker_id'])
        
        text = (
            f"⚠️ Admin zakazni tahrirladi! Iltimos, tekshirib tasdiqlang.\n"
            f"Zakaz #{order['id']}\n"
            f"📏 Arka: {execution['metr']} metr\n"
            f"🎈 Logotip: {execution['logotip_soni']} dona\n"
            f"🚗 Transport: {execution['transport_km']} km\n"
            f"💰 Hisoblangan summa: {execution['summa']:,.0f} so'm".replace(",", " ")
        )
        if execution.get('photo_file_id'):
            await call.bot.send_photo(
                worker['tg_id'],
                photo=execution['photo_file_id'],
                caption=text,
                reply_markup=kb.worker_reconfirm_kb(execution_id)
            )
        else:
            await call.bot.send_message(
                worker['tg_id'],
                text,
                reply_markup=kb.worker_reconfirm_kb(execution_id)
            )
        await call.message.answer("✅ Tahrirlangan hisobot xodimga yuborildi.")
        await call.answer()
        return

    await state.update_data(execution_id=execution_id, field=field)
    await call.message.answer(f"Yangi qiymatni kiriting ({field} uchun):")
    await state.set_state(AdminEditExecutionForm.waiting_for_value)
    await call.answer()

@router.message(AdminEditExecutionForm.waiting_for_value, F.from_user.id == ADMIN_ID)
async def admin_exec_edit_value(message: Message, state: FSMContext):
    text = message.text.strip().replace(",", ".")
    try:
        val = float(text)
    except ValueError:
        await message.answer("Iltimos, faqat raqam kiriting.")
        return
        
    data = await state.get_data()
    execution_id = data['execution_id']
    field = data['field']
    
    execution = await db.get_execution(execution_id)
    metr = execution['metr']
    logotip = execution['logotip_soni']
    km = execution['transport_km']
    
    if field == "metr":
        metr = val
    elif field == "logotip":
        logotip = int(val)
    elif field == "km":
        km = val
        
    order = await db.get_order(execution['order_id'])
    worker = await db.get_worker_by_id(order['worker_id'])
    
    arka_narxi = worker.get("arka_narxi") if worker else None
    logotip_narxi = worker.get("logotip_narxi") if worker else None
    km_narxi = worker.get("km_narxi") if worker else None
    
    arka_narxi = arka_narxi or ARKA_NARXI_METR
    logotip_narxi = logotip_narxi or LOGOTIP_NARXI_DONA
    km_narxi = km_narxi or TRANSPORT_NARXI_KM
        
    summa = (metr * arka_narxi) + (logotip * logotip_narxi) + (km * km_narxi)
    
    await db.update_execution(execution_id, metr, logotip, km, summa)
    await state.clear()
    
    await message.answer(
        f"✅ Saqlandi!\n\n"
        f"📏 Arka: {metr} metr\n"
        f"🎈 Logotip: {logotip} dona\n"
        f"🚗 Transport: {km} km\n"
        f"💰 Yangi summa: {summa:,.0f} so'm\n\n".replace(",", " ") +
        "Yana nimadir o'zgartirasizmi yoki xodimga jo'natasizmi?",
        reply_markup=kb.admin_edit_execution_kb(execution_id)
    )


# ---------------- ADMIN HISOB-KITOB ----------------

@router.message(F.text == "📊 Hisob-kitob", F.from_user.id == ADMIN_ID)
async def admin_hisob_kitob(message: Message):
    qarz = await db.get_admin_total_debt()
    text = (
        "📊 Sizning hisob-kitobingiz:\n\n"
        f"💸 Admin siz (Dilfuza) dan: {qarz:,.0f} so'm qarz"
    ).replace(",", " ")
    await message.answer(text, reply_markup=kb.admin_hisob_kitob_kb())


@router.callback_query(F.data == "admin_qarz_qoshish")
async def admin_qarz_qoshish_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call):
        await call.answer()
        return
    await call.message.answer("Yangi qarz summasini kiriting (so'mda):", reply_markup=kb.cancel_kb())
    await state.set_state(AdminQarzForm.summa)
    await call.answer()


@router.message(AdminQarzForm.summa, F.from_user.id == ADMIN_ID)
async def admin_qarz_summa(message: Message, state: FSMContext):
    text = message.text.strip().replace(" ", "").replace(",", "")
    if not text.isdigit():
        await message.answer("Iltimos, faqat raqam kiriting.")
        return
    summa = float(text)
    await state.update_data(summa=summa)
    await message.answer("Qarz izohi (masalan: 'Ombor', 'Mahsulot xaridi'). Izohsiz bo'lsa, '-' yuboring:", reply_markup=kb.cancel_kb())
    await state.set_state(AdminQarzForm.izoh)


@router.message(AdminQarzForm.izoh, F.from_user.id == ADMIN_ID)
async def admin_qarz_izoh(message: Message, state: FSMContext):
    izoh = message.text.strip()
    data = await state.get_data()
    summa = data["summa"]
    await db.add_admin_debt(summa, izoh if izoh != "-" else "")
    qarz_jami = await db.get_admin_total_debt()
    await message.answer(
        f"✅ {summa:,.0f} so'm qarz qo'shildi.\n"
        f"💸 Jami qarz: {qarz_jami:,.0f} so'm".replace(",", " "),
        reply_markup=kb.admin_menu_kb()
    )
    await state.clear()


@router.callback_query(F.data == "admin_qarz_tozalash")
async def admin_qarz_tozalash(call: CallbackQuery):
    if not is_admin(call):
        await call.answer()
        return
    await db.mark_admin_debts_paid()
    await call.message.edit_text("✅ Barcha qarzlar to'landi deb belgilandi. Balans: 0 so'm.")
    await call.answer("Tozalandi")


# ---------------- HISOBOT ----------------

@router.message(F.text == "💰 Hisobot", F.from_user.id == ADMIN_ID)
async def hisobot_menu(message: Message):
    await message.answer("Qaysi hisobotni ko'rmoqchisiz?", reply_markup=kb.hisobot_menu_kb())


@router.callback_query(F.data == "qarzlar")
async def qarzlar_callback(call: CallbackQuery):
    if not is_admin(call):
        await call.answer()
        return
    summary = await db.get_unpaid_debts_summary()
    if not summary:
        await call.message.answer("Sharchilar ro'yxati bo'sh.")
        await call.answer()
        return
    for row in summary:
        if row["jami"] and row["jami"] > 0:
            text = f"👤 {row['ism']}: {row['jami']:,.0f} so'm qarz".replace(",", " ")
            await call.message.answer(text, reply_markup=kb.worker_debt_paid_kb(row["id"]))
    if all((not r["jami"]) or r["jami"] == 0 for r in summary):
        await call.message.answer("Hech kimga qarz yo'q. 🎉")
    await call.answer()


@router.callback_query(F.data.startswith("tolov_"))
async def tolov_callback(call: CallbackQuery):
    if not is_admin(call):
        await call.answer()
        return
    worker_id = int(call.data.split("_")[1])
    worker = await db.get_worker_by_id(worker_id)
    if not worker:
        await call.message.edit_text("Xatolik: Sharchi topilmadi.")
        await call.answer()
        return
    
    unpaid_debt = await db.get_worker_unpaid_debt(worker_id)
    if unpaid_debt <= 0:
        await call.message.edit_text(f"👤 {worker['ism']} ga to'lanishi kerak bo'lgan qarz mavjud emas.")
        await call.answer()
        return
        
    try:
        text = (
            f"⚠️ Admin siz bilan hisob-kitob qilindi (to'landi) deb belgiladi.\n"
            f"Buni tasdiqlaysizmi?\n\n"
            f"💰 Summa: {unpaid_debt:,.0f} so'm"
        ).replace(",", " ")
        await call.bot.send_message(worker["tg_id"], text, reply_markup=kb.worker_confirm_payment_kb(worker_id))
        await call.message.edit_text(f"👤 {worker['ism']} ga hisob-kitobni tasdiqlash so'rovi yuborildi. Kutilmoqda...")
    except Exception as e:
        await call.message.edit_text(
            f"❌ {worker['ism']} ga xabar yuborishda xatolik. "
            f"Ehtimol, u botni bloklagan yoki hali start bosmagan."
        )
    await call.answer()


@router.callback_query(F.data == "oylik")
async def oylik_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call):
        await call.answer()
        return
    await call.message.edit_text("Qaysi oy uchun hisobot kerak?", reply_markup=kb.months_inline_kb("oylik"))
    await call.answer()


@router.callback_query(F.data.startswith("oylik_"))
async def oylik_natija_callback(call: CallbackQuery):
    if not is_admin(call):
        await call.answer()
        return
    year_month = call.data.split("_")[1]
    exec_summary, cash_summary = await db.monthly_report(year_month)

    kirim   = cash_summary.get("kirim", 0)
    chiqim  = cash_summary.get("chiqim", 0)
    xarajat = exec_summary["jami_xarajat"] or 0

    def fmt_sana(s):
        """YYYY-MM-DD → DD.MM.YYYY"""
        try:
            from datetime import datetime
            return datetime.strptime(str(s), "%Y-%m-%d").strftime("%d.%m.%Y")
        except Exception:
            return str(s)

    # Har bir buyurtma batafsil ro'yxati
    details = await db.admin_monthly_report_detail(year_month)

    lines = [f"📅 <b>{year_month} oyi — Batafsil hisobot</b>\n"]

    for i, row in enumerate(details, start=1):
        magazin = row["magazin_kodi"] or "—"
        sana    = fmt_sana(row["sana"]) if row["sana"] else "—"
        sharchi = row["ism"] or "—"
        metr    = row["metr"] or 0
        logotip = row["logotip_soni"] or 0
        km      = row["transport_km"] or 0
        summa   = row["summa"] or 0

        ish_qismlari = []
        if metr:
            ish_qismlari.append(f"{metr} m arka")
        if logotip:
            ish_qismlari.append(f"{logotip} ta logotip shar")
        if km:
            ish_qismlari.append(f"{km} km transport")
        ish_text = ", ".join(ish_qismlari) if ish_qismlari else "ish"

        summa_fmt = f"{summa:,.0f}".replace(",", " ")
        lines.append(
            f"<b>{i}.</b> 📅 {sana} | 🏪 <b>{magazin}</b> | 👤 {sharchi}\n"
            f"   └ {ish_text}\n"
            f"   └ 💰 <b>{summa_fmt} so'm</b>"
        )

    # Jami raqamlarni detail ro'yxatdan hisoblash (aniq mos keladi)
    jami_summa   = sum(row["summa"]        or 0 for row in details)
    jami_metr    = sum(row["metr"]         or 0 for row in details)
    jami_logotip = sum(row["logotip_soni"] or 0 for row in details)
    jami_km      = sum(row["transport_km"] or 0 for row in details)

    sof = kirim - chiqim - jami_summa
    lines.append(
        f"\n{'─'*30}\n"
        f"📦 Jami buyurtmalar: <b>{len(details)} ta</b>\n"
        f"📏 Jami arka: <b>{jami_metr} metr</b>\n"
        f"🎈 Jami logotip: <b>{int(jami_logotip)} dona</b>\n"
        f"🚗 Jami transport: <b>{jami_km} km</b>\n"
        f"💸 Sharchilarga jami: <b>{jami_summa:,.0f} so'm</b>\n\n"
        f"➕ Kirim: <b>{kirim:,.0f} so'm</b>\n"
        f"➖ Chiqim: <b>{chiqim:,.0f} so'm</b>\n"
        f"📊 Sof natija: <b>{sof:,.0f} so'm</b>"
    )
    full_text = "\n".join(lines).replace(",", " ")

    await call.message.edit_text(full_text, parse_mode="HTML", reply_markup=kb.hisobot_menu_kb())
    await call.answer()



# ---------------- TO'LOV (chiqim) ----------------

@router.message(F.text == "💸 To'lov", F.from_user.id == ADMIN_ID)
async def tolov_start(message: Message, state: FSMContext):
    workers = await db.list_active_workers()
    if not workers:
        await message.answer(
            "Hozircha sharchilar ro'yxati bo'sh. Avval '➕ Sharchi qo'shish' orqali sharchi qo'shing.",
            reply_markup=kb.admin_menu_kb(),
        )
        return
    
    await message.answer(
        "Kimga to'lov qilasiz?",
        reply_markup=kb.workers_inline_kb(workers, prefix="tolovworker")
    )
    await state.set_state(TolovForm.worker_id)


@router.callback_query(TolovForm.worker_id, F.data.startswith("tolovworker_"))
async def tolov_worker_callback(call: CallbackQuery, state: FSMContext):
    worker_id = int(call.data.split("_")[1])
    await state.update_data(worker_id=worker_id)
    worker = await db.get_worker_by_id(worker_id)
    await call.message.answer(f"{worker['ism']} ga qancha summa berasiz?", reply_markup=kb.cancel_kb())
    await state.set_state(TolovForm.summa)
    await call.answer()


@router.message(TolovForm.summa, F.from_user.id == ADMIN_ID)
async def tolov_summa(message: Message, state: FSMContext):
    text = message.text.strip().replace(" ", "")
    if not text.isdigit():
        await message.answer("Iltimos, faqat raqam kiriting.")
        return
    
    summa = float(text)
    data = await state.get_data()
    worker_id = data.get("worker_id")
    worker = await db.get_worker_by_id(worker_id)
    if not worker:
        await message.answer("Xatolik: Sharchi topilmadi.")
        await state.clear()
        return
    
    try:
        text_worker = (
            f"⚠️ Admin sizga {summa:,.0f} so'm to'lov qilmoqchi.\n"
            f"Buni tasdiqlaysizmi?"
        ).replace(",", " ")
        await message.bot.send_message(
            worker["tg_id"],
            text_worker,
            reply_markup=kb.worker_confirm_tolov_kb(worker_id, summa)
        )
        await message.answer(
            f"👤 {worker['ism']} ga {summa:,.0f} so'm to'lov tasdiqlash so'rovi yuborildi. Kutilmoqda...".replace(",", " "),
            reply_markup=kb.admin_menu_kb()
        )
    except Exception as e:
        await message.answer(
            f"❌ {worker['ism']} ga xabar yuborib bo'lmadi. Botni bloklagan bo'lishi mumkin.",
            reply_markup=kb.admin_menu_kb()
        )
    await state.clear()

from states import EditWorkerPricesForm

@router.message(F.text == "👥 Sharchilar", F.from_user.id == ADMIN_ID)
async def admin_sharchilar_menu(message: Message):
    workers = await db.list_active_workers()
    if not workers:
        await message.answer("Sharchilar topilmadi.")
        return
    await message.answer("Tahrirlash uchun sharchini tanlang:", reply_markup=kb.admin_workers_list_kb(workers))

@router.callback_query(F.data.startswith("adm_wk_"), F.from_user.id == ADMIN_ID)
async def admin_worker_detail(call: CallbackQuery):
    worker_id = int(call.data.split("_")[2])
    worker = await db.get_worker_by_id(worker_id)
    if not worker:
        await call.answer("Sharchi topilmadi", show_alert=True)
        return
    
    arka = worker.get("arka_narxi")
    logo = worker.get("logotip_narxi")
    km = worker.get("km_narxi")
    
    text = (f"👤 <b>{worker['ism']}</b>\n\n"
            f"<b>Joriy maxsus narxlar:</b>\n"
            f"🎈 Arka 1m: {f'{arka:,.0f} so`m' if arka else 'Standart'}\n"
            f"🖨 Logotip 1 dona: {f'{logo:,.0f} so`m' if logo else 'Standart'}\n"
            f"🚗 Transport 1km: {f'{km:,.0f} so`m' if km else 'Standart'}")
    
    await call.message.edit_text(text, reply_markup=kb.admin_worker_detail_kb(worker_id), parse_mode="HTML")

@router.callback_query(F.data.startswith("adm_wedit_"), F.from_user.id == ADMIN_ID)
async def admin_worker_edit_start(call: CallbackQuery, state: FSMContext):
    worker_id = int(call.data.split("_")[2])
    await state.update_data(edit_worker_id=worker_id)
    await state.set_state(EditWorkerPricesForm.arka)
    await call.message.answer("1 metr arka narxini kiriting (Agar standart bo'lsa 0 yozing):")
    await call.answer()

@router.message(EditWorkerPricesForm.arka, F.from_user.id == ADMIN_ID)
async def admin_worker_edit_arka(message: Message, state: FSMContext):
    try:
        val = float(message.text)
    except:
        await message.answer("Faqat son kiriting:")
        return
    await state.update_data(arka=val)
    await state.set_state(EditWorkerPricesForm.logotip)
    await message.answer("1 dona logotip narxini kiriting (Agar standart bo'lsa 0 yozing):")

@router.message(EditWorkerPricesForm.logotip, F.from_user.id == ADMIN_ID)
async def admin_worker_edit_logo(message: Message, state: FSMContext):
    try:
        val = float(message.text)
    except:
        await message.answer("Faqat son kiriting:")
        return
    await state.update_data(logotip=val)
    await state.set_state(EditWorkerPricesForm.km)
    await message.answer("1 km transport narxini kiriting (Agar standart bo'lsa 0 yozing):")

@router.message(EditWorkerPricesForm.km, F.from_user.id == ADMIN_ID)
async def admin_worker_edit_km(message: Message, state: FSMContext):
    try:
        val = float(message.text)
    except:
        await message.answer("Faqat son kiriting:")
        return
    data = await state.get_data()
    worker_id = data['edit_worker_id']
    
    arka = data['arka'] if data['arka'] > 0 else None
    logo = data['logotip'] if data['logotip'] > 0 else None
    km = val if val > 0 else None
    
    await db.update_worker_prices(worker_id, arka, logo, km)
    await state.clear()
    await message.answer("Muvaffaqiyatli saqlandi! Ushbu sharchining keyingi hisob-kitoblari yangi narxlarda hisoblanadi.")
