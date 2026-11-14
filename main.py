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
SESSION_STRING = '1BVtsOHIBuxNFoP5Fy9dB_U61OhCHTncB6F_nUfrjq3e3ZZ9GRPpOccFJPz3w0eHKSqCBSfBempqHDUgOVvrnEt393UYXpMTVAYbljT3RyXUb1_9YUMIVzmf-QIxjKy_Ab5770nUyADF6fPBwk97zKWO7ilFK1a2DufhQN31nrO3s72MQKBOVILmIN2WCg8AJ0wqAtM6gXCB3zig5f8-XQrJglNaULQgRkl3rWhv-cEcknVzQFvmL9Fv5oSwcWrks3kze2sGam1ZpLhWa6c4kI8qxwbniwUam8v7qZFlEHX7DQycl2JgDPlhiGGlsQBOmzjfN5EMjIk1mhxuhviw8wH9DqIhh_6w='
OPENROUTER_API_KEY = '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' 

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
ai_client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)

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

# ပထမဆုံး ပို့မယ့် စာသား
WELCOME_MESSAGE = """မင်္ဂလာပါခင်ဗျာ။ 
ကျွန်တော် အခုလောလောဆယ် ဖုန်းနဲ့ ဝေးနေလို့ပါ။ 
စာလေးချန်ခဲ့ပေးပါဦးနော်။ 
ကျွန်တော် အဆင်ပြေတာနဲ့ ချက်ချင်း ပြန်ဆက်သွယ်ပေးပါ့မယ်ခင်ဗျာ။ 
စိတ်မဆိုးနော်။

🟢 ကျွန်တော့်ရဲ့ AI က မေးခွန်း ၁၀ ကြောင်းကို အပြည့်အဝ ဖြေပေးသွားပါမယ်။"""

# စာကြောင်း ၁၀ ကြောင်း ပြည့်သွားရင် ပို့မယ့် စာသား
LIMIT_MESSAGE = """သတ်မှတ်ချက် ပြည့်သွားပါပြီ။ 

ကျွန်တော် ပြန်ရောက်တာနဲ့ ဆက်သွယ်ပေးပါ့မယ်ခင်ဗျာ။
ကျေးဇူးတင်ပါတယ်။"""

@client.on(events.NewMessage(incoming=True))
async def handler(event):
    global afk_enabled
    if not event.is_private or event.out or not afk_enabled:
        return
        
    sender_id = event.sender_id
    
    # အကယ်၍ ဒီလူက စကားမစသေးရင် (ပထမဆုံးစာ)
    if sender_id not in user_states:
        user_states[sender_id] = {"count": 0, "history": []}
        
        try:
            await event.mark_read()
            # ပထမဆုံး စာသားကို အရင်ပို့မယ်
            await asyncio.sleep(random.randint(2, 5)) # ခဏစောင့်
            await event.reply(WELCOME_MESSAGE)
        except Exception as e:
            print(f"Error replying: {e}")

    # AI နဲ့ ပြန်ဖြေမယ့်အပိုင်း (၁၀ ကြောင်း ကန့်သတ်ချက်)
    if user_states[sender_id]["count"] < 10:
        try:
            await event.mark_read()
            user_message = event.message.message
            
            # စကားပြောသမိုင်းကို သိမ်းထားမယ်
            user_states[sender_id]["history"].append({"role": "user", "content": user_message})
            
            # AI ဆီ မေးမယ်
            response = await ai_client.chat.completions.create(
                model="openrouter/free",
                messages=[
                    {"role": "system", "content": "မင်းက ကျွန်တော့်ရဲ့ ကိုယ်ပိုင်လက်ထောက်ပါ။ ကျွန်တော် အခု မအားလို့ မရှိပါဘူး။ ဒါကြောင့် စာပို့လာတဲ့သူကို ယဉ်ယဉ်ကျေးကျေးနဲ့ ချိုချိုသာသာ မြန်မာလိုပဲ ပြန်ဖြေပေးပါ။ ကျွန်တော် ပြန်ရောက်တာနဲ့ ဆက်သွယ်ပါ့မယ်လို့ ပြောပေးပါ။ အင်္ဂလိပ်လို လုံးဝ မပြန်ပါနဲ့။"}
                ] + user_states[sender_id]["history"]
            )
            
            ai_reply = response.choices[0].message.content
            
            # သမိုင်းထဲမှာ AI ရဲ့ အဖြေကို ထည့်မယ်
            user_states[sender_id]["history"].append({"role": "assistant", "content": ai_reply})
            
            # စက္ကန့် ၅ ကနေ ၁၀ အတွင်း စောင့်ပြီး ပြန်ပို့မယ် (Ban မခံရအောင်)
            await asyncio.sleep(random.randint(5, 10)) 
            await event.reply(ai_reply)
            
            # စကားပြောတဲ့ အရေအတွက် တိုးမယ်
            user_states[sender_id]["count"] += 1
            
        except Exception as e:
            print(f"Error replying: {e}")
            
    # အကယ်၍ ၁၀ ကြောင်း ပြည့်သွားရင်
    elif user_states[sender_id]["count"] == 10:
        try:
            await event.mark_read()
            await asyncio.sleep(random.randint(2, 5))
            await event.reply(LIMIT_MESSAGE)
            # နောက်တစ်ခါ ထပ်မပို့အောင် Count ကို ၁၁ ထားလိုက်မယ်
            user_states[sender_id]["count"] += 1 
        except Exception as e:
            print(f"Error replying: {e}")

@client.on(events.NewMessage(outgoing=True, pattern=r'^/afk$'))
async def enable_afk(event):
    global afk_enabled, user_states
    afk_enabled = True
    user_states.clear() # Reset လုပ်မယ်
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
