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
from utils.emoji import ZAI
from discord .ext import commands 

class _ai (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    """AI commands"""

    def help_custom (self ):
        emoji =ZAI
        label ="AI Commands"
        description ="Show you the commands of AI"
        return emoji ,label ,description 

    @commands .group ()
    async def __AI__ (self ,ctx :commands .Context ):
        """`ai activate`, `ai deactivate`, `ai analyze`, `ai analyse`, `ai code`, `ai explain`, `ai conversation-clear`, `ai mood-analyzer`, `ai personality`, `ai conversation-stats`, `ai summarize`, `ai ask`, `ai fact`, `ai database-clear`, `ai roleplay-enable`, `ai roleplay-disable`"""
        pass 
