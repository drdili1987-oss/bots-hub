"""Bot ichidagi barcha matnlar. Har bir kalit uz/ru/kk tillarida mavjud bo'lishi shart."""

TEXTS = {'uz': {'choose_language': 'Assalomu alaykum! 👋\nTilni tanlang:',
        'invalid_language': 'Iltimos, quyidagi tugmalardan birini tanlang 👇',
        'name_request': 'Ismingiz va familiyangizni kiriting:',
        'age_request': 'Yoshingizni kiriting (masalan, 25):',
        'invalid_age': "Iltimos, faqat to'g'ri raqam kiriting (masalan, 25):",
        'gender_request': 'Jinsingizni tanlang:',
        'btn_male': 'Erkak',
        'btn_female': 'Ayol',
        'country_request': 'Qaysi davlatdansiz?',
        'city_request': 'Qaysi shahardansiz?',
        'occupation_request': 'Kasbingiz yoki sohangiz nima? (masalan: Dasturchi, Talaba, Haydovchi...)',
        'invalid_name': 'Ism juda qisqa. Qaytadan kiriting:',
        'phone_request': '📱 <b>Telefon raqamingizni yuboring:</b>\n'
                         '\n'
                         'Quyidagi «📱 Raqamni yuborish» tugmasini bosing yoki raqamingizni yozib yuboring (masalan: '
                         '<code>+998901234567</code>).\n'
                         '\n'
                         '🔒 <i><b>Xavfsizlik kafolati:</b> Raqamingiz faqat haqdor/qarzdor sizni aniqlashi uchun '
                         "kerak. Bot shaxsiy parollar yoki bank ma'lumotlariga kira olmaydi.</i>",
        'send_contact_btn': '📱 Raqamni yuborish',
        'invalid_phone': 'Iltimos, «📱 Raqamni yuborish» tugmasi orqali kontakt yuboring.',
        'invalid_contact': "Iltimos, o'zingizning kontaktingizni yuboring, boshqa birovnikini emas.",
        'registered_welcome': "Xush kelibsiz, {name}! ✅\nRo'yxatdan muvaffaqiyatli o'tdingiz.",
        'main_menu_title': '🏠 Asosiy menyu',
        'btn_creditors': '📥 Qarz oldim',
        'btn_debtors': '📤 Qarz berdim',
        'btn_history': '📊 Qarzlar tarixi',
        'btn_income': '📥 Kirim',
        'btn_outcome': '📤 Chiqim',
        'btn_settings': '⚙️ Sozlamalar',
        'btn_donat': '💝 Donat',
        'btn_cancel': '❌ Bekor qilish',
        'btn_main_menu': '🏠 Asosiy menyu',
        'btn_skip': "➡️ O'tkazib yuborish",
        'btn_confirm': '✅ Tasdiqlash',
        'btn_reject': '❌ Bekor qilish',
        'btn_add_new': "➕ Yangi qo'shish",
        'enter_description': 'Qarz uchun izoh kiriting (ixtiyoriy).\nMasalan: <i>Tushlik uchun</i>',
        'no_creditors': "Sizda hozircha haqdorlar (siz qarzdor bo'lgan shaxslar) yo'q.",
        'no_debtors': "Sizda hozircha qarzdorlar yo'q.",
        'creditors_title': '👥 <b>Haqdorlaringiz</b> (siz ularga qarzdorsiz):',
        'debtors_title': '👤 <b>Qarzdorlaringiz</b> (ular sizga qarzdor):',
        'pending_person': "Kutilmoqda (hali qo'shilmagan)",
        'status_pending': 'tasdiqlanmagan',
        'status_active': 'faol',
        'no_history': "Tarix hozircha bo'sh.",
        'history_title': '📊 <b>Qarzlar tarixi</b> (oxirgi 30 ta):',
        'enter_recipient': "Ikkinchi tomonning telefon raqami (+99890...), Telegram ID raqami, @username'ini yozing "
                           'yoki kontaktini yuboring:',
        'enter_alias': "👤 <b>Ushbu shaxsga o'zingiz uchun nom (psevdonim / nik) bering:</b>\n"
                       '<i>Masalan: Dilmurod bankir, Dilshod iPhone, Umar mahalla</i>\n'
                       '\n'
                       "🔒 <i>Bu nom faqat o'zingizga ko'rinadi (ikkinchi tomonga ko'rinmaydi).\n"
                       "Agar nom kiritishni xohlamasangiz, «➡️ O'tkazib yuborish» tugmasini bosing:</i>",
        'cancelled': 'Bekor qilindi.',
        'cannot_add_self': "O'zingizni qo'sha olmaysiz.",
        'choose_currency': 'Valyutani tanlang:',
        'enter_amount': '💰 <b>Qarz summasini kiriting:</b>\n<i>Masalan: 123 000 yoki 300 000</i>',
        'invalid_amount': "Noto'g'ri summa. Iltimos, musbat raqam kiriting (masalan: 123 000 yoki 300 000):",
        'role_creditor': "sizdan qarzdor bo'lishni",
        'role_debtor': 'sizga qarz berishni',
        'enter_due_date': 'Qarz qaytarish muddatini tanlang yoki KK.OO.YYYY (kun.oy.yil) formatida kiriting (masalan: '
                          '31.12.2026):',
        'invalid_due_date': "Noto'g'ri sana formati. Iltimos, muddatni KK.OO.YYYY formatida kiriting (masalan: "
                            '31.12.2026) yoki quyidagi tugmalardan birini tanlang:',
        'btn_1_week': '1 hafta',
        'btn_1_month': '1 oy',
        'btn_no_due_date': "Muddat yo'q",
        'debt_confirm_request': "<b>{name}</b> ({role}) sizga yangi qarz so'rovini yubordi.\n"
                                '\n'
                                '💰 Miqdor: <b>{amount} {currency}</b>\n'
                                'Muddat: {due_date}\n'
                                '\n'
                                'Tasdiqlaysizmi?',
        'debt_incoming_request': "🔔 <b>{name}</b> sizga qarz so'rovi yubordi.\n"
                                 'Summasi: <b>{amount} {currency}</b>\n'
                                 '\n'
                                 'Tasdiqlaysizmi?',
        'debt_request_sent': "✅ Qarzdor allaqachon botdan ro'yxatdan o'tgan!\n"
                             "Unga to'g'ridan-to'g'ri bot orqali tasdiqlash xabari yuborildi! Tasdiqlashini kuting.",
        'debt_request_send_failed': "So'rovni yuborib bo'lmadi. Ehtimol, foydalanuvchi botni bloklagan.",
        'debt_link_generated': 'Bu foydalanuvchi botda topilmadi.\n'
                               'Quyidagi havolani unga yuboring, u kirib tasdiqlagach qarz faollashadi:\n'
                               '\n'
                               '{link}',
        'sms_sent': '📱 Foydalanuvchi Telegram botimizda topilmadi.\n'
                    '<b>+{phone}</b> raqamiga qarz haqida SMS xabar yuborildi!\n'
                    '\n'
                    'Shuningdek, ushbu taklif havolasini ham unga yuborishingiz mumkin:\n'
                    '{link}',
        'sms_not_sent': 'Foydalanuvchi Telegram botimizda topilmadi.\n'
                        '(SMS yuborilmadi: {reason})\n'
                        '\n'
                        'Quyidagi havolani unga yuboring, u kirib tasdiqlagach qarz faollashadi:\n'
                        '\n'
                        '{link}',
        'debt_not_found': "Bu qarz topilmadi yoki allaqachon ko'rib chiqilgan.",
        'debt_confirmed_by_you': '✅ <b>Qarz tasdiqlandi!</b>\n'
                                 '\n'
                                 '👤 Kim: <b>{name}</b>\n'
                                 '💰 Summasi: <b>{amount} {currency}</b>\n'
                                 "{desc_line}Endi qarz faol holatga o'tdi.",
        'debt_confirmed_by_other': '✅ <b>{name}</b> qarzni tasdiqladi!\n'
                                   '\n'
                                   '💰 Summasi: <b>{amount} {currency}</b>\n'
                                   '{desc_line}Endi qarz faol holatda.',
        'debt_rejected_by_you': '❌ <b>Qarz rad etildi!</b>\n'
                                '\n'
                                '👤 Kim: <b>{name}</b>\n'
                                '💰 Summasi: <b>{amount} {currency}</b>\n'
                                '{desc_line}',
        'debt_rejected_by_other': "❌ <b>{name}</b> qarz so'rovini rad etdi!\n"
                                  '\n'
                                  '💰 Summasi: <b>{amount} {currency}</b>\n'
                                  '{desc_line}',
        'no_active_debtors': "Sizga hech kim qarzdor emas (faol qarzlar yo'q).",
        'no_active_creditors': "Siz hech kimga qarzdor emassiz (faol qarzlar yo'q).",
        'choose_person_income': 'Kimdan pul qabul qildingiz? Tanlang:',
        'choose_person_outcome': "Kimga to'lov qildingiz? Tanlang:",
        'enter_payment_amount': 'Summani kiriting (maksimal: {max_amount} {currency}):',
        'invalid_payment_amount': "Noto'g'ri summa. 0 dan katta va {max_amount} dan oshmagan raqam kiriting:",
        'payment_type_income': 'sizga pul berdi',
        'payment_type_outcome': "sizdan pul oldi / siz unga to'ladingiz",
        'payment_confirm_request': '🔔 <b>{name}</b> {type} deb bildirdi.\n'
                                   'Summasi: <b>{amount} {currency}</b>\n'
                                   '\n'
                                   'Tasdiqlaysizmi?',
        'payment_request_sent': "So'rov yuborildi. Tasdiqlashini kuting.",
        'payment_confirmed_by_you': "✅ <b>To'lov tasdiqlandi!</b>\n"
                                    '\n'
                                    '👤 Kim: <b>{name}</b>\n'
                                    "💰 To'lov summasi: <b>{amount} {currency}</b>\n"
                                    '📋 Umumiy qarz: <b>{total} {currency}</b>\n'
                                    '{desc_line}{status_line}',
        'payment_confirmed_by_other': "✅ <b>{name}</b> to'lovni tasdiqladi!\n"
                                      '\n'
                                      '💰 Tasdiqlangan summa: <b>{amount} {currency}</b>\n'
                                      '📋 Umumiy qarz: <b>{total} {currency}</b>\n'
                                      '{desc_line}{status_line}',
        'debt_fully_closed': "🎉 Qarz to'liq yopildi!",
        'debt_partially_closed': '📊 Qolgan qarz: <b>{remaining} {currency}</b>',
        'payment_rejected_by_you': "❌ <b>To'lov rad etildi!</b>\n"
                                   '\n'
                                   '👤 Kim: <b>{name}</b>\n'
                                   '💰 Rad etilgan summa: <b>{amount} {currency}</b>\n'
                                   '📋 Umumiy qarz: <b>{total} {currency}</b>\n'
                                   '{desc_line}',
        'payment_rejected_by_other': "❌ <b>{name}</b> to'lovni rad etdi!\n"
                                     '\n'
                                     '💰 Rad etilgan summa: <b>{amount} {currency}</b>\n'
                                     '📋 Umumiy qarz: <b>{total} {currency}</b>\n'
                                     '{desc_line}',
        'debt_reminder': '⏰ Hurmatli foydalanuvchi, sizda <b>{name}</b> oldida <b>{amount} {currency}</b> miqdorida '
                         "qarz mavjud. Iltimos, imkon qadar tezroq to'lashga harakat qiling. 🙏",
        'donat_text': '💝 <b>Donat</b>\n'
                      '\n'
                      "Agar bot sizga foydali bo'lsa, quyidagi kartaga ixtiyoriy summa o'tkazishingiz mumkin:\n"
                      '\n'
                      '💳 <b>Karta raqami:</b>\n'
                      '<code>9860 2601 0101 9743</code>\n'
                      '\n'
                      '👤 <b>Karta egasi:</b> Dilmurod Rustamov\n'
                      '\n'
                      'Rahmat! 🙏',
        'settings_title': "⚙️ <b>Sozlamalar</b>\n\nQuyidagi sozlamalarni o'zgartiring:",
        'btn_change_language': "🌐 Tilni o'zgartirish",
        'choose_new_language': 'Yangi tilni tanlang:',
        'language_changed': "✅ Til muvaffaqiyatli o'zgartirildi!",
        'not_admin': 'Bu buyruq faqat admin uchun.',
        'admin_stats': '📊 <b>Statistika</b>\n'
                       '\n'
                       '👤 Jami foydalanuvchilar: {total_users}\n'
                       '💳 Faol qarzlar soni: {active_debts}\n'
                       '💰 Umumiy aylanma (UZS): {total_uzs}\n'
                       '💵 Umumiy aylanma (USD): {total_usd}',
        'broadcast_prompt': "Barcha foydalanuvchilarga yuborilishi kerak bo'lgan xabar matnini kiriting:",
        'broadcast_preview': 'Quyidagi xabar barcha foydalanuvchilarga yuboriladi:\n\n{text}',
        'broadcast_done': '✅ Yuborildi: {sent} ta.\n❌ Xatolik: {failed} ta.',
        'broadcast_cancelled': 'Broadcast bekor qilindi.',
        'btn_personal_finance': '💼 Shaxsiy moliya',
        'fin_main_menu': '💼 <b>Shaxsiy Moliya Markazi</b>\n'
                         '\n'
                         "Bu bo'limda shaxsiy daromad va xarajatlaringizni to'liq nazorat qilishingiz mumkin.\n"
                         '\n'
                         '⚡️ <b>Tez kiritish:</b>\n'
                         'Bitta xabar bilan istalgan vaqtda yozib yuborishingiz mumkin:\n'
                         '• <code>-50k taksi</code>\n'
                         '• <code>+5mln oylik</code>\n'
                         '• <code>-120 000 bozor</code>\n'
                         '• <code>+100$ bonus</code>\n'
                         '• <code>35000 obed</code>\n'
                         '\n'
                         'Quyidagi tugmalar orqali davom eting 👇',
        'fin_btn_income': "➕ Kirim qo'shish",
        'fin_btn_expense': "➖ Chiqim qo'shish",
        'fin_btn_balance': '💼 Balans',
        'fin_btn_history': '📜 Xarajatlar tarixi',
        'fin_btn_report': '📊 Hisobot',
        'fin_enter_amount': '💰 <b>{type_text} summasini kiriting:</b>\n<i>Masalan: 50 000, 100k, 2.5 mln yoki 100$</i>',
        'fin_choose_currency': '💵 <b>Valyutani tanlang:</b>',
        'fin_choose_category': '📂 <b>Kategoriyani tanlang:</b>',
        'fin_enter_custom_category': '✏️ <b>Yangi kategoriya nomini kiriting:</b>',
        'fin_enter_note': '📝 <b>Izoh kiriting (ixtiyoriy):</b>\n'
                          '<i>Masalan: benzin, tushlik, bozorlik...</i>\n'
                          "Agar izoh kerak bo'lmasa, «➡️ O'tkazib yuborish» tugmasini bosing:",
        'fin_choose_date': '📅 <b>Sanani tanlang yoki KK.OO.YYYY formatida kiriting (masalan: 06.10.2026):</b>',
        'fin_saved_success': '✅ <b>{type_title} muvaffaqiyatli saqlandi!</b>\n'
                             '\n'
                             '{sign} <b>{amount} {currency}</b>\n'
                             '📂 Kategoriya: <b>{category}</b>\n'
                             '📝 Izoh: <i>{note}</i>\n'
                             '📅 Sana: <b>{date}</b>',
        'fin_deleted_success': "🗑 <b>Tranzaksiya muvaffaqiyatli o'chirildi!</b>",
        'fin_updated_success': '✅ <b>Tranzaksiya yangilandi!</b>',
        'fin_tx_not_found': "Tranzaksiya topilmadi yoki o'chirilgan.",
        'fin_period_today': '📅 Bugun',
        'fin_period_week': '🗓 Bu hafta',
        'fin_period_month': '📊 Bu oy',
        'fin_period_all': '📈 Barchasi',
        'btn_report': '📊 Hisobotlar',
        'report_main_title': '📊 <b>Umumiy Hisobotlar Markazi</b>',
        'btn_guide': "📹 Qo'llanma",
        'video_guide_caption': "📹 <b>«Temir Daftar» botidan foydalanish bo'yicha video qo'llanma</b>\n\nUshbu videoda botning barcha imkoniyatlari: qarzlar hisobini yuritish, shaxsiy moliya (kirim-chiqim) va hisobotlar bilan ishlash batafsil ko'rsatilgan.",
        'video_guide_text': "📹 <b>«Temir Daftar» botidan foydalanish qo'llanmasi</b>\n\n"
                            "1️⃣ <b>Qarzlar hisobi:</b>\n"
                            "• «📥 Qarz oldim» yoki «📤 Qarz berdim» tugmasi orqali yangi qarz kiriting.\n"
                            "• Ikkinchi tomonning telefon raqami yoki @username'ini kiriting.\n"
                            "• Muddat o'tganda bot avtomatik eslatma yuboradi.\n\n"
                            "2️⃣ <b>Shaxsiy moliya (Kirim/Chiqim):</b>\n"
                            "• Kunlik xarajat va daromadlaringizni yozib boring.\n"
                            "• Tezkor kiritish: <code>-50k taksi</code> yoki <code>+5mln oylik</code> deb yozishingiz ham mumkin!\n\n"
                            "3️⃣ <b>Hisobotlar va Tahlil:</b>\n"
                            "• «📊 Hisobotlar» bo'limida oylik va haftalik moliyaviy holatingizni ko'ring.\n\n"
                            "🎥 <i>Video qo'llanma havolasi:</i>\n{video_url}"},
 'ru': {'choose_language': 'Здравствуйте! 👋\nВыберите язык:',
        'invalid_language': 'Пожалуйста, выберите одну из кнопок ниже 👇',
        'name_request': 'Введите ваше имя и фамилию:',
        'age_request': 'Введите ваш возраст (например, 25):',
        'invalid_age': 'Пожалуйста, введите правильное число (например, 25):',
        'gender_request': 'Выберите ваш пол:',
        'btn_male': 'Мужской',
        'btn_female': 'Женский',
        'country_request': 'Из какой вы страны?',
        'city_request': 'Из какого вы города?',
        'occupation_request': 'Ваша профессия или сфера деятельности? (например: Программист, Студент...)',
        'invalid_name': 'Имя слишком короткое. Введите заново:',
        'phone_request': '📱 <b>Отправьте ваш номер телефона:</b>\n'
                         '\n'
                         'Нажмите кнопку «📱 Отправить номер» ниже или введите номер вручную (например: '
                         '<code>+998901234567</code>).\n'
                         '\n'
                         '🔒 <i><b>Гарантия безопасности:</b> Ваш номер используется только для связи между должником и '
                         'кредитором. Бот не имеет доступа к личным паролям и банковским картам.</i>',
        'send_contact_btn': '📱 Отправить номер',
        'invalid_phone': 'Пожалуйста, отправьте контакт через кнопку «📱 Отправить номер».',
        'invalid_contact': 'Пожалуйста, отправьте свой собственный контакт.',
        'registered_welcome': 'Добро пожаловать, {name}! ✅\nВы успешно зарегистрированы.',
        'main_menu_title': '🏠 Главное меню',
        'btn_creditors': '📥 Взял в долг',
        'btn_debtors': '📤 Дал в долг',
        'btn_history': '📊 История долгов',
        'btn_income': '📥 Приход',
        'btn_outcome': '📤 Расход',
        'btn_settings': '⚙️ Настройки',
        'btn_donat': '💝 Донат',
        'btn_cancel': '❌ Отмена',
        'btn_main_menu': '🏠 Главное меню',
        'btn_skip': '➡️ Пропустить',
        'btn_confirm': '✅ Подтвердить',
        'btn_reject': '❌ Отклонить',
        'btn_add_new': '➕ Добавить нового',
        'enter_description': '📝 <b>Введите комментарий к долгу:</b>\n'
                             '<i>Например: за что взят или дан долг (ремонт машины, зарплата, товар...)</i>\n'
                             '\n'
                             'Если комментарий не нужен, нажмите «➡️ Пропустить»:',
        'no_creditors': 'У вас пока нет кредиторов (тех, кому вы должны).',
        'no_debtors': 'У вас пока нет должников.',
        'creditors_title': '👥 <b>Ваши кредиторы</b> (вы им должны):',
        'debtors_title': '👤 <b>Ваши должники</b> (они должны вам):',
        'pending_person': 'Ожидается (ещё не присоединился)',
        'status_pending': 'не подтверждено',
        'status_active': 'активен',
        'no_history': 'История пока пуста.',
        'history_title': '📊 <b>История долгов</b> (последние 30):',
        'enter_recipient': 'Введите номер телефона (+99890...), Telegram ID, @username или отправьте контакт второй '
                           'стороны:',
        'enter_alias': '👤 <b>Введите имя (псевдоним / ник) для этого человека:</b>\n'
                       '<i>Например: Дилмурод банкир, Дилшод iPhone, Умар махалля</i>\n'
                       '\n'
                       '🔒 <i>Это имя будет видно только вам (другая сторона его не увидит).\n'
                       'Если не хотите указывать ник, нажмите «➡️ Пропустить»:</i>',
        'cancelled': 'Отменено.',
        'cannot_add_self': 'Нельзя добавить самого себя.',
        'choose_currency': 'Выберите валюту:',
        'enter_amount': '💰 <b>Введите сумму долга:</b>\n<i>Например: 123 000 или 300 000</i>',
        'invalid_amount': 'Неверная сумма. Пожалуйста, введите положительное число (например: 123 000 или 300 000):',
        'role_creditor': 'что вы должны ему',
        'role_debtor': 'что он должен вам',
        'enter_due_date': 'Выберите срок возврата долга или введите в формате ДД.ММ.ГГГГ (например: 31.12.2026):',
        'invalid_due_date': 'Неверный формат даты. Пожалуйста, введите в формате ДД.ММ.ГГГГ (например: 31.12.2026) или выберите кнопку ниже:',
        'btn_1_week': '1 неделя',
        'btn_1_month': '1 месяц',
        'btn_no_due_date': 'Без срока',
        'debt_confirm_request': '🔔 <b>{name}</b> указал, {role}.\nСумма: <b>{amount} {currency}</b>\n\nПодтверждаете?',
        'debt_incoming_request': '🔔 <b>{name}</b> отправил вам запрос на долг.\n'
                                 'Сумма: <b>{amount} {currency}</b>\n'
                                 '\n'
                                 'Подтверждаете?',
        'debt_request_sent': 'Запрос отправлен. Ожидайте подтверждения.',
        'debt_request_send_failed': 'Не удалось отправить запрос. Возможно, пользователь заблокировал бота.',
        'debt_link_generated': 'Этот пользователь не найден в боте.\n'
                               'Отправьте ему следующую ссылку, после перехода и подтверждения долг активируется:\n'
                               '\n'
                               '{link}',
        'sms_sent': '📱 Пользователь не найден в боте.\n'
                    'На номер <b>+{phone}</b> отправлено SMS-уведомление!\n'
                    '\n'
                    'Также вы можете отправить ему эту ссылку:\n'
                    '{link}',
        'sms_not_sent': 'Пользователь не найден в боте.\n'
                        '(SMS не отправлено: {reason})\n'
                        '\n'
                        'Отправьте ему следующую ссылку для подтверждения:\n'
                        '\n'
                        '{link}',
        'debt_not_found': 'Долг не найден или уже обработан.',
        'debt_confirmed_by_you': '✅ <b>Долг подтверждён!</b>\n'
                                 '\n'
                                 '👤 Кто: <b>{name}</b>\n'
                                 '💰 Сумма: <b>{amount} {currency}</b>\n'
                                 '{desc_line}Теперь долг активен.',
        'debt_confirmed_by_other': '✅ <b>{name}</b> подтвердил(а) долг!\n'
                                   '\n'
                                   '💰 Сумма: <b>{amount} {currency}</b>\n'
                                   '{desc_line}Теперь долг активен.',
        'debt_rejected_by_you': '❌ <b>Долг отклонён!</b>\n'
                                '\n'
                                '👤 Кто: <b>{name}</b>\n'
                                '💰 Сумма: <b>{amount} {currency}</b>\n'
                                '{desc_line}',
        'debt_rejected_by_other': '❌ <b>{name}</b> отклонил(а) запрос на долг!\n'
                                  '\n'
                                  '💰 Сумма: <b>{amount} {currency}</b>\n'
                                  '{desc_line}',
        'no_active_debtors': 'Вам никто не должен (нет активных долгов).',
        'no_active_creditors': 'Вы никому не должны (нет активных долгов).',
        'choose_person_income': 'От кого вы получили деньги? Выберите:',
        'choose_person_outcome': 'Кому вы заплатили? Выберите:',
        'enter_payment_amount': 'Введите сумму (максимум: {max_amount} {currency}):',
        'invalid_payment_amount': 'Неверная сумма. Введите число больше 0 и не более {max_amount}:',
        'payment_type_income': 'передал(а) вам деньги',
        'payment_type_outcome': 'получил(а) от вас деньги / вы оплатили',
        'payment_confirm_request': '🔔 <b>{name}</b> указал(а), что {type}.\n'
                                   'Сумма: <b>{amount} {currency}</b>\n'
                                   '\n'
                                   'Подтверждаете?',
        'payment_request_sent': 'Запрос отправлен. Ожидайте подтверждения.',
        'payment_confirmed_by_you': '✅ <b>Платёж подтверждён!</b>\n'
                                    '\n'
                                    '👤 Кто: <b>{name}</b>\n'
                                    '💰 Сумма платежа: <b>{amount} {currency}</b>\n'
                                    '📋 Общий долг: <b>{total} {currency}</b>\n'
                                    '{desc_line}{status_line}',
        'payment_confirmed_by_other': '✅ <b>{name}</b> подтвердил(а) платёж!\n'
                                      '\n'
                                      '💰 Подтверждённая сумма: <b>{amount} {currency}</b>\n'
                                      '📋 Общий долг: <b>{total} {currency}</b>\n'
                                      '{desc_line}{status_line}',
        'debt_fully_closed': '🎉 Долг полностью закрыт!',
        'debt_partially_closed': '📊 Остаток долга: <b>{remaining} {currency}</b>',
        'payment_rejected_by_you': '❌ <b>Платёж отклонён!</b>\n'
                                   '\n'
                                   '👤 Кто: <b>{name}</b>\n'
                                   '💰 Отклонённая сумма: <b>{amount} {currency}</b>\n'
                                   '📋 Общий долг: <b>{total} {currency}</b>\n'
                                   '{desc_line}',
        'payment_rejected_by_other': '❌ <b>{name}</b> отклонил(а) платёж!\n'
                                     '\n'
                                     '💰 Отклонённая сумма: <b>{amount} {currency}</b>\n'
                                     '📋 Общий долг: <b>{total} {currency}</b>\n'
                                     '{desc_line}',
        'debt_reminder': '⏰ Уважаемый пользователь, у вас есть долг перед <b>{name}</b> в размере <b>{amount} '
                         '{currency}</b>. Пожалуйста, постарайтесь погасить его как можно скорее. 🙏',
        'donat_text': '💝 <b>Донат</b>\n'
                      '\n'
                      'Если бот был вам полезен, вы можете перевести любую сумму на карту:\n'
                      '\n'
                      '💳 <b>Номер карты:</b>\n'
                      '<code>9860 2601 0101 9743</code>\n'
                      '\n'
                      '👤 <b>Владелец карты:</b> Dilmurod Rustamov\n'
                      '\n'
                      'Спасибо! 🙏',
        'settings_title': '⚙️ <b>Настройки</b>\n\nИзмените настройки ниже:',
        'btn_change_language': '🌐 Изменить язык',
        'choose_new_language': 'Выберите новый язык:',
        'language_changed': '✅ Язык успешно изменён!',
        'not_admin': 'Эта команда доступна только администратору.',
        'admin_stats': '📊 <b>Статистика</b>\n'
                       '\n'
                       '👤 Всего пользователей: {total_users}\n'
                       '💳 Активных долгов: {active_debts}\n'
                       '💰 Общий оборот (UZS): {total_uzs}\n'
                       '💵 Общий оборот (USD): {total_usd}',
        'broadcast_prompt': 'Введите текст сообщения для рассылки всем пользователям:',
        'broadcast_preview': 'Это сообщение будет отправлено всем пользователям:\n\n{text}',
        'broadcast_done': '✅ Отправлено: {sent}.\n❌ Ошибок: {failed}.',
        'broadcast_cancelled': 'Рассылка отменена.',
        'btn_personal_finance': '💼 Личные финансы',
        'fin_main_menu': '💼 <b>Центр личных финансов</b>\n'
                         '\n'
                         'В этом разделе вы можете полностью контролировать свои доходы и расходы.\n'
                         '\n'
                         '⚡️ <b>Быстрый ввод:</b>\n'
                         'Вы можете отправить сообщение в любой момент:\n'
                         '• <code>-50k такси</code>\n'
                         '• <code>+5mln зарплата</code>\n'
                         '• <code>-120 000 базар</code>\n'
                         '• <code>+100$ бонус</code>\n'
                         '• <code>35000 обед</code>\n'
                         '\n'
                         'Используйте кнопки ниже 👇',
        'fin_btn_income': '➕ Добавить доход',
        'fin_btn_expense': '➖ Добавить расход',
        'fin_btn_balance': '💼 Баланс',
        'fin_btn_history': '📜 История расходов',
        'fin_btn_report': '📊 Отчет',
        'fin_enter_amount': '💰 <b>Введите сумму ({type_text}):</b>\n<i>Например: 50 000, 100k, 2.5 mln или 100$</i>',
        'fin_choose_currency': '💵 <b>Выберите валюту:</b>',
        'fin_choose_category': '📂 <b>Выберите категорию:</b>',
        'fin_enter_custom_category': '✏️ <b>Введите название новой категории:</b>',
        'fin_enter_note': '📝 <b>Введите комментарий (необязательно):</b>\n'
                          '<i>Например: бензин, обед, продукты...</i>\n'
                          'Если комментарий не нужен, нажмите «➡️ Пропустить»:',
        'fin_choose_date': '📅 <b>Выберите дату или введите в формате ДД.ММ.ГГГГ (например: 06.10.2026):</b>',
        'fin_saved_success': '✅ <b>{type_title} успешно сохранено!</b>\n'
                             '\n'
                             '{sign} <b>{amount} {currency}</b>\n'
                             '📂 Категория: <b>{category}</b>\n'
                             '📝 Комментарий: <i>{note}</i>\n'
                             '📅 Дата: <b>{date}</b>',
        'fin_deleted_success': '🗑 <b>Запись успешно удалена!</b>',
        'fin_updated_success': '✅ <b>Запись обновлена!</b>',
        'fin_tx_not_found': 'Запись не найдена или удалена.',
        'fin_period_today': '📅 Сегодня',
        'fin_period_week': '🗓 Эта неделя',
        'fin_period_month': '📊 Этот месяц',
        'fin_period_all': '📈 Все время',
        'btn_report': '📊 Отчеты',
        'report_main_title': '📊 <b>Центр финансовых отчетов</b>',
        'btn_guide': '📹 Инструкция',
        'video_guide_caption': '📹 <b>Видео-инструкция по использованию бота «Temir Daftar»</b>\n\nВ этом видео показаны все возможности бота: учет долгов, личные финансы (доходы/расходы) и отчеты.',
        'video_guide_text': '📹 <b>Руководство по использованию бота «Temir Daftar»</b>\n\n'
                            '1️⃣ <b>Учет долгов:</b>\n'
                            '• Добавляйте долги через «📥 Взял в долг» или «📤 Дал в долг».\n'
                            '• Укажите телефон или @username второй стороны.\n'
                            '• Бот автоматически напомнит о наступлении срока.\n\n'
                            '2️⃣ <b>Личные финансы:</b>\n'
                            '• Учитывайте ежедневные доходы и расходы.\n'
                            '• Быстрый ввод: <code>-50k такси</code> или <code>+5mln зарплата</code>!\n\n'
                            '3️⃣ <b>Отчеты и Аналитика:</b>\n'
                            '• Смотрите финансовую аналитику в разделе «📊 Отчеты».\n\n'
                            '🎥 <i>Ссылка на видео-инструкцию:</i>\n{video_url}'},
 'kk': {'choose_language': 'Сәлеметсіз бе! 👋\nТілді таңдаңыз:',
        'invalid_language': 'Төмендегі түймелердің бірін таңдаңыз 👇',
        'name_request': 'Атыңыз бен тегіңізді енгізіңіз:',
        'age_request': 'Жасыңызды енгізіңіз (мысалы, 25):',
        'invalid_age': 'Дұрыс сан енгізіңіз (мысалы, 25):',
        'gender_request': 'Жынысыңызды таңдаңыз:',
        'btn_male': 'Еркек',
        'btn_female': 'Әйел',
        'country_request': 'Қай елденсіз?',
        'city_request': 'Қай қаладансыз?',
        'occupation_request': 'Кәсібіңіз немесе салаңыз қандай?',
        'invalid_name': 'Аты тым қысқа. Қайта енгізіңіз:',
        'phone_request': '📱 <b>Телефон нөміріңізді жіберіңіз:</b>\n'
                         '\n'
                         'Төмендегі «📱 Нөмірді жіберу» түймесін басыңыз немесе нөміріңізді жазыңыз (мысалы: '
                         '<code>+998901234567</code>).\n'
                         '\n'
                         '🔒 <i><b>Қауіпсіздік кепілдігі:</b> Сіздің нөміріңіз тек борышқор мен несие берушіні '
                         'байланыстыру үшін қолданылады. Бот құпия сөздер мен банк карталарына қол жеткізе '
                         'алмайды.</i>',
        'send_contact_btn': '📱 Нөмірді жіберу',
        'invalid_phone': 'Өтінеміз, «📱 Нөмірді жіберу» түймесі арқылы контакт жіберіңіз.',
        'invalid_contact': 'Өз контактіңізді жіберіңіз, басқа адамдікін емес.',
        'registered_welcome': 'Қош келдіңіз, {name}! ✅\nСіз сәтті тіркелдіңіз.',
        'main_menu_title': '🏠 Басты мәзір',
        'btn_creditors': '📥 Қарыз алдым',
        'btn_debtors': '📤 Қарыз бердім',
        'btn_history': '📊 Қарыздар тарихы',
        'btn_income': '📥 Кіріс',
        'btn_outcome': '📤 Шығыс',
        'btn_settings': '⚙️ Баптаулар',
        'btn_donat': '💝 Донат',
        'btn_cancel': '❌ Бас тарту',
        'btn_main_menu': '🏠 Басты мәзір',
        'btn_skip': '➡️ Өткізіп жіберу',
        'btn_confirm': '✅ Растау',
        'btn_reject': '❌ Қабылдамау',
        'btn_add_new': '➕ Жаңасын қосу',
        'enter_description': '📝 <b>Қарыз үшін түсініктеме енгізіңіз:</b>\n'
                             '<i>Мысалы: не үшін алынды немесе берілді (көлік жөндеу, айлық, тауар үшін...)</i>\n'
                             '\n'
                             'Егер түсініктеме қажет болмаса, «➡️ Өткізіп жіберу» түймесін басыңыз:',
        'no_creditors': 'Сізде әзірге несие берушілер жоқ (сіз қарыз болған адамдар).',
        'no_debtors': 'Сізде әзірге борышқорлар жоқ.',
        'creditors_title': '👥 <b>Несие берушілеріңіз</b> (сіз оларға қарызсыз):',
        'debtors_title': '👤 <b>Борышқорларыңыз</b> (олар сізге қарыз):',
        'pending_person': 'Күтілуде (әлі қосылмаған)',
        'status_pending': 'расталмаған',
        'status_active': 'белсенді',
        'no_history': 'Тарих әзірге бос.',
        'history_title': '📊 <b>Қарыздар тарихы</b> (соңғы 30):',
        'enter_recipient': 'Екінші тараптың телефон нөмірін (+99890...), Telegram ID, @username немесе контактісін '
                           'жіберіңіз:',
        'enter_alias': '👤 <b>Бұл адамға өзіңіз үшін ат (лақап ат / лақап) беріңіз:</b>\n'
                       '<i>Мысалы: Дилмурод банкир, Дилшод iPhone, Омар махалла</i>\n'
                       '\n'
                       '🔒 <i>Бұл атау тек өзіңізге көрінеді (екінші тарапқа көрінбейді).\n'
                       'Егер ат енгізгіңіз келмесе, «➡️ Өткізіп жіберу» түймесін басыңыз:</i>',
        'cancelled': 'Бас тартылды.',
        'cannot_add_self': 'Өзіңізді қоса алмайсыз.',
        'choose_currency': 'Валютаны таңдаңыз:',
        'enter_amount': '💰 <b>Қарыз сомасын енгізіңіз:</b>\n<i>Мысалы: 123 000 немесе 300 000</i>',
        'invalid_amount': 'Қате сома. Оң сан енгізіңіз (мысалы: 123 000 немесе 300 000):',
        'role_creditor': 'сізден қарыз алуды',
        'role_debtor': 'сізге қарыз беруді',
        'enter_due_date': 'Қарызды қайтару мерзімін таңдаңыз немесе КК.АА.ЖЖЖЖ форматында енгізіңіз (мысалы: 31.12.2026):',
        'invalid_due_date': 'Қате күн форматы. Өтініш, мерзімді КК.АА.ЖЖЖЖ форматында енгізіңіз (мысалы: 31.12.2026) немесе батырманы таңдаңыз:',
        'btn_1_week': '1 апта',
        'btn_1_month': '1 ай',
        'btn_no_due_date': 'Мерзімсіз',
        'debt_confirm_request': '🔔 <b>{name}</b> {role} білдірді.\nСомасы: <b>{amount} {currency}</b>\n\nРастайсыз ба?',
        'debt_incoming_request': '🔔 <b>{name}</b> сізге қарыз сұрауын жіберді.\n'
                                 'Сомасы: <b>{amount} {currency}</b>\n'
                                 '\n'
                                 'Растайсыз ба?',
        'debt_request_sent': 'Сұрау жіберілді. Растауын күтіңіз.',
        'debt_request_send_failed': 'Сұрауды жіберу мүмкін болмады. Мүмкін, пайдаланушы ботты бұғаттаған.',
        'debt_link_generated': 'Бұл пайдаланушы ботта табылмады.\n'
                               'Төмендегі сілтемені оған жіберіңіз, ол кіріп растаған соң қарыз белсенді болады:\n'
                               '\n'
                               '{link}',
        'sms_sent': '📱 Пайдаланушы ботта табылмады.\n'
                    '<b>+{phone}</b> нөміріне SMS хабарлама жіберілді!\n'
                    '\n'
                    'Сондай-ақ мына сілтемені де оған жібере аласыз:\n'
                    '{link}',
        'sms_not_sent': 'Пайдаланушы ботта табылмады.\n'
                        '(SMS жіберілмеді: {reason})\n'
                        '\n'
                        'Төмендегі сілтемені оған жіберіңіз, ол кіріп растаған соң қарыз белсенді болады:\n'
                        '\n'
                        '{link}',
        'debt_not_found': 'Бұл қарыз табылмады немесе қаралып қойылған.',
        'debt_confirmed_by_you': '✅ <b>Қарыз расталды!</b>\n'
                                 '\n'
                                 '👤 Кім: <b>{name}</b>\n'
                                 '💰 Сомасы: <b>{amount} {currency}</b>\n'
                                 '{desc_line}Енді қарыз белсенді.',
        'debt_confirmed_by_other': '✅ <b>{name}</b> қарызды растады!\n'
                                   '\n'
                                   '💰 Сомасы: <b>{amount} {currency}</b>\n'
                                   '{desc_line}Енді қарыз белсенді.',
        'debt_rejected_by_you': '❌ <b>Қарыз қабылданбады!</b>\n'
                                '\n'
                                '👤 Кім: <b>{name}</b>\n'
                                '💰 Сомасы: <b>{amount} {currency}</b>\n'
                                '{desc_line}',
        'debt_rejected_by_other': '❌ <b>{name}</b> қарыз сұрауын қабылдамады!\n'
                                  '\n'
                                  '💰 Сомасы: <b>{amount} {currency}</b>\n'
                                  '{desc_line}',
        'no_active_debtors': 'Сізге ешкім қарыз емес (белсенді қарыздар жоқ).',
        'no_active_creditors': 'Сіз ешкімге қарыз емессіз (белсенді қарыздар жоқ).',
        'choose_person_income': 'Кімнен ақша алдыңыз? Таңдаңыз:',
        'choose_person_outcome': 'Кімге төлем жасадыңыз? Таңдаңыз:',
        'enter_payment_amount': 'Соманы енгізіңіз (максимум: {max_amount} {currency}):',
        'invalid_payment_amount': 'Қате сома. 0-ден үлкен және {max_amount}-ден аспайтын сан енгізіңіз:',
        'payment_type_income': 'сізге ақша берді',
        'payment_type_outcome': 'сізден ақша алды / сіз төледіңіз',
        'payment_confirm_request': '🔔 <b>{name}</b> {type} деп білдірді.\n'
                                   'Сомасы: <b>{amount} {currency}</b>\n'
                                   '\n'
                                   'Растайсыз ба?',
        'payment_request_sent': 'Сұрау жіберілді. Растауын күтіңіз.',
        'payment_confirmed_by_you': '✅ <b>Төлем расталды!</b>\n'
                                    '\n'
                                    '👤 Кім: <b>{name}</b>\n'
                                    '💰 Төлем сомасы: <b>{amount} {currency}</b>\n'
                                    '📋 Жалпы қарыз: <b>{total} {currency}</b>\n'
                                    '{desc_line}{status_line}',
        'payment_confirmed_by_other': '✅ <b>{name}</b> төлемді растады!\n'
                                      '\n'
                                      '💰 Расталған сома: <b>{amount} {currency}</b>\n'
                                      '📋 Жалпы қарыз: <b>{total} {currency}</b>\n'
                                      '{desc_line}{status_line}',
        'debt_fully_closed': '🎉 Қарыз толық жабылды!',
        'debt_partially_closed': '📊 Қалған қарыз: <b>{remaining} {currency}</b>',
        'payment_rejected_by_you': '❌ <b>Төлем қабылданбады!</b>\n'
                                   '\n'
                                   '👤 Кім: <b>{name}</b>\n'
                                   '💰 Қабылданбаған сома: <b>{amount} {currency}</b>\n'
                                   '📋 Жалпы қарыз: <b>{total} {currency}</b>\n'
                                   '{desc_line}',
        'payment_rejected_by_other': '❌ <b>{name}</b> төлемді қабылдамады!\n'
                                     '\n'
                                     '💰 Қабылданбаған сома: <b>{amount} {currency}</b>\n'
                                     '📋 Жалпы қарыз: <b>{total} {currency}</b>\n'
                                     '{desc_line}',
        'debt_reminder': '⏰ Құрметті пайдаланушы, сізде <b>{name}</b> алдында <b>{amount} {currency}</b> мөлшерінде '
                         'қарыз бар. Оны мүмкіндігінше тезірек өтеуге тырысыңыз. 🙏',
        'donat_text': '💝 <b>Донат</b>\n'
                      '\n'
                      'Егер бот сізге пайдалы болса, кез келген соманы картаға аударуыңызға болады:\n'
                      '\n'
                      '💳 <b>Карта нөмірі:</b>\n'
                      '<code>9860 2601 0101 9743</code>\n'
                      '\n'
                      '👤 <b>Карта иесі:</b> Dilmurod Rustamov\n'
                      '\n'
                      'Рахмет! 🙏',
        'settings_title': '⚙️ <b>Баптаулар</b>\n\nТөмендегі баптауларды өзгертіңіз:',
        'btn_change_language': '🌐 Тілді өзгерту',
        'choose_new_language': 'Жаңа тілді таңдаңыз:',
        'language_changed': '✅ Тіл сәтті өзгертілді!',
        'not_admin': 'Бұл команда тек әкімші үшін.',
        'admin_stats': '📊 <b>Статистика</b>\n'
                       '\n'
                       '👤 Барлық пайдаланушылар: {total_users}\n'
                       '💳 Белсенді қарыздар саны: {active_debts}\n'
                       '💰 Жалпы айналым (UZS): {total_uzs}\n'
                       '💵 Жалпы айналым (USD): {total_usd}',
        'broadcast_prompt': 'Барлық пайдаланушыларға жіберілетін хабарлама мәтінін енгізіңіз:',
        'broadcast_preview': 'Бұл хабарлама барлық пайдаланушыларға жіберіледі:\n\n{text}',
        'broadcast_done': '✅ Жіберілді: {sent}.\n❌ Қателер: {failed}.',
        'broadcast_cancelled': 'Broadcast бас тартылды.',
        'btn_personal_finance': '💼 Жеке қаржы',
        'fin_main_menu': '💼 <b>Жеке қаржы орталығы</b>\n'
                         '\n'
                         'Бұл бөлімде жеке кірістер мен шығыстарды толық бақылай аласыз.\n'
                         '\n'
                         '⚡️ <b>Жылдам енгізу:</b>\n'
                         'Кез келген уақытта хабарлама жібере аласыз:\n'
                         '• <code>-50k такси</code>\n'
                         '• <code>+5mln айлық</code>\n'
                         '• <code>-120 000 базар</code>\n'
                         '• <code>+100$ бонус</code>\n'
                         '• <code>35000 түскі ас</code>\n'
                         '\n'
                         'Төмендегі түймелерді қолданыңыз 👇',
        'fin_btn_income': '➕ Кіріс қосу',
        'fin_btn_expense': '➖ Шығыс қосу',
        'fin_btn_balance': '💼 Баланс',
        'fin_btn_history': '📜 Шығыстар тарихы',
        'fin_btn_report': '📊 Есеп',
        'fin_enter_amount': '💰 <b>{type_text} сомасын енгізіңіз:</b>\n<i>Мысалы: 50 000, 100k, 2.5 mln немесе 100$</i>',
        'fin_choose_currency': '💵 <b>Валютаны таңдаңыз:</b>',
        'fin_choose_category': '📂 <b>Санатты таңдаңыз:</b>',
        'fin_enter_custom_category': '✏️ <b>Жаңа санат атауын енгізіңіз:</b>',
        'fin_enter_note': '📝 <b>Түсініктеме енгізіңіз (міндетті емес):</b>\n'
                          'Егер түсініктеме қажет болмаса, «➡️ Өткізіп жіберу» түймесін басыңыз:',
        'fin_choose_date': '📅 <b>Күнді таңдаңыз немесе КК.АА.ЖЖЖЖ форматында енгізіңіз:</b>',
        'fin_saved_success': '✅ <b>{type_title} сәтті сақталды!</b>\n'
                             '\n'
                             '{sign} <b>{amount} {currency}</b>\n'
                             '📂 Санат: <b>{category}</b>\n'
                             '📝 Түсініктеме: <i>{note}</i>\n'
                             '📅 Күні: <b>{date}</b>',
        'fin_deleted_success': '🗑 <b>Жазба сәтті жойылды!</b>',
        'fin_updated_success': '✅ <b>Жазба жаңартылды!</b>',
        'fin_tx_not_found': 'Жазба табылмады немесе жойылған.',
        'fin_period_today': '📅 Бүгін',
        'fin_period_week': '🗓 Осы апта',
        'fin_period_month': '📊 Осы ай',
        'fin_period_all': '📈 Барлық уақыт',
        'btn_report': '📊 Есептер',
        'report_main_title': '📊 <b>Қаржылық есептер орталығы</b>',
        'btn_guide': '📹 Нұсқаулық',
        'video_guide_caption': '📹 <b>«Temir Daftar» ботын пайдалану бойынша бейне-нұсқаулық</b>\n\nБұл бейнеде боттың барлық мүмкіндіктері көрсетілген: қарыздар есебі, жеке қаржы және есептер.',
        'video_guide_text': '📹 <b>«Temir Daftar» ботын пайдалану нұсқаулығы</b>\n\n'
                            '1️⃣ <b>Қарыздар есебі:</b>\n'
                            '• «📥 Қарыз алдым» немесе «📤 Қарыз бердім» батырмасы арқылы жаңа қарыз енгізіңіз.\n'
                            '• Екінші тараптың телефон нөмірін немесе @username енгізіңіз.\n'
                            '• Мерзімі келгенде бот автоматты түрде ескерту жібереді.\n\n'
                            '2️⃣ <b>Жеке қаржы:</b>\n'
                            '• Күнделікті кірістер мен шығыстарды есепке алыңыз.\n'
                            '• Жылдам енгізу: <code>-50k такси</code> немесе <code>+5mln жалақы</code>!\n\n'
                            '3️⃣ <b>Есептер мен Сараптама:</b>\n'
                            '• «📊 Есептер» бөлімінде қаржылық талдауды қараңыз.\n\n'
                            '🎥 <i>Бейне-нұсқаулық сілтемесі:</i>\n{video_url}'},
 'en': {'choose_language': 'Hello! 👋\nChoose your language:',
        'invalid_language': 'Please select one of the buttons below 👇',
        'name_request': 'Enter your first and last name:',
        'age_request': 'Enter your age (e.g., 25):',
        'invalid_age': 'Please enter a valid number (e.g., 25):',
        'gender_request': 'Select your gender:',
        'btn_male': 'Male',
        'btn_female': 'Female',
        'country_request': 'Which country are you from?',
        'city_request': 'Which city are you from?',
        'occupation_request': 'What is your profession or occupation?',
        'invalid_name': 'Name is too short. Please try again:',
        'phone_request': '📱 <b>Send your phone number:</b>\n'
                         '\n'
                         'Click the «📱 Send Contact» button below or type your number (e.g., '
                         '<code>+998901234567</code>).\n'
                         '\n'
                         '🔒 <i><b>Security Guarantee:</b> Your number is only used for identifying debt records '
                         'between parties. The bot has no access to personal passwords or bank cards.</i>',
        'send_contact_btn': '📱 Send Contact',
        'invalid_phone': 'Please use the «📱 Send Contact» button.',
        'invalid_contact': 'Please send your own contact.',
        'registered_welcome': 'Welcome, {name}! ✅\nYou have successfully registered.',
        'main_menu_title': '🏠 Main Menu',
        'btn_creditors': '📥 Borrowed',
        'btn_debtors': '📤 Lent',
        'btn_history': '📊 Debt History',
        'btn_income': '📥 Income',
        'btn_outcome': '📤 Outcome',
        'btn_settings': '⚙️ Settings',
        'btn_donat': '💝 Donate',
        'btn_cancel': '❌ Cancel',
        'btn_main_menu': '🏠 Main Menu',
        'btn_skip': '➡️ Skip',
        'btn_confirm': '✅ Confirm',
        'btn_reject': '❌ Reject',
        'btn_add_new': '➕ Add New',
        'enter_description': '📝 <b>Enter a description for the debt:</b>\n'
                             '<i>E.g., why it was given/taken (car repair, salary, goods...)</i>\n'
                             '\n'
                             'If no description is needed, click «➡️ Skip»:',
        'no_creditors': 'You have no creditors yet.',
        'no_debtors': 'You have no debtors yet.',
        'creditors_title': '👥 <b>Your Creditors</b> (you owe them):',
        'debtors_title': '👤 <b>Your Debtors</b> (they owe you):',
        'pending_person': 'Pending (not joined yet)',
        'status_pending': 'pending',
        'status_active': 'active',
        'no_history': 'History is empty.',
        'history_title': '📊 <b>Debt History</b> (last 30):',
        'enter_recipient': "Enter the second party's phone number (+99890...), Telegram ID, @username or send their "
                           'contact:',
        'enter_alias': '👤 <b>Enter a private alias / nickname for this person:</b>\n'
                       '<i>E.g.: Dilmurod banker, Dilshod iPhone, Umar neighborhood</i>\n'
                       '\n'
                       '🔒 <i>This name will only be visible to you (the other party will not see it).\n'
                       'If you do not want to set an alias, click «➡️ Skip»:</i>',
        'cancelled': 'Cancelled.',
        'cannot_add_self': 'You cannot add yourself.',
        'choose_currency': 'Choose currency:',
        'enter_amount': '💰 <b>Enter debt amount:</b>\n<i>E.g.: 123 000 or 300 000</i>',
        'invalid_amount': 'Invalid amount. Please enter a positive number (e.g.: 123 000 or 300 000):',
        'role_creditor': 'that you owe them',
        'role_debtor': 'that they owe you',
        'enter_due_date': 'Choose the debt return due date or enter in DD.MM.YYYY format (e.g. 31.12.2026):',
        'invalid_due_date': 'Invalid date format. Please enter in DD.MM.YYYY format (e.g. 31.12.2026) or select a button below:',
        'btn_1_week': '1 week',
        'btn_1_month': '1 month',
        'btn_no_due_date': 'No due date',
        'debt_confirm_request': '🔔 <b>{name}</b> indicated {role}.\n'
                                'Amount: <b>{amount} {currency}</b>\n'
                                '\n'
                                'Do you confirm?',
        'debt_incoming_request': '🔔 <b>{name}</b> sent you a debt request.\n'
                                 'Amount: <b>{amount} {currency}</b>\n'
                                 '\n'
                                 'Do you confirm?',
        'debt_request_sent': 'Request sent. Waiting for confirmation.',
        'debt_request_send_failed': 'Failed to send the request. The user might have blocked the bot.',
        'debt_link_generated': 'This user was not found in the bot.\n'
                               'Send them the following link. Once they confirm, the debt will be activated:\n'
                               '\n'
                               '{link}',
        'sms_sent': '📱 User not found in the bot.\n'
                    'An SMS notification was sent to <b>+{phone}</b>!\n'
                    '\n'
                    'You can also send them this link:\n'
                    '{link}',
        'sms_not_sent': 'User not found in the bot.\n'
                        '(SMS not sent: {reason})\n'
                        '\n'
                        'Send them the following link to confirm:\n'
                        '\n'
                        '{link}',
        'debt_not_found': 'Debt not found or already processed.',
        'debt_confirmed_by_you': '✅ <b>Debt confirmed!</b>\n'
                                 '\n'
                                 '👤 Who: <b>{name}</b>\n'
                                 '💰 Amount: <b>{amount} {currency}</b>\n'
                                 '{desc_line}The debt is now active.',
        'debt_confirmed_by_other': '✅ <b>{name}</b> confirmed the debt!\n'
                                   '\n'
                                   '💰 Amount: <b>{amount} {currency}</b>\n'
                                   '{desc_line}The debt is now active.',
        'debt_rejected_by_you': '❌ <b>Debt rejected!</b>\n'
                                '\n'
                                '👤 Who: <b>{name}</b>\n'
                                '💰 Amount: <b>{amount} {currency}</b>\n'
                                '{desc_line}',
        'debt_rejected_by_other': '❌ <b>{name}</b> rejected the debt request!\n'
                                  '\n'
                                  '💰 Amount: <b>{amount} {currency}</b>\n'
                                  '{desc_line}',
        'no_active_debtors': 'No one owes you (no active debts).',
        'no_active_creditors': "You don't owe anyone (no active debts).",
        'choose_person_income': 'From whom did you receive money? Choose:',
        'choose_person_outcome': 'To whom did you pay? Choose:',
        'enter_payment_amount': 'Enter amount (maximum: {max_amount} {currency}):',
        'invalid_payment_amount': 'Invalid amount. Enter a number greater than 0 and up to {max_amount}:',
        'payment_type_income': 'gave you money',
        'payment_type_outcome': 'received money from you / you paid',
        'payment_confirm_request': '🔔 <b>{name}</b> stated that they {type}.\n'
                                   'Amount: <b>{amount} {currency}</b>\n'
                                   '\n'
                                   'Do you confirm?',
        'payment_request_sent': 'Request sent. Waiting for confirmation.',
        'payment_confirmed_by_you': '✅ <b>Payment confirmed!</b>\n'
                                    '\n'
                                    '👤 Who: <b>{name}</b>\n'
                                    '💰 Payment amount: <b>{amount} {currency}</b>\n'
                                    '📋 Total debt: <b>{total} {currency}</b>\n'
                                    '{desc_line}{status_line}',
        'payment_confirmed_by_other': '✅ <b>{name}</b> confirmed the payment!\n'
                                      '\n'
                                      '💰 Confirmed amount: <b>{amount} {currency}</b>\n'
                                      '📋 Total debt: <b>{total} {currency}</b>\n'
                                      '{desc_line}{status_line}',
        'debt_fully_closed': '🎉 Debt fully closed!',
        'debt_partially_closed': '📊 Remaining debt: <b>{remaining} {currency}</b>',
        'payment_rejected_by_you': '❌ <b>Payment rejected!</b>\n'
                                   '\n'
                                   '👤 Who: <b>{name}</b>\n'
                                   '💰 Rejected amount: <b>{amount} {currency}</b>\n'
                                   '📋 Total debt: <b>{total} {currency}</b>\n'
                                   '{desc_line}',
        'payment_rejected_by_other': '❌ <b>{name}</b> rejected the payment!\n'
                                     '\n'
                                     '💰 Rejected amount: <b>{amount} {currency}</b>\n'
                                     '📋 Total debt: <b>{total} {currency}</b>\n'
                                     '{desc_line}',
        'debt_reminder': '⏰ Dear user, you have an active debt to <b>{name}</b> for the amount of <b>{amount} '
                         '{currency}</b>. Please try to pay it off as soon as possible. 🙏',
        'donat_text': '💝 <b>Donate</b>\n'
                      '\n'
                      'If this bot has been useful to you, you can transfer any amount to this card:\n'
                      '\n'
                      '💳 <b>Card number:</b>\n'
                      '<code>9860 2601 0101 9743</code>\n'
                      '\n'
                      '👤 <b>Cardholder:</b> Dilmurod Rustamov\n'
                      '\n'
                      'Thank you! 🙏',
        'settings_title': '⚙️ <b>Settings</b>\n\nChange your settings below:',
        'btn_change_language': '🌐 Change Language',
        'choose_new_language': 'Choose a new language:',
        'language_changed': '✅ Language successfully changed!',
        'not_admin': 'This command is for admins only.',
        'admin_stats': '📊 <b>Statistics</b>\n'
                       '\n'
                       '👤 Total users: {total_users}\n'
                       '💳 Active debts: {active_debts}\n'
                       '💰 Total volume (UZS): {total_uzs}\n'
                       '💵 Total volume (USD): {total_usd}',
        'broadcast_prompt': 'Enter the message to broadcast to all users:',
        'broadcast_preview': 'This message will be sent to all users:\n\n{text}',
        'broadcast_done': '✅ Sent: {sent}.\n❌ Errors: {failed}.',
        'broadcast_cancelled': 'Broadcast cancelled.',
        'btn_personal_finance': '💼 Personal Finance',
        'fin_main_menu': '💼 <b>Personal Finance Hub</b>\n'
                         '\n'
                         'Track and manage your personal income and expenses with ease.\n'
                         '\n'
                         '⚡️ <b>Quick Input:</b>\n'
                         'You can send a message anytime like:\n'
                         '• <code>-50k taxi</code>\n'
                         '• <code>+5mln salary</code>\n'
                         '• <code>-120 000 groceries</code>\n'
                         '• <code>+100$ bonus</code>\n'
                         '• <code>35000 lunch</code>\n'
                         '\n'
                         'Choose an option below 👇',
        'fin_btn_income': '➕ Add Income',
        'fin_btn_expense': '➖ Add Expense',
        'fin_btn_balance': '💼 Balance',
        'fin_btn_history': '📜 Expenses History',
        'fin_btn_report': '📊 Report',
        'fin_enter_amount': '💰 <b>Enter {type_text} amount:</b>\n<i>E.g.: 50 000, 100k, 2.5 mln or 100$</i>',
        'fin_choose_currency': '💵 <b>Select Currency:</b>',
        'fin_choose_category': '📂 <b>Select Category:</b>',
        'fin_enter_custom_category': '✏️ <b>Enter new category name:</b>',
        'fin_enter_note': '📝 <b>Enter note (optional):</b>\nIf no note is needed, click «➡️ Skip»:',
        'fin_choose_date': '📅 <b>Select date or enter DD.MM.YYYY format:</b>',
        'fin_saved_success': '✅ <b>{type_title} saved successfully!</b>\n'
                             '\n'
                             '{sign} <b>{amount} {currency}</b>\n'
                             '📂 Category: <b>{category}</b>\n'
                             '📝 Note: <i>{note}</i>\n'
                             '📅 Date: <b>{date}</b>',
        'fin_deleted_success': '🗑 <b>Transaction deleted successfully!</b>',
        'fin_updated_success': '✅ <b>Transaction updated!</b>',
        'fin_tx_not_found': 'Transaction not found or deleted.',
        'fin_period_today': '📅 Today',
        'fin_period_week': '🗓 This Week',
        'fin_period_month': '📊 This Month',
        'fin_period_all': '📈 All Time',
        'btn_report': '📊 Reports',
        'report_main_title': '📊 <b>Financial Reports Center</b>',
        'btn_guide': '📹 Video Guide',
        'video_guide_caption': '📹 <b>Video guide on using the «Temir Daftar» bot</b>\n\nThis video demonstrates all bot features: debt tracking, personal finances (income/expenses), and financial reports.',
        'video_guide_text': '📹 <b>«Temir Daftar» User Guide</b>\n\n'
                            '1️⃣ <b>Debt Tracking:</b>\n'
                            '• Add debts via «📥 Borrowed» or «📤 Lent».\n'
                            '• Enter the other party\'s phone number or @username.\n'
                            '• Automatic reminders on due dates.\n\n'
                            '2️⃣ <b>Personal Finance:</b>\n'
                            '• Track your daily income and expenses.\n'
                            '• Quick input: <code>-50k taxi</code> or <code>+5mln salary</code>!\n\n'
                            '3️⃣ <b>Reports & Analytics:</b>\n'
                            '• View financial stats in the «📊 Reports» section.\n\n'
                            '🎥 <i>Video guide link:</i>\n{video_url}'}}
