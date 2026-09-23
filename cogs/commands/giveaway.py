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
import time
import random
import datetime
import typing
from typing import Optional, List
import asyncio
import sqlite3
import aiosqlite
from contextlib import suppress

import discord
from discord.ext import commands, tasks

from core import Cog, Context, zyrox
from utils.config import BRAND_NAME, is_bot_owner
from utils.emoji import TICK, CROSS, ARROWRED, ZTADA

DB_PATH = os.path.abspath(os.path.join("db", "giveaways.db"))

def init_giveaway_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS Giveaway (
        guild_id INTEGER,
        host_id INTEGER,
        start_time REAL,
        ends_at REAL,
        prize TEXT,
        winners INTEGER,
        message_id INTEGER,
        channel_id INTEGER,
        PRIMARY KEY (guild_id, message_id)
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS GiveawayParticipants (
        message_id INTEGER,
        user_id INTEGER,
        guild_id INTEGER,
        PRIMARY KEY (message_id, user_id)
    )''')
    conn.commit()
    conn.close()

init_giveaway_db()

def parse_time(time_str: str) -> Optional[int]:
    """Parse time strings like '10m', '1h', '2d', '1w', '30s', '1h30m' into seconds."""
    if not time_str:
        return None
    time_str = str(time_str).strip().lower()
    if time_str.isdigit():
        return int(time_str) * 60

    units = {
        's': 1, 'sec': 1, 'second': 1, 'seconds': 1,
        'm': 60, 'min': 60, 'minute': 60, 'minutes': 60,
        'h': 3600, 'hr': 3600, 'hour': 3600, 'hours': 3600,
        'd': 86400, 'day': 86400, 'days': 86400,
        'w': 604800, 'wk': 604800, 'week': 604800, 'weeks': 604800
    }

    matches = re.findall(r'(\d+)\s*([a-zA-Z]+)', time_str)
    if not matches:
        return None

    total_seconds = 0
    for amount, unit in matches:
        amount = int(amount)
        unit = unit.lower()
        if unit in units:
            total_seconds += amount * units[unit]
        else:
            return None
    return total_seconds if total_seconds > 0 else None

def check_giveaway_perms(ctx: Context) -> bool:
    """Checks if the user has permission to manage giveaways."""
    if not ctx.guild:
        return False
    if is_bot_owner(ctx.author.id):
        return True
    if ctx.author.id == ctx.guild.owner_id:
        return True
    perms = ctx.author.guild_permissions
    if perms.administrator or perms.manage_guild or perms.manage_messages:
        return True
    for role in ctx.author.roles:
        if role.name.lower() in ["giveaway", "giveaways", "gw", "giveaway manager", "giveaway host"]:
            return True
    return False


class GiveawayEnterView(discord.ui.View):
    """Persistent button view for giveaway entries."""
    def __init__(self, cog=None, count: int = 0):
        super().__init__(timeout=None)
        self.cog = cog
        btn_label = f"🎉 Enter ({count})" if count > 0 else "🎉 Enter Giveaway"
        button = discord.ui.Button(
            label=btn_label,
            style=discord.ButtonStyle.primary,
            custom_id="giveaway_enter_btn"
        )
        button.callback = self.enter_cb
        self.add_item(button)

    async def enter_cb(self, interaction: discord.Interaction):
        if self.cog:
            await self.cog.handle_button_entry(interaction)
        else:
            # Fallback direct handler if cog reference not bound
            await interaction.response.send_message("🎉 Entry received! Best of luck!", ephemeral=True)


class Giveaway(Cog):
    """Reliable, feature-rich Giveaway system with interactive buttons and reactions."""
    def __init__(self, bot: zyrox):
        self.bot = bot
        self.db_path = DB_PATH
        self._loop_started = False

    async def cog_load(self) -> None:
        # Register persistent view so button interactions work after restart
        self.bot.add_view(GiveawayEnterView(self))
        asyncio.create_task(self._startup_init())

    def cog_unload(self) -> None:
        if self.GiveawayEnd.is_running():
            self.GiveawayEnd.cancel()

    async def _startup_init(self) -> None:
        await self.bot.wait_until_ready()
        await self.check_for_ended_giveaways()
        if not self.GiveawayEnd.is_running():
            self.GiveawayEnd.start()

    async def handle_button_entry(self, interaction: discord.Interaction):
        message_id = interaction.message.id
        user_id = interaction.user.id
        guild_id = interaction.guild_id

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT prize, host_id FROM Giveaway WHERE message_id = ?", (message_id,)) as cur:
                gw = await cur.fetchone()
            if not gw:
                return await interaction.response.send_message(f"{CROSS} This giveaway has already ended!", ephemeral=True)

            prize, host_id = gw

            async with db.execute("SELECT user_id FROM GiveawayParticipants WHERE message_id = ? AND user_id = ?", (message_id, user_id)) as cur:
                already_in = await cur.fetchone()

            if already_in:
                await db.execute("DELETE FROM GiveawayParticipants WHERE message_id = ? AND user_id = ?", (message_id, user_id))
                await db.commit()
                async with db.execute("SELECT count(*) FROM GiveawayParticipants WHERE message_id = ?", (message_id,)) as cur:
                    new_count = (await cur.fetchone())[0]
                await interaction.response.send_message(f"You left the giveaway for **{prize}**.", ephemeral=True)
            else:
                await db.execute("INSERT INTO GiveawayParticipants(message_id, user_id, guild_id) VALUES(?, ?, ?)", (message_id, user_id, guild_id))
                await db.commit()
                async with db.execute("SELECT count(*) FROM GiveawayParticipants WHERE message_id = ?", (message_id,)) as cur:
                    new_count = (await cur.fetchone())[0]
                await interaction.response.send_message(f"🎉 You have entered the giveaway for **{prize}**! Good luck!", ephemeral=True)

        with suppress(Exception):
            view = GiveawayEnterView(self, count=new_count)
            await interaction.message.edit(view=view)

    async def get_participants(self, message: discord.Message) -> List[int]:
        """Gathers participants from both database button clicks AND reactions."""
        participants = set()
        # 1. From database table
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("SELECT user_id FROM GiveawayParticipants WHERE message_id = ?", (message.id,)) as cursor:
                    rows = await cursor.fetchall()
                    for r in rows:
                        participants.add(r[0])
        except Exception:
            pass

        # 2. From reactions on the message
        if message.reactions:
            for reaction in message.reactions:
                try:
                    async for user in reaction.users():
                        if not user.bot and user.id != self.bot.user.id:
                            participants.add(user.id)
                except Exception:
                    pass

        participants.discard(self.bot.user.id)
        return list(participants)

    async def check_for_ended_giveaways(self):
        try:
            now = time.time()
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    "SELECT ends_at, guild_id, message_id, host_id, winners, prize, channel_id FROM Giveaway WHERE ends_at <= ?",
                    (now,)
                ) as cursor:
                    ended_giveaways = await cursor.fetchall()
            for giveaway in ended_giveaways:
                await self.end_giveaway(giveaway)
        except Exception as e:
            print(f"[Giveaway] Error checking ended giveaways: {e}")

    async def end_giveaway(self, giveaway):
        ends_at, guild_id, message_id, host_id, winners, prize, channel_id = giveaway
        try:
            guild = self.bot.get_guild(guild_id)
            if guild is None:
                try:
                    guild = await self.bot.fetch_guild(guild_id)
                except Exception:
                    guild = None
            if guild is None:
                return

            channel = guild.get_channel(channel_id)
            if channel is None:
                try:
                    channel = await self.bot.fetch_channel(channel_id)
                except Exception:
                    channel = None
            if channel is None:
                return

            try:
                message = await channel.fetch_message(message_id)
            except (discord.NotFound, discord.HTTPException) as e:
                if isinstance(e, discord.NotFound) or getattr(e, 'code', None) == 10008:
                    async with aiosqlite.connect(self.db_path) as db:
                        await db.execute("DELETE FROM Giveaway WHERE message_id = ?", (message_id,))
                        await db.execute("DELETE FROM GiveawayParticipants WHERE message_id = ?", (message_id,))
                        await db.commit()
                return

            participants = await self.get_participants(message)
            now = int(time.time())

            if len(participants) < 1:
                embed = discord.Embed(
                    title=f"🎉 {prize} — Ended",
                    description=(
                        f"**Winner(s):** No winner (Not enough participants)\n"
                        f"**Hosted by:** <@{host_id}>\n"
                        f"**Ended:** <t:{now}:R>"
                    ),
                    color=0x7289da
                )
                embed.set_footer(text="0 Winners • Ended")
                view = discord.ui.View()
                view.add_item(discord.ui.Button(label="Giveaway Ended", style=discord.ButtonStyle.secondary, disabled=True))
                with suppress(Exception):
                    await message.edit(content="🎉 **GIVEAWAY ENDED** 🎉", embed=embed, view=view)
                with suppress(Exception):
                    await message.reply(f"No one won the **{prize}** giveaway due to not enough participants.")
            else:
                winners_count = min(len(participants), int(winners))
                winner_ids = random.sample(participants, k=winners_count)
                winners_str = ", ".join(f"<@{uid}>" for uid in winner_ids)

                embed = discord.Embed(
                    title=f"🎉 {prize} — Ended",
                    description=(
                        f"**Winner(s):** {winners_str}\n"
                        f"**Hosted by:** <@{host_id}>\n"
                        f"**Ended:** <t:{now}:R>"
                    ),
                    color=0x2ecc71
                )
                embed.set_footer(text=f"{winners_count} Winner(s) • Ended")
                view = discord.ui.View()
                view.add_item(discord.ui.Button(label=f"Ended ({len(participants)} entries)", style=discord.ButtonStyle.secondary, disabled=True))
                with suppress(Exception):
                    await message.edit(content="🎉 **GIVEAWAY ENDED** 🎉", embed=embed, view=view)
                with suppress(Exception):
                    await message.reply(
                        f"🎉 Congratulations {winners_str}! You won **{prize}**!\n"
                        f"Hosted by <@{host_id}> • [Jump to Giveaway]({message.jump_url})"
                    )

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM Giveaway WHERE message_id = ?", (message_id,))
                await db.execute("DELETE FROM GiveawayParticipants WHERE message_id = ?", (message_id,))
                await db.commit()

        except Exception as e:
            print(f"[Giveaway] Error ending giveaway {message_id}: {e}")

    @tasks.loop(seconds=5)
    async def GiveawayEnd(self):
        try:
            now = time.time()
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    "SELECT ends_at, guild_id, message_id, host_id, winners, prize, channel_id FROM Giveaway WHERE ends_at <= ?",
                    (now,)
                ) as cursor:
                    ended_giveaways = await cursor.fetchall()
            for giveaway in ended_giveaways:
                await self.end_giveaway(giveaway)
        except Exception as e:
            print(f"[Giveaway] Error in GiveawayEnd task: {e}")

    @GiveawayEnd.before_loop
    async def before_giveaway_end(self):
        await self.bot.wait_until_ready()

    # ══════════════════════════════════════════════════════════════════
    # COMMANDS
    # ══════════════════════════════════════════════════════════════════

    @commands.group(name="giveaway", aliases=["gwy", "gw"], invoke_without_command=True)
    @commands.check(check_giveaway_perms)
    async def giveaway_group(self, ctx: Context):
        """Shows the Giveaway commands and usage guide."""
        embed = discord.Embed(
            title="🎉 Giveaway System Guide",
            description=(
                f"**Main Commands:**\n"
                f"• `{ctx.prefix}gstart <time> [winners] <prize>` — Start a giveaway\n"
                f"• `{ctx.prefix}gend [message_id]` — End a giveaway immediately\n"
                f"• `{ctx.prefix}greroll [message_id]` — Pick a new winner for an ended giveaway\n"
                f"• `{ctx.prefix}glist` — List all active giveaways in this server\n\n"
                f"**Usage Examples:**\n"
                f"• `{ctx.prefix}gstart 10m 1 Discord Nitro` (10 minutes, 1 winner)\n"
                f"• `{ctx.prefix}gstart 1h Discord Nitro` (1 hour, 1 winner)\n"
                f"• `{ctx.prefix}gstart 2d 3 Steam Key` (2 days, 3 winners)\n"
                f"• `{ctx.prefix}gend` (Reply to the giveaway message or run in same channel)\n\n"
                f"**Supported Time Units:** `s` (seconds), `m` (minutes), `h` (hours), `d` (days), `w` (weeks)"
            ),
            color=0xFF0000
        )
        embed.set_footer(text=f"{BRAND_NAME} Giveaways • Run by {ctx.author.display_name}")
        await ctx.send(embed=embed)

    @giveaway_group.command(name="start")
    @commands.check(check_giveaway_perms)
    async def giveaway_start_sub(self, ctx: Context, time_str: str = None, winners: typing.Optional[int] = None, *, prize: str = None):
        await self.gstart_cmd(ctx, time_str=time_str, winners=winners, prize=prize)

    @giveaway_group.command(name="end")
    @commands.check(check_giveaway_perms)
    async def giveaway_end_sub(self, ctx: Context, message_id: typing.Optional[int] = None):
        await self.gend_cmd(ctx, message_id=message_id)

    @giveaway_group.command(name="reroll")
    @commands.check(check_giveaway_perms)
    async def giveaway_reroll_sub(self, ctx: Context, message_id: typing.Optional[int] = None):
        await self.greroll_cmd(ctx, message_id=message_id)

    @giveaway_group.command(name="list")
    @commands.check(check_giveaway_perms)
    async def giveaway_list_sub(self, ctx: Context):
        await self.glist_cmd(ctx)

    @commands.command(name="gstart", aliases=["gwstart"])
    @commands.check(check_giveaway_perms)
    async def gstart_cmd(self, ctx: Context, time_str: str = None, winners: typing.Optional[int] = None, *, prize: str = None):
        """Starts a new giveaway in the current channel."""
        if not time_str or not prize:
            embed = discord.Embed(
                title="🎉 Giveaway Setup Guide",
                description=(
                    f"**Usage:** `{ctx.prefix}gstart <time> [winners] <prize>`\n"
                    f"**Alias:** `{ctx.prefix}giveaway start <time> [winners] <prize>`\n\n"
                    f"**Examples:**\n"
                    f"• `{ctx.prefix}gstart 10m 1 Discord Nitro` (1 winner for 10 minutes)\n"
                    f"• `{ctx.prefix}gstart 1h Discord Nitro` (Defaults to 1 winner)\n"
                    f"• `{ctx.prefix}gstart 2d 3 Steam Key` (3 winners for 2 days)\n\n"
                    f"**Supported Units:** `s` (seconds), `m` (minutes), `h` (hours), `d` (days), `w` (weeks)"
                ),
                color=0xFF0000
            )
            embed.set_footer(text="Tip: You can reply or click the button to enter!")
            return await ctx.send(embed=embed)

        seconds = parse_time(time_str)
        if not seconds:
            return await ctx.send(f"{CROSS} Invalid time format `{time_str}`! Examples: `10m`, `1h`, `2d`, `1w`.")

        if seconds > 31 * 86400:
            return await ctx.send(f"{CROSS} Giveaway duration cannot exceed 31 days.")

        if winners is None or winners < 1:
            winners = 1

        if winners > 25:
            return await ctx.send(f"{CROSS} Number of winners cannot exceed 25.")

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT count(*) FROM Giveaway WHERE guild_id = ?", (ctx.guild.id,)) as cur:
                count = (await cur.fetchone())[0]

        if count >= 15:
            return await ctx.send(f"{CROSS} You can only run up to 15 active giveaways simultaneously in this server.")

        now = time.time()
        ends_at = now + seconds

        embed = discord.Embed(
            title=f"🎉 {prize}",
            description=(
                f"Click the button below or react with 🎉 to participate!\n\n"
                f"• **Winners:** `{winners}`\n"
                f"• **Hosted by:** {ctx.author.mention}\n"
                f"• **Ends:** <t:{int(ends_at)}:R> (<t:{int(ends_at)}:f>)"
            ),
            color=0xFF0000
        )
        embed.set_footer(text=f"{winners} Winner(s) • Ends")
        embed.timestamp = datetime.datetime.fromtimestamp(ends_at, tz=datetime.timezone.utc)

        view = GiveawayEnterView(self, count=0)
        giveaway_msg = await ctx.send(content="🎉 **GIVEAWAY** 🎉", embed=embed, view=view)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO Giveaway (guild_id, host_id, start_time, ends_at, prize, winners, message_id, channel_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (ctx.guild.id, ctx.author.id, now, ends_at, prize, winners, giveaway_msg.id, ctx.channel.id)
            )
            await db.commit()

        try:
            await giveaway_msg.add_reaction("🎉")
        except Exception:
            pass

        with suppress(Exception):
            await ctx.message.delete()

    @commands.command(name="gend", aliases=["gwend"])
    @commands.check(check_giveaway_perms)
    async def gend_cmd(self, ctx: Context, message_id: typing.Optional[int] = None):
        """Ends a running giveaway early."""
        target_id = message_id
        if not target_id and ctx.message.reference:
            target_id = ctx.message.reference.resolved.id if ctx.message.reference.resolved else ctx.message.reference.message_id

        async with aiosqlite.connect(self.db_path) as db:
            if target_id:
                async with db.execute("SELECT ends_at, guild_id, message_id, host_id, winners, prize, channel_id FROM Giveaway WHERE message_id = ?", (target_id,)) as cur:
                    gw = await cur.fetchone()
            else:
                async with db.execute(
                    "SELECT ends_at, guild_id, message_id, host_id, winners, prize, channel_id FROM Giveaway WHERE channel_id = ? ORDER BY ends_at ASC LIMIT 1",
                    (ctx.channel.id,)
                ) as cur:
                    gw = await cur.fetchone()

                if not gw:
                    async with db.execute(
                        "SELECT ends_at, guild_id, message_id, host_id, winners, prize, channel_id FROM Giveaway WHERE guild_id = ? ORDER BY ends_at ASC LIMIT 1",
                        (ctx.guild.id,)
                    ) as cur:
                        gw = await cur.fetchone()

        if not gw:
            return await ctx.send(f"{CROSS} No active giveaway found. Please specify the giveaway message ID or reply to the giveaway message with `{ctx.prefix}gend`.")

        await ctx.send(f"{TICK} Ending giveaway for **{gw[5]}**...")
        await self.end_giveaway(gw)

    @commands.command(name="greroll", aliases=["gwreroll"])
    @commands.check(check_giveaway_perms)
    async def greroll_cmd(self, ctx: Context, message_id: typing.Optional[int] = None):
        """Rerolls a giveaway to pick a new winner."""
        target_id = message_id
        if not target_id and ctx.message.reference:
            target_id = ctx.message.reference.resolved.id if ctx.message.reference.resolved else ctx.message.reference.message_id

        if not target_id:
            return await ctx.send(f"{CROSS} Please provide the giveaway message ID or reply to the giveaway message with `{ctx.prefix}greroll`.")

        try:
            message = await ctx.channel.fetch_message(target_id)
        except Exception:
            return await ctx.send(f"{CROSS} Could not find giveaway message `{target_id}` in this channel.")

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT message_id FROM Giveaway WHERE message_id = ?", (target_id,)) as cur:
                if await cur.fetchone():
                    return await ctx.send(f"{CROSS} This giveaway is currently running! Use `{ctx.prefix}gend` to end it first.")

        participants = await self.get_participants(message)
        if not participants:
            return await ctx.send(f"{CROSS} No participants found to reroll this giveaway.")

        new_winner_id = random.choice(participants)
        await message.reply(f"🎉 **GIVEAWAY REROLL:** The new winner is <@{new_winner_id}>! Congratulations!")

    @commands.command(name="glist", aliases=["gwlist"])
    @commands.check(check_giveaway_perms)
    async def glist_cmd(self, ctx: Context):
        """Lists all active giveaways in the server."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT message_id, channel_id, prize, winners, ends_at, host_id FROM Giveaway WHERE guild_id = ? ORDER BY ends_at ASC",
                (ctx.guild.id,)
            ) as cur:
                rows = await cur.fetchall()

        if not rows:
            embed = discord.Embed(
                title=f"🎉 Active Giveaways — {ctx.guild.name}",
                description="There are currently no active giveaways running in this server.",
                color=0xFF0000
            )
            return await ctx.send(embed=embed)

        embed = discord.Embed(
            title=f"🎉 Active Giveaways — {ctx.guild.name} ({len(rows)})",
            color=0xFF0000
        )
        for msg_id, ch_id, prize, winners, ends_at, host_id in rows:
            embed.add_field(
                name=f"🎁 {prize}",
                value=(
                    f"• **Channel:** <#{ch_id}>\n"
                    f"• **Winners:** `{winners}`\n"
                    f"• **Hosted by:** <@{host_id}>\n"
                    f"• **Ends:** <t:{int(ends_at)}:R> (<t:{int(ends_at)}:f>)\n"
                    f"• **Jump:** [View Giveaway](https://discord.com/channels/{ctx.guild.id}/{ch_id}/{msg_id})"
                ),
                inline=False
            )
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        await ctx.send(embed=embed)

    async def cog_command_error(self, ctx: Context, error):
        if isinstance(error, commands.CheckFailure):
            return await ctx.send(f"{CROSS} You need **Manage Server**, **Manage Messages**, or a **Giveaways** role to use this command!")
        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(f"{CROSS} Missing argument `{error.param.name}`. Run `{ctx.prefix}giveaway` for help.")
        print(f"[Giveaway] Command error in {ctx.command}: {error}")


async def setup(bot: zyrox):
    await bot.add_cog(Giveaway(bot))
