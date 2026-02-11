import os
from dotenv import load_dotenv
import logging
from psycopg import connect
from psycopg.conninfo import make_conninfo

load_dotenv()


logger = logging.getLogger(__name__)
logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)



DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_PORT= os.getenv("DB_PORT")
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


CONNECTION_INFO = make_conninfo(
    host = DB_HOST,
    port = DB_PORT,
    dbname = DB_NAME,
    user = DB_USER,
    password = DB_PASSWORD
)

try:  
    logger.info(f"Attempting to connect with database {DB_NAME} on host {DB_HOST}:{DB_PORT}")
    db_connection = connect(CONNECTION_INFO)
    logger.info(f"Connected to {DB_NAME}")
    db_connection.commit()
    db_connection.close()
except Exception as e:
    logger.error(f"Failed to connect to database {DB_NAME} {e}")
