import asyncio
import random
import os
import threading
from flask import Flask
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ==========================================
# သင့်ရဲ့ အချက်အလက်များ
# ==========================================
API_ID = 36255475 
API_HASH = 'f0d7017664d12f199d5683782f2bb0bb'
SESSION_STRING = '1BVtsOHIBuxNFoP5Fy9dB_U61OhCHTncB6F_nUfrjq3e3ZZ9GRPpOccFJPz3w0eHKSqCBSfBempqHDUgOVvrnEt393UYXpMTVAYbljT3RyXUb1_9YUMIVzmf-QIxjKy_Ab5770nUyADF6fPBwk97zKWO7ilFK1a2DufhQN31nrO3s72MQKBOVILmIN2WCg8AJ0wqAtM6gXCB3zig5f8-XQrJglNaULQgRkl3rWhv-cEcknVzQFvmL9Fv5oSwcWrks3kze2sGam1ZpLhWa6c4kI8qxwbniwUam8v7qZFlEHX7DQycl2JgDPlhiGGlsQBOmzjfN5EMjIk1mhxuhviw8wH9DqIhh_6w='

DEFAULT_REPLY = "မင်္ဂလာပါခင်ဗျာ။ ကျွန်တော် အခုလောလောဆယ် ဖုန်းနဲ့ ဝေးနေလို့ပါ။ စာလေးချန်ခဲ့ပေးပါဦးနော်။ ကျွန်တော် အဆင်ပြေတာနဲ့ ချက်ချင်း ပြန်ဆက်သွယ်ပေးပါ့မယ်ခင်ဗျာ။ စိတ်မဆိုးနော်။"

# StringSession ကို အသုံးပြုပါမယ်
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

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
# Telegram Bot Logic
# ==========================================
afk_enabled = False
replied_users = set()

@client.on(events.NewMessage(incoming=True))
async def handler(event):
    global afk_enabled
    if not event.is_private or event.out or not afk_enabled:
        return
    sender_id = event.sender_id
    if sender_id not in replied_users:
        try:
            await event.mark_read()
            await asyncio.sleep(random.randint(2, 5))
            await event.reply(DEFAULT_REPLY)
            replied_users.add(sender_id)
        except Exception as e:
            print(f"Error replying: {e}")

@client.on(events.NewMessage(outgoing=True, pattern=r'^/afk$'))
async def enable_afk(event):
    global afk_enabled, replied_users
    afk_enabled = True
    replied_users.clear()
    await event.reply("✅ AFK auto-replies are ON.")

@client.on(events.NewMessage(outgoing=True, pattern=r'^/back$'))
async def disable_afk(event):
    global afk_enabled, replied_users
    afk_enabled = False
    replied_users.clear()
    await event.reply("❌ AFK auto-replies are OFF.")

async def main():
    await client.start()
    print("Telegram Client is running...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main())
