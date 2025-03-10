import re
from os import environ,getenv
from Script import script 

id_pattern = re.compile(r'^.\d+$')
def is_enabled(value, default):
    if value.lower() in ["true", "yes", "1", "enable", "y"]:
        return True
    elif value.lower() in ["false", "no", "0", "disable", "n"]:
        return False
    else:
        return default

# Bot information
SESSION = environ.get('SESSION', 'Media_search')
API_ID = int(environ.get('API_ID', '21187284'))
API_HASH = environ.get('API_HASH', 'dd55d48a8c624dae7d34dcffe07034b8')
BOT_TOKEN = environ.get('BOT_TOKEN', "")
BOT_USERNAME = environ.get('BOT_USERNAME', 'All_Movie_Finder_Bot')
MEDIATOR_BOT = environ.get('MEDIATOR_BOT', 'Pikashow_Movies_Bot')
FORWARD_LINK = "https://vegamovies4u.xyz/wait?Autofiler2"

# Bot settings
CACHE_TIME = int(environ.get('CACHE_TIME', 300))
USE_CAPTION_FILTER = bool(environ.get('USE_CAPTION_FILTER', False))

# Bot Images
PICS = (environ.get('PICS' ,'https://graph.org/file/040c13521abcaf21a4adb.jpg https://graph.org/file/d3ce0fbe68fad09c3cfd1.jpg')).split() #SAMPLE PIC
NOR_IMG = environ.get("NOR_IMG", "https://te.legra.ph/file/a27dc8fe434e6b846b0f8.jpg")
MELCOW_VID = environ.get("MELCOW_VID", "https://telegram.me/shaho_movie_request")
SPELL_IMG = environ.get("SPELL_IMG", "https://te.legra.ph/file/15c1ad448dfe472a5cbb8.jpg")

# ADMINS, CHANNELS & PREMIUM USER
ADMINS = [int(admin) if id_pattern.search(admin) else admin for admin in environ.get('ADMINS', '6552970915').split()]
CHANNELS = [int(ch) if id_pattern.search(ch) else ch for ch in environ.get('CHANNELS', '-1002462264302').split()]
auth_users = [int(user) if id_pattern.search(user) else user for user in environ.get('AUTH_USERS', '').split()]
AUTH_USERS = (auth_users + ADMINS) if auth_users else []
PREMIUM_USER = [int(user) if id_pattern.search(user) else user for user in environ.get('PREMIUM_USER', '').split()]

# Premium And Referal Settings
SUBSCRIPTION = (environ.get('SUBSCRIPTION', 'https://graph.org/file/35323f5f7bb90113b4337.jpg'))
CODE = (environ.get('CODE', 'https://graph.org/file/2dce415ac8d303ee7c7ca.jpg'))
REFERAL_COUNT = int(environ.get('REFERAL_COUNT', '20')) # number of referal count
REFERAL_PREMEIUM_TIME = environ.get('REFERAL_PREMEIUM_TIME', '1_Month')

# MOVIE UPDATE CHANNEL
MV_UPDATE_CHANNEL = -1002410949273  # ID of the log of daily movies update CHANNEL
SEND_MV_LOGS = bool(environ.get('SEND_MV_LOGS', False)) #send newmovies log to update channel 

# This Is Your Bot Support Group Id , Here Bot Will Not Give File Because This Is Support Group.
support_chat_id = environ.get('SUPPORT_CHAT_ID', '-1002281736778')
SUPPORT_CHAT_ID = int(support_chat_id) if support_chat_id and id_pattern.search(support_chat_id) else None

# This Channel Is For When User Request Any File Name With command or hashtag like - /request or #request
reqst_channel = environ.get('REQST_CHANNEL_ID', '-1002321570567')
REQST_CHANNEL = int(reqst_channel) if reqst_channel and id_pattern.search(reqst_channel) else None

# Force Subscription
auth_channel = environ.get('AUTH_CHANNEL', '-1002090374492')  # public channel 
second_auth_channel = environ.get('SECOND_AUTH_CHANNEL', '')  # Add the second auth channel or Group (should private)
third_auth_channel = environ.get('THIRD_AUTH_CHANNEL', '')  # Add the third auth channel or Group (should private)

AUTH_CHANNEL = int(auth_channel) if auth_channel and id_pattern.search(auth_channel) else None
SECOND_AUTH_CHANNEL = int(second_auth_channel) if second_auth_channel and id_pattern.search(second_auth_channel) else None
THIRD_AUTH_CHANNEL = int(third_auth_channel) if third_auth_channel and id_pattern.search(third_auth_channel) else None

#auth_grp = environ.get('AUTH_GROUP', '-1002105025900 -1002065604244 -1001994677259 -1002121994889 -1001902541817 -1001946073826 -1001959069308 -1001984828576')
auth_grp = environ.get('AUTH_GROUP')
AUTH_GROUPS = [int(ch) for ch in auth_grp.split()] if auth_grp else None

# MongoDB information for session files
DATABASE_URI_SESSIONS_F = environ.get('DATABASE_URI_SESSIONS_F', "mongodb+srv://Database2:Kanhaiya@cluster0.ie0wq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
# MongoDB information
DATABASE_URI = environ.get('DATABASE_URI', "mongodb+srv://Kanhaiya:kanhaiya960@cluster0.ljdbg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DATABASE_NAME = environ.get('DATABASE_NAME', "Kanhaiya")
# 2nd MongoDB for only storing telegram files
DATABASE_URI2 = environ.get('DATABASE_URI2', "mongodb+srv://Kanhaiya:kanhaiya960@cluster0.ljdbg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DATABASE_NAME2 = environ.get('DATABASE_NAME2', "Kanhaiya")
COLLECTION_NAME = environ.get('COLLECTION_NAME', 'Kanhaiya')

# #first shortlink
# SHORTLINK_URL = environ.get('FIRST_SHORTLINK_URL', 'shortxlinks.com')
# SHORTLINK_API = environ.get('FIRST_SHORTLINK_API', 'b474897e83e3e42619c67d2f56648aac5bb767ea')

# #second shortlink 
# SECOND_SHORTLINK_URL = environ.get('SECOND_SHORTLINK_URL', 'shortxlinks.com')
# SECOND_SHORTLINK_API = environ.get('SECOND_SHORTLINK_API', 'b474897e83e3e42619c67d2f56648aac5bb767ea')

#first shortlink
SHORTLINK_URL = environ.get('FIRST_SHORTLINK_URL', 'genzurl.com')
SHORTLINK_API = environ.get('FIRST_SHORTLINK_API', 'ca1672e0cf3d48a903fab7fe451c1a627e0e8e2c')

#second shortlink 
SECOND_SHORTLINK_URL = environ.get('SECOND_SHORTLINK_URL', 'genzurl.com')
SECOND_SHORTLINK_API = environ.get('SECOND_SHORTLINK_API', 'ca1672e0cf3d48a903fab7fe451c1a627e0e8e2c')

#third shortlink
THIRD_SHORTLINK_URL = environ.get('THIRD_SHORTLINK_URL', 'genzurl.com')
THIRD_SHORTLINK_API = environ.get('THIRD_SHORTLINK_API', 'ca1672e0cf3d48a903fab7fe451c1a627e0e8e2c')

#verify tutorial 
VERIFY_TUTORIAL = environ.get('FIRST_VERIFY_TUTORIAL', 'https://t.me/how2dow/76')
SECOND_VERIFY_TUTORIAL = environ.get('SECOND_VERIFY_TUTORIAL', 'https://t.me/how2dow/76')
THIRD_VERIFY_TUTORIAL = environ.get('THIRD_VERIFY_TUTORIAL', 'https://t.me/how2dow/55')

#shortlink on for file2link 
IS_SREAM_SHORTLINK = bool(environ.get('IS_SREAM_SHORTLINK', False))
IS_SHORTLINK = bool(environ.get('IS_SHORTLINK', False))

TUTORIAL = environ.get('TUTORIAL', 'https://t.me/how2dow/55')
IS_TUTORIAL = bool(environ.get('IS_TUTORIAL', False))


GRP_LNK = environ.get('GRP_LNK', 'https://t.me/MovieSearchGroupHD')
CHNL_LNK = environ.get('CHNL_LNK', 'https://t.me/Movies_4_Download')
SUPPORT_CHAT = environ.get('SUPPORT_CHAT', 'Kanus_Support')
LOG_CHANNEL = int(environ.get('LOG_CHANNEL', '-1002321570567'))
LOG_CHANNEL_V = int(environ.get('LOG_CHANNEL', '-1002321570567'))
LOG_CHANNEL_RQ = int(environ.get('LOG_CHANNEL', '-1002321570567'))
LOG_CHANNEL_NRM = int(environ.get('LOG_CHANNEL', '-1002321570567'))
PREMIUM_LOGS = int(environ.get('PREMIUM_LOGS', '-1002450886765'))
INDEX_REQ_CHANNEL = int(environ.get('INDEX_REQ_CHANNEL', '-1002450886765'))
PM_MSG_LOG_CHANNEL = int(environ.get('PM_MSG_LOG_CHANNEL', '-1002410949273'))
LOG_CHANNEL_SESSIONS_FILES = int(environ.get('LOG_CHANNEL_SESSIONS_FILES', '-1002450886765'))
FILE_STORE_CHANNEL = [int(ch) for ch in (environ.get('FILE_STORE_CHANNEL', '-1002410949273')).split()]
DELETE_CHANNELS = [int(dch) if id_pattern.search(dch) else dch for dch in environ.get('DELETE_CHANNELS', '-1002410949273').split()]

ASKFSUBINGRP = bool(environ.get('ASKFSUBINGRP', True))
MIDVERIFY = bool(environ.get('MIDVERIFY', True))
VERIFY = bool(environ.get('VERIFY', True))
JOINREQ_MSG = bool(environ.get('JOINREQ_MSG', False))
NO_RESULTS_MSG = bool(environ.get("NO_RESULTS_MSG", False))

MAX_B_TN = environ.get("MAX_B_TN", "10")
MAX_BTN = is_enabled((environ.get('MAX_BTN', "True")), True)
PORT = environ.get("PORT", "8080")
MSG_ALRT = environ.get('MSG_ALRT', 'Hello My Dear Friends ❤️')
P_TTI_SHOW_OFF = is_enabled((environ.get('P_TTI_SHOW_OFF', "False")), False)
IMDB = is_enabled((environ.get('IMDB', "False")), False)
AUTO_FFILTER = is_enabled((environ.get('AUTO_FFILTER', "True")), True)
AUTO_DELETE = is_enabled((environ.get('AUTO_DELETE', "True")), True)
SINGLE_BUTTON = is_enabled((environ.get('SINGLE_BUTTON', "True")), True)
CUSTOM_FILE_CAPTION = environ.get("CUSTOM_FILE_CAPTION", f"{script.CAPTION}")
BATCH_FILE_CAPTION = environ.get("BATCH_FILE_CAPTION", CUSTOM_FILE_CAPTION)
IMDB_TEMPLATE = environ.get("IMDB_TEMPLATE", f"{script.IMDB_TEMPLATE_TXT}")
LONG_IMDB_DESCRIPTION = is_enabled(environ.get("LONG_IMDB_DESCRIPTION", "False"), False)
SPELL_CHECK_REPLY = is_enabled(environ.get("SPELL_CHECK_REPLY", "True"), True)
MAX_LIST_ELM = environ.get("MAX_LIST_ELM", None)
MELCOW_NEW_USERS = is_enabled((environ.get('MELCOW_NEW_USERS', "True")), True)
PROTECT_CONTENT = is_enabled((environ.get('PROTECT_CONTENT', "False")), False)
PUBLIC_FILE_STORE = is_enabled((environ.get('PUBLIC_FILE_STORE', "True")), True)

#filters added 
LANGUAGES = ["malayalam", "mal", "tamil", "tam" ,"english", "eng", "hindi", "hin", "telugu", "tel", "kannada", "kan"]
SEASONS = ["season 1" , "season 2" , "season 3" , "season 4", "season 5" , "season 6" , "season 7" , "season 8" , "season 9" , "season 10"]
EPISODES = ["E01", "E02", "E03", "E04", "E05", "E06", "E07", "E08", "E09", "E10", "E11", "E12", "E13", "E14", "E15", "E16", "E17", "E18", "E19", "E20", "E21", "E22", "E23", "E24", "E25", "E26", "E27", "E28", "E29", "E30", "E31", "E32", "E33", "E34", "E35", "E36", "E37", "E38", "E39", "E40"]
QUALITIES = ["360p", "480p", "720p", "1080p", "1440p", "2160p"]
YEARS = ["1900", "1991", "1992", "1993", "1994", "1995", "1996", "1997", "1998", "1999", "2000", "2001", "2002", "2003", "2004", "2005", "2006", "2007", "2008", "2009", "2010", "2011", "2012", "2013", "2014", "2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025"]

#added shortner in stream and download 
STREAM_SITE = (environ.get('STREAM_SITE', 'tryshort.in'))
STREAM_API = (environ.get('STREAM_API', '3058e5209596c0369b6ed7681b22f5e8216e02b5'))
STREAMHTO = (environ.get('STREAMHTO', 'https://t.me/how2dow/57'))

#old stream codes snippet 
ON_HEROKU = False
# for stream #added
BIN_CHANNEL = environ.get("BIN_CHANNEL", "-1002410949273")
if len(BIN_CHANNEL) == 0:
    print('Error - BIN_CHANNEL is missing, exiting now')
    exit()
else:
    BIN_CHANNEL = int(BIN_CHANNEL)
URL = environ.get("URL", "http://109.107.186.165:6979")  #if heroku then paste the app link here ex: https://heroku......./
# if len(URL) == 0:
    # print('Error - URL is missing, exiting now')
    # exit()
# else:
    # if URL.startswith(('https://', 'http://')):
        # if not URL.endswith("/"):
            # URL += '/'
    # elif is_valid_ip(URL):
        # URL = f'http://{URL}/'
    # else:
        # print('Error - URL is not valid, exiting now')
        # exit()

LOG_STR = "Current Cusomized Configurations are:-\n"
LOG_STR += ("IMDB Results are enabled, Bot will be showing imdb details for you queries.\n" if IMDB else "IMBD Results are disabled.\n")
LOG_STR += ("P_TTI_SHOW_OFF found , Users will be redirected to send /start to Bot PM instead of sending file file directly\n" if P_TTI_SHOW_OFF else "P_TTI_SHOW_OFF is disabled files will be send in PM, instead of sending start.\n")
LOG_STR += ("SINGLE_BUTTON is Found, filename and files size will be shown in a single button instead of two separate buttons\n" if SINGLE_BUTTON else "SINGLE_BUTTON is disabled , filename and file_sixe will be shown as different buttons\n")
LOG_STR += (f"CUSTOM_FILE_CAPTION enabled with value {CUSTOM_FILE_CAPTION}, your files will be send along with this customized caption.\n" if CUSTOM_FILE_CAPTION else "No CUSTOM_FILE_CAPTION Found, Default captions of file will be used.\n")
LOG_STR += ("Long IMDB storyline enabled." if LONG_IMDB_DESCRIPTION else "LONG_IMDB_DESCRIPTION is disabled , Plot will be shorter.\n")
LOG_STR += ("Spell Check Mode Is Enabled, bot will be suggesting related movies if movie not found\n" if SPELL_CHECK_REPLY else "SPELL_CHECK_REPLY Mode disabled\n")
LOG_STR += (f"MAX_LIST_ELM Found, long list will be shortened to first {MAX_LIST_ELM} elements\n" if MAX_LIST_ELM else "Full List of casts and crew will be shown in imdb template, restrict them by adding a value to MAX_LIST_ELM\n")
LOG_STR += f"Your current IMDB template is {IMDB_TEMPLATE}"
