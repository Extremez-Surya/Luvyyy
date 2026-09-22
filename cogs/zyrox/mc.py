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

import discord
from utils.emoji import MINECRAFT
from discord.ext import commands


class _mc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """Minecraft commands"""
  
    def help_custom(self):
		      emoji = MINECRAFT
		      label = "Minecraft Commands"
		      description = "Show you Commands of Minecraft"
		      return emoji, label, description

    @commands.group()
    async def __Minecraft__(self, ctx: commands.Context):
        """`minecraft setup` , `minecraft reset` , `minecraft status`"""
        pass
