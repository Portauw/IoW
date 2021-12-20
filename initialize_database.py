from config import cfg
from src.database import DbManager, Base, IntraDaySecondData, DisplayStats, PlatformSync


# 1 - create new db-manager
db_manager = DbManager(cfg.full_sqlite_path)

# 2 - generate database schema
Base.metadata.create_all(db_manager.get_engine())

# 3 - create a new session
session = db_manager.get_session()

# 4 - [OPTIONAL] Add static data to empty database
