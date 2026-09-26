import os
import time
from telebot import apihelper
apihelper.CONNECT_TIMEOUT = 60
apihelper.READ_TIMEOUT = 60

import telebot
from google import genai
from PIL import Image

# التوكن الخاص ببوتك
TOKEN = "8986693714:AAHfo3JQOlpFUuHcmpyusNyc-eujmDJMyOQ"
bot = telebot.TeleBot(TOKEN)

# قراءة مفتاح جيميناي بطريقة آمنة من بيئة العمل أو وضعه مباشرة هنا للتجربة
API_KEY = os.getenv("GEMINI_API_KEY", "حطي_مفتاحك_هنا_لو_عايزة_تجربيه_مباشرة")
gemini_client = genai.Client(api_key=API_KEY)

users_file = "users_list.txt"

def save_and_track_user(message):
    try:
        user_id = str(message.from_user.id)
        first_name = message.from_user.first_name or ""
        last_name = message.from_user.last_name or ""
        full_name = f"{first_name} {last_name}".strip()
        if not full_name:
            full_name = "بدون اسم"
        
        content = ""
        if os.path.exists(users_file):
            with open(users_file, "r", encoding="utf-8") as f:
                content = f.read()
            
        if user_id not in content:
            with open(users_file, "a", encoding="utf-8") as f:
                f.write(f"ID: {user_id} - Name: {full_name}\n")
    except Exception:
        pass

@bot.message_handler(commands=['start'])
def send_welcome(message):
    save_and_track_user(message)
    bot.reply_to(message, "أهلاً بكِ يا سماء! أنا بوت Ai pro، جاهز أساعدك في أي سؤال، اسألي اللي تحبيه!")

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    try:
        save_and_track_user(message)
        bot.reply_to(message, "جاري التفكير والرد، ثواني...")
        
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=message.text
        )
        
        if response and response.text:
            bot.reply_to(message, response.text)
        else:
            bot.reply_to(message, "عذراً، لم أستطع توليد رد مناسب.")
            
    except Exception as e:
        bot.reply_to(message, f"عذراً، حدث خطأ: {e}")

@bot.message_handler(content_types=['photo'])
def handle_image(message):
    try:
        save_and_track_user(message)
        bot.reply_to(message, "جاري استقبال الصورة وفهمها، ثواني...")
        
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        image_path = "temp_image.jpg"
        with open(image_path, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        img = Image.open(image_path)
        user_caption = message.caption if message.caption else "اشرح لي ما تحويه هذه الصورة بالتفصيل."

        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[img, user_caption]
        )
        
        if response and response.text:
            bot.reply_to(message, response.text)
        else:
            bot.reply_to(message, "عذراً، لم أتمكن من تحليل الصورة.")
        
    except Exception as e:
        bot.reply_to(message, f"عذراً، حدث خطأ في معالجة الصورة: {e}")

bot.remove_webhook()
bot.infinity_polling(timeout=60, long_polling_timeout=60)