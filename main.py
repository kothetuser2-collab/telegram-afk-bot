import asyncio
import random
import os
import threading
from datetime import datetime, timedelta
from flask import Flask
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from openai import AsyncOpenAI

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
ai_client = AsyncOpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY
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
user_cooldowns = {}  

WELCOME_MESSAGE = """✅ **Auto Reply**
━━━━━━━━━━━━━━━
မင်္ဂလာပါခင်ဗျာ။ 
ကျွန်တော် အခုလောလောဆယ် ဖုန်းနဲ့ ဝေးနေလို့ပါ။ 
စာလေးချန်ခဲ့ပေးပါဦးနော်။ 
ကျွန်တော် အဆင်ပြေတာနဲ့ ချက်ချင်း ပြန်ဆက်သွယ်ပေးပါ့မယ်ခင်ဗျာ။ 
စိတ်မဆိုးနော်။
━━━━━━━━━━━━━━━
🤖 **AI နဲ့ စကားပြောလိုပါက "ဟုတ်ကဲ့" လို့ ပြန်ပို့ပြီး စကားပြောနိုင်ပါတယ်။**
🟢 ကျွန်တော့်ရဲ့ AI က မေးခွန်း ၁၀၀ ကြောင်းကို အပြည့်အဝ ဖြေပေးသွားပါမယ်။"""

LIMIT_MESSAGE = """🛑 **သတ်မှတ်ချက် ပြည့်သွားပါပြီ** 
━━━━━━━━━━━━━━━
ကျွန်တော် ပြန်ရောက်တာနဲ့ ဆက်သွယ်ပေးပါ့မယ်ခင်ဗျာ။
ကျေးဇူးတင်ပါတယ်။"""

@client.on(events.NewMessage(incoming=True))
async def handler(event):
    global afk_enabled
    if not event.is_private or event.out or not afk_enabled:
        return

    # သင့်အကောင့် Online ဖြစ်နေလား စစ်ဆေးမယ်
    try:
        me = await client.get_me()
        if me.status and me.status.__class__.__name__ == 'UserStatusOnline':
            # သင် Online ဖြစ်နေရင် ဘာမှ ပြန်မဖြေဘူး
            return
    except Exception as e:
        print(f"Error checking status: {e}")
        
    sender_id = event.sender_id
    now = datetime.now()

    # သူငယ်ချင်းကို ၂၄ နာရီ ပိတ်ထားခြင်း ရှိမရှိ စစ်မယ်
    if sender_id in user_cooldowns:
        cooldown_end = user_cooldowns[sender_id]
        if now < cooldown_end:
            return
        else:
            del user_cooldowns[sender_id]
            if sender_id in user_states:
                del user_states[sender_id]

    # ပထမဆုံးစာ ပို့ချင်းမှာ မူလစာသား (Quote ပုံစံနဲ့) အရင်ပို့မယ်
    if sender_id not in user_states:
        user_states[sender_id] = {
            "count": 0, 
            "history": [],
            "last_message_time": now
        }
        try:
            await event.mark_read()
            await asyncio.sleep(random.randint(2, 5)) 
            await event.reply(WELCOME_MESSAGE, reply_to=event.message.id, parse_mode='md') 
        except Exception as e:
            print(f"Error replying: {e}")

    # ၅ မိနစ် စောင့်ဆိုင်းချိန် စစ်ဆေးခြင်း
    time_diff = (now - user_states[sender_id]["last_message_time"]).total_seconds()
    
    if time_diff > 300:  # ၅ မိနစ်
        user_cooldowns[sender_id] = now + timedelta(hours=24)
        try:
            await event.mark_read()
            await asyncio.sleep(2)
            cooldown_msg = "🛑 **စကားပြောချိန် ၅ မိနစ် ကျော်သွားပါပြီ။**\n\nသင့်အကောင့်ကို ၂၄ နာရီ ပိတ်ထားပါမယ်။ ၂၄ နာရီ ပြည့်မှ ပြန်လည် စကားပြောနိုင်ပါမယ်။"
            await event.reply(cooldown_msg, reply_to=event.message.id, parse_mode='md')
        except Exception as e:
            print(f"Error replying: {e}")
        return

    user_states[sender_id]["last_message_time"] = now

    if user_states[sender_id]["count"] < 100:
        try:
            await event.mark_read()
            user_message = event.message.message
            
            user_states[sender_id]["history"].append({"role": "user", "content": user_message})
            
            if len(user_states[sender_id]["history"]) > 10:
                user_states[sender_id]["history"] = user_states[sender_id]["history"][-10:]
            
            response = await ai_client.chat.completions.create(
                model="openai/gpt-oss-20b", 
                messages=[
                    {"role": "system", "content": "မင်းက ကျွန်တော့်ရဲ့ ကိုယ်ပိုင်လက်ထောက်ပါ။ မြန်မာလိုပဲ ယဉ်ယဉ်ကျေးကျေးနဲ့ ချိုချိုသာသာ ပြန်ဖြေပေးပါ။ အင်္ဂလိပ်လို လုံးဝ မပြန်ပါနဲ့။"},
                ] + user_states[sender_id]["history"]
            )
            
            ai_reply = response.choices[0].message.content
            user_states[sender_id]["history"].append({"role": "assistant", "content": ai_reply})
            
            formatted_ai_reply = f"🤖 **AI Reply**\n━━━━━━━━━━━━━━━\n{ai_reply}\n━━━━━━━━━━━━━━━"
            
            await asyncio.sleep(random.randint(3, 7)) 
            await event.reply(formatted_ai_reply, reply_to=event.message.id, parse_mode='md') 
            user_states[sender_id]["count"] += 1
            
        except Exception as e:
            print(f"Error replying: {e}")
            
    elif user_states[sender_id]["count"] == 100:
        try:
            await event.mark_read()
            await asyncio.sleep(random.randint(2, 5))
            await event.reply(LIMIT_MESSAGE, reply_to=event.message.id, parse_mode='md')
            user_states[sender_id]["count"] += 1 
        except Exception as e:
            print(f"Error replying: {e}")

@client.on(events.NewMessage(outgoing=True, pattern=r'^/afk$'))
async def enable_afk(event):
    global afk_enabled, user_states, user_cooldowns
    afk_enabled = True
    user_states.clear()
    user_cooldowns.clear()
    await event.reply("✅ AI AFK auto-replies are ON.")

@client.on(events.NewMessage(outgoing=True, pattern=r'^/back$'))
async def disable_afk(event):
    global afk_enabled, user_states, user_cooldowns
    afk_enabled = False
    user_states.clear()
    user_cooldowns.clear()
    await event.reply("❌ AI AFK auto-replies are OFF.")

async def main():
    await client.start()
    print("Telegram Client with AI is running...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main())
