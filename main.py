import os
from dotenv import load_dotenv
from bale import Bot, Message
from fastapi import FastAPI
import asyncio

load_dotenv()
TOKEN = os.getenv("BALE_TOKEN")
if not TOKEN:
    raise RuntimeError("متغیر محیطی BALE_TOKEN پیدا نشد")

bot = Bot(token=TOKEN)
app = FastAPI()

user_data = {}

# مراحل گفتگو
(
    GET_PARTICIPATION,
    GET_CAR_PRICE,
    GET_PROFIT,
    ASK_DIVIDE,
    END
) = range(5)

def format_number(number):
    return "{:,}".format(int(number))

def convert_to_million_billion(number):
    number = float(number)
    if number >= 1_000_000_000:
        return f"{number / 1_000_000_000:.1f} میلیارد"
    elif number >= 1_000_000:
        return f"{number / 1_000_000:.1f} میلیون"
    else:
        return f"{number:.0f}"

@app.get("/")
async def root():
    return {"message": "ربات بله فعال است"}

@bot.event
async def on_ready():
    print(f"{bot.user} is ready!")

@bot.event
async def on_message(message: Message):
    chat_id = message.chat.id
    text = message.text.strip().lower()

    if text == "/start":
        await message.reply("سلام! برای محاسبه سود شراکت، لطفاً *سهم خود* را به تومان وارد کنید (مثلاً 50,000,000):")
        user_data[chat_id] = {"state": GET_PARTICIPATION}

    elif chat_id in user_data:
        current_state = user_data[chat_id]["state"]

        if current_state == GET_PARTICIPATION:
            try:
                participation = float(text.replace(",", ""))
                formatted_num = format_number(participation)
                readable_num = convert_to_million_billion(participation)
                await message.reply(
                    f"مبلغ واردشده: {formatted_num} تومان\n"
                    f"({readable_num} تومان)\n\n"
                    "حالا قیمت *کل ماشین* را به تومان وارد کنید:"
                )
                user_data[chat_id].update({
                    "participation": participation,
                    "state": GET_CAR_PRICE
                })
            except ValueError:
                await message.reply("لطفاً یک عدد معتبر وارد کنید (مثلاً 50,000,000)!")

        elif current_state == GET_CAR_PRICE:
            try:
                car_price = float(text.replace(",", ""))
                formatted_num = format_number(car_price)
                readable_num = convert_to_million_billion(car_price)
                await message.reply(
                    f"مبلغ واردشده: {formatted_num} تومان\n"
                    f"({readable_num} تومان)\n\n"
                    "میزان *سود کل* را به تومان وارد کنید:"
                )
                user_data[chat_id].update({
                    "car_price": car_price,
                    "state": GET_PROFIT
                })
            except ValueError:
                await message.reply("لطفاً یک عدد معتبر وارد کنید (مثلاً 500,000,000)!")

        elif current_state == GET_PROFIT:
            try:
                total_profit = float(text.replace(",", ""))
                participation = user_data[chat_id]["participation"]
                car_price = user_data[chat_id]["car_price"]

                user_share = (participation / car_price) * total_profit
                formatted_share = format_number(user_share)
                readable_share = convert_to_million_billion(user_share)

                await message.reply(
                    f"✅ سهم شما از سود:\n"
                    f"{formatted_share} تومان\n"
                    f"({readable_share} تومان)\n\n"
                    "آیا می‌خواهید این عدد بر *دو* تقسیم شود؟ (بله/خیر)"
                )
                user_data[chat_id].update({
                    "user_share": user_share,
                    "state": ASK_DIVIDE
                })
            except ValueError:
                await message.reply("لطفاً یک عدد معتبر وارد کنید (مثلاً 200,000,000)!")

        elif current_state == ASK_DIVIDE:
            if text == "بله":
                user_share = user_data[chat_id]["user_share"]
                divided_share = user_share / 2
                formatted_share = format_number(divided_share)
                readable_share = convert_to_million_billion(divided_share)

                await message.reply(
                    f"✅ سهم شما پس از تقسیم:\n"
                    f"{formatted_share} تومان\n"
                    f"({readable_share} تومان)\n\n"
                    "محاسبه پایان یافت. برای شروع مجدد /start را بفرستید."
                )
                del user_data[chat_id]
            elif text == "خیر":
                await message.reply("محاسبه پایان یافت. برای شروع مجدد /start را بفرستید.")
                del user_data[chat_id]
            else:
                await message.reply("لطفاً فقط «بله» یا «خیر» وارد کنید!")
    else:
        await message.reply("برای شروع، /start را ارسال کنید.")

async def start_bot():
    await bot.start()

if __name__ == "__main__":
    import uvicorn
    loop = asyncio.get_event_loop()
    loop.create_task(start_bot())
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
