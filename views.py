import discord
from datetime import datetime
import database # Importa o arquivo database.py

# CONFIGURAÇÕES
ID_CANAL_LOGS_CHEFIA = 1473020868752834713  # <--- COLOCAR O ID DO SEU CANAL AQUI
CARGOS_CHEFIA = ["Supervisor", "Gerente", "Diretor"]

# --- PAINEL PRINCIPAL ---
class PainelPrincipal(discord.ui.View):
    def __init__(self, bot_ref):
        super().__init__(timeout=None)
        self.bot = bot_ref # Referência ao bot para deletar mensagens

    async def reposicionar_painel(self, channel):
        """Deleta mensagens antigas do bot e reenvia o painel para o final."""
        async for message in channel.history(limit=5):
            if message.author == self.bot.user and message.components:
                # Verifica se é o painel (botão de abrir tem ID 'btn_abrir')
                if message.components[0].children[0].custom_id == "btn_abrir":
                    await message.delete()

        embed = discord.Embed(
            title="📝 Controle de Ponto & Efetivo", 
            description="Utilize os botões abaixo para registrar sua atividade.",
            color=0x2b2d31
        )
        await channel.send(embed=embed, view=PainelPrincipal(self.bot))

    @discord.ui.button(label="Abrir Ponto", style=discord.ButtonStyle.success, emoji="⏰", custom_id="btn_abrir")
    async def abrir_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 1. Checa DB
        if database.buscar_ponto_aberto(interaction.user.id):
            await interaction.response.send_message("❌ Você já está em serviço.", ephemeral=True)
            return

        # 2. Envia Log Visual
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        embed_log = discord.Embed(title="🟢 Início de Turno", color=0x00ff00)
        embed_log.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed_log.add_field(name="Horário", value=f"`{agora}`")
        
        await interaction.response.defer()
        msg = await interaction.channel.send(embed=embed_log)

        # 3. Salva no DB
        database.abrir_ponto_db(interaction.user.id, interaction.user.name, msg.id)

        # 4. Move o painel para baixo
        await self.reposicionar_painel(interaction.channel)

    @discord.ui.button(label="Fechar Ponto", style=discord.ButtonStyle.danger, emoji="🛑", custom_id="btn_fechar")
    async def fechar_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 1. Checa DB
        ponto = database.buscar_ponto_aberto(interaction.user.id)
        if not ponto:
            await interaction.response.send_message("❌ Nenhum turno aberto.", ephemeral=True)
            return

        ponto_id, entrada_str, msg_id = ponto
        
        # 2. Atualiza DB
        saida = database.fechar_ponto_db(ponto_id)

        # 3. Calcula Horas
        fmt = "%Y-%m-%d %H:%M:%S"
        d1 = datetime.strptime(entrada_str, fmt)
        d2 = datetime.strptime(saida, fmt)
        diff = d2 - d1

        # 4. Edita a mensagem original
        try:
            msg_original = await interaction.channel.fetch_message(msg_id)
            embed_final = discord.Embed(title="🔴 Turno Finalizado", color=0xff0000)
            embed_final.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            embed_final.add_field(name="Entrada", value=f"`{entrada_str}`", inline=True)
            embed_final.add_field(name="Saída", value=f"`{saida}`", inline=True)
            embed_final.add_field(name="⏳ Duração", value=f"**{str(diff)}**", inline=False)
            await msg_original.edit(embed=embed_final)
        except:
            await interaction.channel.send(f"⚠️ Log original perdido. Turno fechado. Duração: {diff}")

        await interaction.response.defer()
        await self.reposicionar_painel(interaction.channel)

    @discord.ui.button(label="Solicitar Folga", style=discord.ButtonStyle.primary, emoji="📅", custom_id="btn_folga")
    async def folga_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(FolgaModal())

# --- MODAL DE FOLGA ---
class FolgaModal(discord.ui.Modal, title="Solicitação de Dispensa"):
    motivo = discord.ui.TextInput(label="Motivo", style=discord.TextStyle.short, placeholder="Ex: Médico")

    async def on_submit(self, interaction: discord.Interaction):
        # 1. Verifica Pendência
        if database.verificar_folga_pendente(interaction.user.id):
            await interaction.response.send_message("⚠️ Você já tem um pedido pendente.", ephemeral=True)
            return

        # 2. Salva no DB
        folga_id, agora = database.criar_folga_db(interaction.user.id, interaction.user.name, self.motivo.value)

        # 3. Notifica Chefia
        canal_logs = interaction.guild.get_channel(ID_CANAL_LOGS_CHEFIA)
        if canal_logs:
            embed = discord.Embed(title=f"Solicitação #{folga_id}", description=f"**Motivo:** {self.motivo.value}", color=0xffff00)
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            await canal_logs.send(embed=embed, view=PainelAdmin(folga_id))
            await interaction.response.send_message("✅ Enviado ao comando.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Erro: Canal da chefia não configurado.", ephemeral=True)

# --- BOTÕES DE ADMIN ---
class PainelAdmin(discord.ui.View):
    def __init__(self, folga_id):
        super().__init__(timeout=None)
        self.folga_id = folga_id

    async def check_perm(self, interaction):
        roles = [r.name for r in interaction.user.roles]
        if any(c in roles for c in CARGOS_CHEFIA) or interaction.user.guild_permissions.administrator:
            return True
        return False

    @discord.ui.button(label="Aprovar", style=discord.ButtonStyle.success, custom_id="adm_aprov")
    async def aprovar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_perm(interaction): return
        database.atualizar_status_folga(self.folga_id, "APROVADO", interaction.user.name)
        embed = interaction.message.embeds[0]
        embed.color = 0x00ff00
        embed.add_field(name="Status", value=f"✅ APROVADO por {interaction.user.name}")
        self.stop()
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="Negar", style=discord.ButtonStyle.danger, custom_id="adm_neg")
    async def negar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_perm(interaction): return
        database.atualizar_status_folga(self.folga_id, "NEGADO", interaction.user.name)
        embed = interaction.message.embeds[0]
        embed.color = 0xff0000
        embed.add_field(name="Status", value=f"🚫 NEGADO por {interaction.user.name}")
        self.stop()
        await interaction.response.edit_message(embed=embed, view=None)