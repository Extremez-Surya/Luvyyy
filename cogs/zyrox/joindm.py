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
from utils.emoji import MESSAGE
from discord.ext import commands

class _joindm(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    """__Join Dm__"""
    def help_custom(self):
              emoji = MESSAGE
              label = "Joindm"
              description = "Show you Commands of Joindm"
              return emoji, label, description
    @commands.group()
    async def __Joindm__(self, ctx: commands.Context):
        """`joindm enable` , `joindm disable` , `joindm message` , `joindm test`"""