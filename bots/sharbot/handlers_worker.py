from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
import keyboards as kb
from states import BajarildiForm
from config import ADMIN_ID, XODIM_ID, ARKA_NARXI_METR, LOGOTIP_NARXI_DONA, TRANSPORT_NARXI_KM

router = Router()


@router.message(CommandStart(), F.from_user.id != ADMIN_ID, F.from_user.id != XODIM_ID)
async def cmd_start_worker(message: Message):
    worker = await db.get_worker_by_tgid(message.from_user.id)
    if not worker:
        await message.answer(
            "Assalomu alaykum! Siz hozircha tizimda ro'yxatdan o'tmagansiz.\n"
            "Iltimos, admin bilan bog'lanib, sizni sharchi sifatida qo'shishini so'rang.\n\n"
            f"Sizning Telegram ID raqamingiz: {message.from_user.id}"
        )
        return
    await message.answer(
        f"Assalomu alaykum, {worker['ism']}!\nQuyidagi menyudan foydalaning:",
        reply_markup=kb.worker_menu_kb(),
    )


@router.callback_query(F.data.startswith("qabul_"))
async def qabul_callback(call: CallbackQuery):
    order_id = int(call.data.split("_")[1])
    await db.set_order_status(order_id, "qabul_qilingan")
    order = await db.get_order(order_id)

    await call.message.edit_text(call.message.text + "\n\n✅ QABUL QILINDI")
    await call.bot.send_message(
        ADMIN_ID, f"✅ Sharchi #{order_id} zakazni qabul qildi (magazin: {order['magazin_kodi']})."
    )
    await call.answer("Qabul qilindi")


@router.callback_query(F.data.startswith("rad_"))
async def rad_callback(call: CallbackQuery):
    order_id = int(call.data.split("_")[1])
    await db.set_order_status(order_id, "rad_etildi")
    order = await db.get_order(order_id)

    await call.message.edit_text(call.message.text + "\n\n❌ RAD ETILDI")
    await call.bot.send_message(
        ADMIN_ID, f"❌ Sharchi #{order_id} zakazni rad etdi (magazin: {order['magazin_kodi']}). Boshqa sharchi tayinlang."
    )
    await call.answer("Rad etildi")


@router.message(F.text == "📋 Mening buyurtmalarim", F.from_user.id != ADMIN_ID)
async def worker_orders(message: Message):
    worker = await db.get_worker_by_tgid(message.from_user.id)
    if not worker:
        await message.answer("Siz ro'yxatdan o'tmagansiz.")
        return
    orders = await db.list_worker_orders(worker["id"], status="qabul_qilingan")
    if not orders:
        await message.answer("Sizda bajarilishi kerak bo'lgan buyurtma yo'q.")
        return
    await message.answer("Buyurtmalaringiz:", reply_markup=kb.worker_orders_kb(orders))


@router.message(F.text == "📊 Hisob-kitob", F.from_user.id != ADMIN_ID, F.from_user.id != XODIM_ID)
async def worker_hisob_kitob(message: Message):
    worker = await db.get_worker_by_tgid(message.from_user.id)
    if not worker:
        await message.answer("Siz ro'yxatdan o'tmagansiz.")
        return

    unpaid_debt = await db.get_worker_unpaid_debt(worker["id"])
    text = (
        f"📊 Hisob-kitob:\n\n"
        f"👤 Sharchi: {worker['ism']}\n"
        f"💰 Admin sizdan qarzdorligi: {unpaid_debt:,.0f} so'm".replace(",", " ")
    )
    await message.answer(text)

@router.message(F.text == "📅 Oylik hisobot", F.from_user.id != ADMIN_ID, F.from_user.id != XODIM_ID)
async def worker_oylik_hisobot(message: Message):
    worker = await db.get_worker_by_tgid(message.from_user.id)
    if not worker:
        await message.answer("Siz ro'yxatdan o'tmagansiz.")
        return
    await message.answer("Qaysi oy uchun hisobot kerak?", reply_markup=kb.months_inline_kb("workeroylik"))

@router.callback_query(F.data.startswith("workeroylik_"))
async def worker_oylik_natija(call: CallbackQuery):
    worker = await db.get_worker_by_tgid(call.from_user.id)
    if not worker:
        await call.answer("Siz ro'yxatdan o'tmagansiz.", show_alert=True)
        return

    year_month = call.data.split("_")[1]

    # Umumiy yig'indi
    exec_summary = await db.worker_monthly_report(worker["id"], year_month)

    if not exec_summary or exec_summary["buyurtmalar_soni"] == 0:
        await call.message.edit_text(f"📅 {year_month} oyi uchun sizda tasdiqlangan buyurtmalar yo'q.")
        await call.answer()
        return

    # Batafsil ro'yxat (har bir buyurtma)
    details = await db.worker_monthly_report_detail(worker["id"], year_month)

    def fmt_sana(s):
        """YYYY-MM-DD → DD.MM.YYYY"""
        try:
            from datetime import datetime
            return datetime.strptime(str(s), "%Y-%m-%d").strftime("%d.%m.%Y")
        except Exception:
            return str(s)

    lines = [f"📅 <b>{year_month} oyi — Batafsil hisobot</b>\n"]

    for i, row in enumerate(details, start=1):
        magazin   = row["magazin_kodi"] or "—"
        sana      = fmt_sana(row["sana"]) if row["sana"] else "—"
        metr      = row["metr"] or 0
        logotip   = row["logotip_soni"] or 0
        km        = row["transport_km"] or 0
        summa     = row["summa"] or 0

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
            f"<b>{i}.</b> 📅 {sana} | 🏪 <b>{magazin}</b>\n"
            f"   └ {ish_text}\n"
            f"   └ 💰 <b>{summa_fmt} so'm</b>"
        )

    # Jami raqamlarni detail ro'yxatdan hisoblash (aniq mos keladi)
    jami_summa   = sum(row["summa"]        or 0 for row in details)
    jami_metr    = sum(row["metr"]         or 0 for row in details)
    jami_logotip = sum(row["logotip_soni"] or 0 for row in details)
    jami_km      = sum(row["transport_km"] or 0 for row in details)

    jami_fmt = f"{jami_summa:,.0f}".replace(",", " ")
    lines.append(
        f"\n{'─'*30}\n"
        f"📦 Jami buyurtmalar: <b>{len(details)} ta</b>\n"
        f"📏 Jami arka: <b>{jami_metr} m</b>\n"
        f"🎈 Jami logotip: <b>{int(jami_logotip)} dona</b>\n"
        f"🚗 Jami transport: <b>{jami_km} km</b>\n"
        f"💰 Jami summa: <b>{jami_fmt} so'm</b>"
    )

    await call.message.edit_text("\n".join(lines), parse_mode="HTML")
    await call.answer()



@router.callback_query(F.data.startswith("buyurtma_"))
async def buyurtma_detail(call: CallbackQuery):
    order_id = int(call.data.split("_")[1])
    order = await db.get_order(order_id)
    text = (
        f"📦 Zakaz #{order['id']}\n"
        f"🏪 Magazin: {order['magazin_kodi']}\n"
        f"📅 Sana: {order['sana']}\n"
        f"📍 Manzil: {order['manzil']}\n"
        f"📐 Taxminiy arka: {order.get('arka_metr', 0)} metr\n"
        f"🔴 Qizil logotip: {order.get('qizil', 0)} dona\n"
        f"⚪ Oq logotip: {order.get('oq', 0)} dona\n"
        f"🟠 Orange logotip: {order.get('orange', 0)} dona\n"
        f"🟡 Sariq logotip: {order.get('sariq', 0)} dona\n"
        f"Holat: {order['status']}"
    )
    await call.message.answer(text, reply_markup=kb.bajarildi_kb(order_id))
    await call.answer()


@router.callback_query(F.data.startswith("bajarildi_"))
async def bajarildi_start(call: CallbackQuery, state: FSMContext):
    order_id = int(call.data.split("_")[1])
    await state.update_data(order_id=order_id)
    await call.message.answer("Necha METR arka qilindi?")
    await state.set_state(BajarildiForm.metr)
    await call.answer()


@router.message(BajarildiForm.metr, F.from_user.id != ADMIN_ID)
async def bajarildi_metr(message: Message, state: FSMContext):
    text = message.text.strip().replace(",", ".")
    try:
        metr = float(text)
    except ValueError:
        await message.answer("Iltimos, raqam kiriting (masalan 12.5).")
        return
    await state.update_data(metr=metr)
    await message.answer("Nechta shar logotip berildi (jami dona)?")
    await state.set_state(BajarildiForm.logotip)


@router.message(BajarildiForm.logotip, F.from_user.id != ADMIN_ID)
async def bajarildi_logotip(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("Iltimos, faqat raqam kiriting.")
        return
    await state.update_data(logotip=int(message.text.strip()))
    await message.answer("Do'kon uzoqmi? Transport kerak bo'ldimi?", reply_markup=kb.ha_yoq_kb())
    await state.set_state(BajarildiForm.uzoqmi)


@router.callback_query(F.data.startswith("w_reconfirm_"), F.from_user.id != ADMIN_ID)
async def worker_reconfirm_callback(call: CallbackQuery, state: FSMContext):
    execution_id = int(call.data.split("_")[2])
    execution = await db.get_execution(execution_id)
    if not execution:
        await call.answer("Topilmadi", show_alert=True)
        return
    
    if execution['tasdiqlangan'] == 1:
        await call.answer("Allaqachon tasdiqlangan!", show_alert=True)
        return

    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer("O'zgarishlar tasdiqlandi va adminga yuborildi. Tasdiqlanishini kuting.")
    
    order = await db.get_order(execution['order_id'])
    text = (
        f"♻️ Ishchi tasdiqladi: Zakaz #{order['id']}\n"
        f"🏪 Magazin: {order['magazin_kodi']}\n"
        f"📏 Arka: {execution['metr']} metr\n"
        f"🎈 Logotip: {execution['logotip_soni']} dona\n"
        f"🚗 Transport: {execution['transport_km']} km\n"
        f"💰 Hisoblangan summa: {execution['summa']:,.0f} so'm".replace(",", " ")
    )
    if execution.get('photo_file_id'):
        await call.bot.send_photo(
            ADMIN_ID,
            photo=execution['photo_file_id'],
            caption=text,
            reply_markup=kb.tasdiqlash_kb(execution_id)
        )
    else:
        await call.bot.send_message(
            ADMIN_ID,
            text,
            reply_markup=kb.tasdiqlash_kb(execution_id)
        )
    await call.answer()


@router.callback_query(BajarildiForm.uzoqmi, F.data.in_({"uzoq_ha", "uzoq_yoq"}))
async def bajarildi_uzoqmi(call: CallbackQuery, state: FSMContext):
    if call.data == "uzoq_yoq":
        await state.update_data(km=0)
        await call.message.answer("Iltimos, ish joyidan rasm (arka/logotip) yuboring.")
        await state.set_state(BajarildiForm.rasm)
        await call.answer()
        return
    await call.message.answer("Necha KM bo'ldi?")
    await state.set_state(BajarildiForm.km)
    await call.answer()


@router.message(BajarildiForm.km, F.from_user.id != ADMIN_ID)
async def bajarildi_km(message: Message, state: FSMContext):
    text = message.text.strip().replace(",", ".")
    try:
        km = float(text)
    except ValueError:
        await message.answer("Iltimos, raqam kiriting.")
        return
    await state.update_data(km=km)
    await message.answer("Iltimos, ish joyidan rasm (arka/logotip) yuboring.")
    await state.set_state(BajarildiForm.rasm)


@router.message(BajarildiForm.rasm, F.photo, F.from_user.id != ADMIN_ID)
async def bajarildi_rasm(message: Message, state: FSMContext):
    photo_file_id = message.photo[-1].file_id
    await state.update_data(photo_file_id=photo_file_id)
    await _bajarildi_yakunlash(message, state, message.bot)


async def _bajarildi_yakunlash(message: Message, state: FSMContext, bot):
    data = await state.get_data()
    order = await db.get_order(data["order_id"])

    worker = await db.get_worker_by_id(order["worker_id"])
    arka_narxi = worker.get("arka_narxi") or ARKA_NARXI_METR
    logotip_narxi = worker.get("logotip_narxi") or LOGOTIP_NARXI_DONA
    km_narxi = worker.get("km_narxi") or TRANSPORT_NARXI_KM

    summa = (
        data["metr"] * arka_narxi
        + data["logotip"] * logotip_narxi
        + data["km"] * km_narxi
    )

    execution_id = await db.create_execution(data["order_id"], data["metr"], data["logotip"], data["km"], summa, data.get("photo_file_id"))
    await db.set_order_status(data["order_id"], "bajarilgan")

    text = (
        f"📦 Zakaz #{order['id']} bajarildi deb belgilandi\n"
        f"🏪 Magazin: {order['magazin_kodi']}\n"
        f"📏 Arka: {data['metr']} metr\n"
        f"🎈 Logotip: {data['logotip']} dona\n"
        f"🚗 Transport: {data['km']} km\n"
        f"💰 Hisoblangan summa: {summa:,.0f} so'm".replace(",", " ")
    )
    if data.get("photo_file_id"):
        await bot.send_photo(ADMIN_ID, photo=data["photo_file_id"], caption=text, reply_markup=kb.tasdiqlash_kb(execution_id), disable_notification=False)
    else:
        await bot.send_message(ADMIN_ID, text, reply_markup=kb.tasdiqlash_kb(execution_id), disable_notification=False)

    # Notify xodim
    from config import XODIM_ID
    text_xodim = (
        f"🔔 **Buyurtma bajarildi!**\n\n"
        f"🏪 Magazin: {order['magazin_kodi']}\n"
        f"📏 Arka: {data['metr']} metr\n"
        f"🎈 Logotip: {data['logotip']} dona\n"
        f"🚗 Transport: {data['km']} km\n\n"
        f"Iltimos, bezatilgan do'kon rasmlarini (arka va logotipli sharlar rasmini) yuklang:"
    )
    try:
        await bot.send_message(XODIM_ID, text_xodim, reply_markup=kb.xodim_upload_kb(order['id']), disable_notification=False)
    except Exception:
        pass

    await message.answer("✅ Ma'lumotlar adminga yuborildi. Tasdiqlanishini kuting.")
    await state.clear()


@router.callback_query(F.data.startswith("wconfirm_pay_"))
async def worker_confirm_payment_callback(call: CallbackQuery):
    worker_id = int(call.data.split("_")[2])
    worker = await db.get_worker_by_id(worker_id)
    if not worker:
        await call.message.edit_text("Xatolik: Sharchi topilmadi.")
        await call.answer()
        return

    unpaid_debt = await db.get_worker_unpaid_debt(worker_id)
    await db.mark_worker_debts_paid(worker_id)

    # Edit worker's message
    await call.message.edit_text(
        f"✅ Hisob-kitob tasdiqlandi.\n"
        f"💰 Qabul qilingan summa: {unpaid_debt:,.0f} so'm\n"
        f"Balansingiz yangilandi (0 so'm).".replace(",", " ")
    )
    
    # Notify admin
    await call.bot.send_message(
        ADMIN_ID,
        f"✅ {worker['ism']} hisob-kitobni (to'lovni) tasdiqladi.\n"
        f"💰 To'langan summa: {unpaid_debt:,.0f} so'm\n"
        f"Balans yopildi.".replace(",", " ")
    )
    await call.answer("Tasdiqlandi")


@router.callback_query(F.data.startswith("wreject_pay_"))
async def worker_reject_payment_callback(call: CallbackQuery):
    worker_id = int(call.data.split("_")[2])
    worker = await db.get_worker_by_id(worker_id)
    if not worker:
        await call.message.edit_text("Xatolik: Sharchi topilmadi.")
        await call.answer()
        return

    # Edit worker's message
    await call.message.edit_text("❌ Hisob-kitob rad etildi. Ma'lumot adminga yuborildi.")

    # Notify admin
    await call.bot.send_message(
        ADMIN_ID,
        f"❌ {worker['ism']} hisob-kitobni (to'lovni) rad etdi."
    )
    await call.answer("Rad etildi")


@router.callback_query(F.data.startswith("wc_tl_"))
async def worker_confirm_tolov_callback(call: CallbackQuery):
    parts = call.data.split("_")
    worker_id = int(parts[2])
    summa = float(parts[3])
    
    worker = await db.get_worker_by_id(worker_id)
    if not worker:
        await call.message.edit_text("Xatolik: Sharchi topilmadi.")
        await call.answer()
        return
        
    await db.create_debt(worker_id, None, -summa)
    await db.add_cashflow("chiqim", summa, f"{worker['ism']} ga to'lov")
    
    # Edit worker's message
    await call.message.edit_text(
        f"✅ To'lov tasdiqlandi.\n"
        f"💰 Qabul qilingan summa: {summa:,.0f} so'm\n"
        f"Ushbu summa balansingizdan chegirildi.".replace(",", " ")
    )
    
    # Notify admin
    await call.bot.send_message(
        ADMIN_ID,
        f"✅ {worker['ism']} {summa:,.0f} so'm to'lovni tasdiqladi.\n"
        f"Summa uning qarzidan chegirildi va chiqim hisobotiga qo'shildi.".replace(",", " ")
    )
    await call.answer("To'lov tasdiqlandi")


@router.callback_query(F.data.startswith("wr_tl_"))
async def worker_reject_tolov_callback(call: CallbackQuery):
    worker_id = int(call.data.split("_")[2])
    worker = await db.get_worker_by_id(worker_id)
    if not worker:
        await call.message.edit_text("Xatolik: Sharchi topilmadi.")
        await call.answer()
        return
        
    # Edit worker's message
    await call.message.edit_text("❌ To'lov rad etildi. Ma'lumot adminga yuborildi.")
    
    # Notify admin
    await call.bot.send_message(
        ADMIN_ID,
        f"❌ {worker['ism']} to'lovni rad etdi."
    )
    await call.answer("To'lov rad etildi")
