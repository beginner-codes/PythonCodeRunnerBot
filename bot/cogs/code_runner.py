from bot.cog import Cog
from datetime import datetime, timedelta
from nextcord.ext.commands import command
from typing import Tuple
import asyncio
import nextcord
import json
import pathlib
import re


class CodeRunner(Cog):
    def __init__(self, client):
        super().__init__(client)
        self._exec_rate_limit = {}
        self._code_runner_emojis = "▶️⏯"

    @command()
    async def exec(self, ctx, *, content=""):
        if not ctx.guild:
            return

        if content.strip() == "modules":
            with (
                pathlib.Path(__file__).parent.parent / "allowed_modules.txt"
            ).open() as allowed_modules_file:
                allowed_modules_list = list(
                    line.strip()
                    for line in allowed_modules_file.readlines()
                    if line.strip()
                )
                length = len(max(allowed_modules_list, key=len)) + 2
                allowed_modules = "".join(
                    f"{module:{length}}" for module in allowed_modules_list
                )
            await ctx.send(
                embed=nextcord.Embed(
                    description=f"Here are all of the allowed modules:\n```\n{allowed_modules}\n```",
                    title="✅ Exec/Eval Allowed Modules",
                    color=0x0000FF,
                )
            )
            return

        message: nextcord.Message = ctx.message
        if message.reference:
            ref_message = await ctx.channel.fetch_message(message.reference.message_id)
            await self._exec(
                ctx.message,
                ref_message.content[ref_message.content.find("`") :].strip(),
                ctx.author,
                user_input=message.clean_content[message.clean_content.find(" ") + 1 :],
            )
            return

        await self._exec(ctx.message, content, ctx.author)
        self.log.debug(f"{ctx.author} ran code from {message.jump_url}")

    @Cog.listener()
    async def on_raw_reaction_add(self, reaction: nextcord.RawReactionActionEvent):
        if (
            reaction.emoji.name
            not in self._code_runner_emojis + self._formatting_emojis
        ):
            return

        now = datetime.utcnow()
        delta = now - self._exec_rate_limit.get(reaction.message_id, now)
        channel: nextcord.TextChannel = self.client.get_channel(reaction.channel_id)
        message = await channel.fetch_message(reaction.message_id)
        if timedelta(seconds=0) < delta < timedelta(minutes=2):
            await message.remove_reaction(reaction.emoji, reaction.member)
            return

        member = channel.guild.get_member(reaction.user_id)
        if member.bot:
            return

        self._exec_rate_limit[reaction.message_id] = now

        if reaction.emoji.name in self._code_runner_emojis:
            await self._exec(
                message,
                message.content,
                reaction.member,
            )
            self.log.debug(
                f"{reaction.member} used an emoji to run code in {message.jump_url}"
            )

    async def _exec(
        self,
        message: nextcord.Message,
        content: str,
        member: nextcord.Member = None,
        user_input: str = "",
    ):
        if (
            not len(content.strip())
            or content.find("```") < 0
            or content.rfind("```") <= 0
        ):
            await message.channel.send(
                content="" if member is None else member.mention,
                embed=nextcord.Embed(
                    title="Exec - No Code",
                    description=(
                        "\n**NO PYTHON CODE BLOCK FOUND**\n\nThe command format is as follows:\n\n"
                        "\n!exec \\`\\`\\`py\nYOUR CODE HERE\n\\`\\`\\`\n"
                    ),
                    color=0xFF0000,
                ),
                reference=message,
                allowed_mentions=nextcord.AllowedMentions(
                    replied_user=member is None, users=[member] if member else False
                ),
            )
            return

        title = "✅ Exec - Success"
        color = 0x0000FF

        restricted = not member.guild_permissions.manage_messages
        if not restricted:
            title += " (Super User 🦸)"

        if user_input:
            code, *_ = re.match(
                r"^.*?```(?:python|py)?\s*(.+?)\s*```.*$", content, re.DOTALL
            ).groups()
        else:
            code, user_input = re.match(
                r"^.*?```(?:python|py)?\s*(.+?)\s*```\s*(.+)?$", content, re.DOTALL
            ).groups()

        out, err, duration = await self.code_runner(
            "exec",
            code,
            user_input,
            restricted=restricted,
        )

        output = [out]
        if err:
            title = "❌ Exec - Exception Raised"
            color = 0xFFFF00
            output.append(err)

        elif not out:
            output = ["*No output or exceptions*"]

        out = "\n\n".join(output)
        old_out = out
        if out.count("\n") > 30:
            lines = out.split("\n")
            out = "\n".join(
                lines[:15]
                + [f".\n.\nRemoved {len(lines) - 30} lines\n.\n."]
                + lines[-17:]
            )
        if len(out) > 1000:
            out = (
                old_out[:497]
                + f"\n.\n.\nRemoved {len(old_out) - 1000} characters\n.\n.\n"
                + old_out[-504:]
            )
        embed = nextcord.Embed(
            title=title, description=f"```\n{out}\n```", color=color
        ).set_footer(text=f"!exec modules | Completed in {duration:0.4f} milliseconds")
        if "https://xkcd.com/353/" in old_out:
            embed.set_image(url="https://imgs.xkcd.com/comics/python.png")

        await message.channel.send(
            content="" if member is None else member.mention,
            embed=embed,
            reference=message,
            allowed_mentions=nextcord.AllowedMentions(
                replied_user=member is None,
                users=[member] if member else False,
                roles=[],
            ),
        )

    async def code_runner(
        self, mode: str, code: str, user_input: str = "", restricted=True
    ) -> Tuple[str, str, float]:
        proc = await asyncio.create_subprocess_shell(
            f"python -m bot.runner {mode}",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        data = json.dumps(
            {
                "code": code.replace(" ", " "),
                "input": user_input,
                "restricted": restricted,
            }
        ).encode()
        formatted_user_input = "\n    ".join(user_input.split("\n"))
        formatted_code = "\n    >>> ".join(code.split("\n"))
        self.log.debug(
            f"Running ({mode}, {restricted=}) code\n    >>> {formatted_code}\nInput\n    {formatted_user_input}"
        )
        stdout, stderr = await proc.communicate(data)
        out, duration = self._split_run_time(stdout.decode())

        return out, stderr.decode(), duration

    @command()
    async def eval(self, ctx, *, content):
        if content.casefold().strip() == "help":
            await ctx.send(
                embed=nextcord.Embed(
                    title="Statement Eval - Help",
                    description=(
                        "This command allows you to run a single statement and see the results. For security "
                        "reasons what code you can run is very limited."
                    ),
                    color=0xFBBC05,
                ),
            )
            return

        code = re.sub(r"^\s*(```(python|py)|`?)\s*|\s*(```|`)\s*$", "", content)
        title = "✅ Eval - Success"
        color = 0x0000FF

        code_message = f"\n```py\n>>> {code}"

        out, err, duration = await self.code_runner("eval", code)

        output = out
        if err:
            title = "❌ Eval - Exception Raised"
            color = 0xFFFF00
            output = err

        await ctx.send(
            embed=nextcord.Embed(
                title=title,
                description=f"{code_message.strip()}\n{output}\n```",
                color=color,
            ).set_footer(text=f"Completed in {duration:0.4f} milliseconds"),
            reference=ctx.message,
            mention_author=True,
        )
        self.log.debug(f"{ctx.author} eval'd code from {ctx.message.jump_url}")

    def _split_run_time(self, content: str):
        parts = re.match(r"^(.+?)?\n\^{4}(\d+)\^{4}$", content, re.DOTALL)
        if parts:
            parts = parts.groups()
            if len(parts) == 2 and parts[-1].isdigit():
                return parts[0] if parts[0] else "", int(parts[1]) / 1000000
        return content, 0


def setup(client):
    client.add_cog(CodeRunner(client))
