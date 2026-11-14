import asyncio
import random
import os
import threading
from flask import Flask
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import openai

# ==========================================
# သင့်ရဲ့ အချက်အလက်များ
# ==========================================
API_ID = 36255475 
API_HASH = 'f0d7017664d12f199d5683782f2bb0bb'
SESSION_STRING = '1BVtsOL0Bu1uSCTce9u9dzbkcaktoLBp-uMtkb2KRDr7Wkk4Ddz-PCnCcV_kfnOrVQCZcFrAvZA9HQkvI5CNVpYGyfxQDlpAYRx-QvneDVh1PJS0S3VvJ7PiYNQ83F2AeFYB5YVXNPdm5EcqK6LefhPEDnpxZn09kzob3lIZQGl6YzARcPBvV7ZfuwbXdBiHMDTeHN-qwEyENyUyeP6us2xKTgNhhmQA7PpAlNJyB4t1OhuwclYzB16Yxp4PQgMVpwNVE9ESkM1PPuLDdTf-J-fBcoku2Lyjg6GcaglbT_IsHVnnQ2nMfalxJslx-Dw1TjkM3q5h5iNoGLy-g6vAHt-vZCtSTZvw='

# သင့်ရဲ့ Groq API Key
GROQ_API_KEY = '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' 

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# Groq ကို သုံးဖို့ ပြင်ဆင်ခြင်း
openai.api_base = "https://api.groq.com/openai/v1"
openai.api_key = GROQ_API_KEY

# ==========================================
# Render အတွက် Web Server
# ==========================================
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ==========================================
# Telegram Bot Logic (AI)
# ==========================================
afk_enabled = False
user_states = {} 

WELCOME_MESSAGE = """မင်္ဂလာပါခင်ဗျာ။ 
ကျွန်တော် အခုလောလောဆယ် ဖုန်းနဲ့ ဝေးနေလို့ပါ။ 
စာလေးချန်ခဲ့ပေးပါဦးနော်။ 
ကျွန်တော် အဆင်ပြေတာနဲ့ ချက်ချင်း ပြန်ဆက်သွယ်ပေးပါ့မယ်ခင်ဗျာ။ 
စိတ်မဆိုးနော်။

🟢 ကျွန်တော့်ရဲ့ AI က မေးခွန်း ၁၀ ကြောင်းကို အပြည့်အဝ ဖြေပေးသွားပါမယ်။"""

LIMIT_MESSAGE = """သတ်မှတ်ချက် ပြည့်သွားပါပြီ။ 

ကျွန်တော် ပြန်ရောက်တာနဲ့ ဆက်သွယ်ပေးပါ့မယ်ခင်ဗျာ။
ကျေးဇူးတင်ပါတယ်။"""

@client.on(events.NewMessage(incoming=True))
async def handler(event):
    global afk_enabled
    if not event.is_private or event.out or not afk_enabled:
        return
        
    sender_id = event.sender_id
    
    # ပထမဆုံးစာ ပို့ချင်းမှာ မူလစာသား (Quote ပုံစံနဲ့) အရင်ပို့မယ်
    if sender_id not in user_states:
        user_states[sender_id] = {"count": 0}
        try:
            await event.mark_read()
            await asyncio.sleep(random.randint(2, 5)) 
            await event.reply(WELCOME_MESSAGE, reply_to=event.message.id)
        except Exception as e:
            print(f"Error replying: {e}")

    # AI နဲ့ ပြန်ဖြေမယ့်အပိုင်း (၁၀ ကြောင်း ကန့်သတ်ချက်)
    if user_states[sender_id]["count"] < 10:
        try:
            await event.mark_read()
            user_message = event.message.message
            
            # Groq ကို ခေါ်မယ် (သီးသန့် Thread နဲ့ run မယ်)
            response = await asyncio.to_thread(
                openai.ChatCompletion.create,
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "မင်းက ကျွန်တော့်ရဲ့ ကိုယ်ပိုင်လက်ထောက်ပါ။ မြန်မာလိုပဲ ယဉ်ယဉ်ကျေးကျေးနဲ့ ချိုချိုသာသာ ပြန်ဖြေပေးပါ။ အင်္ဂလိပ်လို လုံးဝ မပြန်ပါနဲ့။"},
                    {"role": "user", "content": user_message}
                ]
            )
            
            ai_reply = response.choices[0].message.content
            
            await asyncio.sleep(random.randint(5, 10)) 
            await event.reply(ai_reply, reply_to=event.message.id) 
            user_states[sender_id]["count"] += 1
            
        except Exception as e:
            print(f"Error replying: {e}")
            
    # ၁၀ ကြောင်း ပြည့်သွားရင် သတိပေးစာ ပို့မယ်
    elif user_states[sender_id]["count"] == 10:
        try:
            await event.mark_read()
            await asyncio.sleep(random.randint(2, 5))
            await event.reply(LIMIT_MESSAGE, reply_to=event.message.id)
            user_states[sender_id]["count"] += 1 
        except Exception as e:
            print(f"Error replying: {e}")

@client.on(events.NewMessage(outgoing=True, pattern=r'^/afk$'))
async def enable_afk(event):
    global afk_enabled, user_states
    afk_enabled = True
    user_states.clear()
    await event.reply("✅ AI AFK auto-replies are ON.")

@client.on(events.NewMessage(outgoing=True, pattern=r'^/back$'))
async def disable_afk(event):
    global afk_enabled, user_states
    afk_enabled = False
    user_states.clear()
    await event.reply("❌ AI AFK auto-replies are OFF.")

async def main():
    await client.start()
    print("Telegram Client with AI is running...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main())
