from dotenv import load_dotenv

from dashboard import create_app

load_dotenv()

app = create_app()
