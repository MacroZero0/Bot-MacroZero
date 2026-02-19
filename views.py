import discord
from datetime import datetime
import database

# =============================================
# CONFIGURAÇÕES — EDITE APENAS AQUI
# =============================================
ID_CANAL_PAINEL     = 1473020833600639077  # <-- Canal onde o painel de ponto fica fixo
ID_CANAL_LOGS_PONTO = 1474111883530473753  # <-- Canal onde os logs de entrada/saída aparecem
ID_CANAL_LOGS_CHEFIA = 1473020868752834713 # <-- Canal da chefia (solicitações de folga)
CARGOS_CHEFIA = ["Supervisor", "Gerente", "Diretor"]
# =============================================

# --- PAINEL PRINCIPAL ---
class PainelPrincipal(discord.ui.View):
    def __init__(self, bot_ref):
        super().__init__(timeout=None)
        self.bot = bot_ref

    async def reposicionar_painel(self, channel):
        """Deleta o painel antigo e reenvia para o final do canal."""
        async for message in channel.history(limit=20):
            if message.author == self.bot.user and message.components:
                try:
                    if message.components[0].children[0].custom_id == "btn_abrir":
                        await message.delete()
                        break
                except (IndexError, AttributeError):
                    continue

        embed = discord.Embed(
            title="📝 Controle de Ponto & Efetivo",
            description=(
                "Utilize os botões abaixo para registrar sua atividade.\n\n"
                "⏰ **Abrir Ponto** — Inicia seu turno\n"
                "🛑 **Fechar Ponto** — Encerra seu turno\n"
                "📅 **Solicitar Folga** — Envia pedido à supervisão"
            ),
            color=0x2b2d31
        )
        embed.set_footer(text="Sistema de Ponto • Mac")
        await channel.send(embed=embed, view=PainelPrincipal(self.bot))

    @discord.ui.button(label="Abrir Ponto", style=discord.ButtonStyle.success, emoji="⏰", custom_id="btn_abrir")
    async def abrir_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 1. Checa DB
        if database.buscar_ponto_aberto(interaction.user.id):
            await interaction.response.send_message("❌ Você já está em serviço.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        # 2. Envia log no canal de logs de ponto (canal separado)
        canal_logs_ponto = interaction.guild.get_channel(ID_CANAL_LOGS_PONTO)
        if not canal_logs_ponto:
            await interaction.followup.send("❌ Erro: Canal de logs de ponto não encontrado.", ephemeral=True)
            return

        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        embed_log = discord.Embed(title="🟢 Turno em Aberto", color=0x00ff00)
        embed_log.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed_log.add_field(name="Entrada", value=f"`{agora}`", inline=True)
        embed_log.add_field(name="Status", value="🟡 Em andamento...", inline=True)
        embed_log.set_footer(text=f"ID: {interaction.user.id}")
        msg = await canal_logs_ponto.send(embed=embed_log)

        # 3. Salva no DB com o ID da mensagem no canal de logs
        database.abrir_ponto_db(interaction.user.id, interaction.user.name, msg.id)

        await interaction.followup.send("✅ Ponto aberto com sucesso!", ephemeral=True)

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

        await interaction.response.defer(ephemeral=True)

        # 2. Atualiza DB
        saida = database.fechar_ponto_db(ponto_id)

        # 3. Calcula duração
        fmt = "%Y-%m-%d %H:%M:%S"
        d1 = datetime.strptime(entrada_str, fmt)
        d2 = datetime.strptime(saida, fmt)
        diff = d2 - d1
        horas, resto = divmod(int(diff.total_seconds()), 3600)
        minutos, segundos = divmod(resto, 60)
        duracao_fmt = f"{horas:02d}h {minutos:02d}m {segundos:02d}s"

        # 4. Edita a mensagem original no canal de logs de ponto
        canal_logs_ponto = interaction.guild.get_channel(ID_CANAL_LOGS_PONTO)
        if canal_logs_ponto:
            try:
                msg_original = await canal_logs_ponto.fetch_message(msg_id)
                embed_final = discord.Embed(title="🔴 Turno Finalizado", color=0xff0000)
                embed_final.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
                embed_final.add_field(name="Entrada", value=f"`{entrada_str}`", inline=True)
                embed_final.add_field(name="Saída", value=f"`{saida}`", inline=True)
                embed_final.add_field(name="⏳ Duração Total", value=f"**{duracao_fmt}**", inline=False)
                embed_final.set_footer(text=f"ID: {interaction.user.id}")
                await msg_original.edit(embed=embed_final)
            except discord.NotFound:
                await canal_logs_ponto.send(
                    f"⚠️ Log original perdido.\n"
                    f"**{interaction.user.display_name}** — Entrada: `{entrada_str}` | Saída: `{saida}` | Duração: `{duracao_fmt}`"
                )
        else:
            await interaction.followup.send("❌ Erro: Canal de logs de ponto não encontrado.", ephemeral=True)

        await interaction.followup.send(f"✅ Ponto fechado! Duração: **{duracao_fmt}**", ephemeral=True)

        # 5. Move o painel para baixo
        await self.reposicionar_painel(interaction.channel)

    @discord.ui.button(label="Solicitar Folga", style=discord.ButtonStyle.primary, emoji="📅", custom_id="btn_folga")
    async def folga_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(FolgaModal())


# --- MODAL DE FOLGA ---
class FolgaModal(discord.ui.Modal, title="Solicitação de Dispensa"):
    motivo = discord.ui.TextInput(
        label="Motivo",
        style=discord.TextStyle.short,
        placeholder="Ex: Consulta médica, compromisso pessoal..."
    )

    async def on_submit(self, interaction: discord.Interaction):
        if database.verificar_folga_pendente(interaction.user.id):
            await interaction.response.send_message("⚠️ Você já tem um pedido pendente.", ephemeral=True)
            return

        folga_id, agora = database.criar_folga_db(interaction.user.id, interaction.user.name, self.motivo.value)

        canal_logs = interaction.guild.get_channel(ID_CANAL_LOGS_CHEFIA)
        if canal_logs:
            embed = discord.Embed(
                title=f"📋 Solicitação de Folga #{folga_id}",
                description=f"**Motivo:** {self.motivo.value}",
                color=0xffff00
            )
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            embed.add_field(name="Data", value=f"`{agora}`")
            embed.set_footer(text=f"ID do solicitante: {interaction.user.id}")
            await canal_logs.send(embed=embed, view=PainelAdmin(folga_id))
            await interaction.response.send_message("✅ Solicitação enviada à Supervisão!", ephemeral=True)
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
        await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)
        return False

    @discord.ui.button(label="Aprovar", style=discord.ButtonStyle.success, custom_id="adm_aprov")
    async def aprovar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_perm(interaction):
            return
        database.atualizar_status_folga(self.folga_id, "APROVADO", interaction.user.name)
        embed = interaction.message.embeds[0]
        embed.color = 0x00ff00
        embed.add_field(name="Decisão", value=f"✅ **APROVADO** por {interaction.user.name}")
        self.stop()
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="Negar", style=discord.ButtonStyle.danger, custom_id="adm_neg")
    async def negar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_perm(interaction):
            return
        database.atualizar_status_folga(self.folga_id, "NEGADO", interaction.user.name)
        embed = interaction.message.embeds[0]
        embed.color = 0xff0000
        embed.add_field(name="Decisão", value=f"🚫 **NEGADO** por {interaction.user.name}")
        self.stop()
        await interaction.response.edit_message(embed=embed, view=None)