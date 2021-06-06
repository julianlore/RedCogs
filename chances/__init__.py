from .chances import Chances

def setup(bot):
    n = Chances(bot)
    bot.add_cog(n)
