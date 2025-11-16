import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
import re
import logging
import asyncio

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ==============================================================================
# CONFIGURAÇÕES GERAIS (EDITÁVEIS)
# ==============================================================================
# Token de acesso do seu bot Telegram (OBRIGATÓRIO)
TOKEN = "7483214978:AAEsfpNCn3qonuBLbDERbPDpQH7CG45TC9g"
# ID do usuário administrador (para receber alertas de erro e usar o bot de forma interativa)
USER_ID = 1603479629
# ID do grupo/canal de destino onde as programações serão postadas (OBRIGATÓRIO)
GROUP_ID = -1002326740811

# ==============================================================================
# CONFIGURAÇÕES DE EXTRAÇÃO DIÁRIA AUTOMÁTICA (EDITÁVEIS)
# ==============================================================================
# HORA (0-23) para a extração automática diária (ex: 18 para 18:00)
DAILY_EXTRACTION_HOUR = 19
# MINUTO (0-59) para a extração automática diária (ex: 0 para 18:00)
DAILY_EXTRACTION_MINUTE = 0
# Texto explicativo para a extração diária (opcional, apenas para referência)
DAILY_EXTRACTION_EXPLANATION = "A extração diária será executada automaticamente para o dia seguinte às 18:00."

# ==============================================================================
# CONFIGURAÇÕES DA CHAMADA PARA AÇÃO (CTA) (EDITÁVEIS)
# ==============================================================================
# Texto completo da Chamada para Ação (CTA) que será enviada após cada categoria (EDITÁVEL)
# Se esta variável for deixada vazia (ex: CTA_MESSAGE = ""), a CTA não será enviada.
CTA_MESSAGE = (
    ""
)
# Texto explicativo para a CTA (opcional, apenas para referência)
CTA_EXPLANATION = "Este é o texto de marketing que será postado no final de cada categoria de programação."

# ==============================================================================
# LISTA DE CANAIS POR CATEGORIA (EDITÁVEL)
# Formato: "Nome da Categoria": [{"name": "NOME_DO_CANAL", "url": "URL_DO_MEUGUIA_TV"}]
# ==============================================================================
CHANNELS = {
    "Filmes": [
        {"name": "AMC", "url": "https://meuguia.tv/programacao/canal/MGM"},
        {"name": "CANAL_BRASIL", "url": "https://meuguia.tv/programacao/canal/CBR"},
        {"name": "CINEMAX", "url": "https://meuguia.tv/programacao/canal/MNX"},
        {"name": "HBO", "url": "https://meuguia.tv/programacao/canal/HBO"},
        {"name": "HBO_2", "url": "https://meuguia.tv/programacao/canal/HB2"},
        {"name": "HBO_FAMILY", "url": "https://meuguia.tv/programacao/canal/HFA"},
        {"name": "HBO_PLUS", "url": "https://meuguia.tv/programacao/canal/HPL"},
        {"name": "HBO_SIGNATURE", "url": "https://meuguia.tv/programacao/canal/HFE"},
        {"name": "MEGAPIX", "url": "https://meuguia.tv/programacao/canal/MPX"},
        {"name": "PARAMOUNT_CHANNEL", "url": "https://meuguia.tv/programacao/canal/PAR"},
        {"name": "SPACE", "url": "https://meuguia.tv/programacao/canal/SPA"},
        {"name": "TCM_TURNER_CLASSIC", "url": "https://meuguia.tv/programacao/canal/TCM"},
        {"name": "TNT", "url": "https://meuguia.tv/programacao/canal/TNT"},
        {"name": "TELECINE_ACTION", "url": "https://meuguia.tv/programacao/canal/TC2"},
        {"name": "TELECINE_CULT", "url": "https://meuguia.tv/programacao/canal/TC5"},
        {"name": "TELECINE_FUN", "url": "https://meuguia.tv/programacao/canal/TC6"},
        {"name": "TELECINE_PIPOCA", "url": "https://meuguia.tv/programacao/canal/TC4"},
        {"name": "TELECINE_PREMIUM", "url": "https://meuguia.tv/programacao/canal/TC1"},
        {"name": "TELECINE_TOUCH", "url": "https://meuguia.tv/programacao/canal/TC3"},
    ],
    "Esportes": [
        {"name": "BAND_SPORTS", "url": "https://meuguia.tv/programacao/canal/BSP"},
        {"name": "COMBATE", "url": "https://meuguia.tv/programacao/canal/135"},
        {"name": "ESPN", "url": "https://meuguia.tv/programacao/canal/ESP"},
        {"name": "ESPN_2", "url": "https://meuguia.tv/programacao/canal/ES2"},
        {"name": "ESPN_3", "url": "https://meuguia.tv/programacao/canal/ES3"},
        {"name": "ESPN_4", "url": "https://meuguia.tv/programacao/canal/ES4"},
        {"name": "ESPN_5", "url": "https://meuguia.tv/programacao/canal/ES5"},
        {"name": "OFF_HD", "url": "https://meuguia.tv/programacao/canal/OFF"},
        {"name": "PREMIERE_CLUBES", "url": "https://meuguia.tv/programacao/canal/121"},
        {"name": "SPORTV", "url": "https://meuguia.tv/programacao/canal/SPO"},
        {"name": "SPORTV_2", "url": "https://meuguia.tv/programacao/canal/SP2"},
        {"name": "SPORTV_3", "url": "https://meuguia.tv/programacao/canal/SP3"},
    ],
    "Variedades": [
        {"name": "ARTE_1", "url": "https://meuguia.tv/programacao/canal/BQ5"},
        {"name": "BIS", "url": "https://meuguia.tv/programacao/canal/MSH"},
        {"name": "CANAL_RURAL", "url": "https://meuguia.tv/programacao/canal/RUR"},
        {"name": "CANAL_DO_BOI", "url": "https://meuguia.tv/programacao/canal/BOI"},
        {"name": "COMEDY_CENTRAL", "url": "https://meuguia.tv/programacao/canal/CCE"},
        {"name": "E! ENTERTAINMENT_TELEVISION", "url": "https://meuguia.tv/programacao/canal/EET"},
        {"name": "FUTURA", "url": "https://meuguia.tv/programacao/canal/FUT"},
        {"name": "GNT", "url": "https://meuguia.tv/programacao/canal/GNT"},
        {"name": "MULTISHOW", "url": "https://meuguia.tv/programacao/canal/MSW"},
        {"name": "TV_JUSTIÇA", "url": "https://meuguia.tv/programacao/canal/JUS"},
        {"name": "TV_SENADO", "url": "https://meuguia.tv/programacao/canal/SEN"},
        {"name": "TRAVEL_BOX_BRAZIL", "url": "https://meuguia.tv/programacao/canal/TRB"},
        {"name": "VIVA", "url": "https://meuguia.tv/programacao/canal/VIV"},
        {"name": "WOOHOO", "url": "https://meuguia.tv/programacao/canal/WOO"},
    ],
    "Notícias": [
        {"name": "BBC_WORLD_NEWS", "url": "https://meuguia.tv/programacao/canal/BBC"},
        {"name": "BAND_NEWS", "url": "https://meuguia.tv/programacao/canal/NEW"},
        {"name": "BLOOMBERG", "url": "https://meuguia.tv/programacao/canal/BIT"},
        {"name": "CNN_INTERNATIONAL", "url": "https://meuguia.tv/programacao/canal/CNN"},
        {"name": "DEUTSCHE_WELLE", "url": "https://meuguia.tv/programacao/canal/DWL"},
        {"name": "GLOBO_NEWS", "url": "https://meuguia.tv/programacao/canal/GLN"},
    ],
    "Infantil": [
        {"name": "BABY_TV", "url": "https://meuguia.tv/programacao/canal/BAB"},
        {"name": "CARTOON_NETWORK", "url": "https://meuguia.tv/programacao/canal/CAR"},
        {"name": "DISCOVERY_KIDS", "url": "https://meuguia.tv/programacao/canal/DIK"},
        {"name": "GLOOB", "url": "https://meuguia.tv/programacao/canal/GOB"},
        {"name": "NICK_JR.", "url": "https://meuguia.tv/programacao/canal/NJR"},
        {"name": "NICKELODEON", "url": "https://meuguia.tv/programacao/canal/NIC"},
        {"name": "TOONCAST", "url": "https://meuguia.tv/programacao/canal/TOC"},
    ],
    "Séries": [
        {"name": "A&E", "url": "https://meuguia.tv/programacao/canal/MDO"},
        {"name": "AXN", "url": "https://meuguia.tv/programacao/canal/AXN"},
        {"name": "ANIMAL_PLANET", "url": "https://meuguia.tv/programacao/canal/APL"},
        {"name": "DISCOVERY_HD_THEATER", "url": "https://meuguia.tv/programacao/canal/DHD"},
        {"name": "EUROCHANNEL", "url": "https://meuguia.tv/programacao/canal/EUR"},
        {"name": "FILM & ARTS", "url": "https://meuguia.tv/programacao/canal/BRA"},
        {"name": "LIFETIME", "url": "https://meuguia.tv/programacao/canal/ANX"},
        {"name": "SONY", "url": "https://meuguia.tv/programacao/canal/SET"},
        {"name": "STUDIO_UNIVERSAL", "url": "https://meuguia.tv/programacao/canal/HAL"},
        {"name": "TBS", "url": "https://meuguia.tv/programacao/canal/TBS"},
        {"name": "TNT_SÉRIES", "url": "https://meuguia.tv/programacao/canal/TNS"},
        {"name": "UNIVERSAL_CHANNEL", "url": "https://meuguia.tv/programacao/canal/USA"},
        {"name": "WARNER_CHANNEL", "url": "https://meuguia.tv/programacao/canal/WBT"},
    ],
    "TV_Aberta": [
        {"name": "BAND", "url": "https://meuguia.tv/programacao/canal/BAN"},
        {"name": "GLOBO", "url": "https://meuguia.tv/programacao/canal/GRD"},
        {"name": "MTV", "url": "https://meuguia.tv/programacao/canal/MTV"},
        {"name": "RECORD_NEWS", "url": "https://meuguia.tv/programacao/canal/RCN"},
        {"name": "RECORD_TV", "url": "https://meuguia.tv/programacao/canal/REC"},
        {"name": "REDE_TV", "url": "https://meuguia.tv/programacao/canal/RTV"},
        {"name": "REDE_VIDA", "url": "https://meuguia.tv/programacao/canal/VDA"},
        {"name": "SBT", "url": "https://meuguia.tv/programacao/canal/SBT"},
        {"name": "TV_APARECIDA", "url": "https://meuguia.tv/programacao/canal/TAP"},
        {"name": "TV_BRASIL", "url": "https://meuguia.tv/programacao/canal/TED"},
        {"name": "TV_CULTURA", "url": "https://meuguia.tv/programacao/canal/CUL"},
        {"name": "TV_GAZETA", "url": "https://meuguia.tv/programacao/canal/GAZ"},
    ],
    "Documentários": [
        {"name": "DISCOVERY_CHANNEL", "url": "https://meuguia.tv/programacao/canal/DIS"},
        {"name": "DISCOVERY_HOME &_HEALTH", "url": "https://meuguia.tv/programacao/canal/HEA"},
        {"name": "DISCOVERY_SCIENCE", "url": "https://meuguia.tv/programacao/canal/DSC"},
        {"name": "DISCOVERY_TURBO", "url": "https://meuguia.tv/programacao/canal/DTU"},
        {"name": "DISCOVERY_WORLD", "url": "https://meuguia.tv/programacao/canal/DIW"},
        {"name": "HISTORY_CHANNEL", "url": "https://meuguia.tv/programacao/canal/HIS"},
        {"name": "TLC", "url": "https://meuguia.tv/programacao/canal/TRV"},
    ],
}

# ==============================================================================
# EMOJIS E IDs DOS TÓPICOS DO GRUPO/CANAL (EDITÁVEL)
# O nome da chave DEVE ser o mesmo nome da chave em CHANNELS.
# O topic_id é o ID do tópico no grupo/canal do Telegram.
# ==============================================================================
CATEGORIES = {
    "Filmes": {"emoji": "🎬", "topic_id": 4},
    "Esportes": {"emoji": "⚽", "topic_id": 8},
    "Variedades": {"emoji": "🎭", "topic_id": 68},
    "Notícias": {"emoji": "📰", "topic_id": 67},
    "Infantil": {"emoji": "🧸", "topic_id": 66},
    "Séries": {"emoji": "📺", "topic_id": 52},
    "TV_Aberta": {"emoji": "📡", "topic_id": 10},
    "Documentários": {"emoji": "📚", "topic_id": 6},
}

# Estado global para controle da extração
EXTRACTION_STATE = {"running": False, "selected_date": None, "selected_category": None, "selected_channel": None, "header_sent": {}}

# Função para obter o dia da semana em pt-br
def get_day_of_week(date):
    logging.info(f"Obtendo dia da semana para {date}...")
    days = ["SEGUNDA-FEIRA", "TERÇA-FEIRA", "QUARTA-FEIRA", "QUINTA-FEIRA", "SEXTA-FEIRA", "SÁBADO", "DOMINGO"]
    return days[date.weekday()]

# Função para formatar o nome do canal (em CAIXA ALTA e sem separadores)
def format_channel_name(channel_name):
    # Remove caracteres especiais e converte para maiúsculas
    name = channel_name.replace("_", " ")
    return name.upper()

# Função para extrair programações com retry
def extract_programs(url, date_str, retries=3, timeout=20):
    logging.info(f"Iniciando extração para URL: {url}, Data: {date_str}")
    headers = {"User-Agent": "Mozilla/5.0"}
   
    for attempt in range(retries):
        try:
            logging.info(f"Tentativa {attempt + 1}/{retries}: Enviando requisição HTTP para {url}...")
            response = requests.get(url, headers=headers, timeout=timeout)
            logging.info(f"Requisição bem-sucedida. Status: {response.status_code}")
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            logging.info("HTML parseado com BeautifulSoup.")
           
            # Formato da data: "d/m" para o site (ex.: 15/5)
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            target_date = f"{int(date_obj.strftime('%d'))}/{int(date_obj.strftime('%m'))}"
            logging.info(f"Procurando programações para o dia {target_date}...")
            programs = []
           
            # Localizar o bloco do dia
            logging.info("Buscando cabeçalhos de dias...")
            day_headers = soup.find_all("li", class_="subheader devicepadding")
            logging.info(f"Encontrados {len(day_headers)} cabeçalhos de dias.")
            current_day = None
            for header in day_headers:
                day_text = header.text.strip()
                logging.info(f"Verificando dia: {day_text}")
                day_match = re.search(r"\d{1,2}/\d{1,2}", day_text)
                if day_match:
                    site_date = day_match.group().strip()
                    if site_date == target_date:
                        current_day = header
                        logging.info(f"Dia {target_date} encontrado!")
                        break
                    else:
                        logging.info(f"Data não corresponde: '{site_date}' != '{target_date}'")
           
            if not current_day:
                logging.warning(f"Dia {target_date} não encontrado no site.")
                return []
           
            # Encontrar programações após o cabeçalho do dia
            logging.info("Procurando programações para o dia encontrado...")
            for sibling in current_day.find_next_siblings():
                if sibling.name == "li" and "subheader" in sibling.get("class", []):
                    logging.info("Novo dia encontrado, parando busca.")
                    break
                if sibling.name == "li" and sibling.find("a", class_="devicepadding"):
                    logging.info("Programa potencial encontrado, analisando...")
                    time_div = sibling.find("div", class_="lileft time")
                    content_div = sibling.find("div", class_="licontent")
                    if not (time_div and content_div):
                        logging.warning("Faltam elementos time ou content, pulando.")
                        continue
                   
                    time = time_div.text.strip()
                    title_tag = content_div.find("h2")
                    category_tag = content_div.find("h3")
                    if not (title_tag and category_tag):
                        logging.warning("Faltam elementos title ou category, pulando.")
                        continue
                   
                    title = title_tag.text.strip()
                    category = category_tag.text.strip()
                   
                    # Ignorar anúncios
                    if "Publicidade" in title or not category:
                        logging.info(f"Programa ignorado: {title} (Publicidade ou sem categoria).")
                        continue
                   
                    programs.append({"time": time, "title": title, "category": category})
                    logging.info(f"Programa adicionado: {time} | {title} | {category}")
           
            if not programs:
                logging.info("Nenhum programa válido encontrado para este dia.")
            else:
                logging.info(f"Total de programas encontrados: {len(programs)}")
            return programs
       
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro ao acessar {url} (tentativa {attempt + 1}/{retries}): {str(e)}")
            if attempt < retries - 1:
                logging.info("Aguardando 5 segundos antes da próxima tentativa...")
                time.sleep(5)
            else:
                logging.error("Todas as tentativas falharam. Retornando None.")
                return None
        except Exception as e:
            logging.error(f"Erro inesperado na extração: {str(e)}")
            return None

# Função para formatar programações
def format_programs(channel_name, programs, category, date_str):
    logging.info(f"Formatando programações para {channel_name}, categoria {category}...")
    if not programs:
        logging.info("Nenhum programa para formatar.")
        return None
   
    messages = []
    # Converter data para o formato DD/MM/AA
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    date_display = date_obj.strftime("%d/%m/%y")
    
    # Aplica a formatação de nome de canal solicitada (CAIXA ALTA, sem separadores)
    formatted_channel_name = format_channel_name(channel_name)
    
    # Remove o link bit.ly da mensagem
    current_message = f"✅ {formatted_channel_name} ({date_display})\n\n"
    program_count = 0
   
    for program in programs:
        current_message += f"🕒 {program['time']} | {program['title']}\n{program['category']}\n"
        program_count += 1
       
        if program_count >= 10:
            messages.append(current_message)
            # Reinicia o cabeçalho da mensagem para a próxima parte
            current_message = f"✅ {formatted_channel_name} ({date_display})\n\n"
            program_count = 0
   
    if program_count > 0:
        messages.append(current_message)
   
    logging.info(f"Programações formatadas: {len(messages)} mensagens.")
    return messages

# Função para enviar a CTA
async def send_cta(context: ContextTypes.DEFAULT_TYPE, chat_id: int, topic_id: int, category: str):
    # Usa a variável de configuração CTA_MESSAGE
    cta_message = CTA_MESSAGE
    
    # Se a CTA_MESSAGE estiver vazia, não envia a mensagem
    if not cta_message.strip():
        logging.info(f"CTA_MESSAGE vazia. Pulando envio da CTA para {category}.")
        return
        
    retries = 3
    for attempt in range(retries):
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                message_thread_id=topic_id,
                text=cta_message
            )
            logging.info(f"CTA enviada para o tópico {topic_id} da categoria {category}.")
            break
        except telegram.error.RetryAfter as e:
            logging.warning(f"Rate limit atingido ao enviar CTA. Aguardando {e.retry_after} segundos...")
            time.sleep(e.retry_after)
            continue
        except telegram.error.TimedOut as e:
            logging.error(f"Timeout ao enviar CTA para {category} (tentativa {attempt + 1}/{retries}): {str(e)}")
            if attempt < retries - 1:
                logging.info("Aguardando 5 segundos antes da próxima tentativa...")
                time.sleep(5)
            else:
                logging.error("Todas as tentativas falharam. Pulando envio da CTA.")
                await context.bot.send_message(
                    chat_id=USER_ID,
                    text=f"❌ Erro: Falha ao enviar CTA para {category} devido a timeout."
                )

# Função para extração diária
async def schedule_daily_extraction(context: ContextTypes.DEFAULT_TYPE):
    while True:
        now = datetime.now()
        # Usa as variáveis de configuração DAILY_EXTRACTION_HOUR e DAILY_EXTRACTION_MINUTE
        if now.hour == DAILY_EXTRACTION_HOUR and now.minute == DAILY_EXTRACTION_MINUTE and not EXTRACTION_STATE["running"]:
            logging.info("Iniciando extração diária para o dia seguinte...")
            EXTRACTION_STATE["running"] = True
            tomorrow = now + timedelta(days=1)
            tomorrow_date = tomorrow.strftime("%Y-%m-%d")
           
            for category in CATEGORIES.keys():
                if not EXTRACTION_STATE["running"]:
                    break
               
                # Reiniciar o estado do header
                EXTRACTION_STATE["header_sent"][category] = False
               
                # Enviar o header da categoria
                if not EXTRACTION_STATE["header_sent"].get(category, False):
                    date_obj = datetime.strptime(tomorrow_date, "%Y-%m-%d")
                    emoji = CATEGORIES[category]["emoji"]
                    day_week = get_day_of_week(date_obj)
                    date_formatted = date_obj.strftime("%d/%m/%Y")
                    
                    # Remove o link bit.ly do header
                    header = f"{emoji} PROGRAMAÇÃO DE {category.upper()}\n📅 {day_week}, {date_formatted}"
                    
                    topic_id = CATEGORIES[category]["topic_id"]
                    retries = 3
                    for attempt in range(retries):
                        try:
                            await context.bot.send_message(chat_id=GROUP_ID, message_thread_id=topic_id, text=header)
                            logging.info(f"Header enviado para {category}: {header}")
                            EXTRACTION_STATE["header_sent"][category] = True
                            break
                        except telegram.error.RetryAfter as e:
                            logging.warning(f"Rate limit atingido ao enviar header. Aguardando {e.retry_after} segundos...")
                            time.sleep(e.retry_after)
                            continue
                        except telegram.error.TimedOut as e:
                            logging.error(f"Timeout ao enviar header para {category} (tentativa {attempt + 1}/{retries}): {str(e)}")
                            if attempt < retries - 1:
                                logging.info("Aguardando 5 segundos antes da próxima tentativa...")
                                time.sleep(5)
                            else:
                                logging.error("Todas as tentativas falharam. Pulando envio do header.")
                                await context.bot.send_message(chat_id=USER_ID, text=f"❌ Erro: Falha ao enviar header para {category} devido a timeout.")
               
                channels = CHANNELS[category]
                for channel in channels:
                    if not EXTRACTION_STATE["running"]:
                        break
                   
                    logging.info(f"Extraindo para canal: {channel['name']}")
                    programs = extract_programs(channel["url"], tomorrow_date)
                    if programs is None:
                        await context.bot.send_message(chat_id=USER_ID, text=f"❌ Erro: Falha ao acessar {channel['name']}. Pulando.")
                        logging.error(f"Falha ao acessar {channel['name']}, pulando.")
                        time.sleep(1)
                        continue
                   
                    messages = format_programs(channel["name"], programs, category, tomorrow_date)
                    if not messages:
                        await context.bot.send_message(chat_id=USER_ID, text=f"❌ Erro: Nenhuma programação para {channel['name']} em {tomorrow_date}. Verifique se o site tem dados para essa data.")
                        logging.info(f"Nenhuma programação encontrada para {channel['name']} em {tomorrow_date}.")
                        time.sleep(1)
                        continue
                   
                    topic_id = CATEGORIES[category]["topic_id"]
                    for msg in messages:
                        if not EXTRACTION_STATE["running"]:
                            break
                        retries = 3
                        for attempt in range(retries):
                            try:
                                await context.bot.send_message(chat_id=GROUP_ID, message_thread_id=topic_id, text=msg)
                                logging.info(f"Mensagem enviada ao tópico {topic_id}: {msg[:50]}...")
                                time.sleep(1) # Atraso de 1 segundo entre mensagens
                                break
                            except telegram.error.RetryAfter as e:
                                logging.warning(f"Rate limit atingido ao enviar mensagem. Aguardando {e.retry_after} segundos...")
                                time.sleep(e.retry_after)
                                continue
                            except telegram.error.TimedOut as e:
                                logging.error(f"Timeout ao enviar mensagem para {channel['name']} (tentativa {attempt + 1}/{retries}): {str(e)}")
                                if attempt < retries - 1:
                                    logging.info("Aguardando 5 segundos antes da próxima tentativa...")
                                    time.sleep(5)
                                else:
                                    logging.error("Todas as tentativas falharam. Pulando mensagem.")
                                    await context.bot.send_message(chat_id=USER_ID, text=f"❌ Erro: Falha ao enviar mensagem para {channel['name']} devido a timeout.")
                        if not EXTRACTION_STATE["running"]:
                            break
                   
                    if not EXTRACTION_STATE["running"]:
                        break
                   
                    time.sleep(2) # Intervalo entre canais
               
                # REMOVIDO: Envio da lista de canais com hashtags
               
                # Enviar a CTA
                if EXTRACTION_STATE["running"]:
                    await send_cta(context, GROUP_ID, CATEGORIES[category]["topic_id"], category)
               
                if not EXTRACTION_STATE["running"]:
                    break
           
            if EXTRACTION_STATE["running"]:
                logging.info("Extração diária concluída com sucesso.")
            EXTRACTION_STATE["running"] = False
            EXTRACTION_STATE["header_sent"].clear()
       
        # Aguardar 1 minuto antes de verificar novamente
        await asyncio.sleep(60)

# Manipuladores de comandos e callbacks
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info("Comando /start recebido.")
    if update.effective_user.id != USER_ID:
        logging.warning(f"Usuário não autorizado: {update.effective_user.id}")
        return
   
    keyboard = [[InlineKeyboardButton("Escolher Data", callback_data="choose_date")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Bem-vindo! Escolha uma data para as programações.", reply_markup=reply_markup)
    logging.info("Mensagem de boas-vindas enviada.")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info("Callback de botão recebido.")
    query = update.callback_query
    if query.from_user.id != USER_ID:
        logging.warning(f"Usuário não autorizado: {query.from_user.id}")
        return
   
    await query.answer()
    data = query.data
    logging.info(f"Dados do botão: {data}")
   
    if data == "choose_date":
        today = datetime.now()
        keyboard = []
        date_buttons = []
        for i in range(14):
            date = today + timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            date_display = date.strftime("%d/%m/%Y")
            label = f"{'Hoje' if i == 0 else 'Amanhã' if i == 1 else ''} - {date_display}".strip()
            # CORREÇÃO: Usar '_' como separador para evitar problemas de split
            date_buttons.append(InlineKeyboardButton(label, callback_data=f"date_{date_str}"))
            # Colocar 2 botões por linha
            if len(date_buttons) == 2:
                keyboard.append(date_buttons)
                date_buttons = []
        if date_buttons: # Adicionar botões restantes
            keyboard.append(date_buttons)
        keyboard.append([InlineKeyboardButton("Voltar ao Início", callback_data="start")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Selecione o dia (disponível até 14 dias).", reply_markup=reply_markup)
        logging.info("Menu de datas exibido.")
   
    elif data.startswith("date_"):
        # CORREÇÃO: Usar '_' como separador para evitar problemas de split
        date_str = data.split("_")[1]
        EXTRACTION_STATE["selected_date"] = date_str
        logging.info(f"Data selecionada: {date_str}")
        keyboard = []
        category_buttons = []
        for cat in CATEGORIES.keys():
            # CORREÇÃO: Usar '_' como separador para evitar problemas de split
            category_buttons.append(InlineKeyboardButton(cat, callback_data=f"category_{cat}"))
            # Colocar 3 botões por linha
            if len(category_buttons) == 3:
                keyboard.append(category_buttons)
                category_buttons = []
        if category_buttons: # Adicionar botões restantes
            keyboard.append(category_buttons)
        keyboard.append([InlineKeyboardButton("Todas as Categorias", callback_data="category_all")])
        keyboard.append([InlineKeyboardButton("Voltar ao Início", callback_data="start")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        date_display = datetime.strptime(date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
        await query.edit_message_text(f"Escolha uma categoria ou todas para {date_display}.", reply_markup=reply_markup)
        logging.info("Menu de categorias exibido.")
   
    elif data.startswith("category_"):
        # CORREÇÃO: Usar '_' como separador para evitar problemas de split
        category = data.split("_")[1]
        EXTRACTION_STATE["selected_category"] = category if category != "all" else None
        logging.info(f"Categoria selecionada: {category}")
        if category == "all":
            keyboard = [
                [InlineKeyboardButton("Iniciar Extração", callback_data="start_extraction")],
                [InlineKeyboardButton("Voltar ao Início", callback_data="start")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            date_display = datetime.strptime(EXTRACTION_STATE["selected_date"], "%Y-%m-%d").strftime("%d/%m/%Y")
            await query.edit_message_text(f"Iniciar extração para Todas as Categorias - {date_display}?", reply_markup=reply_markup)
            logging.info("Confirmação para todas as categorias exibida.")
        else:
            # Lista de canais para a categoria selecionada
            channels_in_category = CHANNELS[category]
            keyboard = []
            
            # Adiciona os botões de canais, 3 por linha
            for i in range(0, len(channels_in_category), 3):
                row = [InlineKeyboardButton(channel["name"], callback_data=f"channel_{channel['name']}") for channel in channels_in_category[i:i+3]]
                keyboard.append(row)
                
            keyboard.append([InlineKeyboardButton("Todos os Canais", callback_data="channel_all")])
            keyboard.append([InlineKeyboardButton("Voltar ao Início", callback_data="start")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            date_display = datetime.strptime(EXTRACTION_STATE["selected_date"], "%Y-%m-%d").strftime("%d/%m/%Y")
            await query.edit_message_text(f"Selecione o canal para {category}, {date_display}.", reply_markup=reply_markup)
            logging.info("Menu de canais exibido.")
   
    elif data.startswith("channel_"):
        channel = data.split("_")[1]
        EXTRACTION_STATE["selected_channel"] = channel if channel != "all" else None
        logging.info(f"Canal selecionado: {channel}")
        date_display = datetime.strptime(EXTRACTION_STATE["selected_date"], "%Y-%m-%d").strftime("%d/%m/%Y")
        if EXTRACTION_STATE["selected_category"]:
            target = f"{EXTRACTION_STATE['selected_category']} - {EXTRACTION_STATE['selected_channel'] or 'Todos os Canais'}"
        else:
            # Este caso não deve ocorrer se a navegação for correta, mas mantido por segurança
            target = "Todas as Categorias"
            
        keyboard = [
            [InlineKeyboardButton("Iniciar Extração", callback_data="start_extraction")],
            [InlineKeyboardButton("Voltar ao Início", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"Iniciar extração para {target} - {date_display}?", reply_markup=reply_markup)
        logging.info("Confirmação de extração exibida.")
   
    elif data == "start_extraction":
        if EXTRACTION_STATE["running"]:
            await query.edit_message_text("Extração já em andamento. Use 'Parar Extração' para interromper.")
            logging.info("Extração já em andamento, comando ignorado.")
            return
       
        EXTRACTION_STATE["running"] = True
        date_display = datetime.strptime(EXTRACTION_STATE["selected_date"], "%Y-%m-%d").strftime("%d/%m/%Y")
        target = "Todas as Categorias" if not EXTRACTION_STATE["selected_category"] else \
                 f"{EXTRACTION_STATE['selected_category']} - {EXTRACTION_STATE['selected_channel'] or 'Todos os Canais'}"
        keyboard = [[InlineKeyboardButton("Parar Extração", callback_data="stop_extraction")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"📢 Extraindo programações para {target} - {date_display}...", reply_markup=reply_markup)
        logging.info(f"Iniciando extração para {target} - {date_display}")
       
        # Verificar se a data é futura e avisar o usuário
        selected_date = datetime.strptime(EXTRACTION_STATE["selected_date"], "%Y-%m-%d")
        today = datetime.now()
        if selected_date > today + timedelta(days=1):
            await context.bot.send_message(chat_id=USER_ID, text="⚠️ Aviso: Programações para datas futuras podem não estar disponíveis ainda.")
            logging.info("Aviso de data futura enviado.")
       
        # Iniciar extração
        categories = list(CATEGORIES.keys()) if not EXTRACTION_STATE["selected_category"] else [EXTRACTION_STATE["selected_category"]]
        for category in categories:
            if not EXTRACTION_STATE["running"]:
                break
               
            # Reiniciar o estado do header para cada categoria
            EXTRACTION_STATE["header_sent"][category] = False
           
            # Enviar o header da categoria apenas uma vez por categoria
            if not EXTRACTION_STATE["header_sent"].get(category, False):
                date_obj = datetime.strptime(EXTRACTION_STATE["selected_date"], "%Y-%m-%d")
                emoji = CATEGORIES[category]["emoji"]
                day_week = get_day_of_week(date_obj)
                date_formatted = date_obj.strftime("%d/%m/%Y")
                
                # Remove o link bit.ly do header
                header = f"{emoji} PROGRAMAÇÃO DE {category.upper()}\n📅 {day_week}, {date_formatted}"
                
                topic_id = CATEGORIES[category]["topic_id"]
                retries = 3
                for attempt in range(retries):
                    try:
                        await context.bot.send_message(chat_id=GROUP_ID, message_thread_id=topic_id, text=header)
                        logging.info(f"Header enviado para {category}: {header}")
                        EXTRACTION_STATE["header_sent"][category] = True
                        break
                    except telegram.error.RetryAfter as e:
                        logging.warning(f"Rate limit atingido ao enviar header. Aguardando {e.retry_after} segundos...")
                        time.sleep(e.retry_after)
                        continue
                    except telegram.error.TimedOut as e:
                        logging.error(f"Timeout ao enviar header para {category} (tentativa {attempt + 1}/{retries}): {str(e)}")
                        if attempt < retries - 1:
                            logging.info("Aguardando 5 segundos antes da próxima tentativa...")
                            time.sleep(5)
                        else:
                            logging.error("Todas as tentativas falharam. Pulando envio do header.")
                            await context.bot.send_message(chat_id=USER_ID, text=f"❌ Erro: Falha ao enviar header para {category} devido a timeout.")
           
            # Filtra canais se um canal específico foi selecionado
            channels = [ch for ch in CHANNELS[category] if EXTRACTION_STATE["selected_channel"] == ch["name"]] if EXTRACTION_STATE["selected_channel"] and EXTRACTION_STATE["selected_channel"] != "all" else CHANNELS[category]
            
            for channel in channels:
                if not EXTRACTION_STATE["running"]:
                    logging.info("Extração interrompida pelo usuário.")
                    break
               
                logging.info(f"Extraindo para canal: {channel['name']}")
                programs = extract_programs(channel["url"], EXTRACTION_STATE["selected_date"])
                if programs is None:
                    await context.bot.send_message(chat_id=USER_ID, text=f"❌ Erro: Falha ao acessar {channel['name']}. Pulando.")
                    logging.error(f"Falha ao acessar {channel['name']}, pulando.")
                    time.sleep(1)
                    continue
               
                messages = format_programs(channel["name"], programs, category, EXTRACTION_STATE["selected_date"])
                if not messages:
                    await context.bot.send_message(chat_id=USER_ID, text=f"❌ Erro: Nenhuma programação para {channel['name']} em {date_display}. Verifique se o site tem dados para essa data.")
                    logging.info(f"Nenhuma programação encontrada para {channel['name']} em {date_display}.")
                    time.sleep(1)
                    continue
               
                topic_id = CATEGORIES[category]["topic_id"]
                for msg in messages:
                    if not EXTRACTION_STATE["running"]:
                        break
                    retries = 3
                    for attempt in range(retries):
                        try:
                            await context.bot.send_message(chat_id=GROUP_ID, message_thread_id=topic_id, text=msg)
                            logging.info(f"Mensagem enviada ao tópico {topic_id}: {msg[:50]}...")
                            time.sleep(1) # Atraso de 1 segundo entre mensagens
                            break
                        except telegram.error.RetryAfter as e:
                            logging.warning(f"Rate limit atingido ao enviar mensagem. Aguardando {e.retry_after} segundos...")
                            time.sleep(e.retry_after)
                            continue
                        except telegram.error.TimedOut as e:
                            logging.error(f"Timeout ao enviar mensagem para {channel['name']} (tentativa {attempt + 1}/{retries}): {str(e)}")
                            if attempt < retries - 1:
                                logging.info("Aguardando 5 segundos antes da próxima tentativa...")
                                time.sleep(5)
                            else:
                                logging.error("Todas as tentativas falharam. Pulando mensagem.")
                                await context.bot.send_message(chat_id=USER_ID, text=f"❌ Erro: Falha ao enviar mensagem para {channel['name']} devido a timeout.")
                    if not EXTRACTION_STATE["running"]:
                        break
               
                if not EXTRACTION_STATE["running"]:
                    break
               
                time.sleep(2) # Intervalo entre canais
           
            # Enviar a CTA
            if EXTRACTION_STATE["running"]:
                await send_cta(context, GROUP_ID, CATEGORIES[category]["topic_id"], category)
           
            if not EXTRACTION_STATE["running"]:
                break
       
        if EXTRACTION_STATE["running"]:
            keyboard = [[InlineKeyboardButton("Voltar ao Início", callback_data="start")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("✅ Extração concluída! Programações enviadas.", reply_markup=reply_markup)
            logging.info("Extração concluída com sucesso.")
        EXTRACTION_STATE["running"] = False
        EXTRACTION_STATE["header_sent"].clear() # Limpa o estado dos headers
   
    elif data == "stop_extraction":
        EXTRACTION_STATE["running"] = False
        keyboard = [[InlineKeyboardButton("Voltar ao Início", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("⛔ Extração interrompida.", reply_markup=reply_markup)
        logging.info("Extração interrompida pelo usuário.")
   
    elif data == "start":
        keyboard = [[InlineKeyboardButton("Escolher Data", callback_data="choose_date")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Bem-vindo! Escolha uma data para as programações.", reply_markup=reply_markup)
        logging.info("Mensagem de boas-vindas enviada.")

def main():
    # Inicializar a aplicação
    app = Application.builder().token(TOKEN).build()
    logging.info("Aplicação inicializada.")
    # Adicionar handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    logging.info("Handlers adicionados.")
    # Iniciar a tarefa de extração diária
    async def start_task(application):
        # Configura o agendamento da extração diária usando as variáveis DAILY_EXTRACTION_HOUR e DAILY_EXTRACTION_MINUTE
        logging.info(f"Agendando extração diária para {DAILY_EXTRACTION_HOUR:02d}:{DAILY_EXTRACTION_MINUTE:02d}. {DAILY_EXTRACTION_EXPLANATION}")
        await asyncio.create_task(schedule_daily_extraction(application))
    # Adicionar inicialização assíncrona para criar a tarefa
    app.job_queue.run_once(start_task, 0)
    # Iniciar o polling (loop principal do bot)
    app.run_polling(allowed_updates=Update.ALL_TYPES)
    logging.info("Polling iniciado.")

if __name__ == "__main__":
    logging.info("Script iniciado.")
    main()
    logging.info("Script finalizado.")
