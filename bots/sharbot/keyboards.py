from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


def admin_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🆕 Yangi zakaz")],
            [KeyboardButton(text="📋 Buyurtmalar"), KeyboardButton(text="➕ Sharchi qo'shish")],
            [KeyboardButton(text="💰 Hisobot"), KeyboardButton(text="💸 To'lov")],
            [KeyboardButton(text="👥 Sharchilar")],
        ],
        resize_keyboard=True,
    )


from datetime import datetime

def worker_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Mening buyurtmalarim"), KeyboardButton(text="📊 Hisob-kitob")],
            [KeyboardButton(text="📅 Oylik hisobot")]
        ],
        resize_keyboard=True,
    )

def months_inline_kb(prefix="oylik"):
    buttons = []
    now = datetime.now()
    month_names = {
        1: "Yanvar", 2: "Fevral", 3: "Mart", 4: "Aprel", 
        5: "May", 6: "Iyun", 7: "Iyul", 8: "Avgust", 
        9: "Sentyabr", 10: "Oktyabr", 11: "Noyabr", 12: "Dekabr"
    }
    
    y, m = now.year, now.month
    for _ in range(6):
        year_month = f"{y}-{m:02d}"
        label = f"{month_names[m]} {y}"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"{prefix}_{year_month}")])
        m -= 1
        if m == 0:
            m = 12
            y -= 1
            
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def workers_inline_kb(workers, prefix="tanla"):
    buttons = [
        [InlineKeyboardButton(text=w["ism"], callback_data=f"{prefix}_{w['id']}")]
        for w in workers
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def qabul_rad_kb(order_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"qabul_{order_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"rad_{order_id}"),
            ]
        ]
    )


def worker_orders_kb(orders):
    buttons = [
        [
            InlineKeyboardButton(
                text=f"#{o['id']} | {o['magazin_kodi']} | {o['sana']}",
                callback_data=f"buyurtma_{o['id']}",
            )
        ]
        for o in orders
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def bajarildi_kb(order_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Bajarildi", callback_data=f"bajarildi_{order_id}")]
        ]
    )


def ha_yoq_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Ha, uzoq", callback_data="uzoq_ha"),
                InlineKeyboardButton(text="Yo'q, yaqin", callback_data="uzoq_yoq"),
            ]
        ]
    )


def tasdiqlash_kb(execution_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"tasdiqlash_{execution_id}")],
            [InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"adminexecedit_{execution_id}")]
        ]
    )


def admin_edit_execution_kb(execution_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📏 Arka metr", callback_data=f"execedit_{execution_id}_metr")],
            [InlineKeyboardButton(text="🎈 Logotip", callback_data=f"execedit_{execution_id}_logotip")],
            [InlineKeyboardButton(text="🚗 Transport km", callback_data=f"execedit_{execution_id}_km")],
            [InlineKeyboardButton(text="📤 Xodimga jo'natish", callback_data=f"execedit_{execution_id}_send")]
        ]
    )


def worker_reconfirm_kb(execution_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"w_reconfirm_{execution_id}")]
        ]
    )


def hisobot_menu_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Umumiy qarzlar", callback_data="qarzlar")],
            [InlineKeyboardButton(text="📅 Oylik hisobot", callback_data="oylik")],
        ]
    )


# kirim_chiqim_menu_kb removed


def worker_debt_paid_kb(worker_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ To'landi deb belgilash", callback_data=f"tolov_{worker_id}")]
        ]
    )


def admin_hisob_kitob_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Qarz qo'shish", callback_data="admin_qarz_qoshish")],
            [InlineKeyboardButton(text="✅ Qarz to'landi (tozalash)", callback_data="admin_qarz_tozalash")],
        ]
    )


def logotip_colors_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔴 Qizil", callback_data="logo_color_qizil"),
                InlineKeyboardButton(text="⚪ Oq", callback_data="logo_color_oq"),
            ],
            [
                InlineKeyboardButton(text="🟠 Orange", callback_data="logo_color_orange"),
                InlineKeyboardButton(text="🟡 Sariq", callback_data="logo_color_sariq"),
            ],
            [
                InlineKeyboardButton(text="➡️ Keyingi", callback_data="logo_color_done"),
            ]
        ]
    )


def edit_order_inline_kb(order_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Magazin kodi", callback_data=f"editord_{order_id}_magazin_kodi"),
                InlineKeyboardButton(text="Sana", callback_data=f"editord_{order_id}_sana")
            ],
            [
                InlineKeyboardButton(text="Manzil", callback_data=f"editord_{order_id}_manzil"),
                InlineKeyboardButton(text="Arka metr", callback_data=f"editord_{order_id}_arka_metr")
            ],
            [
                InlineKeyboardButton(text="Qizil", callback_data=f"editord_{order_id}_qizil"),
                InlineKeyboardButton(text="Oq", callback_data=f"editord_{order_id}_oq")
            ],
            [
                InlineKeyboardButton(text="Orange", callback_data=f"editord_{order_id}_orange"),
                InlineKeyboardButton(text="Sariq", callback_data=f"editord_{order_id}_sariq")
            ],
            [
                InlineKeyboardButton(text="👤 Sharchini o'zgartirish", callback_data=f"editord_{order_id}_sharchi")
            ],
            [InlineKeyboardButton(text="✅ Tugatish", callback_data="editord_done")]
        ]
    )


def admin_orders_kb(orders):
    buttons = []
    for o in orders:
        buttons.append([
            InlineKeyboardButton(
                text=f"#{o['id']} | {o['magazin_kodi']} | {o['sana']}",
                callback_data=f"adminord_{o['id']}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def worker_confirm_payment_kb(worker_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"wconfirm_pay_{worker_id}"),
                InlineKeyboardButton(text="❌ Yo'q", callback_data=f"wreject_pay_{worker_id}"),
            ]
        ]
    )


def worker_confirm_tolov_kb(worker_id: int, summa: float):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"wc_tl_{worker_id}_{int(summa)}"),
                InlineKeyboardButton(text="❌ Yo'q", callback_data=f"wr_tl_{worker_id}"),
            ]
        ]
    )


def cancel_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bosh menyu")]],
        resize_keyboard=True,
    )


def xodim_upload_kb(order_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📷 Rasmlarni yuklash", callback_data=f"xodim_upload_{order_id}"),
            ]
        ]
    )


def xodim_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Aktiv buyurtmalar")],
        ],
        resize_keyboard=True,
    )


def xodim_orders_inline_kb(orders):
    keyboard = []
    for o in orders:
        keyboard.append([InlineKeyboardButton(text=f"📦 #{o['id']} - {o['magazin_kodi']}", callback_data=f"x_ord_{o['id']}")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def xodim_order_detail_kb(order_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Bajarildi", callback_data=f"x_baj_{order_id}"),
            ]
        ]
    )

def admin_workers_list_kb(workers):
    buttons = []
    for w in workers:
        buttons.append([
            InlineKeyboardButton(
                text=f"👤 {w['ism']}",
                callback_data=f"adm_wk_{w['id']}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_worker_detail_kb(worker_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Narxlarni tahrirlash", callback_data=f"adm_wedit_{worker_id}")
            ]
        ]
    )
