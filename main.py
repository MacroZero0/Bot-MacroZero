import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import database
import views

# Setup
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    database.init_db()
    # Passamos o 'bot' para a view para ela poder deletar mensagens
    bot.add_view(views.PainelPrincipal(bot))
    print(f"🔥 Sistema Operacional: {bot.user}")

@bot.command()
@commands.has_permissions(administrator=True)
async def iniciar_sistema(ctx):
    """Cria o painel inicial."""
    await ctx.message.delete()
    view = views.PainelPrincipal(bot)
    await view.reposicionar_painel(ctx.channel)

if TOKEN:
    bot.run(TOKEN)