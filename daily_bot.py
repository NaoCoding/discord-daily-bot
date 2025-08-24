import discord
import datetime
import asyncio

################ Configurations ################
TIME_DIFF = 8       # For GMT+8
REPLY_HOUR = 12     # Reply at 12 PM
REPLY_MINUTE = 0    # Reply at 0 minutes
REPLY_WITHIN = 1    # Reply within 1 hour
################################################

reply_dict = {}

# Read the bot token from a file
token_file_path = "token.txt"
with open(token_file_path, "r") as file:
    token = file.read().strip()

# Request message content intent
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# Create a Discord client instance
client = discord.Client(intents = intents)

# The task that triggers daily at a specific time
async def daily_triggered_task():
    await client.wait_until_ready()
    while not client.is_closed():
        
        # Calculate the next target time
        now = datetime.datetime.now()
        target = now.replace(hour=reply_hour, minute=reply_minute, second=0, microsecond=0)
        if target <= now:
            # If we've already passed the target time today, schedule for tomorrow
            target += datetime.timedelta(days=1)

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
    client.loop.create_task(daily_triggered_task())

@client.event
async def on_custom_time_event(timestamp: discord.datetime):
    print(f"Custom time event triggered at {timestamp}")
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
                await channel.send("It's time for your daily message!")
            except Exception as e:
                print(f"Could not send message to {channel.name} in {guild.name}: {e}")
                
    # Wait for a specified duration to allow for replies
    await asyncio.sleep(reply_within * 3600)
    
    # Check if all users have replied
    for guild in client.guilds:
        for member in guild.members:
            if not member.bot and not reply_dict.get(member.id, True):
                channel = guild.text_channels[0] if guild.text_channels else None
                if channel is not None:
                    try:
                        await channel.send(f"{member.mention}, you missed your daily message!")
                        await channel.send(f"You don't care about your friends!")
                    except Exception as e:
                        print(f"Could not send reminder to {member.name} in {guild.name}: {e}")
    

@client.event
# Incoming message event
async def on_message(message):
    # Ignore messages sent by the bot itself
    if message.author == client.user:
        return
    # Check if the message is a reply to the bot's daily message
    if message.author.id in reply_dict:
        reply_dict[message.author.id] = True

@client.event
async def on_disconnect():
    print("The bot has disconnected")

# Run the bot with the specified token
client.run(token)
