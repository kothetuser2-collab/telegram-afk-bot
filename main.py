import asyncio
import random
import os
import threading
from datetime import datetime, timedelta, timezone
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
ai_client = AsyncOpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_API_KEY)

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

@client.on(events.NewMessage(incoming=True))
async def handler(event):
    global afk_enabled
    if not event.is_private or event.out or not afk_enabled:
        return

    sender_id = event.sender_id
    sender = await event.get_sender()
    sender_name = sender.first_name if sender.first_name else "သူငယ်ချင်း"
    
    # မြန်မာစံတော်ချိန် (UTC + 6:30)
    mm_timezone = timezone(timedelta(hours=6, minutes=30))
    now = datetime.now(mm_timezone)

    if sender_id in user_cooldowns:
        if now < user_cooldowns[sender_id]:
            return
        else:
            del user_cooldowns[sender_id]
            if sender_id in user_states:
                del user_states[sender_id]

    # ပထမဆုံးစာ ပို့ချင်းမှာ Auto Reply ကို အရင်ပို့မယ်
    if sender_id not in user_states:
        user_states[sender_id] = {
            "count": 0, 
            "last_message_time": now,
            "is_afk_sent": False
        }
        try:
            await event.mark_read()
            await asyncio.sleep(random.randint(2, 5)) 
            
            # Ultimate Premium Auto Reply
            dynamic_welcome = f"""✨ **AUTO - REPLY** ✨
            
👤 **ပို့သူ** ▸ {sender_name}
🕒 **အချိန်** ▸ `{now.strftime('%I:%M %p')}`

မင်္ဂလာပါ **{sender_name}** ခင်ဗျာ။ 
ကျွန်တော် အခုလောလောဆယ် ဖုန်းနဲ့ ဝေးနေလို့ပါ။ 
စာလေးချန်ခဲ့ပေးပါဦးနော်။ ပြန်ရောက်တာနဲ့ ဆက်သွယ်ပါ့မယ်။

💬 *AI နဲ့ စကားပြောလိုပါက "ဟုတ်ကဲ့" လို့ ပြန်ပို့ပါ။*"""
            
            await event.reply(dynamic_welcome, reply_to=event.message.id, parse_mode='md') 
            user_states[sender_id]["is_afk_sent"] = True
        except Exception as e:
            print(f"Error replying: {e}")
        return 

    if user_states[sender_id]["is_afk_sent"]:
        time_diff = (now - user_states[sender_id]["last_message_time"]).total_seconds()
        
        if time_diff > 300:  # ၅ မိနစ်
            user_cooldowns[sender_id] = now + timedelta(hours=24)
            try:
                await event.mark_read()
                await asyncio.sleep(2)
                await event.reply("🛑 **စကားပြောချိန် ၅ မိနစ် ကျော်သွားပါပြီ။**\n\nသင့်အကောင့်ကို ၂၄ နာရီ ပိတ်ထားပါမယ်။", reply_to=event.message.id, parse_mode='md')
            except Exception as e:
                print(f"Error replying: {e}")
            return

        user_states[sender_id]["last_message_time"] = now

        if user_states[sender_id]["count"] < 15:
            try:
                await event.mark_read()
                user_message = event.message.message
                
                system_prompt = f"မင်းက ကျွန်တော့်ရဲ့ ကိုယ်ပိုင်လက်ထောက်ပါ။ စကားပြောနေတဲ့သူက '{sender_name}' ပါ။ ရင်းရင်းနီးနီး၊ ချိုချိုသာသာ မြန်မာလိုပဲ ပြန်ဖြေပေးပါ။ အင်္ဂလိပ်လို လုံးဝ မပြန်ပါနဲ့။"
                
                response = await ai_client.chat.completions.create(
                    model="openai/gpt-oss-20b", 
                    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}]
                )
                
                ai_reply = response.choices[0].message.content
                
                # Ultimate Premium AI Reply
                formatted_ai_reply = f"""💎 **AI ASSISTANT** 💎
                
{ai_reply}

⚡ *Powered by Groq AI*"""
                
                await asyncio.sleep(random.randint(3, 7)) 
                await event.reply(formatted_ai_reply, reply_to=event.message.id, parse_mode='md') 
                user_states[sender_id]["count"] += 1
                
            except Exception as e:
                print(f"Error replying: {e}")

@client.on(events.NewMessage(outgoing=True, pattern=r'^/afk$'))
async def enable_afk(event):
    global afk_enabled, user_states, user_cooldowns
    afk_enabled = True
    user_states.clear()
    user_cooldowns.clear()
    await event.reply("✅ **AFK Mode ON**")

@client.on(events.NewMessage(outgoing=True, pattern=r'^/back$'))
async def disable_afk(event):
    global afk_enabled, user_states, user_cooldowns
    afk_enabled = False
    user_states.clear()
    user_cooldowns.clear()
    await event.reply("❌ **AFK Mode OFF**")

async def main():
    await client.start()
    print("Telegram Client with AI is running...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main())
