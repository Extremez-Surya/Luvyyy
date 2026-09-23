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
from contextlib import suppress
from utils.Tools import *
from utils.emoji import REWIND, PREVIOUS, NEXT, FORWARD, DELETE, HOME


class Dropdown(discord.ui.Select):

    def __init__(self, ctx, options, placeholder="Choose a Category for Help", row=0):
        super().__init__(placeholder=placeholder,
                         min_values=1,
                         max_values=1,
                         options=options,
                         row=row)
        self.invoker = ctx.author

    async def callback(self, interaction: discord.Interaction):
        if self.invoker == interaction.user:
            index = self.view.find_index_from_select(self.values[0])
            if index is None:
                index = 0
            await self.view.set_page(index, interaction)
        else:
            await interaction.response.send_message(
                "You must run this command to interact with it.", ephemeral=True)


class View(discord.ui.View):

    def __init__(self, mapping: dict, ctx, homeembed, ui: int):
        super().__init__(timeout=180)
        self.mapping = mapping
        self.ctx = ctx
        self.homeembed = homeembed
        self.index = 0
        self.current_page = 0
        self.ui = ui
        self.message = None

        self.options, self.pages, self.total_pages = self.gen_pages(homeembed)
        self._rebuild()

    def get_embed(self) -> discord.Embed:
        if self.index == 0 and hasattr(self, 'homeembed') and self.homeembed:
            return self.homeembed

        page = self.pages[self.index]
        embed = discord.Embed(
            title=page.get('title') or "Commands",
            description=page.get('description') or "Commands in this category:",
            color=0xFF0000
        )
        fields = page.get('fields', [])
        for item in fields:
            if isinstance(item, dict):
                embed.add_field(name=item.get('name', 'Command'), value=item.get('value', 'No info'), inline=item.get('inline', False))
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                embed.add_field(name=str(item[0]), value=str(item[1]), inline=False)

        if not embed.title and not embed.description and not embed.fields:
            embed.description = "Commands in this category."

        footer_text = f"• Help page {self.index + 1}/{self.total_pages} | Requested by: {self.ctx.author.display_name} | Developed by Vinay Kumar (!Alone💔)"
        embed.set_footer(text=footer_text)
        return embed

    def _rebuild(self):
        self.clear_items()
        is_first = self.index == 0
        is_last = self.index >= len(self.pages) - 1

        row = 0
        if self.ui == 0 or self.ui == 3:
            if self.options:
                self.add_item(Dropdown(ctx=self.ctx, options=self.options[:25], row=row))
                row += 1
        elif self.ui == 2:
            mid = len(self.options) // 2
            o1, o2 = self.options[:mid], self.options[mid:]
            if o1:
                self.add_item(Dropdown(ctx=self.ctx, options=o1[:25], placeholder="Main Commands", row=row))
                row += 1
            if o2:
                o2_opts = [discord.SelectOption(label="Home", emoji=HOME, description="Return to main menu")] + [o for o in o2 if o.label != "Home"]
                self.add_item(Dropdown(ctx=self.ctx, options=o2_opts[:25], placeholder="Extra Commands", row=row))
                row += 1

        btn_row = row
        homeB = discord.ui.Button(label="", emoji=REWIND, style=discord.ButtonStyle.secondary, disabled=is_first, row=btn_row)
        backB = discord.ui.Button(label="", emoji=PREVIOUS, style=discord.ButtonStyle.secondary, disabled=is_first, row=btn_row)
        quitB = discord.ui.Button(label="", emoji=DELETE, style=discord.ButtonStyle.danger, row=btn_row)
        nextB = discord.ui.Button(label="", emoji=NEXT, style=discord.ButtonStyle.secondary, disabled=is_last, row=btn_row)
        lastB = discord.ui.Button(label="", emoji=FORWARD, style=discord.ButtonStyle.secondary, disabled=is_last, row=btn_row)

        homeB.callback = self._home_cb
        backB.callback = self._back_cb
        quitB.callback = self._quit_cb
        nextB.callback = self._next_cb
        lastB.callback = self._last_cb

        self.add_item(homeB)
        self.add_item(backB)
        self.add_item(quitB)
        self.add_item(nextB)
        self.add_item(lastB)

    async def _check(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("You must run this command to interact with it.", ephemeral=True)
            return False
        return True

    async def _home_cb(self, interaction: discord.Interaction):
        if await self._check(interaction):
            await self.set_page(0, interaction)

    async def _back_cb(self, interaction: discord.Interaction):
        if await self._check(interaction):
            await self.set_page(self.index - 1 if self.index > 0 else len(self.pages) - 1, interaction)

    async def _quit_cb(self, interaction: discord.Interaction):
        if await self._check(interaction):
            with suppress(Exception):
                if interaction.message:
                    await interaction.message.delete()
                else:
                    await interaction.response.defer()
                    await interaction.delete_original_response()

    async def _next_cb(self, interaction: discord.Interaction):
        if await self._check(interaction):
            await self.set_page(self.index + 1 if self.index < len(self.pages) - 1 else 0, interaction)

    async def _last_cb(self, interaction: discord.Interaction):
        if await self._check(interaction):
            await self.set_page(len(self.pages) - 1, interaction)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        with suppress(Exception):
            if self.message:
                await self.message.edit(view=self)

    def find_index_from_select(self, value):
        if value == "Home":
            return 0
        i = 0
        used_labels = set()
        for cog in self.get_cogs():
            if cog.__class__.__name__ == "Roleplay":
                continue
            if "help_custom" in dir(cog):
                _, label, _ = cog.help_custom()
                original_label = label
                counter = 1
                while label in used_labels:
                    label = f"{original_label} {counter}"
                    counter += 1
                used_labels.add(label)
                if label == value or value.startswith(original_label + " "):
                    return i + 1
                i += 1
        return 0

    def get_cogs(self):
        return list(self.mapping.keys())

    def gen_pages(self, homeembed):
        options, pages = [], []
        total_pages = 0
        used_labels = set()

        options.append(discord.SelectOption(label="Home", emoji=HOME, description="Return to main menu"))

        # Convert homeembed to page data
        if hasattr(homeembed, '_title'):
            home_page = {
                'title': homeembed._title or '',
                'description': homeembed._description or '',
                'fields': list(homeembed._fields) if hasattr(homeembed, '_fields') else [],
                'footer': None
            }
        else:
            home_page = {
                'title': getattr(homeembed, 'title', '') or '',
                'description': getattr(homeembed, 'description', '') or '',
                'fields': [(f.name, f.value) for f in homeembed.fields] if hasattr(homeembed, 'fields') and homeembed.fields else [],
                'footer': homeembed.footer.text if hasattr(homeembed, 'footer') and homeembed.footer else None
            }

        pages.append(home_page)
        total_pages += 1
        used_labels.add("Home")

        for cog in self.get_cogs():
            if cog.__class__.__name__ == "Roleplay":
                continue
            if "help_custom" in dir(cog):
                emoji, label, description = cog.help_custom()
                original_label = label
                counter = 1
                while label in used_labels:
                    label = f"{original_label} {counter}"
                    counter += 1
                used_labels.add(label)
                options.append(discord.SelectOption(label=label, emoji=emoji, description=description[:100] if description else ""))

                fields = []
                for command in cog.get_commands():
                    params = ""
                    for param in command.clean_params:
                        if param not in ["self", "ctx"]:
                            params += f" <{param}>"
                    help_text = command.help or "No description available"
                    if len(help_text) > 1020:
                        help_text = help_text[:1017] + "..."
                    fields.append((f"{command.name}{params}", f"{help_text}\n•"))

                pages.append({
                    'title': f"{emoji} {original_label}",
                    'description': description or 'Commands in this category:',
                    'fields': fields,
                    'footer': None
                })
                total_pages += 1

        return options, pages, total_pages

    async def set_page(self, page, interaction: discord.Interaction):
        self.index = page
        self.current_page = page
        self._rebuild()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)