import discord
from datetime import datetime, timedelta, timezone
import asyncio
import os

import gemini

################ Configurations ################
config = {
    "reply_hour": 12,
    "reply_minute": 0,
    "reply_within": 3600,  # in seconds
    "use_gemini_api": True,
    "gemini_difficulty": 1
}
################################################

reply_dict = {}
custom_time_event_running = False

# Read the bot token from an environment variable
token = os.environ.get("DISCORD_TOKEN_DAILY_BOT")
if not token:
    raise RuntimeError("The DISCORD_TOKEN environment variable is not set.")

# Request message content intent
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# Create a Discord client instance
client = discord.Client(intents=intents)
client.config = config

# Timezone setup
UTC_PLUS_8 = timezone(timedelta(hours=8))

# The task that triggers daily at a specific time
async def daily_triggered_task():
    await client.wait_until_ready()
    while not client.is_closed():
        
        # Calculate the next target time
        now_utc = datetime.now(timezone.utc)
        now = now_utc.astimezone(UTC_PLUS_8)
        target = now.replace(hour=client.config["reply_hour"], minute=client.config["reply_minute"], second=0, microsecond=0)
        if target <= now:
            # If we've already passed the target time today, schedule for tomorrow
            target += timedelta(days=1)

        wait_time = (target - now).total_seconds()
        await asyncio.sleep(wait_time)

        # Dispatch custom events down here
        client.dispatch("custom_time_event", target)


@client.event
async def on_ready():
    print(f"The bot {client.user} is ready and online!")
    for user in client.users:
        print(user)
    # Start the daily triggered task
    asyncio.create_task(daily_triggered_task())

@client.event
async def on_custom_time_event(timestamp: datetime):
    print(f"Custom time event triggered at {timestamp}")
    global custom_time_event_running
    custom_time_event_running = True

    # Setup the reply dictionary
    global reply_dict
    reply_dict = {}
    for guild in client.guilds:
        for member in guild.members:
            if not member.bot:
                reply_dict[member.id] = False

    # Send the daily message to all guilds
    for guild in client.guilds:
        channel = guild.text_channels[0] if guild.text_channels else None
        if channel is not None:
            try:
                embed = discord.Embed(
                    title="Friendship Booster",
                    description="It's time for your daily message!",
                    timestamp=datetime.now(UTC_PLUS_8)
                )
                await channel.send(embed=embed)
            except (discord.Forbidden, discord.HTTPException) as e:
                print(f"Could not send message to {channel.name} in {guild.name}: {e}")
                
    # Wait for a specified duration to allow for replies
    await asyncio.sleep(client.config["reply_within"])
    
    # Check if all users have replied
    for guild in client.guilds:
        for member in guild.members:
            if not member.bot and not reply_dict.get(member.id, True):
                channel = guild.text_channels[0] if guild.text_channels else None
                if channel is not None:
                    try:
                        embed = discord.Embed(
                            title=f"You don't care about your friends!",
                            description=f"{member.mention}, you missed your daily message!",
                            timestamp=datetime.now(UTC_PLUS_8)
                        )
                        await channel.send(embed=embed)
                    except Exception as e:
                        print(f"Could not send reminder to {member.name} in {guild.name}: {e}")
    
    custom_time_event_running = False
    

@client.event
# Incoming message event
async def on_message(message):
    # Ignore messages sent by the bot itself
    if message.author == client.user:
        return
    
    # Only respond if the custom time event is running
    if custom_time_event_running:
        if message.author.id in reply_dict:
            # Only respond if the user hasn't replied yet
            if not reply_dict[message.author.id]:
                # Mark the user as having replied to prevent duplicate responses
                reply_dict[message.author.id] = True

                # React with a heart emoji
                try:
                    await message.add_reaction("❤️")
                except discord.HTTPException as e:
                    print(f"Could not add reaction for {message.author.name}: {e}")

                if client.config["use_gemini_api"]:
                    passed, response = gemini.FriendshipJudge(message.content, client.config["gemini_difficulty"])
                    if not passed:
                        try:
                            await message.channel.send(f"{message.author.mention}\n{response}")
                        except discord.HTTPException as e:
                            print(f"Could not send message to {message.channel.name}: {e}")
                else:
                    # Scold the user if the reply is too short
                    len_of_message = len(message.content)
                    if len_of_message < 5: # Consider making 5 a constant
                        try:
                            await message.channel.send(f"{message.author.mention}, our friendship only worth {len_of_message} characters?")
                        except discord.HTTPException as e:
                            print(f"Could not send message to {message.channel.name}: {e}")
                        
    # Commands
    if message.content.startswith("$"):
        msg_content_lower = message.content.lower()
        if msg_content_lower.startswith("$help"):
            help_text = (
                # "$setreplyhour <hour> - Set the hour for daily reply (0-23)\n"
                # "$setreplyminute <minute> - Set the minute for daily reply (0-59)\n"
                "$setreplywithin <seconds> - Set the duration to wait for replies (in seconds)\n"
                "$enablegemini - Enable Gemini API for judging replies\n"
                "$disablegemini - Disable Gemini API for judging replies\n"
                "$setgeminidifficulty <level> - Set the difficulty level for Gemini API judging (1-5)\n"
            )
            await message.channel.send(help_text)
        # elif msg_content_lower.startswith("$setreplyhour"):
        #     try:
        #         hour = int(msg_content_lower.split()[1])
        #         if 0 <= hour <= 23:
        #             client.config["reply_hour"] = hour
        #             await message.channel.send(f"Reply time set to {client.config['reply_hour']}:{client.config['reply_minute']:02d}")
        #         else:
        #             await message.channel.send("Invalid hour. Please provide a value between 0 and 23.")
        #     except (IndexError, ValueError):
        #         await message.channel.send("Usage: $setreplyhour <hour>")
        # elif msg_content_lower.startswith("$setreplyminute"):
        #     try:
        #         minute = int(msg_content_lower.split()[1])
        #         if 0 <= minute <= 59:
        #             client.config["reply_minute"] = minute
        #             await message.channel.send(f"Reply time set to {client.config['reply_hour']}:{client.config['reply_minute']:02d}")
        #         else:
        #             await message.channel.send("Invalid minute. Please provide a value between 0 and 59.")
        #     except (IndexError, ValueError):
        #         await message.channel.send("Usage: $setreplyminute <minute>")
        elif msg_content_lower.startswith("$setreplywithin"):
            try:
                seconds = int(msg_content_lower.split()[1])
                if seconds > 0:
                    client.config["reply_within"] = seconds
                    await message.channel.send(f"Reply within duration set to {seconds} seconds")
                else:
                    await message.channel.send("Invalid duration. Please provide a positive value.")
            except (IndexError, ValueError):
                await message.channel.send("Usage: $setreplywithin <seconds>")
        elif msg_content_lower.startswith("$enablegemini"):
            client.config["use_gemini_api"] = True
            await message.channel.send(f"Gemini API usage has been enabled.")
        elif msg_content_lower.startswith("$disablegemini"):
            client.config["use_gemini_api"] = False
            await message.channel.send(f"Gemini API usage has been disabled.")
        elif msg_content_lower.startswith("$setgeminidifficulty"):
            try:
                level = int(msg_content_lower.split()[1])
                if 1 <= level <= 5:
                    client.config["gemini_difficulty"] = level
                    await message.channel.send(f"Gemini API difficulty level set to {level}")
                else:
                    await message.channel.send("Invalid difficulty level. Please provide a value between 1 and 5.")
            except (IndexError, ValueError):
                await message.channel.send("Usage: $setgeminidifficulty <level>")
    

@client.event
async def on_disconnect():
    print("The bot has disconnected")

# Run the bot with the specified token
client.run(token)
