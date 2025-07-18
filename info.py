# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01
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
API_ID = int(environ.get('API_ID', '904789'))
API_HASH = environ.get('API_HASH', '2262ef67ced426b9eea57867b11666a1')
BOT_TOKEN = environ.get('BOT_TOKEN', "")
BOT_USERNAME = environ.get('BOT_USERNAME', 'Filmyzilla_Movie_Bot')
MEDIATOR_BOT = environ.get('MEDIATOR_BOT', 'Filmyzilla_Movie_Bot')
FORWARD_LINK = "https://vegamovies4u.xyz/wait?Autofiler2"


# Bot settings
CACHE_TIME = int(environ.get('CACHE_TIME', 300))
USE_CAPTION_FILTER = bool(environ.get('USE_CAPTION_FILTER', False))
PICS = (environ.get('PICS' , 'https://i.ibb.co/2YNN9MD2/photo-2025-03-31-08-17-12-7487884823235657744.jpg')).split() #SAMPLE PIC
NOR_IMG = environ.get("NOR_IMG", "https://te.legra.ph/file/a27dc8fe434e6b846b0f8.jpg")
MELCOW_VID = environ.get("MELCOW_VID", "https://i.ibb.co/2YNN9MD2/photo-2025-03-31-08-17-12-7487884823235657744.jpg")
SPELL_IMG = environ.get("SPELL_IMG", "https://te.legra.ph/file/15c1ad448dfe472a5cbb8.jpg")

# Premium And Referal Settings
CODE = (environ.get('CODE', 'https://i.ibb.co/ZpG44PGN/photo-2025-03-30-13-18-00-7487591227861237788.jpg'))
SUBSCRIPTION = (environ.get('SUBSCRIPTION', 'https://graph.org/file/35323f5f7bb90113b4337.jpg'))
REFERAL_COUNT = int(environ.get('REFERAL_COUNT', '20')) # number of referal count
REFERAL_PREMEIUM_TIME = environ.get('REFERAL_PREMEIUM_TIME', '1_Month')


# Admins, Channels & Premium Users
OWNER_LNK = environ.get('OWNER_LNK', 'https://t.me/TonyStark_Botz')
ADMINS = [int(admin) if id_pattern.search(admin) else admin for admin in environ.get('ADMINS', '6552970915').split()]
CHANNELS = [int(ch) if id_pattern.search(ch) else ch for ch in environ.get('CHANNELS', '-1002457424722').split()]
auth_users = [int(user) if id_pattern.search(user) else user for user in environ.get('AUTH_USERS', '').split()]
AUTH_USERS = (auth_users + ADMINS) if auth_users else []
PREMIUM_USER = [int(user) if id_pattern.search(user) else user for user in environ.get('PREMIUM_USER', '').split()]

auth_channel = environ.get('AUTH_CHANNEL', '-1002090374492')  # public channel 
second_auth_channel = environ.get('SECOND_AUTH_CHANNEL', '-1002634993647')  # Add the second auth channel or Group (should private)
third_auth_channel = environ.get('THIRD_AUTH_CHANNEL', '-1002682132745')  # Add the third auth channel or Group (should private)
AUTH_CHANNEL = int(auth_channel) if auth_channel and id_pattern.search(auth_channel) else None
SECOND_AUTH_CHANNEL = int(second_auth_channel) if second_auth_channel and id_pattern.search(second_auth_channel) else None
THIRD_AUTH_CHANNEL = int(third_auth_channel) if third_auth_channel and id_pattern.search(third_auth_channel) else None


# Movies Update Channel
MV_UPDATE_CHANNEL = -1002412021360  # ID of the log of daily movies update CHANNEL
SEND_MV_LOGS = bool(environ.get('SEND_MV_LOGS', True)) #send newmovies log to update channel 


#auth_grp = environ.get('AUTH_GROUP')
auth_grp = environ.get('AUTH_GROUP', '')
AUTH_GROUPS = [int(ch) for ch in auth_grp.split()] if auth_grp else None
support_chat_id = environ.get('SUPPORT_CHAT_ID', '-1002281736778')
reqst_channel = environ.get('REQST_CHANNEL_ID', '-1002321570567')
REQST_CHANNEL = int(reqst_channel) if reqst_channel and id_pattern.search(reqst_channel) else None
SUPPORT_CHAT_ID = int(support_chat_id) if support_chat_id and id_pattern.search(support_chat_id) else None
NO_RESULTS_MSG = bool(environ.get("NO_RESULTS_MSG", True))


## MongoDB information for session files
DATABASE_URI_SESSIONS_F = environ.get('DATABASE_URI_SESSIONS_F', "mongodb+srv://Filmyzilla_Movie_Bot:Kanhaiya@cluster0.i6q14.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

# MongoDB information
DATABASE_URI = environ.get('DATABASE_URI', "mongodb+srv://Filmyzilla_Movie_Bot:Kanhaiya@cluster0.i6q14.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DATABASE_NAME = environ.get('DATABASE_NAME', "Cluster0")

# 2nd MongoDB for only storing telegram files
DATABASE_URI2 = environ.get('DATABASE_URI2', "mongodb+srv://Filmyzilla_Movie_Bot_2:Kanhaiya@cluster0.wnzjd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DATABASE_NAME2 = environ.get('DATABASE_NAME2', "Cluster0")
COLLECTION_NAME = environ.get('COLLECTION_NAME', 'Kanhaiya')


ASKFSUBINGRP = bool(environ.get('ASKFSUBINGRP', False))
JOINREQ_MSG = bool(environ.get('JOINREQ_MSG', False))

VERIFY = bool(environ.get('VERIFY', False))
MIDVERIFY = bool(environ.get('MIDVERIFY', False))

# #first shortlink
# SHORTLINK_URL = environ.get('FIRST_SHORTLINK_URL', 'techvjlink.site')
# SHORTLINK_API = environ.get('FIRST_SHORTLINK_API', '5d84c45bd97704c052ca8355670f0d024083f3fb')

# #second shortlink 
# SECOND_SHORTLINK_URL = environ.get('SECOND_SHORTLINK_URL', 'techvjlink.site')
# SECOND_SHORTLINK_API = environ.get('SECOND_SHORTLINK_API', '5d84c45bd97704c052ca8355670f0d024083f3fb')

#first shortlink
SHORTLINK_URL = environ.get('FIRST_SHORTLINK_URL', 'techvjlink.site')
SHORTLINK_API = environ.get('FIRST_SHORTLINK_API', '5d84c45bd97704c052ca8355670f0d024083f3fb')
VERIFY_TUTORIAL = environ.get('FIRST_VERIFY_TUTORIAL', 'https://t.me/Movies_4_Download/614')

#second shortlink 
SECOND_SHORTLINK_URL = environ.get('SECOND_SHORTLINK_URL', 'techvjlink.site')
SECOND_SHORTLINK_API = environ.get('SECOND_SHORTLINK_API', '5d84c45bd97704c052ca8355670f0d024083f3fb')
SECOND_VERIFY_TUTORIAL = environ.get('SECOND_VERIFY_TUTORIAL', 'https://t.me/Movies_4_Download/615')

#third shortlink
THIRD_SHORTLINK_URL = environ.get('THIRD_SHORTLINK_URL', 'techvjlink.site')
THIRD_SHORTLINK_API = environ.get('THIRD_SHORTLINK_API', '5d84c45bd97704c052ca8355670f0d024083f3fb')
THIRD_VERIFY_TUTORIAL = environ.get('THIRD_VERIFY_TUTORIAL', 'https://t.me/Movies_4_Download/616')

#shortlink on for file2link
IS_SHORTLINK = bool(environ.get('IS_SHORTLINK', False))
IS_SREAM_SHORTLINK = bool(environ.get('IS_SREAM_SHORTLINK', False))

#added shortner in stream and download 
STREAM_SITE = (environ.get('STREAM_SITE', 'techvjlink.site'))
STREAM_API = (environ.get('STREAM_API', '5d84c45bd97704c052ca8355670f0d024083f3fb'))
STREAMHTO = (environ.get('STREAMHTO', 'https://t.me/Movies_4_Download/617'))


DELETE_CHANNELS = [int(dch) if id_pattern.search(dch) else dch for dch in environ.get('DELETE_CHANNELS', '-1002412021360').split()]
MAX_B_TN = environ.get("MAX_B_TN", "10")
MAX_BTN = is_enabled((environ.get('MAX_BTN', "True")), True)
PORT = environ.get("PORT", "8080")
GRP_LNK = environ.get('GRP_LNK', 'https://t.me/HD_Filmyzilla_Movies')
CHNL_LNK = environ.get('CHNL_LNK', 'https://t.me/Movies_4_Download')

TUTORIAL = environ.get('TUTORIAL', 'https://t.me/how2dow/55')
IS_TUTORIAL = bool(environ.get('IS_TUTORIAL', True))
MSG_ALRT = environ.get('MSG_ALRT', 'Hello My Dear Friends ❤️')
LOG_CHANNEL = int(environ.get('LOG_CHANNEL', '1002321570567'))
LOG_CHANNEL_V = int(environ.get('LOG_CHANNEL', '-1002321570567'))
LOG_CHANNEL_RQ = int(environ.get('LOG_CHANNEL', '-1002321570567'))
LOG_CHANNEL_NRM = int(environ.get('LOG_CHANNEL', '-1002321570567'))
PREMIUM_LOGS = int(environ.get('PREMIUM_LOGS', '-1002450886765'))
LOG_CHANNEL_SESSIONS_FILES = int(environ.get('LOG_CHANNEL_SESSIONS_FILES', '-1002450886765'))
PM_MSG_LOG_CHANNEL = int(environ.get('PM_MSG_LOG_CHANNEL', '1002412021360'))

SUPPORT_CHAT = environ.get('SUPPORT_CHAT', 'Kanus_Support')
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
INDEX_REQ_CHANNEL = int(environ.get('INDEX_REQ_CHANNEL', '-1002450886765'))
FILE_STORE_CHANNEL = [int(ch) for ch in (environ.get('FILE_STORE_CHANNEL', '')).split()]
MELCOW_NEW_USERS = is_enabled((environ.get('MELCOW_NEW_USERS', "True")), True)
PROTECT_CONTENT = is_enabled((environ.get('PROTECT_CONTENT', "False")), False)
PUBLIC_FILE_STORE = is_enabled((environ.get('PUBLIC_FILE_STORE', "True")), True)

#filters added 
LANGUAGES = ["malayalam", "mal", "tamil", "tam" ,"english", "eng", "hindi", "hin", "telugu", "tel", "kannada", "kan"]
SEASONS = ["season 1" , "season 2" , "season 3" , "season 4", "season 5" , "season 6" , "season 7" , "season 8" , "season 9" , "season 10"]
EPISODES = ["E01", "E02", "E03", "E04", "E05", "E06", "E07", "E08", "E09", "E10", "E11", "E12", "E13", "E14", "E15", "E16", "E17", "E18", "E19", "E20", "E21", "E22", "E23", "E24", "E25", "E26", "E27", "E28", "E29", "E30", "E31", "E32", "E33", "E34", "E35", "E36", "E37", "E38", "E39", "E40"]
QUALITIES = ["360p", "480p", "720p", "1080p", "1440p", "2160p"]
YEARS = ["1900", "1991", "1992", "1993", "1994", "1995", "1996", "1997", "1998", "1999", "2000", "2001", "2002", "2003", "2004", "2005", "2006", "2007", "2008", "2009", "2010", "2011", "2012", "2013", "2014", "2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025"]

#old stream codes snippet 
ON_HEROKU = False
# for stream #added
BIN_CHANNEL = environ.get("BIN_CHANNEL", "-1002412021360")
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

# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01
