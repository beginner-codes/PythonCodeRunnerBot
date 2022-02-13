from __future__ import annotations
from bot.loggable import Loggable
from nextcord.ext import commands
from nextcord import Client
from typing import Union
import logging


class Cog(commands.Cog):
    def __init__(self, client: Union[Client, Loggable]):
        self.client = client
        self.log: logging.Logger = client.log.getChild(f"{type(self).__name__}")

    @commands.Cog.listener()
    async def on_ready(self):
        self.log.debug("Cog ready")
