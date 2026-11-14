import asyncio
import random
import os
import threading
from flask import Flask
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from google import genai
from google.genai import types

# ==========================================
# သင့်ရဲ့ အချက်အလက်များ
# ==========================================
API_ID = 36255475 
API_HASH = 'f0d7017664d12f199d5683782f2bb0bb'
SESSION_STRING = '1BVtsOHIBuxNFoP5Fy9dB_U61OhCHTncB6F_nUfrjq3e3ZZ9GRPpOccFJPz3w0eHKSqCBSfBempqHDUgOVvrnEt393UYXpMTVAYbljT3RyXUb1_9YUMIVzmf-QIxjKy_Ab5770nUyADF6fPBwk97zKWO7ilFK1a2DufhQN31nrO3s72MQKBOVILmIN2WCg8AJ0wqAtM6gXCB3zig5f8-XQrJglNaULQgRkl3rWhv-cEcknVzQFvmL9Fv5oSwcWrks3kze2sGam1ZpLhWa6c4kI8qxwbniwUam8v7qZFlEHX7DQycl2JgDPlhiGGlsQBOmzjfN5EMjIk1mhxuhviw8wH9DqIhh_6w='

# သင့်ရဲ့ Gemini API Key
GEMINI_API_KEY = 'AQ.Ab8RN6KPjIHqBH3mwrp7L2M6xqSJfZa8VxK4rxmTKEU69CBzLQ' 

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
ai_client = genai.Client(api_key=GEMINI_API_KEY)

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
    
    # ပထမဆုံးစာ ပို့ချင်းမှာ မူလစာသား အရင်ပို့မယ် (Quote ပုံစံနဲ့)
    if sender_id not in user_states:
        user_states[sender_id] = {"count": 0}
        try:
            await event.mark_read()
            await asyncio.sleep(random.randint(2, 5)) 
            await event.reply(WELCOME_MESSAGE, reply_to=event.message.id) # Quote လုပ်ရန်
        except Exception as e:
            print(f"Error replying: {e}")

    # AI နဲ့ ပြန်ဖြေမယ့်အပိုင်း (၁၀ ကြောင်း ကန့်သတ်ချက်)
    if user_states[sender_id]["count"] < 10:
        try:
            await event.mark_read()
            user_message = event.message.message
            
            response = await asyncio.to_thread(
                ai_client.models.generate_content,
                model='gemini-2.5-flash',
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction="မင်းက ကျွန်တော့်ရဲ့ ကိုယ်ပိုင်လက်ထောက်ပါ။ မြန်မာလိုပဲ ယဉ်ယဉ်ကျေးကျေးနဲ့ ချိုချိုသာသာ ပြန်ဖြေပေးပါ။ အင်္ဂလိပ်လို လုံးဝ မပြန်ပါနဲ့။"
                )
            )
            
            ai_reply = response.text
            
            await asyncio.sleep(random.randint(5, 10)) 
            # AI ရဲ့ အဖြေကိုလည်း Quote ပုံစံနဲ့ပဲ ပြန်မယ်
            await event.reply(ai_reply, reply_to=event.message.id) 
            user_states[sender_id]["count"] += 1
            
        except Exception as e:
            print(f"Error replying: {e}")
            
    # ၁၀ ကြောင်း ပြည့်သွားရင်
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
