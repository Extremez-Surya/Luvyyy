# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                  ║
# ║   ░█▀▀░█▀█░█▀▄░█▀▀░█░█   ░█▀▄░█▀▀░█░█░█▀▀                     ║
# ║   ░█░░░█░█░█░█░█▀▀░▄▀▄   ░█░█░█▀▀░▀▄▀░▀▀█                     ║
# ║   ░▀▀▀░▀▀▀░▀▀░░▀▀▀░▀░▀   ░▀▀░░▀▀▀░░▀░░▀▀▀                     ║
# ║                                                                  ║
# ║            © 2026 Vinay Kumar (!Alone💔) — All Rights Reserved              ║
# ║                                                                  ║
# ║   discord  ──  https://discord.com/users/731390792567881739                      ║
# ║   youtube  ──  https://discord.com/users/731390792567881739                   ║
# ║   github   ──  https://github.com/kumar_vinay                        ║
# ║                                                                  ║
# ╚══════════════════════════════════════════════════════════════════╝

from __future__ import annotations
import os
import re
import json
import shutil
import datetime
import asyncio
import typing
from typing import Optional, Tuple
from contextlib import suppress

import discord
from discord.ext import commands, tasks

from core import Cog, Context, zyrox
from utils.config import BRAND_NAME, is_bot_owner
from utils.emoji import TICK, CROSS

BIRTHDAYS_FILE = os.path.abspath(os.path.join("jsondb", "birthdays.json"))
BIRTHDAY_LOGS_FILE = os.path.abspath(os.path.join("jsondb", "birthday_logs.json"))

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

MONTH_MAP = {
    'jan': 1, 'january': 1, 'feb': 2, 'february': 2,
    'mar': 3, 'march': 3, 'apr': 4, 'april': 4,
    'may': 5, 'jun': 6, 'june': 6, 'jul': 7, 'july': 7,
    'aug': 8, 'august': 8, 'sep': 9, 'september': 9,
    'oct': 10, 'october': 10, 'nov': 11, 'november': 11,
    'dec': 12, 'december': 12
}

def read_db(filename: str) -> dict:
    """Safely reads a JSON file handling UTF-8, UTF-8-BOM, UTF-16, and corrupted data."""
    if not os.path.exists(filename):
        return {}
    try:
        with open(filename, 'rb') as fb:
            raw = fb.read()
        if not raw or not raw.strip():
            return {}

        # 1. Try UTF-8 with BOM or standard UTF-8
        try:
            return json.loads(raw.decode('utf-8-sig'))
        except UnicodeDecodeError:
            # 2. Try UTF-16 (fixes files saved with Windows/PowerShell UTF-16 BOM)
            try:
                data = json.loads(raw.decode('utf-16'))
                write_db(filename, data)
                return data
            except Exception:
                pass
        except json.JSONDecodeError:
            return {}
    except Exception as e:
        print(f"[Birthday] Error reading {filename}: {e}")
    return {}

def write_db(filename: str, data: dict):
    """Safely writes JSON data using UTF-8 encoding."""
    try:
        os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
        temp_file = f"{filename}.tmp"
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        shutil.move(temp_file, filename)
    except Exception as e:
        print(f"[Birthday] Error writing {filename}: {e}")

def parse_birthday(text: str) -> Optional[Tuple[int, int, Optional[int]]]:
    """
    Parses a birthday string into (month, day, year).
    Supports: '15-08', '15/08', '15 08', '15 August', 'August 15', '15-08-2005'
    """
    if not text:
        return None
    text = text.strip().lower()

    # 1. Check for named month (e.g. '15 Aug', 'August 15', '15 August 2004')
    for m_name, m_num in MONTH_MAP.items():
        if m_name in text:
            nums = [int(n) for n in re.findall(r'\d+', text)]
            if not nums:
                return None
            day = nums[0]
            year = nums[1] if len(nums) > 1 and 1900 <= nums[1] <= 2100 else None
            if 1 <= day <= 31:
                return m_num, day, year

    # 2. Check for numeric separators (-, /, ., space)
    parts = [int(p) for p in re.split(r'[-/.\s]+', text) if p.isdigit()]
    if len(parts) >= 2:
        p1, p2 = parts[0], parts[1]
        year = parts[2] if len(parts) >= 3 and 1900 <= parts[2] <= 2100 else None

        # If p1 > 12, it must be DD-MM
        if p1 > 12 and 1 <= p2 <= 12 and 1 <= p1 <= 31:
            return p2, p1, year
        # If p2 > 12, it must be MM-DD
        if p2 > 12 and 1 <= p1 <= 12 and 1 <= p2 <= 31:
            return p1, p2, year
        # Default to DD-MM (international / Indian standard)
        if 1 <= p1 <= 31 and 1 <= p2 <= 12:
            return p2, p1, year

    return None

def format_birthday_display(date_str: str) -> str:
    """Formats MM-DD or MM-DD-YYYY into 'DD Month YYYY'."""
    try:
        parts = date_str.split('-')
        month = int(parts[0])
        day = int(parts[1])
        year = parts[2] if len(parts) > 2 else None
        m_name = MONTH_NAMES[month] if 1 <= month <= 12 else str(month)
        if year:
            return f"{day} {m_name} {year}"
        return f"{day} {m_name}"
    except Exception:
        return date_str

def days_until_birthday(month: int, day: int) -> int:
    """Calculates days remaining until the next birthday."""
    today = datetime.date.today()
    try:
        bday_this_year = datetime.date(today.year, month, day)
    except ValueError:
        # Leap year handling for Feb 29
        bday_this_year = datetime.date(today.year, month, 28)

    if bday_this_year < today:
        try:
            bday_next_year = datetime.date(today.year + 1, month, day)
        except ValueError:
            bday_next_year = datetime.date(today.year + 1, month, 28)
        return (bday_next_year - today).days
    return (bday_this_year - today).days


class Birthdays(Cog):
    """Birthday tracking, reminders, and celebration system."""

    def __init__(self, client: zyrox):
        self.client = client
        self.announced_today = set()
        self.last_announced_day = None

    async def cog_load(self) -> None:
        if not self.check_birthdays.is_running():
            self.check_birthdays.start()

    def cog_unload(self) -> None:
        if self.check_birthdays.is_running():
            self.check_birthdays.cancel()

    # ══════════════════════════════════════════════════════════════════
    # COMMANDS
    # ══════════════════════════════════════════════════════════════════

    @commands.group(name="birthday", aliases=["bday"], invoke_without_command=True)
    @commands.guild_only()
    async def birthday_group(self, ctx: Context, *, member: Optional[discord.Member] = None):
        """Check your own or another member's birthday."""
        target = member or ctx.author
        db = read_db(BIRTHDAYS_FILE)
        user_id = str(target.id)

        if user_id not in db:
            if target == ctx.author:
                embed = discord.Embed(
                    title="🎂 Birthday Not Set",
                    description=(
                        f"You haven't set your birthday yet!\n\n"
                        f"Use `{ctx.prefix}setbirthday <date>` to set your birthday.\n"
                        f"**Examples:** `{ctx.prefix}setbirthday 15-08` or `{ctx.prefix}setbirthday 15 August`"
                    ),
                    color=0xFF0000
                )
            else:
                embed = discord.Embed(
                    title="🎂 Birthday Not Found",
                    description=f"{target.mention} has not set their birthday yet.",
                    color=0xFF0000
                )
            return await ctx.send(embed=embed)

        raw_date = db[user_id]
        display_date = format_birthday_display(raw_date)
        parts = raw_date.split('-')
        m, d = int(parts[0]), int(parts[1])
        days_left = days_until_birthday(m, d)

        if days_left == 0:
            countdown_text = "🎉 **It's their birthday TODAY! Happy Birthday!** 🎂"
        elif days_left == 1:
            countdown_text = "⏳ **Tomorrow is their birthday!** 🎈"
        else:
            countdown_text = f"⏳ **{days_left} days** remaining until their next birthday!"

        embed = discord.Embed(
            title=f"🎂 {target.display_name}'s Birthday",
            description=(
                f"• **Date:** `{display_date}`\n"
                f"• **Status:** {countdown_text}"
            ),
            color=0xFF0000
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        await ctx.send(embed=embed)

    @birthday_group.command(name="set")
    @commands.guild_only()
    async def bday_set_sub(self, ctx: Context, *, date_str: str = None):
        await self.set_birthday(ctx, date_str=date_str)

    @birthday_group.command(name="remove")
    @commands.guild_only()
    async def bday_remove_sub(self, ctx: Context):
        await self.remove_birthday(ctx)

    @birthday_group.command(name="list")
    @commands.guild_only()
    async def bday_list_sub(self, ctx: Context):
        await self.list_birthdays(ctx)

    @birthday_group.command(name="setup")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def bday_setup_sub(self, ctx: Context, channel: discord.TextChannel, role: Optional[discord.Role] = None):
        await self.birthday_setup(ctx, channel=channel, role=role)

    @commands.command(name="setbirthday", aliases=["bday_set", "setbday"])
    @commands.guild_only()
    async def set_birthday(self, ctx: Context, *, date_str: str = None):
        """Set your birthday. Example: ;setbirthday 15-08 or ;setbirthday 15 August"""
        if not date_str:
            embed = discord.Embed(
                title="🎂 Set Your Birthday",
                description=(
                    "Please reply with your birth date.\n\n"
                    "**Supported Formats:**\n"
                    "• `15-08` (DD-MM)\n"
                    "• `15 August` or `August 15`\n"
                    "• `15-08-2005` (with year)\n\n"
                    "*(You have 60 seconds to reply)*"
                ),
                color=0xFF0000
            )
            prompt_msg = await ctx.send(embed=embed)

            def check(m):
                return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

            try:
                reply = await self.client.wait_for('message', timeout=60.0, check=check)
                date_str = reply.content
            except asyncio.TimeoutError:
                return await ctx.send(f"{CROSS} You took too long to reply. Run `{ctx.prefix}setbirthday <date>` when ready.")

        parsed = parse_birthday(date_str)
        if not parsed:
            embed = discord.Embed(
                title=f"{CROSS} Invalid Birthday Format",
                description=(
                    f"Could not understand `{date_str}`.\n\n"
                    f"**Examples of valid formats:**\n"
                    f"• `{ctx.prefix}setbirthday 15-08`\n"
                    f"• `{ctx.prefix}setbirthday 15 August`\n"
                    f"• `{ctx.prefix}setbirthday 15-08-2005`"
                ),
                color=0xFF0000
            )
            return await ctx.send(embed=embed)

        month, day, year = parsed
        db = read_db(BIRTHDAYS_FILE)
        store_date = f"{month:02d}-{day:02d}-{year}" if year else f"{month:02d}-{day:02d}"
        db[str(ctx.author.id)] = store_date
        write_db(BIRTHDAYS_FILE, db)

        display_text = format_birthday_display(store_date)
        days_left = days_until_birthday(month, day)

        embed = discord.Embed(
            title=f"{TICK} Birthday Set Successfully!",
            description=(
                f"Your birthday has been set to **{display_text}**! 🎂\n\n"
                f"We will wish you in this server when your special day arrives!"
            ),
            color=0x2ecc71
        )
        if days_left == 0:
            embed.description += "\n\n🎉 **Wait, today is your birthday! Happy Birthday!** 🥳"
        else:
            embed.set_footer(text=f"{days_left} days remaining until your birthday!")

        await ctx.send(embed=embed)

    @commands.command(name="removebirthday", aliases=["bday_remove", "delbday"])
    @commands.guild_only()
    async def remove_birthday(self, ctx: Context):
        """Remove your saved birthday."""
        db = read_db(BIRTHDAYS_FILE)
        user_id = str(ctx.author.id)

        if user_id in db:
            del db[user_id]
            write_db(BIRTHDAYS_FILE, db)
            await ctx.send(f"{TICK} Your birthday has been successfully removed.")
        else:
            await ctx.send(f"{CROSS} You have no saved birthday.")

    @commands.command(name="listbirthdays", aliases=["bday_list", "birthdays"])
    @commands.guild_only()
    async def list_birthdays(self, ctx: Context):
        """List members who have birthdays today or coming up."""
        now = datetime.date.today()
        today_prefix = now.strftime("%m-%d")
        db = read_db(BIRTHDAYS_FILE)

        # 1. Check for birthdays today
        today_members = []
        upcoming_members = []

        for user_id_str, date_str in db.items():
            user_id = int(user_id_str)
            member = ctx.guild.get_member(user_id)
            if not member:
                continue

            try:
                parts = date_str.split('-')
                m, d = int(parts[0]), int(parts[1])
            except Exception:
                continue

            if date_str.startswith(today_prefix):
                today_members.append(member)
            else:
                days_left = days_until_birthday(m, d)
                if 1 <= days_left <= 30:
                    upcoming_members.append((days_left, member, date_str))

        embed = discord.Embed(
            title=f"🎂 Birthdays in {ctx.guild.name}",
            color=0xFF0000
        )

        if today_members:
            mentions = "\n".join(f"🎉 {m.mention} (`{m.display_name}`)" for m in today_members)
            embed.add_field(name="🎈 Birthdays Today!", value=mentions, inline=False)
        else:
            embed.add_field(name="🎈 Birthdays Today", value="No member has a birthday today!", inline=False)

        if upcoming_members:
            upcoming_members.sort(key=lambda x: x[0])
            upcoming_text = "\n".join(
                f"• {m.mention}: **{format_birthday_display(d_str)}** (in {d_left} days)"
                for d_left, m, d_str in upcoming_members[:10]
            )
            embed.add_field(name="⏳ Upcoming Birthdays (Next 30 Days)", value=upcoming_text, inline=False)

        embed.set_footer(text=f"Total registered birthdays: {len([uid for uid in db if ctx.guild.get_member(int(uid))])}")
        await ctx.send(embed=embed)

    @commands.command(name="birthdaysetup", aliases=["bday_setup"])
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def birthday_setup(self, ctx: Context, channel: discord.TextChannel, role: Optional[discord.Role] = None):
        """Set up the birthday notification channel and optional birthday role."""
        db = read_db(BIRTHDAY_LOGS_FILE)
        guild_id = str(ctx.guild.id)

        config = {
            "birthday_channel_id": channel.id,
            "birthday_role_id": role.id if role else None
        }
        db[guild_id] = config
        write_db(BIRTHDAY_LOGS_FILE, db)

        role_desc = f"and Birthday Role set to {role.mention}" if role else "*(No role configured)*"
        embed = discord.Embed(
            title=f"{TICK} Birthday Setup Configured!",
            description=(
                f"• **Announcement Channel:** {channel.mention}\n"
                f"• **Birthday Role:** {role_desc}\n\n"
                f"The bot will automatically wish celebrating members at midnight!"
            ),
            color=0x2ecc71
        )
        await ctx.send(embed=embed)

    # ══════════════════════════════════════════════════════════════════
    # BACKGROUND TASK: Auto-announce birthdays
    # ══════════════════════════════════════════════════════════════════

    @tasks.loop(minutes=30)
    async def check_birthdays(self):
        """Periodically checks for celebrating members and sends birthday announcements."""
        try:
            today = datetime.date.today()
            today_str = today.strftime("%m-%d")

            # Reset announced cache when day changes
            if self.last_announced_day != today_str:
                self.announced_today.clear()
                self.last_announced_day = today_str

            birthdays_db = read_db(BIRTHDAYS_FILE)
            logs_db = read_db(BIRTHDAY_LOGS_FILE)

            if not birthdays_db or not logs_db:
                return

            for guild_id_str, settings in logs_db.items():
                try:
                    guild_id = int(guild_id_str)
                    guild = self.client.get_guild(guild_id)
                    if not guild:
                        continue

                    channel_id = settings.get("birthday_channel_id")
                    role_id = settings.get("birthday_role_id")
                    channel = guild.get_channel(channel_id) if channel_id else None
                    role = guild.get_role(role_id) if role_id else None

                    if not channel:
                        continue

                    for user_id_str, date_str in birthdays_db.items():
                        if not date_str.startswith(today_str):
                            continue

                        user_id = int(user_id_str)
                        track_key = f"{guild_id}:{user_id}:{today_str}"

                        if track_key in self.announced_today:
                            continue

                        member = guild.get_member(user_id)
                        if not member:
                            try:
                                member = await guild.fetch_member(user_id)
                            except Exception:
                                member = None

                        if not member:
                            continue

                        # Send announcement
                        embed = discord.Embed(
                            title="🎉 HAPPY BIRTHDAY! 🎂",
                            description=(
                                f"Wishing a fantastic and joyous Birthday to {member.mention}! 🎈🥳\n\n"
                                f"May your day be filled with lots of happiness and fun!"
                            ),
                            color=0xFF0000
                        )
                        embed.set_thumbnail(url=member.display_avatar.url)
                        embed.set_footer(text=f"{BRAND_NAME} Birthday Wishes")

                        with suppress(Exception):
                            await channel.send(content=f"🎉 Happy Birthday {member.mention}! 🎂", embed=embed)

                        # Assign birthday role if configured
                        if role and role < guild.me.top_role and guild.me.guild_permissions.manage_roles:
                            with suppress(Exception):
                                await member.add_roles(role, reason="Birthday role assignment")

                        self.announced_today.add(track_key)

                except Exception as e:
                    print(f"[Birthday] Error processing guild {guild_id_str}: {e}")

        except Exception as e:
            print(f"[Birthday] Error in check_birthdays task: {e}")

    @check_birthdays.before_loop
    async def before_check_birthdays(self):
        await self.client.wait_until_ready()


async def setup(client: zyrox):
    await client.add_cog(Birthdays(client))
