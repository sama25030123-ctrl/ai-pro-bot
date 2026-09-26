import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
import time
from telebot import apihelper
apihelper.CONNECT_TIMEOUT = 60
apihelper.READ_TIMEOUT = 60

import telebot
from google import genai
from PIL import Image

# التوكن الصحيح الخاص بك
TOKEN = "8986693714:AAEcJP1URFpA8uYpld0Q2g8nIWvzqSE6wCI"
bot = telebot.TeleBot(TOKEN)

gemini_client = genai.Client(api_key="AQ.Ab8RN6IJ7b1tdwHeDQx9bCo9DAuV4NT-B0gFGFrHoy1L9tADtg")

users_file = "users_list.txt"
user_chats = {}

def get_user_chat(user_id):
    if user_id not in user_chats:
        system_instruction = (
            "أنت مساعد ذكي وودود جداً، اسمك 'My AI'. مهمتك هي مساعدة الطلاب والمستخدمين "
            "في تلخيص النصوص، شرح الصور بدقة، وفهم التسجيلات الصوتية، والإجابة على أي أسئلة بأسلوب منظم وواضح باللغة العربية."
        )
        user_chats[user_id] = gemini_client.chats.create(
            model='gemini-2.5-flash',
            config={
                'system_instruction': system_instruction,
            }
        )
    return user_chats[user_id]

def track_user(message):
    user_id = str(message.from_user.id)
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""
    full_name = f"{first_name} {last_name}".strip()
    if not full_name:
        full_name = "بدون اسم"
    
    try:
        if os.path.exists(users_file):
            with open(users_file, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            content = ""
    except Exception:
        content = ""
        
    if user_id not in content:
        with open(users_file, "a", encoding="utf-8") as f:
            f.write(f"ID: {user_id} - Name: {full_name}\n")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    track_user(message)
    user_id = message.chat.id
    user_chats.pop(user_id, None)
    bot.reply_to(message, "أهلاً بكِ يا سماء، أنا بوت 'My AI' الذكي جاهز لمساعدتك في كل حاجة؛ اسأليني، ابعتي صور، أو ريكوردات وهكون معاكي وفاكر كلامنا كله! 🚀")

@bot.message_handler(content_types=['photo'])
def handle_image(message):
    track_user(message)
    try:
        user_id = message.chat.id
        bot.reply_to(message, "جاري استقبال الصورة وفهمها، ثواني...")
        
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        image_path = "temp_image.jpg"
        with open(image_path, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        img = Image.open(image_path)
        user_caption = message.caption if message.caption else "اشرح لي ما تحويه هذه الصورة بالتفصيل وأجب على أي سياق مطلوب."

        chat = get_user_chat(user_id)
        response = chat.send_message([img, user_caption])

        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, f"عذراً، حدث خطأ أثناء معالجة الصورة: {e}")

@bot.message_handler(content_types=['voice', 'audio'])
def handle_audio(message):
    track_user(message)
    try:
        user_id = message.chat.id
        bot.reply_to(message, "جاري استقبال الريكورد وسماعه، ثواني...")
        
        file_info = bot.get_file(message.voice.file_id if message.voice else message.audio.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        audio_path = "temp_audio.ogg"
        with open(audio_path, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        # رفع الملف الصوتي لـ Gemini لمعالجته وفهمه مباشرة
        audio_file_ref = gemini_client.files.upload(file=audio_path)
        
        chat = get_user_chat(user_id)
        response = chat.send_message([audio_file_ref, "استمع إلى هذا التسجيل الصوتي بدقة، ولخصه، وأجب عما ورد فيه باللغة العربية."])

        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, f"عذراً، حدث خطأ أثناء معالجة الريكورد: {e}")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    track_user(message)
    user_id = message.chat.id
    user_text = message.text
    
    bot.reply_to(message, "جاري التفكير والرد، ثواني...")
    chat = get_user_chat(user_id)
    
    try:
        response = chat.send_message(user_text)
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, f"عذراً، حدث خطأ: {e}")

print("البوت يعمل الآن بكامل الميزات...")
bot.remove_webhook()
bot.infinity_polling(timeout=60, long_polling_timeout=60)