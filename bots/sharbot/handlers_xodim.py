import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

import database as db
import keyboards as kb
from states import XodimPhotoForm, XodimBajarildiForm
from config import XODIM_ID, ADMIN_ID, ARKA_NARXI_METR, LOGOTIP_NARXI_DONA, TRANSPORT_NARXI_KM

router = Router()
logger = logging.getLogger("handlers_xodim")

@router.message(CommandStart(), F.from_user.id == XODIM_ID)
async def xodim_start(message: Message):
    await message.answer(
        "Assalomu alaykum, Xodim! Boshqaruv botiga xush kelibsiz.\n"
        "Sizga yangi buyurtmalar va buyurtmalarning bajarilishi haqidagi xabarlar yuboriladi.",
        reply_markup=kb.xodim_menu_kb()
    )

@router.message(F.text.in_({"❌ Bosh menyu", "Bosh menyu"}), F.from_user.id == XODIM_ID)
async def xodim_cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Bosh menyuga qaytildi.",
        reply_markup=kb.xodim_menu_kb(),
    )

@router.message(F.text == "📋 Aktiv buyurtmalar", F.from_user.id == XODIM_ID)
async def xodim_active_orders(message: Message):
    orders = await db.get_orders_by_statuses(["yuborilgan", "qabul_qilingan"])
    if not orders:
        await message.answer("Hozircha faol buyurtmalar yo'q.")
        return
    await message.answer(
        "Aktiv buyurtmalar ro'yxati:",
        reply_markup=kb.xodim_orders_inline_kb(orders)
    )

@router.callback_query(F.data.startswith("x_ord_"), F.from_user.id == XODIM_ID)
async def xodim_order_detail(call: CallbackQuery):
    order_id = int(call.data.split("_")[2])
    order = await db.get_order(order_id)
    if not order:
        await call.message.edit_text("Buyurtma topilmadi.")
        await call.answer()
        return
    
    worker = await db.get_worker_by_id(order["worker_id"])
    wname = worker["ism"] if worker else "?"
    
    text = (
        f"📦 Buyurtma #{order['id']}\n"
        f"🏪 Magazin: {order['magazin_kodi']}\n"
        f"📅 Sana: {order['sana']}\n"
        f"📍 Manzil: {order['manzil']}\n"
        f"📐 Taxminiy arka: {order.get('arka_metr', 0)} metr\n"
        f"🔴 Qizil logotip: {order.get('qizil', 0)} dona\n"
        f"⚪ Oq logotip: {order.get('oq', 0)} dona\n"
        f"🟠 Orange logotip: {order.get('orange', 0)} dona\n"
        f"🟡 Sariq logotip: {order.get('sariq', 0)} dona\n"
        f"👤 Sharchi: {wname}\n"
        f"Holat: {order['status']}"
    )
    await call.message.answer(text, reply_markup=kb.xodim_order_detail_kb(order_id))
    await call.answer()

@router.callback_query(F.data.startswith("x_baj_"), F.from_user.id == XODIM_ID)
async def xodim_bajarildi_start(call: CallbackQuery, state: FSMContext):
    order_id = int(call.data.split("_")[2])
    await state.update_data(order_id=order_id)
    await call.message.answer("Necha METR arka qilindi?", reply_markup=kb.cancel_kb())
    await state.set_state(XodimBajarildiForm.metr)
    await call.answer()

@router.message(XodimBajarildiForm.metr, F.from_user.id == XODIM_ID)
async def xodim_bajarildi_metr(message: Message, state: FSMContext):
    text = message.text.strip().replace(",", ".")
    try:
        metr = float(text)
    except ValueError:
        await message.answer("Iltimos, raqam kiriting (masalan 12.5).", reply_markup=kb.cancel_kb())
        return
    await state.update_data(metr=metr)
    await message.answer("Nechta shar logotip berildi (jami dona)?", reply_markup=kb.cancel_kb())
    await state.set_state(XodimBajarildiForm.logotip)

@router.message(XodimBajarildiForm.logotip, F.from_user.id == XODIM_ID)
async def xodim_bajarildi_logotip(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("Iltimos, faqat raqam kiriting.", reply_markup=kb.cancel_kb())
        return
    await state.update_data(logotip=int(message.text.strip()))
    await message.answer("Do'kon uzoqmi? Transport kerak bo'ldimi?", reply_markup=kb.ha_yoq_kb())
    await state.set_state(XodimBajarildiForm.uzoqmi)

@router.callback_query(XodimBajarildiForm.uzoqmi, F.data.in_({"uzoq_ha", "uzoq_yoq"}), F.from_user.id == XODIM_ID)
async def xodim_bajarildi_uzoqmi(call: CallbackQuery, state: FSMContext):
    if call.data == "uzoq_yoq":
        await state.update_data(km=0)
        await _xodim_bajarildi_yakunlash(call.message, state, call.bot)
        await call.answer()
        return
    await call.message.answer("Necha KM bo'ldi?", reply_markup=kb.cancel_kb())
    await state.set_state(XodimBajarildiForm.km)
    await call.answer()

@router.message(XodimBajarildiForm.km, F.from_user.id == XODIM_ID)
async def xodim_bajarildi_km(message: Message, state: FSMContext):
    text = message.text.strip().replace(",", ".")
    try:
        km = float(text)
    except ValueError:
        await message.answer("Iltimos, raqam kiriting.", reply_markup=kb.cancel_kb())
        return
    await state.update_data(km=km)
    await _xodim_bajarildi_yakunlash(message, state, message.bot)

async def _xodim_bajarildi_yakunlash(message: Message, state: FSMContext, bot):
    data = await state.get_data()
    order_id = data["order_id"]
    order = await db.get_order(order_id)
    if not order:
        await message.answer("Xatolik: Buyurtma topilmadi.", reply_markup=kb.xodim_menu_kb())
        await state.clear()
        return
        
    worker = await db.get_worker_by_id(order["worker_id"])
    arka_narxi = worker.get("arka_narxi") if worker else None
    logotip_narxi = worker.get("logotip_narxi") if worker else None
    km_narxi = worker.get("km_narxi") if worker else None
    
    arka_narxi = arka_narxi or ARKA_NARXI_METR
    logotip_narxi = logotip_narxi or LOGOTIP_NARXI_DONA
    km_narxi = km_narxi or TRANSPORT_NARXI_KM

    summa = (
        data["metr"] * arka_narxi
        + data["logotip"] * logotip_narxi
        + data["km"] * km_narxi
    )
    
    execution_id = await db.create_execution(order_id, data["metr"], data["logotip"], data["km"], summa)
    await db.set_order_status(order_id, "bajarilgan")
    
    worker = await db.get_worker_by_id(order["worker_id"])
    wname = worker["ism"] if worker else "Sharchi"
    
    text_admin = (
        f"📦 Zakaz #{order_id} xodim tomonidan bajarildi deb belgilandi\n"
        f"🏪 Magazin: {order['magazin_kodi']}\n"
        f"📏 Arka: {data['metr']} metr\n"
        f"🎈 Logotip: {data['logotip']} dona\n"
        f"🚗 Transport: {data['km']} km\n"
        f"👤 Sharchi: {wname}\n"
        f"💰 Hisoblangan summa: {summa:,.0f} so'm".replace(",", " ")
    )
    await bot.send_message(ADMIN_ID, text_admin, reply_markup=kb.tasdiqlash_kb(execution_id), disable_notification=False)
    
    await message.answer(
        "✅ Buyurtma bajarildi deb belgilandi. Tafsilotlar adminga tasdiqlash uchun yuborildi.\n\n"
        "Endi hisobot rasmlarini yuborishingiz kerak.\n"
        "1. Qilingan arkaning rasmini yuboring (photo yuboring):",
        reply_markup=kb.cancel_kb()
    )
    
    # Switch to photo upload state
    await state.clear()
    await state.set_state(XodimPhotoForm.arka_photo)
    await state.update_data(order_id=order_id)

@router.callback_query(F.data.startswith("xodim_upload_"), F.from_user.id == XODIM_ID)
async def xodim_upload_start(call: CallbackQuery, state: FSMContext):
    order_id = int(call.data.split("_")[2])
    await state.update_data(order_id=order_id)
    await call.message.answer(
        "1. Qilingan arkaning rasmini yuboring (photo yuboring):",
        reply_markup=kb.cancel_kb()
    )
    await state.set_state(XodimPhotoForm.arka_photo)
    await call.answer()

@router.message(XodimPhotoForm.arka_photo, F.from_user.id == XODIM_ID)
async def xodim_arka_photo(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer("Iltimos, rasm yuboring (photo):", reply_markup=kb.cancel_kb())
        return
    
    file_id = message.photo[-1].file_id
    await state.update_data(arka_photo_id=file_id)
    await message.answer(
        "2. Endi logotipli sharlar rasmini yuboring (photo yuboring):",
        reply_markup=kb.cancel_kb()
    )
    await state.set_state(XodimPhotoForm.logo_photo)

@router.message(XodimPhotoForm.logo_photo, F.from_user.id == XODIM_ID)
async def xodim_logo_photo(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer("Iltimos, rasm yuboring (photo):", reply_markup=kb.cancel_kb())
        return
    
    logo_file_id = message.photo[-1].file_id
    data = await state.get_data()
    arka_file_id = data.get("arka_photo_id")
    order_id = data.get("order_id")
    
    order = await db.get_order(order_id)
    worker = await db.get_worker_by_id(order["worker_id"]) if order else None
    wname = worker["ism"] if worker else "Sharchi"
    magazin = order["magazin_kodi"] if order else "?"
    
    # Notify Admin
    try:
        await message.bot.send_photo(
            ADMIN_ID,
            photo=arka_file_id,
            caption=f"📷 Xodim dan hisobot rasmi (Arka)\n🏪 Magazin: {magazin}\n👤 Sharchi: {wname}",
            disable_notification=False
        )
        await message.bot.send_photo(
            ADMIN_ID,
            photo=logo_file_id,
            caption=f"📷 Xodim dan hisobot rasmi (Logo sharlar)\n🏪 Magazin: {magazin}\n👤 Sharchi: {wname}",
            disable_notification=False
        )
    except Exception as e:
        logger.error(f"Failed to forward photos to Admin: {e}")
        
    # Notify Worker
    if worker:
        try:
            await message.bot.send_photo(
                worker["tg_id"],
                photo=arka_file_id,
                caption=f"📷 Xodim dan buyurtma bezak rasmi (Arka)\n🏪 Magazin: {magazin}",
                disable_notification=False
            )
            await message.bot.send_photo(
                worker["tg_id"],
                photo=logo_file_id,
                caption=f"📷 Xodim dan buyurtma bezak rasmi (Logo sharlar)\n🏪 Magazin: {magazin}",
                disable_notification=False
            )
        except Exception as e:
            logger.error(f"Failed to forward photos to Worker: {e}")
            
    await message.answer(
        "✅ Rahmat! Rasmlar adminga va sharchiga yuborildi.",
        reply_markup=kb.xodim_menu_kb()
    )
    await state.clear()
