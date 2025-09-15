import discord
from datetime import datetime, timedelta, timezone
import asyncio
import os

################ Configurations ################
REPLY_HOUR = 12     # Reply at 12 PM
REPLY_MINUTE = 0    # Reply at 0 minutes
REPLY_WITHIN = 3600 # Reply within 1 hour
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

# Timezone setup
utc_plus_8 = timezone(timedelta(hours=8))

# The task that triggers daily at a specific time
async def daily_triggered_task():
    await client.wait_until_ready()
    while not client.is_closed():
        
        # Calculate the next target time
        now_utc = datetime.now(timezone.utc)
        now = now_utc.astimezone(utc_plus_8)
        target = now.replace(hour=REPLY_HOUR, minute=REPLY_MINUTE, second=0, microsecond=0)
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
                    timestamp=datetime.now()
                )
                await channel.send(embed=embed)
            except (discord.Forbidden, discord.HTTPException) as e:
                print(f"Could not send message to {channel.name} in {guild.name}: {e}")
                
    # Wait for a specified duration to allow for replies
    await asyncio.sleep(REPLY_WITHIN)
    
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
                            timestamp=datetime.now()
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

                # Scold the user if the reply is too short
                len_of_message = len(message.content)
                if len_of_message < 5: # Consider making 5 a constant
                    try:
                        await message.channel.send(f"{message.author.mention}, our friendship only worth {len_of_message} characters?")
                    except discord.HTTPException as e:
                        print(f"Could not send message to {message.channel.name}: {e}")
    

@client.event
async def on_disconnect():
    print("The bot has disconnected")

# Run the bot with the specified token
client.run(token)
