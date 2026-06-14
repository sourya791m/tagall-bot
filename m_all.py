import asyncio
import random
import os
import sys
import json
from telethon import TelegramClient
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
from telethon.events import NewMessage

# ===== YOUR CONFIGURATION =====
api_id = 30383835
api_hash = '60e3f17fbb622289247272bd57518b30'
phone = '+917248505296'

# 👑 Who can use .tagall? Put your Telegram user ID here
AUTHORIZED_USERS = [6426112987, 8076739291, 7582699157, 8094653178]

# ===============================

BATCH_SIZE = 10
SLEEP_BETWEEN_BATCHES = 6

_stop_flag = {}
_tasks = {}
_current_group = {}


def get_mention(user):
    if user.username:
        return f"@{user.username}"
    elif user.first_name:
        name = user.first_name
        if user.last_name:
            name += f" {user.last_name}"
        name = name.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f'<a href="tg://user?id={user.id}">{name}</a>'
    return None


async def fetch_users(client, group):
    print(f"📋 Fetching members from {group.title}...")
    all_users = []
    offset = 0
    limit = 200
    while True:
        participants = await client(GetParticipantsRequest(
            group, ChannelParticipantsSearch(''), offset, limit, hash=0
        ))
        if not participants.users:
            break
        all_users.extend(participants.users)
        offset += len(participants.users)
    return [u for u in all_users if not u.bot]


async def tag_all_task(client, group, chat_id, reply_to=None):
    global _stop_flag
    _stop_flag[chat_id] = False

    users = await fetch_users(client, group)

    mentions = []
    for u in users:
        m = get_mention(u)
        if m:
            mentions.append(m)

    if not mentions:
        await client.send_message(group, "❌ No one to tag.")
        return

    random.shuffle(mentions)
    total = len(mentions)

    intro_emojis = random.choice(["🌟", "🔥", "⚡", "💫", "🎯"])
    await client.send_message(
        group,
        f"{intro_emojis} **Sabko bula rahe hain!**\n"
        f"Total **{total}** members — stay tuned 🚀",
        parse_mode='md',
        reply_to=reply_to
    )
    await asyncio.sleep(2)

    batch_num = 0
    for i in range(0, total, BATCH_SIZE):
        if _stop_flag.get(chat_id, False):
            break

        batch = mentions[i:i + BATCH_SIZE]
        batch_num += 1

        emoji = random.choice(["🔥", "✨", "⚡", "💥", "🌟", "🎯", "👀", "🚀"])
        tag_text = " ".join(batch)

        line = random.choice([
            "Aajao sab online 📢",
            "GC active karo ⚡",
            "Kaha ho sab 😭",
            "Sabko wait hai 👀",
            "Aajao warna miss karoge 🔥",
            "Revive time 🚀",
            "Attention please 🫡",
            "Sab log aa jao 💬",
        ])

        msg = (
            f"{emoji} **Batch {batch_num}**\n"
            f"━━━━━━━━━━━━━\n"
            f"{tag_text}\n"
            f"━━━━━━━━━━━━━\n"
            f"📝 {line}"
        )

        await client.send_message(group, msg, parse_mode='html')
        print(f"  ✅ Batch {batch_num}: {len(batch)} users tagged in {group.title}")
        await asyncio.sleep(SLEEP_BETWEEN_BATCHES)

    tagged = min(batch_num * BATCH_SIZE, total)
    if _stop_flag.get(chat_id, False):
        await client.send_message(
            group,
            f"⛔ **Stopped.** Tagged {tagged}/{total} users.",
            parse_mode='md'
        )
    else:
        await client.send_message(
            group,
            f"✅ **Done! 🎉**\nTagged all **{tagged}** members. GC is alive! 🔥",
            parse_mode='md'
        )


async def main():
    client = TelegramClient('tag_session', api_id, api_hash)
    await client.start(phone=phone)

    me = await client.get_me()
    print(f"✅ Running as: {me.first_name} (ID: {me.id})")
    print(f"👑 Authorized: {AUTHORIZED_USERS}")
    print("🔥 Bot is live! Use .tagall in ANY group you're in.")
    print("   .stop - Stop tagging in current chat")
    print("   .ping - Check if bot is alive")

    @client.on(NewMessage(pattern=r'\.tagall'))
    async def tagall_cmd(event):
        uid = event.sender_id
        chat_id = event.chat_id

        if uid not in AUTHORIZED_USERS:
            await event.reply("❌ Not authorized.")
            return

        # If a tag-all is already running in this chat, stop it first
        if chat_id in _tasks and not _tasks[chat_id].done():
            _stop_flag[chat_id] = True
            await asyncio.sleep(1)

        group = await event.get_chat()
        await event.reply("🚀 Starting tag-all...")
        _tasks[chat_id] = asyncio.ensure_future(
            tag_all_task(client, group, chat_id, reply_to=event.message.id)
        )

    @client.on(NewMessage(pattern=r'\.stop'))
    async def stop_cmd(event):
        uid = event.sender_id
        chat_id = event.chat_id

        if uid not in AUTHORIZED_USERS:
            await event.reply("❌ Not authorized.")
            return

        _stop_flag[chat_id] = True
        await event.reply("⛔ Stopping tagging in this chat...")

    @client.on(NewMessage(pattern=r'\.ping'))
    async def ping_cmd(event):
        uid = event.sender_id
        if uid not in AUTHORIZED_USERS:
            await event.reply("❌ Not authorized.")
            return
        await event.reply("🏓 **Pong!** Bot is alive and watching this group.", parse_mode='md')

    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user.")