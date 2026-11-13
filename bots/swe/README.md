# SWE oylik test boti

Study World Education o'quv markazi talabalari uchun har oylik test. Test 4 bosqichdan iborat, o'quvchi bosqichini o'zi tanlaydi:

| Bosqich | Mavzular |
|---|---|
| 1 | Harflar, tashdid, tanvin, madd tabiiy, maxrajlar, harf sifatlari |
| 2 | Tajvid qoidalari va harflar |
| 3 | Harf sifatlari, tajvid qoidalari, Qur'ondan misollar (mushaf rasmi) |
| 4 | Qur'on, tajvid, aqida, fiqh |

Har bosqichda 20 savol (har mavzudan oson, o'rta va qiyin), har biriga 60 soniya, «Bilmayman» varianti bor. Daraja foizda: 40% gacha Boshlang'ich, 40–74% O'rta, 75%+ Yuqori.

## Ishlatish (test faqat dars vaqtida)
- Ustoz darsda botga yozadi: `/ochish Ahmadjon 40` (guruh nomi yoki starosta ismi) → bot 40 daqiqaga **4 xonali kod** beradi. Kod doskaga yoziladi.
- O'quvchi `/start` → ism → kod → bosqich → test. Kodsiz yoki dars tugagandan keyin test ochilmaydi.
- `/holat` — ochiq darslar, kodlar va nechta o'quvchi topshirgani. `/yopish` — hamma ochiq darslarni hozir yopish.
- Bu buyruqlar faqat adminlar uchun (`ADMIN_IDS`).

### Himoya
- Kod faqat ochiq dars vaqtida ishlaydi; har darsda yangi kod. Bot havolasi tarqalsa ham, koddan tashqari test ochilmaydi.
- Bir darsda bir o'quvchi testni faqat bir marta topshiradi; test o'rtasida `/start` bilan qayta boshlab bo'lmaydi.
- 5 marta noto'g'ri kod → 10 daqiqa blok (kodni taxmin qilib topishga qarshi).
- Savol xabarlari himoyalangan (`protect_content`): forward qilib, saqlab bo'lmaydi.
- To'g'ri javoblar o'quvchiga ko'rsatilmaydi; savollar har safar bankdan tasodifiy, variantlar aralash.

## O'qish (audio) topshirig'i
Test savollaridan keyin **bitta rasmda 4 ta so'z** chiqadi (har testda tasodifiy): 1-bosqich — Muallim soniydagi madd so'zlari, 2-bosqich — tashdid, tanvin, hamza va muqaddarali so'zlar, 3–4-bosqich — mushafdan so'z va iboralar. O'quvchi ularni o'qib **bitta ovozli xabar** yuboradi (3 s – 5 daqiqa).
Audio adminlarga so'zlar rasmi bilan **1–5 ⭐ tugmalari** bilan keladi; baho qo'yilgach o'quvchiga yuboriladi, bahoni o'zgartirish mumkin. O'qish bahosi test balliga qo'shilmaydi.
So'zlar: `reading.json` va `words/` papkasi.

## Savollar
`questions.json`: `topics`, `stages` (har bosqichda mavzu → ball → nechta savol), `levels`, `advice`, `questions`.
Har savolda `source` (kitob va sahifa) va `approved` bor. Botga faqat `"approved": true` savollar kiradi; bosqichga tasdiqlangan savol yetmasa, u «tayyorlanmoqda» bo'lib turadi. O'zgarishdan keyin `python -m pytest -q`.

## Server
- Render: build `pip install -r swe/requirements.txt`, start `python swe/bot.py` (webhook).
- Supabase (`kirish-test-bot` loyihasi): `swe_results` va `swe_sessions` jadvallari; `swe_*` funksiyalari orqali, `DB_SECRET` bilan.
