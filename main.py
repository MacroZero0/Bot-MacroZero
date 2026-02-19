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

    # Registra as views persistentes (necessário após restart)
    bot.add_view(views.PainelPrincipal(bot))

    # Auto-inicializa o painel no canal configurado
    await auto_iniciar_painel()

    print(f"🔥 Sistema Operacional: {bot.user}")

async def auto_iniciar_painel():
    """
    Verifica se o painel já existe no canal configurado.
    Se não existir, cria automaticamente. Roda toda vez que o bot liga.
    """
    canal = bot.get_channel(views.ID_CANAL_PAINEL)
    if not canal:
        print(f"⚠️  Canal do painel (ID: {views.ID_CANAL_PAINEL}) não encontrado!")
        return

    # Procura se o painel já existe nas últimas 50 mensagens
    painel_existe = False
    async for message in canal.history(limit=50):
        if message.author == bot.user and message.components:
            try:
                if message.components[0].children[0].custom_id == "btn_abrir":
                    painel_existe = True
                    break
            except (IndexError, AttributeError):
                continue

    if not painel_existe:
        print("📋 Painel não encontrado — criando automaticamente...")
        painel = views.PainelPrincipal(bot)
        await painel.reposicionar_painel(canal)
        print("✅ Painel criado com sucesso!")
    else:
        print("✅ Painel já existe no canal — nenhuma ação necessária.")

# Mantido como fallback para admins reposicionarem manualmente
@bot.command()
@commands.has_permissions(administrator=True)
async def resetar_painel(ctx):
    """Força o reposicionamento do painel para o final do canal."""
    await ctx.message.delete()
    painel = views.PainelPrincipal(bot)
    await painel.reposicionar_painel(ctx.channel)

if TOKEN:
    bot.run(TOKEN)