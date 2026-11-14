import asyncio
import random
import os
import threading
from flask import Flask
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from openai import AsyncOpenAI

# ==========================================
# သင့်ရဲ့ အချက်အလက်များ
# ==========================================
API_ID = 36255475 
API_HASH = 'f0d7017664d12f199d5683782f2bb0bb'
SESSION_STRING = '1BVtsOL0Bu4VH9X8If3KfbhUqQUuP55jnEzNmzzDMl-sS4jhBywoaVx6g2tHyXDUJWULVkhYU5Yrrfn1s4c98ceyYyEcju26971-JybbmNFE9qJfUu0rbZ4Z1rJTr8CjUtNWHAWq6Kt7sNGCy8iqzh5fXdpRKvThUTc3dhiNDgJaL6Fbe7GiMTko_bpLoGFaY5ej4ZHQXQzy7OU1u7PeeeKYX9X5EnFHrEX7903tL_aiezjnNtTJXuMTWZfwOpw306vSLCx0CJSaxT3wFra-ee5800zgCJzk4c1PSh9k6wiRrRlrhCDX5W3fHQ_cPY-0i6yxRPqqAb13Pv4pylBICOERhixDkIlg='

OPENROUTER_API_KEY = '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' 

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# OpenRouter ကို သုံးဖို့ ပြင်ဆင်ခြင်း
ai_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
    default_headers={
        "HTTP-Referer": "https://render.com", 
        "X-Title": "Telegram Bot"
    }
)

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
    
    if sender_id not in user_states:
        user_states[sender_id] = {"count": 0}
        try:
            await event.mark_read()
            await asyncio.sleep(random.randint(2, 5)) 
            await event.reply(WELCOME_MESSAGE, reply_to=event.message.id)
        except Exception as e:
            print(f"Error replying: {e}")

    if user_states[sender_id]["count"] < 10:
        try:
            await event.mark_read()
            user_message = event.message.message
            
            response = await ai_client.chat.completions.create(
                model="openrouter/free",
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
