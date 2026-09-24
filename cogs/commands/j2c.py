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
import aiosqlite
import asyncio
from typing import Dict, List, Optional, Set
from contextlib import suppress

import discord
from discord.ext import commands
from discord import ui, SelectOption, TextStyle

from core import Cog, Context
from utils.emoji import TICK, CROSS, WARNING, SYSTEM

BANNER_FILE = os.path.abspath(os.path.join("assets", "j2c_interface.png"))

def build_interface_embed() -> discord.Embed:
    embed = discord.Embed(
        title="TempVoice Interface",
        description=(
            "This **interface** can be used to manage temporary voice channels.\n"
            "More options are available with **;j2c** commands.\n\n"
            "Press the buttons below to use the interface"
        ),
        color=0xE02B56
    )
    if os.path.exists(BANNER_FILE):
        embed.set_image(url="attachment://interface.png")
    return embed


class JoinToCreate(Cog):
    """High-performance Join To Create temporary voice channel system."""

    def __init__(self, bot):
        self.bot = bot
        self.db_path = "j2c_data.db"
        self.category_name = "J2C"
        self.setup_data: Dict[int, Dict] = {}
        self.private_channels: Dict[int, Dict] = {}  # {vc_id: data}
        self.blocked_users: Dict[int, Set[int]] = {}  # {vc_id: {user_ids}}
        self.trusted_users: Dict[int, Set[int]] = {}  # {vc_id: {user_ids}}
        self.creating_vc: Set[int] = set()

        # Register persistent view
        self.panel_view = ControlPanelView(self)
        self.bot.add_view(self.panel_view)

    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS guild_setup (
                    guild_id INTEGER PRIMARY KEY,
                    join_channel_id INTEGER,
                    control_channel_id INTEGER,
                    control_message_id INTEGER,
                    category_id INTEGER
                )
            """)
            with suppress(Exception):
                await db.execute("ALTER TABLE guild_setup ADD COLUMN category_id INTEGER")

            await db.execute("""
                CREATE TABLE IF NOT EXISTS private_channels (
                    vc_id INTEGER PRIMARY KEY,
                    guild_id INTEGER,
                    owner_id INTEGER,
                    member_limit INTEGER DEFAULT 2,
                    region TEXT DEFAULT '',
                    is_locked BOOLEAN DEFAULT FALSE,
                    has_waiting_room BOOLEAN DEFAULT FALSE,
                    has_chat BOOLEAN DEFAULT TRUE
                )
            """)
            with suppress(Exception):
                await db.execute("ALTER TABLE private_channels ADD COLUMN has_chat BOOLEAN DEFAULT TRUE")

            await db.execute("""
                CREATE TABLE IF NOT EXISTS blocked_users (
                    vc_id INTEGER,
                    user_id INTEGER,
                    PRIMARY KEY (vc_id, user_id)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS trusted_users (
                    vc_id INTEGER,
                    user_id INTEGER,
                    PRIMARY KEY (vc_id, user_id)
                )
            """)
            await db.commit()

    async def load_data(self):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT guild_id, join_channel_id, control_channel_id, control_message_id, category_id FROM guild_setup") as cur:
                async for row in cur:
                    guild_id, join_cid, ctrl_cid, ctrl_mid, cat_id = row
                    self.setup_data[guild_id] = {
                        "join_channel_id": join_cid,
                        "control_channel_id": ctrl_cid,
                        "control_message_id": ctrl_mid,
                        "category_id": cat_id
                    }

            async with db.execute("SELECT vc_id, guild_id, owner_id, member_limit, region, is_locked, has_waiting_room, has_chat FROM private_channels") as cur:
                async for row in cur:
                    vc_id, guild_id, owner_id, limit, region, locked, wr, chat = row
                    self.private_channels[vc_id] = {
                        "owner": owner_id,
                        "limit": limit or 0,
                        "region": region or "",
                        "is_locked": bool(locked),
                        "has_waiting_room": bool(wr),
                        "has_chat": bool(chat),
                        "guild_id": guild_id
                    }

            async with db.execute("SELECT vc_id, user_id FROM blocked_users") as cur:
                async for row in cur:
                    vc_id, user_id = row
                    if vc_id not in self.blocked_users:
                        self.blocked_users[vc_id] = set()
                    self.blocked_users[vc_id].add(user_id)

            async with db.execute("SELECT vc_id, user_id FROM trusted_users") as cur:
                async for row in cur:
                    vc_id, user_id = row
                    if vc_id not in self.trusted_users:
                        self.trusted_users[vc_id] = set()
                    self.trusted_users[vc_id].add(user_id)

    async def save_guild_setup(self, guild_id: int, data: Dict):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO guild_setup (guild_id, join_channel_id, control_channel_id, control_message_id, category_id)
                VALUES (?, ?, ?, ?, ?)
            """, (guild_id, data["join_channel_id"], data["control_channel_id"], data["control_message_id"], data.get("category_id")))
            await db.commit()

    async def save_private_channel(self, vc_id: int, guild_id: int, data: Dict):
        self.private_channels[vc_id] = data
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO private_channels 
                (vc_id, guild_id, owner_id, member_limit, region, is_locked, has_waiting_room, has_chat)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                vc_id, guild_id, data["owner"],
                data.get("limit", 0),
                data.get("region", ""),
                data.get("is_locked", False),
                data.get("has_waiting_room", False),
                data.get("has_chat", True)
            ))
            await db.commit()

    async def delete_private_channel(self, vc_id: int):
        self.private_channels.pop(vc_id, None)
        self.blocked_users.pop(vc_id, None)
        self.trusted_users.pop(vc_id, None)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM private_channels WHERE vc_id = ?", (vc_id,))
            await db.execute("DELETE FROM blocked_users WHERE vc_id = ?", (vc_id,))
            await db.execute("DELETE FROM trusted_users WHERE vc_id = ?", (vc_id,))
            await db.commit()

    async def delete_guild_setup(self, guild_id: int):
        self.setup_data.pop(guild_id, None)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM guild_setup WHERE guild_id = ?", (guild_id,))
            await db.execute("DELETE FROM private_channels WHERE guild_id = ?", (guild_id,))
            await db.commit()

    async def block_user(self, vc_id: int, user_id: int):
        if vc_id not in self.blocked_users:
            self.blocked_users[vc_id] = set()
        self.blocked_users[vc_id].add(user_id)
        if vc_id in self.trusted_users:
            self.trusted_users[vc_id].discard(user_id)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR IGNORE INTO blocked_users (vc_id, user_id) VALUES (?, ?)", (vc_id, user_id))
            await db.execute("DELETE FROM trusted_users WHERE vc_id = ? AND user_id = ?", (vc_id, user_id))
            await db.commit()

    async def unblock_user(self, vc_id: int, user_id: int):
        if vc_id in self.blocked_users:
            self.blocked_users[vc_id].discard(user_id)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM blocked_users WHERE vc_id = ? AND user_id = ?", (vc_id, user_id))
            await db.commit()

    async def trust_user(self, vc_id: int, user_id: int):
        if vc_id not in self.trusted_users:
            self.trusted_users[vc_id] = set()
        self.trusted_users[vc_id].add(user_id)
        if vc_id in self.blocked_users:
            self.blocked_users[vc_id].discard(user_id)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR IGNORE INTO trusted_users (vc_id, user_id) VALUES (?, ?)", (vc_id, user_id))
            await db.execute("DELETE FROM blocked_users WHERE vc_id = ? AND user_id = ?", (vc_id, user_id))
            await db.commit()

    async def untrust_user(self, vc_id: int, user_id: int):
        if vc_id in self.trusted_users:
            self.trusted_users[vc_id].discard(user_id)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM trusted_users WHERE vc_id = ? AND user_id = ?", (vc_id, user_id))
            await db.commit()

    @commands.Cog.listener()
    async def on_ready(self):
        await self.init_db()
        await self.load_data()

    # ── Voice Channel Lifecycle (Fast & Lightweight) ──────────────────
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return

        guild = member.guild
        if guild.id not in self.setup_data:
            return

        setup = self.setup_data[guild.id]

        # 1. User joined the "Join To Create" channel
        if after.channel and after.channel.id == setup["join_channel_id"]:
            if member.id in self.creating_vc:
                return
            self.creating_vc.add(member.id)
            try:
                category = None
                if setup.get("category_id"):
                    category = guild.get_channel(setup["category_id"])
                if not category and after.channel.category:
                    category = after.channel.category
                if not category:
                    category = discord.utils.get(guild.categories, name=self.category_name)

                # Channel permissions: owner has full manage rights
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(connect=True, speak=True),
                    member: discord.PermissionOverwrite(
                        connect=True, speak=True, manage_channels=True, move_members=True
                    )
                }

                vc = await guild.create_voice_channel(
                    name=f"{member.display_name}'s VC",
                    category=category,
                    overwrites=overwrites,
                    user_limit=2,
                    reason=f"TempVoice created for {member.name}"
                )

                await member.move_to(vc)

                data = {
                    "owner": member.id,
                    "limit": 2,
                    "region": "",
                    "is_locked": False,
                    "has_waiting_room": False,
                    "has_chat": True,
                    "guild_id": guild.id
                }
                await self.save_private_channel(vc.id, guild.id, data)
            except Exception as e:
                print(f"[J2C] Failed to create voice channel for {member}: {e}")
            finally:
                self.creating_vc.discard(member.id)

        # 2. User left or disconnected from a temporary VC
        if before.channel and before.channel.id in self.private_channels:
            # Check if left channel is empty
            if len(before.channel.members) == 0:
                vc_id = before.channel.id
                with suppress(Exception):
                    await before.channel.delete(reason="TempVoice empty — auto delete")
                await self.delete_private_channel(vc_id)

    # ── J2C Setup & Reset Commands ────────────────────────────────────
    @commands.group(name="j2c", aliases=["jointocreate", "tempvoice", "jtc"], invoke_without_command=True)
    async def j2c_group(self, ctx: Context):
        """TempVoice management interface and commands."""
        embed = discord.Embed(
            title="🔊 TempVoice System",
            description=(
                f"Manage your temporary voice channels easily!\n\n"
                f"**Setup Commands:**\n"
                f"`{ctx.prefix}j2c setup` — Setup the TempVoice interface & Join to Create channel\n"
                f"`{ctx.prefix}j2c reset` — Completely remove and reset TempVoice\n\n"
                f"**Voice Controls (When in your temporary VC):**\n"
                f"`{ctx.prefix}j2c name <new name>` — Rename your VC\n"
                f"`{ctx.prefix}j2c limit <0-99>` — Set user limit\n"
                f"`{ctx.prefix}j2c lock` / `{ctx.prefix}j2c unlock` — Lock/Unlock VC\n"
                f"`{ctx.prefix}j2c trust @user` / `{ctx.prefix}j2c untrust @user`\n"
                f"`{ctx.prefix}j2c block @user` / `{ctx.prefix}j2c unblock @user`\n"
                f"`{ctx.prefix}j2c kick @user` — Kick a user out of VC\n"
                f"`{ctx.prefix}j2c claim` — Claim an abandoned VC\n"
                f"`{ctx.prefix}j2c transfer @user` — Transfer VC ownership\n"
                f"`{ctx.prefix}j2c delete` — Delete your temporary VC"
            ),
            color=0xE02B56
        )
        await ctx.send(embed=embed)

    @j2c_group.command(name="setup")
    @commands.has_permissions(administrator=True)
    async def j2c_setup(self, ctx: Context):
        """Set up the TempVoice system with the control interface."""
        if ctx.guild.id in self.setup_data:
            return await ctx.send(f"{CROSS} TempVoice is already set up in this server! Use `{ctx.prefix}j2c reset` first to re-setup.")

        status_msg = await ctx.send("⚙️ Setting up TempVoice channels and interface...")

        # 1. Category
        category = discord.utils.get(ctx.guild.categories, name=self.category_name)
        if not category:
            category = await ctx.guild.create_category(self.category_name, reason="TempVoice Setup")

        # 2. Join to create voice channel
        join_channel = await ctx.guild.create_voice_channel(
            name="➕ Join to Create",
            category=category,
            reason="TempVoice Join Channel"
        )

        # 3. Control interface text channel
        control_channel = await ctx.guild.create_text_channel(
            name="interface",
            category=category,
            reason="TempVoice Interface Channel"
        )

        # Set permissions on interface channel so @everyone can see and interact, but not type messages
        with suppress(Exception):
            await control_channel.set_permissions(
                ctx.guild.default_role,
                view_channel=True,
                send_messages=False,
                read_message_history=True
            )

        # 4. Send the visual TempVoice interface message
        embed = build_interface_embed()
        view = ControlPanelView(self)

        file = None
        if os.path.exists(BANNER_FILE):
            file = discord.File(BANNER_FILE, filename="interface.png")

        control_message = await control_channel.send(file=file, embed=embed, view=view)

        # 5. Save setup in memory and database
        self.setup_data[ctx.guild.id] = {
            "join_channel_id": join_channel.id,
            "control_channel_id": control_channel.id,
            "control_message_id": control_message.id,
            "category_id": category.id
        }
        await self.save_guild_setup(ctx.guild.id, self.setup_data[ctx.guild.id])

        await status_msg.edit(content=f"{TICK} **TempVoice setup complete!**\n• Interface: {control_channel.mention}\n• Join Channel: {join_channel.mention}")

    @j2c_group.command(name="reset")
    @commands.has_permissions(administrator=True)
    async def j2c_reset(self, ctx: Context):
        """Remove and reset the TempVoice system from the server."""
        if ctx.guild.id not in self.setup_data:
            return await ctx.send(f"{CROSS} TempVoice is not set up in this server.")

        status_msg = await ctx.send("🧹 Resetting TempVoice system...")
        setup = self.setup_data[ctx.guild.id]

        # Delete join and control channels
        for cid in (setup.get("join_channel_id"), setup.get("control_channel_id")):
            if cid:
                ch = ctx.guild.get_channel(cid)
                if ch:
                    with suppress(Exception):
                        await ch.delete(reason="TempVoice Reset")

        # Delete all active temporary VCs in this guild
        for vc_id, data in list(self.private_channels.items()):
            if data.get("guild_id") == ctx.guild.id:
                ch = ctx.guild.get_channel(vc_id)
                if ch:
                    with suppress(Exception):
                        await ch.delete(reason="TempVoice Reset")
                await self.delete_private_channel(vc_id)

        # Delete category if empty
        if setup.get("category_id"):
            cat = ctx.guild.get_channel(setup["category_id"])
            if cat and len(cat.channels) == 0:
                with suppress(Exception):
                    await cat.delete(reason="TempVoice Reset")

        await self.delete_guild_setup(ctx.guild.id)
        await status_msg.edit(content=f"{TICK} **TempVoice system has been completely reset!**")

    # ── Voice Prefix Commands ─────────────────────────────────────────
    def get_user_vc(self, ctx: Context) -> Optional[discord.VoiceChannel]:
        if ctx.author.voice and ctx.author.voice.channel:
            vc_id = ctx.author.voice.channel.id
            if vc_id in self.private_channels and self.private_channels[vc_id]["owner"] == ctx.author.id:
                return ctx.author.voice.channel
        for vc_id, data in self.private_channels.items():
            if data["owner"] == ctx.author.id and data["guild_id"] == ctx.guild.id:
                return ctx.guild.get_channel(vc_id)
        return None

    @j2c_group.command(name="lock")
    async def voice_lock(self, ctx: Context):
        """Lock your temporary voice channel."""
        vc = self.get_user_vc(ctx)
        if not vc:
            return await ctx.send(f"{CROSS} You must own an active temporary voice channel!")
        await vc.set_permissions(ctx.guild.default_role, connect=False)
        self.private_channels[vc.id]["is_locked"] = True
        await self.save_private_channel(vc.id, ctx.guild.id, self.private_channels[vc.id])
        await ctx.send(f"{TICK} **Locked {vc.name}!** Only trusted users can connect.")

    @j2c_group.command(name="unlock")
    async def voice_unlock(self, ctx: Context):
        """Unlock your temporary voice channel."""
        vc = self.get_user_vc(ctx)
        if not vc:
            return await ctx.send(f"{CROSS} You must own an active temporary voice channel!")
        await vc.set_permissions(ctx.guild.default_role, connect=True)
        self.private_channels[vc.id]["is_locked"] = False
        await self.save_private_channel(vc.id, ctx.guild.id, self.private_channels[vc.id])
        await ctx.send(f"{TICK} **Unlocked {vc.name}!** Everyone can now connect.")

    @j2c_group.command(name="name", aliases=["rename"])
    async def voice_name(self, ctx: Context, *, new_name: str):
        """Rename your temporary voice channel."""
        vc = self.get_user_vc(ctx)
        if not vc:
            return await ctx.send(f"{CROSS} You must own an active temporary voice channel!")
        new_name = new_name.strip()[:50]
        try:
            await vc.edit(name=new_name)
            await ctx.send(f"{TICK} Voice channel renamed to **{new_name}**!")
        except discord.HTTPException:
            await ctx.send(f"{CROSS} Discord rate limit: Channels can only be renamed twice every 10 minutes.")

    @j2c_group.command(name="limit")
    async def voice_limit(self, ctx: Context, limit: int):
        """Set the user limit for your temporary voice channel (0 for unlimited)."""
        vc = self.get_user_vc(ctx)
        if not vc:
            return await ctx.send(f"{CROSS} You must own an active temporary voice channel!")
        if limit < 0 or limit > 99:
            return await ctx.send(f"{CROSS} Limit must be between `0` and `99`.")
        await vc.edit(user_limit=limit)
        self.private_channels[vc.id]["limit"] = limit
        await self.save_private_channel(vc.id, ctx.guild.id, self.private_channels[vc.id])
        await ctx.send(f"{TICK} User limit set to **{limit if limit > 0 else 'Unlimited'}**!")

    @j2c_group.command(name="trust", aliases=["permit"])
    async def voice_trust(self, ctx: Context, member: discord.Member):
        """Trust a user to join your channel even when locked."""
        vc = self.get_user_vc(ctx)
        if not vc:
            return await ctx.send(f"{CROSS} You must own an active temporary voice channel!")
        await vc.set_permissions(member, connect=True, speak=True, view_channel=True)
        await self.trust_user(vc.id, member.id)
        await ctx.send(f"{TICK} {member.mention} is now **Trusted**!")

    @j2c_group.command(name="untrust")
    async def voice_untrust(self, ctx: Context, member: discord.Member):
        """Remove trust from a user."""
        vc = self.get_user_vc(ctx)
        if not vc:
            return await ctx.send(f"{CROSS} You must own an active temporary voice channel!")
        await vc.set_permissions(member, overwrite=None)
        await self.untrust_user(vc.id, member.id)
        await ctx.send(f"{TICK} Removed trust from {member.mention}.")

    @j2c_group.command(name="block", aliases=["reject"])
    async def voice_block(self, ctx: Context, member: discord.Member):
        """Block a user from connecting to your temporary voice channel."""
        vc = self.get_user_vc(ctx)
        if not vc:
            return await ctx.send(f"{CROSS} You must own an active temporary voice channel!")
        if member.id == ctx.author.id:
            return await ctx.send(f"{CROSS} You cannot block yourself!")
        await vc.set_permissions(member, connect=False, view_channel=False)
        if member in vc.members:
            with suppress(Exception):
                await member.move_to(None)
        await self.block_user(vc.id, member.id)
        await ctx.send(f"{TICK} Blocked {member.mention} from your voice channel.")

    @j2c_group.command(name="unblock")
    async def voice_unblock(self, ctx: Context, member: discord.Member):
        """Unblock a user."""
        vc = self.get_user_vc(ctx)
        if not vc:
            return await ctx.send(f"{CROSS} You must own an active temporary voice channel!")
        await vc.set_permissions(member, overwrite=None)
        await self.unblock_user(vc.id, member.id)
        await ctx.send(f"{TICK} Unblocked {member.mention}.")

    @j2c_group.command(name="kick")
    async def voice_kick(self, ctx: Context, member: discord.Member):
        """Kick a user out of your temporary voice channel."""
        vc = self.get_user_vc(ctx)
        if not vc:
            return await ctx.send(f"{CROSS} You must own an active temporary voice channel!")
        if member not in vc.members:
            return await ctx.send(f"{CROSS} That user is not in your voice channel.")
        if member.id == ctx.author.id:
            return await ctx.send(f"{CROSS} You cannot kick yourself!")
        await member.move_to(None, reason=f"Kicked by {ctx.author.name}")
        await ctx.send(f"{TICK} Kicked {member.mention} from your voice channel.")

    @j2c_group.command(name="claim")
    async def voice_claim(self, ctx: Context):
        """Claim ownership of the temporary voice channel you are currently in."""
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send(f"{CROSS} You must be inside a temporary voice channel to claim it!")
        vc = ctx.author.voice.channel
        if vc.id not in self.private_channels:
            return await ctx.send(f"{CROSS} This is not an active temporary voice channel.")
        data = self.private_channels[vc.id]
        owner = ctx.guild.get_member(data["owner"])
        if owner and owner in vc.members:
            return await ctx.send(f"{CROSS} The owner ({owner.mention}) is still present in this voice channel!")
        data["owner"] = ctx.author.id
        await self.save_private_channel(vc.id, ctx.guild.id, data)
        await vc.set_permissions(ctx.author, connect=True, speak=True, manage_channels=True, move_members=True)
        with suppress(Exception):
            await vc.edit(name=f"{ctx.author.display_name}'s VC")
        await ctx.send(f"{TICK} 👑 You are now the owner of {vc.mention}!")

    @j2c_group.command(name="transfer")
    async def voice_transfer(self, ctx: Context, member: discord.Member):
        """Transfer ownership of your temporary voice channel to another member."""
        vc = self.get_user_vc(ctx)
        if not vc:
            return await ctx.send(f"{CROSS} You must own an active temporary voice channel!")
        if member not in vc.members:
            return await ctx.send(f"{CROSS} That member is not inside your voice channel.")
        self.private_channels[vc.id]["owner"] = member.id
        await self.save_private_channel(vc.id, ctx.guild.id, self.private_channels[vc.id])
        await vc.set_permissions(member, connect=True, speak=True, manage_channels=True, move_members=True)
        await ctx.send(f"{TICK} Transferred ownership of {vc.mention} to {member.mention}!")

    @j2c_group.command(name="delete")
    async def voice_delete(self, ctx: Context):
        """Delete your temporary voice channel."""
        vc = self.get_user_vc(ctx)
        if not vc:
            return await ctx.send(f"{CROSS} You must own an active temporary voice channel!")
        for m in vc.members:
            with suppress(Exception):
                await m.move_to(None)
        with suppress(Exception):
            await vc.delete(reason=f"Deleted by owner {ctx.author.name}")
        await self.delete_private_channel(vc.id)
        await ctx.send(f"{TICK} Deleted your temporary voice channel.")


# ╔══════════════════════════════════════════════════════════════════╗
# ║                   PERSISTENT CONTROL PANEL VIEW                  ║
# ╚══════════════════════════════════════════════════════════════════╝

class ControlPanelView(ui.View):
    """The 3x5 button grid matching TempVoice interface design."""

    def __init__(self, cog: JoinToCreate):
        super().__init__(timeout=None)
        self.cog = cog

    async def get_user_channel(self, interaction: discord.Interaction) -> Optional[discord.VoiceChannel]:
        """Finds the temporary voice channel associated with the user."""
        # Check channel user is currently in
        if interaction.user.voice and interaction.user.voice.channel:
            vc = interaction.user.voice.channel
            if vc.id in self.cog.private_channels:
                return vc

        # Otherwise check if user owns an active temporary VC in this guild
        for vc_id, data in self.cog.private_channels.items():
            if data["owner"] == interaction.user.id and data.get("guild_id") == interaction.guild.id:
                ch = interaction.guild.get_channel(vc_id)
                if ch:
                    return ch
        return None

    def is_owner(self, vc_id: int, user_id: int) -> bool:
        return self.cog.private_channels.get(vc_id, {}).get("owner") == user_id

    # ── ROW 0: NAME | LIMIT | PRIVACY | WAITING ROOM | CHAT ────────────
    @ui.button(emoji="🏷️", style=discord.ButtonStyle.secondary, custom_id="j2c:name", row=0)
    async def btn_name(self, interaction: discord.Interaction, button: ui.Button):
        vc = await self.get_user_channel(interaction)
        if not vc or not self.is_owner(vc.id, interaction.user.id):
            return await interaction.response.send_message("❌ You must be the owner of a temporary voice channel to rename it!", ephemeral=True)
        await interaction.response.send_modal(RenameModal(vc))

    @ui.button(emoji="👥", style=discord.ButtonStyle.secondary, custom_id="j2c:limit", row=0)
    async def btn_limit(self, interaction: discord.Interaction, button: ui.Button):
        vc = await self.get_user_channel(interaction)
        if not vc or not self.is_owner(vc.id, interaction.user.id):
            return await interaction.response.send_message("❌ You must be the owner of a temporary voice channel to set user limit!", ephemeral=True)
        await interaction.response.send_modal(LimitModal(self.cog, vc))

    @ui.button(emoji="🔒", style=discord.ButtonStyle.secondary, custom_id="j2c:privacy", row=0)
    async def btn_privacy(self, interaction: discord.Interaction, button: ui.Button):
        vc = await self.get_user_channel(interaction)
        if not vc or not self.is_owner(vc.id, interaction.user.id):
            return await interaction.response.send_message("❌ You must be the owner of a temporary voice channel to change privacy!", ephemeral=True)

        is_locked = self.cog.private_channels[vc.id].get("is_locked", False)
        new_state = not is_locked
        self.cog.private_channels[vc.id]["is_locked"] = new_state
        await self.cog.save_private_channel(vc.id, interaction.guild.id, self.cog.private_channels[vc.id])

        await vc.set_permissions(interaction.guild.default_role, connect=not new_state)
        await vc.set_permissions(interaction.user, connect=True, speak=True, view_channel=True)

        msg = "🔒 Channel is now **Locked**! Only trusted users can connect." if new_state else "🔓 Channel is now **Unlocked**! Anyone can connect."
        await interaction.response.send_message(msg, ephemeral=True)

    @ui.button(emoji="🕒", style=discord.ButtonStyle.secondary, custom_id="j2c:waiting", row=0)
    async def btn_waiting(self, interaction: discord.Interaction, button: ui.Button):
        vc = await self.get_user_channel(interaction)
        if not vc or not self.is_owner(vc.id, interaction.user.id):
            return await interaction.response.send_message("❌ You must be the owner of a temporary voice channel!", ephemeral=True)

        wr = self.cog.private_channels[vc.id].get("has_waiting_room", False)
        new_wr = not wr
        self.cog.private_channels[vc.id]["has_waiting_room"] = new_wr
        await self.cog.save_private_channel(vc.id, interaction.guild.id, self.cog.private_channels[vc.id])

        if new_wr:
            await vc.set_permissions(interaction.guild.default_role, speak=False)
            res = "🕒 **Waiting Room Mode Enabled!** Connected users cannot speak until approved."
        else:
            await vc.set_permissions(interaction.guild.default_role, speak=True)
            res = "🕒 **Waiting Room Mode Disabled!** Connected users can speak freely."
        await interaction.response.send_message(res, ephemeral=True)

    @ui.button(emoji="💬", style=discord.ButtonStyle.secondary, custom_id="j2c:chat", row=0)
    async def btn_chat(self, interaction: discord.Interaction, button: ui.Button):
        vc = await self.get_user_channel(interaction)
        if not vc or not self.is_owner(vc.id, interaction.user.id):
            return await interaction.response.send_message("❌ You must be the owner of a temporary voice channel!", ephemeral=True)

        chat = self.cog.private_channels[vc.id].get("has_chat", True)
        new_chat = not chat
        self.cog.private_channels[vc.id]["has_chat"] = new_chat
        await self.cog.save_private_channel(vc.id, interaction.guild.id, self.cog.private_channels[vc.id])

        await vc.set_permissions(interaction.guild.default_role, send_messages=new_chat)
        res = "💬 Channel text chat has been **Enabled** for members." if new_chat else "💬 Channel text chat has been **Disabled** for members."
        await interaction.response.send_message(res, ephemeral=True)

    # ── ROW 1: TRUST | UNTRUST | INVITE | KICK | REGION ────────────────
    @ui.button(emoji="➕", style=discord.ButtonStyle.secondary, custom_id="j2c:trust", row=1)
    async def btn_trust(self, interaction: discord.Interaction, button: ui.Button):
        vc = await self.get_user_channel(interaction)
        if not vc or not self.is_owner(vc.id, interaction.user.id):
            return await interaction.response.send_message("❌ You must own a temporary voice channel to trust members!", ephemeral=True)

        view = SingleMemberSelectView(placeholder="Select member to trust...", callback_func=self.cb_trust, vc=vc)
        await interaction.response.send_message("Select a member to **Trust** (can join even when locked):", view=view, ephemeral=True)

    async def cb_trust(self, interaction: discord.Interaction, selected_id: int, vc: discord.VoiceChannel):
        target = interaction.guild.get_member(selected_id)
        if not target:
            return await interaction.response.send_message("User not found!", ephemeral=True)
        await vc.set_permissions(target, connect=True, speak=True, view_channel=True)
        await self.cog.trust_user(vc.id, target.id)
        await interaction.response.send_message(f"✅ {target.mention} is now **Trusted** and can join your channel!", ephemeral=True)

    @ui.button(emoji="➖", style=discord.ButtonStyle.secondary, custom_id="j2c:untrust", row=1)
    async def btn_untrust(self, interaction: discord.Interaction, button: ui.Button):
        vc = await self.get_user_channel(interaction)
        if not vc or not self.is_owner(vc.id, interaction.user.id):
            return await interaction.response.send_message("❌ You must own a temporary voice channel!", ephemeral=True)

        trusted_set = self.cog.trusted_users.get(vc.id, set())
        options = []
        for uid in trusted_set:
            m = interaction.guild.get_member(uid)
            if m:
                options.append(SelectOption(label=m.display_name, value=str(m.id), description=f"ID: {m.id}"))
        if not options:
            return await interaction.response.send_message("ℹ️ No trusted users currently registered for your channel.", ephemeral=True)

        view = DropdownSelectView(options=options[:25], placeholder="Select user to untrust...", callback_func=self.cb_untrust, vc=vc)
        await interaction.response.send_message("Select a user to remove from trusted list:", view=view, ephemeral=True)

    async def cb_untrust(self, interaction: discord.Interaction, selected_value: str, vc: discord.VoiceChannel):
        uid = int(selected_value)
        target = interaction.guild.get_member(uid)
        if target:
            await vc.set_permissions(target, overwrite=None)
        await self.cog.untrust_user(vc.id, uid)
        await interaction.response.send_message(f"❌ Removed trust from <@{uid}>.", ephemeral=True)

    @ui.button(emoji="📩", style=discord.ButtonStyle.secondary, custom_id="j2c:invite", row=1)
    async def btn_invite(self, interaction: discord.Interaction, button: ui.Button):
        vc = await self.get_user_channel(interaction)
        if not vc:
            return await interaction.response.send_message("❌ You are not connected to a temporary voice channel!", ephemeral=True)

        view = SingleMemberSelectView(placeholder="Select member to invite...", callback_func=self.cb_invite, vc=vc)
        await interaction.response.send_message("Select a member to invite to your voice channel:", view=view, ephemeral=True)

    async def cb_invite(self, interaction: discord.Interaction, selected_id: int, vc: discord.VoiceChannel):
        target = interaction.guild.get_member(selected_id)
        if not target:
            return await interaction.response.send_message("User not found!", ephemeral=True)
        try:
            invite = await vc.create_invite(max_age=3600, max_uses=1, reason=f"TempVoice invite from {interaction.user.name}")
            embed = discord.Embed(
                title="📩 Voice Channel Invitation",
                description=f"**{interaction.user.display_name}** invited you to join **{vc.name}** in **{interaction.guild.name}**!\n\n👉 **[Click Here to Join Voice Channel]({invite.url})**",
                color=0xE02B56
            )
            await target.send(embed=embed)
            await interaction.response.send_message(f"📩 Sent invite to {target.mention}!", ephemeral=True)
        except Exception:
            await interaction.response.send_message(f"⚠️ Could not DM {target.mention}. Share this invite link directly:\n{invite.url}", ephemeral=True)

    @ui.button(emoji="👢", style=discord.ButtonStyle.secondary, custom_id="j2c:kick", row=1)
    async def btn_kick(self, interaction: discord.Interaction, button: ui.Button):
        vc = await self.get_user_channel(interaction)
        if not vc or not self.is_owner(vc.id, interaction.user.id):
            return await interaction.response.send_message("❌ You must own a temporary voice channel to kick members!", ephemeral=True)

        other_members = [m for m in vc.members if m.id != interaction.user.id]
        if not other_members:
            return await interaction.response.send_message("ℹ️ No other members currently in your voice channel to kick.", ephemeral=True)

        options = [SelectOption(label=m.display_name, value=str(m.id), description=f"ID: {m.id}") for m in other_members[:25]]
        view = DropdownSelectView(options=options, placeholder="Select member to kick...", callback_func=self.cb_kick, vc=vc)
        await interaction.response.send_message("Select a member to kick out of your voice channel:", view=view, ephemeral=True)

    async def cb_kick(self, interaction: discord.Interaction, selected_value: str, vc: discord.VoiceChannel):
        target = interaction.guild.get_member(int(selected_value))
        if target and target in vc.members:
            await target.move_to(None, reason=f"Kicked by TempVoice owner {interaction.user.name}")
            await interaction.response.send_message(f"👢 Kicked {target.mention} from your voice channel.", ephemeral=True)
        else:
            await interaction.response.send_message("User is no longer in the voice channel.", ephemeral=True)

    @ui.button(emoji="🌍", style=discord.ButtonStyle.secondary, custom_id="j2c:region", row=1)
    async def btn_region(self, interaction: discord.Interaction, button: ui.Button):
        vc = await self.get_user_channel(interaction)
        if not vc or not self.is_owner(vc.id, interaction.user.id):
            return await interaction.response.send_message("❌ You must own a temporary voice channel to change regions!", ephemeral=True)

        regions = [
            SelectOption(label="Automatic", value="auto", description="Best region automatically chosen"),
            SelectOption(label="US East", value="us-east"),
            SelectOption(label="US West", value="us-west"),
            SelectOption(label="US Central", value="us-central"),
            SelectOption(label="Europe", value="europe"),
            SelectOption(label="India", value="india"),
            SelectOption(label="Singapore", value="singapore"),
            SelectOption(label="Japan", value="japan"),
            SelectOption(label="Brazil", value="brazil"),
            SelectOption(label="Australia", value="australia")
        ]
        view = DropdownSelectView(options=regions, placeholder="Select Voice RTC Region...", callback_func=self.cb_region, vc=vc)
        await interaction.response.send_message("Select a voice RTC region:", view=view, ephemeral=True)

    async def cb_region(self, interaction: discord.Interaction, selected_value: str, vc: discord.VoiceChannel):
        reg = None if selected_value == "auto" else selected_value
        try:
            await vc.edit(rtc_region=reg)
            self.cog.private_channels[vc.id]["region"] = selected_value
            await self.cog.save_private_channel(vc.id, interaction.guild.id, self.cog.private_channels[vc.id])
            await interaction.response.send_message(f"🌍 Voice RTC region changed to **{selected_value}**!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to set region: `{e}`", ephemeral=True)

    # ── ROW 2: BLOCK | UNBLOCK | CLAIM | TRANSFER | DELETE ─────────────
    @ui.button(emoji="🚫", style=discord.ButtonStyle.secondary, custom_id="j2c:block", row=2)
    async def btn_block(self, interaction: discord.Interaction, button: ui.Button):
        vc = await self.get_user_channel(interaction)
        if not vc or not self.is_owner(vc.id, interaction.user.id):
            return await interaction.response.send_message("❌ You must own a temporary voice channel to block members!", ephemeral=True)

        view = SingleMemberSelectView(placeholder="Select member to block...", callback_func=self.cb_block, vc=vc)
        await interaction.response.send_message("Select a member to **Block** from joining your channel:", view=view, ephemeral=True)

    async def cb_block(self, interaction: discord.Interaction, selected_id: int, vc: discord.VoiceChannel):
        if selected_id == interaction.user.id:
            return await interaction.response.send_message("❌ You cannot block yourself!", ephemeral=True)
        target = interaction.guild.get_member(selected_id)
        if target:
            await vc.set_permissions(target, connect=False, view_channel=False)
            if target in vc.members:
                with suppress(Exception):
                    await target.move_to(None)
        await self.cog.block_user(vc.id, selected_id)
        await interaction.response.send_message(f"🚫 Blocked <@{selected_id}> from joining your voice channel.", ephemeral=True)

    @ui.button(emoji="🔓", style=discord.ButtonStyle.secondary, custom_id="j2c:unblock", row=2)
    async def btn_unblock(self, interaction: discord.Interaction, button: ui.Button):
        vc = await self.get_user_channel(interaction)
        if not vc or not self.is_owner(vc.id, interaction.user.id):
            return await interaction.response.send_message("❌ You must own a temporary voice channel!", ephemeral=True)

        blocked_set = self.cog.blocked_users.get(vc.id, set())
        options = []
        for uid in blocked_set:
            m = interaction.guild.get_member(uid)
            options.append(SelectOption(label=m.display_name if m else f"User {uid}", value=str(uid)))
        if not options:
            return await interaction.response.send_message("ℹ️ No blocked members for your voice channel.", ephemeral=True)

        view = DropdownSelectView(options=options[:25], placeholder="Select user to unblock...", callback_func=self.cb_unblock, vc=vc)
        await interaction.response.send_message("Select a member to unblock:", view=view, ephemeral=True)

    async def cb_unblock(self, interaction: discord.Interaction, selected_value: str, vc: discord.VoiceChannel):
        uid = int(selected_value)
        target = interaction.guild.get_member(uid)
        if target:
            await vc.set_permissions(target, overwrite=None)
        await self.cog.unblock_user(vc.id, uid)
        await interaction.response.send_message(f"🔓 Unblocked <@{uid}>.", ephemeral=True)

    @ui.button(emoji="👑", style=discord.ButtonStyle.secondary, custom_id="j2c:claim", row=2)
    async def btn_claim(self, interaction: discord.Interaction, button: ui.Button):
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message("❌ You must be inside a temporary voice channel to claim it!", ephemeral=True)

        vc = interaction.user.voice.channel
        if vc.id not in self.cog.private_channels:
            return await interaction.response.send_message("❌ This is not a temporary voice channel!", ephemeral=True)

        data = self.cog.private_channels[vc.id]
        owner = interaction.guild.get_member(data["owner"])

        if owner and owner in vc.members:
            return await interaction.response.send_message(f"❌ The current channel owner ({owner.mention}) is still in this voice channel!", ephemeral=True)

        data["owner"] = interaction.user.id
        await self.cog.save_private_channel(vc.id, interaction.guild.id, data)
        await vc.set_permissions(interaction.user, connect=True, speak=True, manage_channels=True, move_members=True)
        with suppress(Exception):
            await vc.edit(name=f"{interaction.user.display_name}'s VC")

        await interaction.response.send_message(f"👑 **Congratulations!** You are now the owner of {vc.mention}!", ephemeral=True)

    @ui.button(emoji="🔄", style=discord.ButtonStyle.secondary, custom_id="j2c:transfer", row=2)
    async def btn_transfer(self, interaction: discord.Interaction, button: ui.Button):
        vc = await self.get_user_channel(interaction)
        if not vc or not self.is_owner(vc.id, interaction.user.id):
            return await interaction.response.send_message("❌ You must own a temporary voice channel to transfer it!", ephemeral=True)

        other_members = [m for m in vc.members if m.id != interaction.user.id]
        if not other_members:
            return await interaction.response.send_message("ℹ️ No other members in your voice channel to transfer ownership to.", ephemeral=True)

        options = [SelectOption(label=m.display_name, value=str(m.id), description=f"ID: {m.id}") for m in other_members[:25]]
        view = DropdownSelectView(options=options, placeholder="Select new channel owner...", callback_func=self.cb_transfer, vc=vc)
        await interaction.response.send_message("Select a member to transfer voice channel ownership to:", view=view, ephemeral=True)

    async def cb_transfer(self, interaction: discord.Interaction, selected_value: str, vc: discord.VoiceChannel):
        target = interaction.guild.get_member(int(selected_value))
        if not target:
            return await interaction.response.send_message("User not found!", ephemeral=True)

        self.cog.private_channels[vc.id]["owner"] = target.id
        await self.cog.save_private_channel(vc.id, interaction.guild.id, self.cog.private_channels[vc.id])
        await vc.set_permissions(target, connect=True, speak=True, manage_channels=True, move_members=True)
        await interaction.response.send_message(f"👑 Transferred ownership of {vc.mention} to {target.mention}!", ephemeral=True)

    @ui.button(emoji="🗑️", style=discord.ButtonStyle.danger, custom_id="j2c:delete", row=2)
    async def btn_delete(self, interaction: discord.Interaction, button: ui.Button):
        vc = await self.get_user_channel(interaction)
        if not vc or not self.is_owner(vc.id, interaction.user.id):
            return await interaction.response.send_message("❌ You must own a temporary voice channel to delete it!", ephemeral=True)

        await interaction.response.send_message("🗑️ Deleting your temporary voice channel...", ephemeral=True)

        for m in vc.members:
            with suppress(Exception):
                await m.move_to(None)

        with suppress(Exception):
            await vc.delete(reason=f"Deleted by TempVoice owner {interaction.user.name}")

        await self.cog.delete_private_channel(vc.id)


# ╔══════════════════════════════════════════════════════════════════╗
# ║                         MODALS & SELECTS                         ║
# ╚══════════════════════════════════════════════════════════════════╝

class RenameModal(ui.Modal, title="Rename Voice Channel"):
    name_input = ui.TextInput(
        label="Channel Name",
        placeholder="Enter new channel name...",
        max_length=50,
        required=True
    )

    def __init__(self, vc: discord.VoiceChannel):
        super().__init__()
        self.vc = vc
        self.name_input.default = vc.name

    async def on_submit(self, interaction: discord.Interaction):
        new_name = self.name_input.value.strip()
        if not new_name:
            return await interaction.response.send_message("Channel name cannot be empty.", ephemeral=True)
        try:
            await self.vc.edit(name=new_name)
            await interaction.response.send_message(f"✅ Voice channel renamed to **{new_name}**!", ephemeral=True)
        except discord.HTTPException:
            await interaction.response.send_message("⏳ Discord rate limit: Channels can only be renamed twice every 10 minutes.", ephemeral=True)


class LimitModal(ui.Modal, title="Set User Limit"):
    limit_input = ui.TextInput(
        label="User Limit (0 = Unlimited)",
        placeholder="Enter number between 0 and 99",
        max_length=2,
        required=True
    )

    def __init__(self, cog: JoinToCreate, vc: discord.VoiceChannel):
        super().__init__()
        self.cog = cog
        self.vc = vc
        self.limit_input.default = str(vc.user_limit or 0)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            val = int(self.limit_input.value.strip())
            if val < 0 or val > 99:
                raise ValueError
        except ValueError:
            return await interaction.response.send_message("❌ Invalid number! Enter a value between 0 and 99.", ephemeral=True)

        await self.vc.edit(user_limit=val)
        if self.vc.id in self.cog.private_channels:
            self.cog.private_channels[self.vc.id]["limit"] = val
            await self.cog.save_private_channel(self.vc.id, interaction.guild.id, self.cog.private_channels[self.vc.id])

        await interaction.response.send_message(f"✅ User limit set to **{val if val > 0 else 'Unlimited'}**!", ephemeral=True)


class SingleMemberSelectView(ui.View):
    def __init__(self, placeholder: str, callback_func, vc: discord.VoiceChannel):
        super().__init__(timeout=60)
        self.callback_func = callback_func
        self.vc = vc
        select = ui.UserSelect(placeholder=placeholder, min_values=1, max_values=1)
        select.callback = self.on_select
        self.add_item(select)

    async def on_select(self, interaction: discord.Interaction):
        select = self.children[0]
        selected_user = select.values[0]
        await self.callback_func(interaction, selected_user.id, self.vc)


class DropdownSelectView(ui.View):
    def __init__(self, options: List[SelectOption], placeholder: str, callback_func, vc: discord.VoiceChannel):
        super().__init__(timeout=60)
        self.callback_func = callback_func
        self.vc = vc
        select = ui.Select(placeholder=placeholder, options=options, min_values=1, max_values=1)
        select.callback = self.on_select
        self.add_item(select)

    async def on_select(self, interaction: discord.Interaction):
        select = self.children[0]
        selected_val = select.values[0]
        await self.callback_func(interaction, selected_val, self.vc)


async def setup(bot):
    await bot.add_cog(JoinToCreate(bot))