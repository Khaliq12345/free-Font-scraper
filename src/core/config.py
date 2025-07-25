import dotenv
import os

dotenv.load_dotenv()

BUNNY_TOKEN = os.getenv(
    "BUNNY_TOKEN"
)
