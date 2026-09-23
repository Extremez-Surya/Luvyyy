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

from discord.ext import commands, tasks
import datetime, pytz, time as t
from discord.ui import Button, Select, View
import aiosqlite, random, typing
import sqlite3
import asyncio
import discord, logging
from utils.emoji import ARROWRED, TADAA, TICK
from discord.utils import get
from utils.Tools import *
import os
import aiohttp
from utils.cv2 import CV2
from contextlib import suppress

db_folder = 'db'
db_file = 'giveaways.db'
db_path = os.path.join(db_folder, db_file)
connection = sqlite3.connect(db_path)

cursor = connection.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS Giveaway (
                    guild_id INTEGER,
                    host_id INTEGER,
                    start_time TIMESTAMP,
                    ends_at TIMESTAMP,
                    prize TEXT,
                    winners INTEGER,
                    message_id INTEGER,
                    channel_id INTEGER,
                    PRIMARY KEY (guild_id, message_id)
                )''')

connection.commit()
connection.close()

def convert(time):
    pos = ["s","m","h","d"]
    time_dict = {"s" : 1, "m" : 60, "h" : 3600 , "d" : 86400 , "f" : 259200}
    unit = time[-1]
    if unit not in pos:
        return
    try:
        val = int(time[:-1])
    except ValueError:
        return
    return val * time_dict[unit]

def WinnerConverter(winner):
    try:
        int(winner)
    except ValueError:
        try:
           return int(winner[:-1])
        except:
            return -4
    return winner

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self) -> None:
        await self.check_for_ended_giveaways() 
        if not self.GiveawayEnd.is_running():
            self.GiveawayEnd.start()

    async def cog_unload(self) -> None:
        self.GiveawayEnd.cancel()

    async def check_for_ended_giveaways(self):
        try:
            now = datetime.datetime.now().timestamp()
            async with aiosqlite.connect(db_path) as db:
                async with db.execute(
                    "SELECT ends_at, guild_id, message_id, host_id, winners, prize, channel_id FROM Giveaway WHERE ends_at <= ?",
                    (now,)
                ) as cursor:
                    ended_giveaways = await cursor.fetchall()
            for giveaway in ended_giveaways:
                await self.end_giveaway(giveaway)
        except Exception as e:
            logging.error(f"Error in check_for_ended_giveaways: {e}")

    async def end_giveaway(self, giveaway):
        try:
            current_time = datetime.datetime.now().timestamp()
            guild = self.bot.get_guild(int(giveaway[1]))
            if guild is None:
                async with aiosqlite.connect(db_path) as db:
                    await db.execute("DELETE FROM Giveaway WHERE message_id = ? AND guild_id = ?", (giveaway[2], giveaway[1]))
                    await db.commit()
                return

            channel = self.bot.get_channel(int(giveaway[6]))
            if channel is None:
                async with aiosqlite.connect(db_path) as db:
                    await db.execute("DELETE FROM Giveaway WHERE message_id = ? AND guild_id = ?", (giveaway[2], giveaway[1]))
                    await db.commit()
                return

            try:
                retries = 3
                for attempt in range(retries):
                    try:
                        message = await channel.fetch_message(int(giveaway[2]))
                        break
                    except (discord.NotFound, discord.HTTPException) as e:
                        if isinstance(e, discord.NotFound) or getattr(e, 'code', None) == 10008 or "10008" in str(e):
                            async with aiosqlite.connect(db_path) as db:
                                await db.execute("DELETE FROM Giveaway WHERE message_id = ? AND guild_id = ?", (giveaway[2], giveaway[1]))
                                await db.commit()
                            return
                        if attempt < retries - 1:
                            await asyncio.sleep(1)
                            continue
                        raise
                    except aiohttp.ClientResponseError as e:
                        if e.status == 503:
                            if attempt < retries - 1:
                                await asyncio.sleep(2 ** attempt)
                                continue
                            else:
                                raise
                        else:
                            raise

                users = []
                if message.reactions:
                    try:
                        users = [i.id async for i in message.reactions[0].users()]
                    except Exception:
                        pass
                if self.bot.user.id in users:
                    users.remove(self.bot.user.id)

                if len(users) < 1:
                    with suppress(Exception):
                        await message.reply(f"No one won the **{giveaway[5]}** giveaway, due to Not enough participants.")
                    async with aiosqlite.connect(db_path) as db:
                        await db.execute("DELETE FROM Giveaway WHERE message_id = ? AND guild_id = ?", (message.id, message.guild.id))
                        await db.commit()
                    return

                winners_count = min(len(users), int(giveaway[4]))
                winner = ', '.join(f'<@!{i}>' for i in random.sample(users, k=winners_count))

                desc = f"Ended at <t:{int(current_time)}:R>\nHosted by <@{int(giveaway[3])}>\nWinner(s): {winner}"
                view = CV2(f"{giveaway[5]}", desc)

                with suppress(Exception):
                    await message.edit(content=f"{TADAA} **GIVEAWAY ENDED** {TADAA}", view=view)
                with suppress(Exception):
                    await message.reply(f"{TADAA} Congrats {winner}, you won **{giveaway[5]}!**, Hosted by <@{int(giveaway[3])}>")

                async with aiosqlite.connect(db_path) as db:
                    await db.execute("DELETE FROM Giveaway WHERE message_id = ? AND guild_id = ?", (message.id, message.guild.id))
                    await db.commit()

            except (discord.HTTPException, aiohttp.ClientResponseError) as e:
                if isinstance(e, discord.NotFound) or getattr(e, 'code', None) == 10008 or "10008" in str(e):
                    async with aiosqlite.connect(db_path) as db:
                        await db.execute("DELETE FROM Giveaway WHERE message_id = ? AND guild_id = ?", (giveaway[2], giveaway[1]))
                        await db.commit()
                else:
                    logging.error(f"Error ending giveaway: {e}")

        except IndexError:
            logging.error(f"Giveaway data is corrupted or missing: {giveaway}")
            async with aiosqlite.connect(db_path) as db:
                await db.execute("DELETE FROM Giveaway WHERE message_id = ? AND guild_id = ?", (giveaway[2], giveaway[1]))
                await db.commit()

    @tasks.loop(seconds=5)
    async def GiveawayEnd(self):
        try:
            now = datetime.datetime.now().timestamp()
            async with aiosqlite.connect(db_path) as db:
                async with db.execute(
                    "SELECT ends_at, guild_id, message_id, host_id, winners, prize, channel_id FROM Giveaway WHERE ends_at <= ?",
                    (now,)
                ) as cursor:
                    ends_raw = await cursor.fetchall()
            for giveaway in ends_raw:
                await self.end_giveaway(giveaway)
        except Exception as e:
            logging.error(f"Error in GiveawayEnd task: {e}")




    @commands.hybrid_command(description="Starts a new giveaway.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_guild_permissions(manage_guild=True)
    async def gstart(self, ctx,
                      time,
                      winners: int,
                      *,
                      prize: str):

        async with aiosqlite.connect(db_path) as db:
            async with db.execute("SELECT message_id, channel_id FROM Giveaway WHERE guild_id = ?", (ctx.guild.id,)) as cursor:
                re = await cursor.fetchall()

        if winners >= 15:
            message = await ctx.send(view=CV2("⚠️ Access Denied", "Cannot exceed more than 15 winners."))
            await asyncio.sleep(5)
            await message.delete()
            return

        g_list = [i[0] for i in re]
        if len(g_list) >= 5:
            message = await ctx.send(view=CV2("⚠️ Access Denied", "You can only host upto 5 giveaways in this Guild."))
            await asyncio.sleep(5)
            await message.delete()
            return

        converted = self.convert(time)
        if converted / 60 >= 50400:
            message = await ctx.send(view=CV2("⚠️ Access Denied", "Time cannot exceed 31 days!"))
            await asyncio.sleep(5)
            await message.delete()
            return

        if converted == -1:
            message = await ctx.send(view=CV2("❌ Error", "Invalid time format"))
            await asyncio.sleep(5)
            await message.delete()
            return
        if converted == -2:
            message = await ctx.send(view=CV2("❌ Error", "Invalid time format. Please provide the time in numbers."))
            await asyncio.sleep(5)
            await message.delete()
            return

        ends = (datetime.datetime.now().timestamp() + converted)

        desc = (
            f"{ARROWRED} Winner(s): **{winners}**\n"
            f"{ARROWRED} Hosted by {ctx.author.mention}\n"
            f"{ARROWRED} Ends <t:{round(ends)}:R> (<t:{round(ends)}:f>)\n\n"
            f"{ARROWRED} React with {TADAA} to participate!"
        )
        
        view = CV2(f"{TADAA} {prize}", desc)

        message = await ctx.send(f"{TADAA} **GIVEAWAY** {TADAA}", view=view)
        try:
           await ctx.message.delete()
        except:
            pass

        async with aiosqlite.connect(db_path) as db:
            await db.execute(
                "INSERT INTO Giveaway(guild_id, host_id, start_time, ends_at, prize, winners, message_id, channel_id) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                (ctx.guild.id, ctx.author.id, datetime.datetime.now(), ends, prize, winners, message.id, ctx.channel.id)
            )
            await db.commit()

        await message.add_reaction(TADAA)

    @commands.Cog.listener("on_message_delete")
    async def GiveawayMessageDelete(self, message):
        if not message.guild or message.author != self.bot.user:
            return

        async with aiosqlite.connect(db_path) as db:
            async with db.execute("SELECT message_id FROM Giveaway WHERE guild_id = ? AND message_id = ?", (message.guild.id, message.id)) as cursor:
                re = await cursor.fetchone()

            if re is not None:
                await db.execute("DELETE FROM Giveaway WHERE channel_id = ? AND message_id = ? AND guild_id = ?", (message.channel.id, message.id, message.guild.id))
                await db.commit()
                print(f"Giveaway message deleted in {message.guild.name} - {message.guild.id}")

    @commands.hybrid_command(name="gend", description="Ends a giveaway before its ending time.", help="Ends a giveaway before its ending time.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_guild_permissions(manage_guild=True)
    async def gend(self, ctx, message_id = None):
        target_message_id = None
        if message_id:
            try:
                target_message_id = int(message_id)
            except ValueError:
                message = await ctx.send(view=CV2("⚠️ Access Denied", "Invalid message ID provided."))
                await asyncio.sleep(5)
                await message.delete()
                return
        elif ctx.message.reference and ctx.message.reference.resolved:
            target_message_id = ctx.message.reference.resolved.id

        if not target_message_id:
            await ctx.send("Please reply to the giveaway message or provide the giveaway ID.")
            return

        current_time = datetime.datetime.now().timestamp()
        async with aiosqlite.connect(db_path) as db:
            async with db.execute('SELECT ends_at, guild_id, message_id, host_id, winners, prize, channel_id FROM Giveaway WHERE message_id = ?', (target_message_id,)) as cursor:
                re = await cursor.fetchone()

            if re is None:
                message = await ctx.send(view=CV2("❌ Error", "The giveaway was not found."))
                await asyncio.sleep(5)
                with suppress(Exception):
                    await message.delete()
                return

            ch = self.bot.get_channel(int(re[6])) or ctx.channel
            try:
                msg = await ch.fetch_message(target_message_id)
            except Exception:
                await db.execute("DELETE FROM Giveaway WHERE message_id = ? AND guild_id = ?", (target_message_id, ctx.guild.id))
                await db.commit()
                await ctx.send("Giveaway message could not be found. Cleared from database.")
                return

            users = []
            if msg.reactions:
                users = [i.id async for i in msg.reactions[0].users()]
            if self.bot.user.id in users:
                users.remove(self.bot.user.id)

            if len(users) < 1:
                await ctx.send(f"{TICK} Successfully Ended the giveaway in <#{int(re[6])}>")
                with suppress(Exception):
                    await msg.reply(f"No one won the **{re[5]}** giveaway, due to not enough participants.")
                await db.execute("DELETE FROM Giveaway WHERE message_id = ? AND guild_id = ?", (msg.id, msg.guild.id))
                await db.commit()
                return

            winners_count = min(len(users), int(re[4]))
            winner = ', '.join(f'<@!{i}>' for i in random.sample(users, k=winners_count))

            desc = f"Ended at <t:{int(current_time)}:R>\nHosted by <@{int(re[3])}>\nWinner(s): {winner}"
            view = CV2(f"🎁 {re[5]}", desc)

            with suppress(Exception):
                await msg.edit(content="🎁 **GIVEAWAY ENDED** 🎁", view=view)

            if int(ctx.channel.id) != int(re[6]):
                await ctx.send(f"{TADAA} Successfully ended the giveaway in <#{int(re[6])}>")

            with suppress(Exception):
                await msg.reply(f" Congrats {winner}, you won **{re[5]}!**, Hosted by <@{int(re[3])}>")
            await db.execute("DELETE FROM Giveaway WHERE message_id = ? AND guild_id = ?", (msg.id, msg.guild.id))
            await db.commit()

    @commands.hybrid_command(description="Rerolls a giveaway on replying the giveaway message.", help="Rerolls a giveaway on replying the giveaway message.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_guild_permissions(manage_guild=True)
    async def greroll(self, ctx, message_id: typing.Optional[int] = None):
        if not ctx.message.reference:
            message = await ctx.reply("Reply to this command with the Giveaway Ended message to reroll.")
            await asyncio.sleep(5)
            with suppress(Exception):
                await message.delete()
            return

        ref_id = ctx.message.reference.resolved.id if ctx.message.reference.resolved else ctx.message.reference.message_id
        try:
            message = await ctx.fetch_message(ref_id)
        except Exception:
            return await ctx.send("Could not find referenced message.")

        async with aiosqlite.connect(db_path) as db:
            async with db.execute("SELECT message_id FROM Giveaway WHERE message_id = ?", (message.id,)) as cursor:
                re = await cursor.fetchone()

        if re is not None:
            msg = await ctx.send(view=CV2("⚠️ Access Denied", "The giveaway is currently running. Please use the `gend` command instead to end the giveaway."))
            await asyncio.sleep(5)
            await msg.delete()
            return

        users = []
        if message.reactions:
            users = [i.id async for i in message.reactions[0].users()]
        if self.bot.user.id in users:
            users.remove(self.bot.user.id)

        if len(users) < 1:
            await message.reply("No one won the giveaway, due to not enough participants.")
            return

        winners = random.sample(users, k=1)
        await message.reply(f" The new winner is " + ", ".join(f"<@{i}>" for i in winners) + ". Congratulations!")

    def convert(self, time):
        pos = ["s", "m", "h", "d"]
        time_dict = {"s": 1, "m": 60, "h": 3600, "d": 86400, "f": 259200}

        unit = time[-1]
        if unit not in pos:
            return -1

        try:
            val = int(time[:-1])
        except ValueError:
            return -2

        return val * time_dict[unit]


    @commands.hybrid_command(name="glist", description="Lists all ongoing giveaways.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_guild_permissions(manage_guild=True)
    async def glist(self, ctx):
        async with aiosqlite.connect(db_path) as db:
            async with db.execute("SELECT prize, ends_at, winners, message_id FROM Giveaway WHERE guild_id = ?", (ctx.guild.id,)) as cursor:
                giveaways = await cursor.fetchall()

        if not giveaways:
            await ctx.send(view=CV2("Ongoing Giveaways", "No ongoing giveaways."))
            return

        desc = ""
        for giveaway in giveaways:
            prize, ends_at, winners, message_id = giveaway
            desc += f"**{prize}**\nEnds: <t:{int(ends_at)}:R> (<t:{int(ends_at)}:f>)\nWinners: {winners}\n[Jump to Message](https://discord.com/channels/{ctx.guild.id}/{ctx.channel.id}/{message_id})\n\n"

        await ctx.send(view=CV2("Ongoing Giveaways", desc))

async def setup(bot):
    await bot.add_cog(Giveaway(bot))
