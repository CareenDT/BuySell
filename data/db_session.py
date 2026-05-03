import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session

SqlAlchemyBase = orm.declarative_base()
__factory = None

def global_init(db_file: str):
    global __factory

    if __factory:
        return
    
    if not db_file or not db_file.strip():
        raise Exception(f"Invalid path for db: {db_file}")
    
    connection_string = f"sqlite:///{db_file.strip()}?check_same_thread=False"

    engine = sa.create_engine(connection_string, echo=False, poolclass=sa.NullPool)
    __factory = orm.sessionmaker(bind=engine)

    from . import __all_models

    SqlAlchemyBase.metadata.create_all(engine)

def create_session() -> Session:
    global __factory
    return __factory()
