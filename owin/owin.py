import aiohttp
import discord
from redbot.core import Config, commands

class Owin(commands.Cog):
    """Display Overwatch wins/losses and relative changes since last refresh."""

    __author__ = ["julianlore"]
    __version__ = "1.0.0"

    def __init__(self, bot):
        self.bot = bot
        self.config: Config = Config.get_conf(self, 9077625945313)
        default: dict = {"userstats": {}}
        self.config.register_guild(**default)

    @staticmethod
    async def get_data_for_user(ctx: commands.Context, battleTag: str):
        uri = 'https://ovrstat.com/stats/pc/' + battleTag.replace('#', '-')
        async with aiohttp.ClientSession() as session:
            async with session.get(uri) as response:
                if response.status != 200:
                    ctx.send(f"{uri} returned response {str(response.status)}.")
                    raise ValueError(f"{uri} returned response {str(response.status)}.")

                userJson = await response.json()
                level = userJson["level"] + (100 * userJson["prestige"])
                qp = userJson["quickPlayStats"]["careerStats"]["allHeroes"]["game"]
                winPercent = round(qp["gamesWon"]/qp["gamesPlayed"] * 100, 3)
                return [level, qp["gamesWon"], qp["gamesLost"], winPercent]

    @commands.command()
    async def owin(self, ctx: commands.Context, *args) -> None:
        """Display Overwatch wins/losses and relative changes since last
        refresh. Subcommand `[p]owin add <BattleTag>` to add a new BattleTag to
        track."""
        async with self.config.guild(ctx.guild).userstats() as userstatsDict:
            if len(args) <= 0:
                if not userstatsDict:
                    return await ctx.send("No players to track. Add BattleTags using the subcommand add. `[p]owin add <BattleTag>`")
                # Add a table and cumulate new stats with difference from old
                # stats. Keep track of maximum width for each column.
                statsTable = [["Player", "Level", "QP Wins", "QP Losses", 
                    "QP Win %" ]]
                for user, oldStatsList in userstatsDict.items():
                    try:
                        newStatsList = await self.get_data_for_user(ctx, user)
                        # Invalid old data, do not compare
                        if len(oldStatsList) != len(newStatsList):
                            userstatsDict[user] = newStatsList
                            # Add user as first column
                            statsTable.append([user] + [str(stat) for stat in newStatsList])
                            continue
                    
                        curRow = [user]
                        for i in range(len(newStatsList)):
                            # Get change since last refresh
                            # Prefix positive changes with a +
                            change = newStatsList[i] - oldStatsList[i]
                            if change > 0:
                                sign = '+'
                            else:
                                sign = ''
                            # No need to show a change if it is 0
                            if change != 0:
                                changeStr = f" ({sign}{str(change)})"
                            else:
                                changeStr = ''
                            curRow.append(str(newStatsList[i]) + changeStr)
                        statsTable.append(curRow)
                        userstatsDict[user] = newStatsList
                    except ValueError:
                        continue # Error message sent in get_data_for_user

                # Now get max width of each column
                maxWidthList = [len(stat) for stat in statsTable[0]]
                for statsTableRow in statsTable:
                    for j in range(len(statsTableRow)):
                        maxWidthList[j] = max(maxWidthList[j], len(statsTableRow[j]))

                # Format the table as a string
                strTable = "```"
                for i in range(len(statsTable)):
                    strTable += '\n'
                    for j in range(len(statsTable[i])):
                        # Add '|' as separators and left justify the max width
                        # of this column
                        strTable += f"|{statsTable[i][j]:<{maxWidthList[j]}}"
                    # Closing last separator
                    strTable += '|'
                    # Add a row of dashes to separate column header for
                    # first row
                    if i == 0:
                        # 1 dash for each column width (maxWidthList), 1 dash
                        # for each column (account for |) and 1 for closing |
                        strTable += '\n' + ((sum(maxWidthList)
                            + len(maxWidthList) + 1) * '-')
                strTable += "\n```"
                return await ctx.send(strTable)
            command = args[0]
            if command == "add":
                if len(args) < 2:
                    return await ctx.send("Invalid number of arguments. Example usage: `[p]owin add <BattleTag>`")
                battleTag = args[1]
                if '#' not in battleTag:
                    return await ctx.send("Please specify the BattleTag #, i.e. `BattleTag#1234`.")
                if battleTag in userstatsDict:
                    return await ctx.send("BattleTag already present in users to track.")
                try:
                    statsList = await Owin.get_data_for_user(ctx, battleTag)
                    userstatsDict[battleTag] = statsList
                    return await ctx.send("BattleTag added successfully!")
                except ValueError:
                    pass # Error message sent in get_data_for_user
            elif command == "clear":
                await self.config.guild(ctx.guild).userstats.clear()
                await ctx.send("Cleared data successfully.")
            elif command == "delete":
                battleTag = args[1]
                if len(args) < 2:
                    return await ctx.send("Invalid number of arguments. Example usage: `[p]owin delete <BattleTag>`")
                userstatsDict[battleTag].pop()
                return await ctx.send("BattleTag deleted successfully.")
            else:
                await ctx.send(f"Invalid command {command}. Supported commands: add, clear, delete")
