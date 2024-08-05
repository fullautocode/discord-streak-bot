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
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        now = get_cdt_time()
        next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        time_until_next_streak = next_midnight - now
        await channel.send(
            f"**I am Streak Bot!**\n"
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
    global streak_count, last_reset
    now = datetime.now(timezone.utc)
    print(f"Running daily update at {now} UTC")
    if last_reset is None or now.date() > last_reset.date():
        streak_count += 1
        channel = bot.get_channel(CHANNEL_ID)
        if channel is None:
            print(f"Channel with ID {CHANNEL_ID} not found")
            return
        await channel.send(f'@everyone Congrats, you made it another day! Day {streak_count} completed. Keep it up!')
        last_reset = now

@bot.command(name='reset')
async def reset_streak(ctx):
    global streak_count, last_reset
    streak_count = 0
    last_reset = datetime.now(timezone.utc)
    await ctx.send(f'@everyone {ctx.author.name} reset the streak! Count is now {streak_count}.')

@bot.command(name='start')
async def start_streak(ctx, count: int = 0):
    global streak_count, last_reset
    streak_count = count
    last_reset = datetime.now(timezone.utc)
    daily_update.start()
    await ctx.send(f'Streak started at {streak_count}!')

@bot.command(name='time')
async def time_until_streak_increases(ctx):
    now = get_cdt_time()
    next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    time_until_next_streak = next_midnight - now
    await ctx.send(f'Time until the streak increases: {format_time_until(time_until_next_streak)}')

@bot.command(name='streak')
async def current_streak(ctx):
    await ctx.send(f'The current streak count is {streak_count}')

@bot.command(name='streakbot')
async def streakbot_commands(ctx):
    await ctx.send(
        f"**Commands:**\n"
        f"`!start` - Start the streak.\n"
        f"`!start {{#}}` - Start the streak from a specific point.\n"
        f"`!reset` - Reset the streak.\n"
        f"`!time` - See how much time until the streak increases.\n"
        f"`!streak` - Get the current streak count.\n"
        f"`!streakbot` - Get the commands list again."
    )

@daily_update.before_loop
async def before_daily_update():
    now = datetime.now(timezone.utc)
    next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    print(f"Sleeping until next midnight: {next_midnight} UTC")
    await asyncio.sleep((next_midnight - now).total_seconds())

# Main Entry Point
def main() -> None:
    print("Starting bot")
    bot.run(TOKEN)

if __name__ == '__main__':
    main()
