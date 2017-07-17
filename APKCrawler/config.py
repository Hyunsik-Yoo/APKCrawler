# separator used by search.py, categories.py, ...
SEPARATOR = ";"

LANG            = "ko_KR" # can be en_US, fr_FR, ...
ANDROID_ID      = "3B5E967080AC7AF2" # "xxxxxxxxxxxxxxxx"
GOOGLE_LOGIN    = "dbgustlr92@gmail.com" # "username@gmail.com"
GOOGLE_PASSWORD = "Macgongmon92"
AUTH_TOKEN      = None # "yyyyyyyyy"

# force the user to edit this file
if any([each == None for each in [ANDROID_ID, GOOGLE_LOGIN, GOOGLE_PASSWORD]]):
    raise Exception("config.py not updated")

