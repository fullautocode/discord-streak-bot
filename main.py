# pip install python-dotenv discord.py pytz

from typing import Final
import os
from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta, timezone
import asyncio
import pytz

# Load token from environment variables
load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')
CHANNEL_ID: Final[int] = int(os.getenv('CHANNEL_ID'))

# Configure intents
intents = discord.Intents.default()
intents.message_content = True  # Enable the MESSAGE_CONTENT intent

# Initialize the bot
bot = commands.Bot(command_prefix='!', intents=intents)
streak_count = 0
last_reset = None

def get_cdt_time():
    """
    Get the current time in the Central Daylight Time (CDT) timezone.
    """
    cdt = pytz.timezone('America/Chicago')
    return datetime.now(cdt)

def format_time_until(time_until_next_streak):
    """
    Format the time until the next streak in hours and minutes.
    """
    total_seconds = int(time_until_next_streak.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours} hours {minutes} minutes"

@bot.event
async def on_ready():
    """
    Event handler that runs when the bot is ready.
    """
    global streak_count
    streak_count = 0  # Ensure no streak is running when the bot joins
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(
            f"**Hello! I'm your Streak Bot. Let's keep the streak going!**\n"
            f"**Commands:**\n"
            f"`!start` - Start the streak.\n"
            f"`!start {{#}}` - Start the streak from a specific point.\n"
            f"`!reset` - Reset the streak.\n"
            f"`!time` - See how much time until the streak increases.\n"
            f"`!streak` - Get the current streak count.\n"
            f"`!streakbot` - Get the commands list again."
        )

@tasks.loop(hours=24)
async def daily_update():
    """
    Task that runs daily to update the streak count and send a message.
    """
    global streak_count, last_reset
    now = datetime.now(timezone.utc)
    print(f"Running daily update at {now} UTC")
    if last_reset is None or now.date() > last_reset.date():
        streak_count += 1
        channel = bot.get_channel(CHANNEL_ID)
        if channel is None:
            print(f"Channel with ID {CHANNEL_ID} not found")
            return
        await channel.send(f'@everyone Congrats, you made it another day! Day {streak_count} completed. Keep it up! 🎉')
        last_reset = now

@bot.command(name='reset')
async def reset_streak(ctx):
    """
    Command to reset the streak count.
    """
    global streak_count, last_reset
    if streak_count == 0:
        await ctx.send("There is no streak running. Start a streak before you can reset it.")
        return
    streak_count = 0
    last_reset = datetime.now(timezone.utc)
    await ctx.send(f'@everyone {ctx.author.name} reset the streak! The count is now {streak_count}.')

@bot.command(name='start')
async def start_streak(ctx, count: int = 0):
    """
    Command to start the streak from a specified point or 0 if not specified.
    """
    global streak_count, last_reset
    if streak_count != 0:
        await ctx.send(
            f"There is already a streak running with a count of {streak_count}. "
            "Do you want to stop that streak and start a new one? "
            "If yes, type `!reset` to reset the current streak first."
        )
        return
    streak_count = count
    last_reset = datetime.now(timezone.utc)
    daily_update.start()
    await ctx.send(f'Streak started at {streak_count}!')

@bot.command(name='time')
async def time_until_streak_increases(ctx):
    """
    Command to display the time until the streak increases.
    """
    if streak_count == 0:
        await ctx.send("There is no streak running. Start a streak before you can check the time.")
        return
    now = get_cdt_time()
    next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    time_until_next_streak = next_midnight - now
    await ctx.send(f'Time until the streak increases: {format_time_until(time_until_next_streak)}')

@bot.command(name='streak')
async def current_streak(ctx):
    """
    Command to display the current streak count.
    """
    if streak_count == 0:
        await ctx.send("There is no streak running. Start a streak before you can check the streak count.")
        return
    await ctx.send(f'The current streak count is {streak_count} 🎉')

@bot.command(name='streakbot')
async def streakbot_commands(ctx):
    """
    Command to display the list of available commands.
    """
    await ctx.send(
        f"**Commands:**\n"
        f"`!start` - Start the streak.\n"
        f"`!start {{#}}` - Start the streak from a specific point.\n"
        f"`!reset` - Reset the streak.\n"
        f"`!time` - See how much time until the streak increases.\n"
        f"`!streak` - Get the current streak count.\n"
        f"`!streakbot` - Get the commands list again."
    )

@start_streak.error
async def start_streak_error(ctx, error):
    """
    Error handler for the start_streak command to handle invalid inputs.
    """
    if isinstance(error, commands.BadArgument):
        await ctx.send("Invalid input. Please use `!start {#}` where {#} is a positive integer.")
    else:
        await ctx.send("An error occurred while trying to start the streak.")

@daily_update.before_loop
async def before_daily_update():
    """
    Function to make the bot wait until the next midnight before starting the daily update loop.
    """
    now = datetime.now(timezone.utc)
    next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    print(f"Sleeping until next midnight: {next_midnight} UTC")
    await asyncio.sleep((next_midnight - now).total_seconds())

# Main Entry Point
def main() -> None:
    """
    Main entry point to start the bot.
    """
    print("Starting bot")
    bot.run(TOKEN)

if __name__ == '__main__':
    main()
