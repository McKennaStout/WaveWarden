import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True  # Necessary for guild member access

client = commands.Bot(command_prefix='!', intents=intents)

# Dictionary to store counts for each sticker type per guild
wave_counts = {}

def count_sticker(message, sticker_name):
    guild_id = str(message.guild.id)
    user_id = str(message.author.id)
    count_updated = False
    if message.stickers:
        for sticker in message.stickers:
            if sticker_name in sticker.name.lower():
                if guild_id not in wave_counts:
                    wave_counts[guild_id] = {}
                if user_id not in wave_counts[guild_id]:
                    wave_counts[guild_id][user_id] = {'wave': 0, 'sup': 0, 'scream': 0}
                wave_counts[guild_id][user_id][sticker_name] += 1
                count_updated = True
    return count_updated

@client.event
async def on_ready():
    print('Bot is ready.')
    await load_wave_counts_from_history()

async def load_wave_counts_from_history():
    for guild in client.guilds:
        for channel in guild.text_channels:
            async for message in channel.history(limit=None):
                for sticker_name in ['wave', 'sup', 'scream']:
                    count_sticker(message, sticker_name)
        await update_unwavering_role_based_on_count(str(guild.id))  # Pass the guild_id correctly
    print("Loaded historical sticker counts.")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    await client.process_commands(message)

    count_updated = False
    for sticker_name in ['wave', 'sup', 'scream']:
        if count_sticker(message, sticker_name):
            count_updated = True

    if count_updated:
        await update_unwavering_role_based_on_count(str(message.guild.id))
        total = sum(wave_counts[str(message.guild.id)][str(message.author.id)].values())
        print(f"Updated counts for {message.author}: Total = {total}")

async def update_unwavering_role_based_on_count(guild_id):
    top_user_id = None
    top_count = -1
    guild_wave_counts = wave_counts.get(str(guild_id), {})
    for user_id, counts in guild_wave_counts.items():
        total_count = sum(counts.values())
        if total_count > top_count:
            top_user_id = user_id
            top_count = total_count

    if top_user_id is None:
        return

    guild = client.get_guild(int(guild_id))
    unwavering_member = guild.get_member(int(top_user_id))
    if unwavering_member is None:
        try:
            unwavering_member = await guild.fetch_member(int(top_user_id))
        except discord.NotFound:
            print(f"Member with ID {top_user_id} not found in guild {guild.name}.")
            return

    role = discord.utils.get(guild.roles, name="unwavering")
    if role is None:
        print(f"Error: 'unwavering' role not found in {guild.name}.")
        return

    current_role_holder = None
    async for member in guild.fetch_members(limit=None):
        if role in member.roles:
            current_role_holder = member
            break

    if current_role_holder and current_role_holder.id == int(top_user_id):
        return  # No change needed

    if current_role_holder:
        await current_role_holder.remove_roles(role)
    
    if unwavering_member:
        await unwavering_member.add_roles(role)
        print(f"Unwavering role assigned to {unwavering_member.display_name} in {guild.name}.")

# Replace 'YOUR_TOKEN' with your bot token
client.run('Your_Token')
