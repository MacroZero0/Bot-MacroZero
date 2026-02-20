# 📟 Sistema Tático de Controle de Ponto e Efetivo (Discord Bot)

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Discord.py](https://img.shields.io/badge/discord.py-v2.3+-blue.svg)
![SQLite](https://img.shields.io/badge/SQLite-Database-lightgrey.svg)

## 📌 Sobre o Projeto
Um bot de Discord desenvolvido em Python projetado para simular e automatizar o controle de ponto, logística de turnos e gestão de folgas de uma guarnição/equipe. Operando através de uma interface interativa (UI Views/Botões), o sistema elimina a necessidade de comandos manuais, persistindo todas as operações em um banco de dados relacional.

**Desenvolvido por:** MacroZero

## ⚙️ Funcionalidades Operacionais
- **Abertura/Fechamento de Ponto:** Registro em tempo real com cálculo automático de horas trabalhadas.
- **Logística Visual:** Painel interativo fixo. O bot substitui logs dinamicamente para manter o canal limpo.
- **Gestão de Folgas:** Sistema de solicitação de ausência com modal interativo.
- **Hierarquia de Comando:** Apenas cargos designados (Supervisores/Admins) recebem e podem aprovar/negar folgas em um canal seguro.
- **Banco de Dados Nativo:** Utiliza SQLite3 para garantir a persistência segura dos dados e auditoria de logs.

## 🚀 Como Implantar (Deploy)
1. Clone este repositório: `git clone https://github.com/SeuUsuario/seu-repo.git`
2. Crie um ambiente virtual: `python -m venv venv` e ative-o.
3. Instale as dependências: `pip install -r requirements.txt` *(certifique-se de criar este arquivo)*.
4. Crie um arquivo `.env` na raiz com o seu token: `DISCORD_TOKEN=seu_token`
5. Edite o arquivo `views.py` e insira o ID do canal de aprovação da chefia.
6. Inicie o sistema: `python main.py`

## 🛡️ Segurança (OpSec)
Este repositório não contém tokens ou informações sensíveis. Todos os dados críticos são gerenciados via variáveis de ambiente.
