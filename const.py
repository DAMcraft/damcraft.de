import dotenv
import os

dotenv.load_dotenv()


IP_INFO_API_KEY = os.environ.get("IPINFO_API_KEY")
TOR_HOSTNAME = os.environ.get("TOR_HOSTNAME")
DISCORD_ID = int(os.environ.get("DISCORD_ID"))
SERVER_ID = int(os.environ.get("SERVER_ID"))
BIRTHDAY = os.environ.get("BIRTHDAY")
ATPROTO_DID = os.environ.get("ATPROTO_DID")
MATRIX_SERVER_BASE_URL = os.environ.get("MATRIX_SERVER_BASE_URL")
MATRIX_SERVER = os.environ.get("MATRIX_SERVER")
SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REFRESH_TOKEN = os.environ.get("SPOTIFY_REFRESH_TOKEN")
MAIN_DOMAIN = os.environ.get("MAIN_DOMAIN")
URL_BASE = "https://" + MAIN_DOMAIN