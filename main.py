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

bot = commands.Bot(command_prefix='!', intents=intents)
streak_count = 0
last_reset = None

def get_cdt_time():
    cdt = pytz.timezone('America/Chicago')
    return datetime.now(cdt)

def format_time_until(time_until_next_streak):
    total_seconds = int(time_until_next_streak.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours} hours {minutes} minutes"

@bot.event
async def on_ready():
    global streak_count
    streak_count = 0 # Ensure no streak is running when the bot joins
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(
            f"**Streak Bot is now online!**\n"
            f"**Commands:**\n"
            f"`!start` - Start the streak.\n"
            f"`!start {{#}}` - Start the streak from a specific point.\n"
            f"`!reset` - Reset the streak.\n"
            f"`!time` - See how much time until the streak increases.\n"
            f"`!streak` - Get the current streak count.\n"
            f"`!commands` - Get the commands list again."
        )

@tasks.loop(hours=24)
async def daily_update():
    global streak_count, last_reset
    chicago_tz = pytz.timezone('America/Chicago')
    now = datetime.now(timezone.utc).astimezone(chicago_tz)
    print(f"Running daily update at {now} Chicago time")
    if last_reset is None or now.date() > last_reset.date():
        streak_count += 1
        channel = bot.get_channel(CHANNEL_ID)
        if channel is None:
            print(f"Channel with ID {CHANNEL_ID} not found")
            return
        await channel.send(f"Day {streak_count} completed. Keep up the good work!")
        last_reset = now

@bot.command(name='reset')
async def reset_streak(ctx):
    global streak_count, last_reset
    if streak_count == 0:
        await ctx.send("There is no streak running. Start a streak before you can reset it.")
        return
    streak_count = 0
    last_reset = datetime.now(timezone.utc)
    await ctx.send(f"Streak has been reset. Count is now {streak_count}.")

@bot.command(name='start')
async def start_streak(ctx, count: int = 0):
    global streak_count, last_reset
    if streak_count != 0:
        await ctx.send(
            f"There is already a streak running with a count of {streak_count}. "
            "Do you want to stop that streak and start a new one? "
            "If yes, type `!reset`, and the new streak will start"
        )
        return
    streak_count = count
    last_reset = datetime.now(timezone.utc)
    daily_update.start()
    await ctx.send(f"Streak started at {streak_count}!")

@bot.command(name='time')
async def time_until_streak_increases(ctx):
    if streak_count == 0:
        await ctx.send("There is no streak running. Start a streak before you can check the time.")
        return
    now = get_cdt_time()
    next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    time_until_next_streak = next_midnight - now
    await ctx.send(f"Time until the streak increases: {format_time_until(time_until_next_streak)}")

@bot.command(name='streak')
async def current_streak(ctx):
    if streak_count == 0:
        await ctx.send("There is no streak running. Start a streak before you can check the streak count.")
        return
    await ctx.send(f"The current streak count is {streak_count}.")

@bot.command(name='commands')
async def streakbot_commands(ctx):
    await ctx.send(
        f"**Commands:**\n"
        f"`!start` - Start the streak.\n"
        f"`!start {{#}}` - Start the streak from a specific point.\n"
        f"`!reset` - Reset the streak.\n"
        f"`!time` - See how much time until the streak increases.\n"
        f"`!streak` - Get the current streak count.\n"
        f"`!commands` - Get the commands list again."
    )

@start_streak.error
async def start_streak_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send("Invalid input. Please use `!start {#}` where {#} is a positive integer.")
    else:
        await ctx.send("An error occurred while trying to start the streak.")

@daily_update.before_loop
async def before_daily_update():
    chicago_tz = pytz.timezone('America/Chicago')
    now = datetime.now(timezone.utc).astimezone(chicago_tz)
    next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    sleep_seconds = (next_midnight - now).total_seconds()
    print(f"Sleeping until next midnight: {next_midnight} Chicago time ({sleep_seconds} seconds)")
    await asyncio.sleep(sleep_seconds)

# Main Entry Point
def main() -> None:
    print("Starting bot")
    bot.run(TOKEN)

if __name__ == '__main__':
    main()
