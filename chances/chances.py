import discord
import asyncio
from redbot.core import commands

class Chances(commands.Cog):
    """Cog for dares, chances that someone does something from 0 to a given
    number."""

    __author__ = ["julianlore"]
    __version__ = "1.0.0"

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def chances(self, ctx: commands.Context, user:discord.Member,
            upperbound:int, *, message:str) -> None:
        """Chances that a dare is to be done if you and the specified user
        guess the same number."""
        if upperbound <= 0:
            return await ctx.send("Invalid upperbound. Enter an integer greater than 0.")
        else:
            async def queryGuessFromUser(userToQuery, otherUser) -> int:
                """ Asks user for a guess and returns their guess """
                await userToQuery.send("Chances that " + message + 
                        "\nEnter a number between 0 and " +
                        str(upperbound) + " (inclusive).\nIf you and " +
                        str(otherUser) +
                        " enter the same number, the dare must be done.")

                # Check to wait for a direct message from the queried user
                def msgFromUser(msg):
                    return msg.author == userToQuery and isinstance(msg.channel, discord.DMChannel)

                invalidMsg = ("Invalid answer. Enter an integer between 0 and " +
                        str(upperbound) + " (inclusive).")
                while True:
                    msg = await self.bot.wait_for('message', timeout=1000.0,
                            check=msgFromUser)
                    try:
                        guess = int(msg.content)
                        if guess < 0 or guess > upperbound:
                            await userToQuery.send(invalidMsg)
                        else:
                            return guess
                    except ValueError:
                        await userToQuery.send(invalidMsg)
                    await asyncio.sleep(1)
            
            # Query author and specified user for both their guesses
            guessGatherFuture = asyncio.gather(
                    queryGuessFromUser(ctx.author, user),
                    queryGuessFromUser(user, ctx.author))
            try:
                guess1, guess2 = await asyncio.wait_for(guessGatherFuture,
                        timeout=300.0)
                if guess1 == guess2:
                    result = "succeeded"
                else:
                    result = "failed"
                return await ctx.send("Chances " + result + ", " +
                        str(ctx.author) + " entered " + str(guess1) + 
                        " and " + str(user) + " entered " + str(guess2) + ".")
            except asyncio.TimeoutError:
                return await ctx.send("Timed out waiting for answers. Chances cancelled.")
