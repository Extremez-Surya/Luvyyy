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

import os
import discord
from discord.ext import commands, tasks
from core import Cog, Context, zyrox
from utils.config import is_bot_owner, BRAND_NAME
from utils.emoji import TICK, CROSS, LOADINGRED
from utils.persistence import (
    create_backup,
    restore_backup,
    auto_restore_if_needed,
    upload_backup_to_discord,
    restore_from_cloud,
    get_backup_channel_id,
    set_backup_channel_id,
    get_current_system_stats,
    LATEST_BACKUP,
    MANIFEST_FILE,
    BACKUP_ROOT
)

class Backup(Cog):
    """Commands and automated background tasks for database persistence and recovery."""
    def __init__(self, bot: zyrox):
        self.bot = bot
        self.auto_backup_loop.start()

    def cog_unload(self):
        self.auto_backup_loop.cancel()

    @tasks.loop(minutes=30)
    async def auto_backup_loop(self):
        """Periodically backs up all database files and syncs to Discord cloud."""
        try:
            await self.bot.wait_until_ready()
            await upload_backup_to_discord(self.bot, reason="scheduled_30m")
        except Exception as e:
            print(f"[BackupCog] Auto backup loop error: {e}")

    @auto_backup_loop.before_loop
    async def before_auto_backup(self):
        await self.bot.wait_until_ready()

    @commands.group(name="backup", aliases=["databackup"], invoke_without_command=True)
    async def backup_cmd(self, ctx: Context):
        """Creates a complete database snapshot and attaches it to the chat."""
        if not is_bot_owner(ctx.author.id):
            return await ctx.send(f"{CROSS} Only Bot Owners can execute backup commands.")

        msg = await ctx.send(f"{LOADINGRED} Creating full database backup archive...")
        try:
            zip_path, stats = create_backup(reason=f"manual_by_{ctx.author.id}")
            await upload_backup_to_discord(self.bot, reason="manual_command")

            file_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
            embed = discord.Embed(
                title=f"📦 {BRAND_NAME} Full Database Backup",
                description="All bot settings, records, antinuke, automod, greet, and roles have been safely archived.",
                color=0x2ecc71
            )
            embed.add_field(name="Total Databases", value=f"`{stats['files_count']}` files", inline=True)
            embed.add_field(name="Total Records", value=f"`{stats['total_records']}` records", inline=True)
            embed.add_field(name="Archive Size", value=f"`{file_size_mb:.2f} MB`", inline=True)
            embed.add_field(
                name="Recovery Instructions",
                value="To restore, run `;restore` and attach this `.zip` file, or run `;restore cloud` to pull the latest backup automatically.",
                inline=False
            )
            embed.set_footer(text=f"Requested by {ctx.author} • Saved in data_backup/latest_backup.zip")

            file = discord.File(zip_path, filename=f"zyrox_backup_{int(stats['timestamp'])}.zip")
            await msg.delete()
            await ctx.send(embed=embed, file=file)

        except Exception as e:
            await msg.edit(content=f"{CROSS} Failed to create backup: `{e}`")

    @backup_cmd.command(name="channel", aliases=["setchannel"])
    async def backup_channel(self, ctx: Context, channel: discord.TextChannel):
        """Sets a dedicated Discord channel for persistent cloud backups."""
        if not is_bot_owner(ctx.author.id):
            return await ctx.send(f"{CROSS} Only Bot Owners can execute backup commands.")

        set_backup_channel_id(channel.id)
        embed = discord.Embed(
            title=f"{TICK} Cloud Backup Channel Set",
            description=f"Persistent backups will now be automatically uploaded to {channel.mention}.\n"
                        f"If the bot is ever reset or redployed, it will automatically pull data from this channel!",
            color=0x2ecc71
        )
        await ctx.send(embed=embed)
        # Upload an initial backup to this new channel immediately
        await upload_backup_to_discord(self.bot, reason="initial_channel_setup")

    @backup_cmd.command(name="status", aliases=["info"])
    async def backup_status(self, ctx: Context):
        """Displays database statistics, last backup details, and persistence health."""
        if not is_bot_owner(ctx.author.id):
            return await ctx.send(f"{CROSS} Only Bot Owners can execute backup commands.")

        stats = get_current_system_stats()
        channel_id = get_backup_channel_id()
        channel_mention = f"<#{channel_id}>" if channel_id else "`None (Using Webhook/Local)`"

        embed = discord.Embed(
            title=f"📊 {BRAND_NAME} Persistence & Backup Health",
            description="The persistence system protects against data loss when the bot restarts or when a new zip is deployed.",
            color=0x3498db
        )
        embed.add_field(name="Tracked Files", value=f"`{stats['files_count']}` databases", inline=True)
        embed.add_field(name="Current Records", value=f"`{stats['total_records']}` rows", inline=True)
        embed.add_field(name="Cloud Channel", value=channel_mention, inline=True)

        if os.path.isfile(LATEST_BACKUP):
            size_mb = os.path.getsize(LATEST_BACKUP) / (1024 * 1024)
            embed.add_field(name="Local Backup Exists", value=f"`Yes ({size_mb:.2f} MB)`", inline=True)
        else:
            embed.add_field(name="Local Backup Exists", value="`No`", inline=True)

        embed.add_field(name="Auto-Sync Interval", value="`Every 30 Minutes + Shutdown`", inline=True)
        embed.add_field(
            name="Top Populated Databases",
            value="\n".join([f"• `{p}`: **{c}** records" for p, c in sorted(stats['details'].items(), key=lambda x: x[1], reverse=True)[:5]]),
            inline=False
        )
        await ctx.send(embed=embed)

    @commands.command(name="restore", aliases=["datarestore"])
    async def restore_cmd(self, ctx: Context, mode: str = "auto"):
        """
        Restores bot databases from an attached zip file, cloud backup channel, or local backup.
        Usage:
          ;restore (with zip attachment)
          ;restore cloud
          ;restore local
        """
        if not is_bot_owner(ctx.author.id):
            return await ctx.send(f"{CROSS} Only Bot Owners can execute restore commands.")

        # 1. If a zip file is attached to the command message
        if ctx.message.attachments:
            att = ctx.message.attachments[0]
            if not att.filename.endswith(".zip"):
                return await ctx.send(f"{CROSS} The attached file must be a `.zip` database archive.")

            msg = await ctx.send(f"{LOADINGRED} Downloading and restoring from attached zip `{att.filename}`...")
            temp_zip = os.path.join(BACKUP_ROOT, "user_restore.zip")
            await att.save(temp_zip)

            success = restore_backup(temp_zip)
            if success:
                # Also refresh local backup
                import shutil
                shutil.copyfile(temp_zip, LATEST_BACKUP)
                new_stats = get_current_system_stats()
                embed = discord.Embed(
                    title=f"{TICK} Database Restored Successfully!",
                    description=f"Restored `{new_stats['files_count']}` database files with `{new_stats['total_records']}` total records from `{att.filename}`.\n"
                                f"All antinuke, automod, greet, roles, and settings have been restored.",
                    color=0x2ecc71
                )
                await msg.edit(content=None, embed=embed)
            else:
                await msg.edit(content=f"{CROSS} Failed to restore database from attached zip. Please verify file integrity.")
            return

        # 2. If mode is 'cloud' or auto with no local backup
        if mode.lower() == "cloud":
            msg = await ctx.send(f"{LOADINGRED} Searching for latest cloud backup from Discord...")
            success = await restore_from_cloud(self.bot)
            if success:
                new_stats = get_current_system_stats()
                embed = discord.Embed(
                    title=f"{TICK} Cloud Backup Restored Successfully!",
                    description=f"Restored `{new_stats['files_count']}` databases with `{new_stats['total_records']}` records from Discord Cloud Backup.",
                    color=0x2ecc71
                )
                await msg.edit(content=None, embed=embed)
            else:
                await msg.edit(content=f"{CROSS} Could not find or download a valid cloud backup. Set a backup channel first with `;backup channel <#channel>`.")
            return

        # 3. Restore from local latest_backup.zip
        if os.path.isfile(LATEST_BACKUP):
            msg = await ctx.send(f"{LOADINGRED} Restoring from local backup `data_backup/latest_backup.zip`...")
            success = restore_backup(LATEST_BACKUP)
            if success:
                new_stats = get_current_system_stats()
                embed = discord.Embed(
                    title=f"{TICK} Local Backup Restored Successfully!",
                    description=f"Restored `{new_stats['files_count']}` databases with `{new_stats['total_records']}` records from local storage.",
                    color=0x2ecc71
                )
                await msg.edit(content=None, embed=embed)
            else:
                await msg.edit(content=f"{CROSS} Local backup restore failed.")
            return

        # If nothing found
        await ctx.send(f"{CROSS} No local backup found. Please attach a backup `.zip` file with `;restore`, or run `;restore cloud` if you configured a backup channel.")

async def setup(bot: zyrox):
    await bot.add_cog(Backup(bot))
