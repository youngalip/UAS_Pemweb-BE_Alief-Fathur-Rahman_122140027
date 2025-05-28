from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker, scoped_session
from zope.sqlalchemy import register
from pyramid.events import NewRequest

# Membuat session factory yang thread-safe
DBSession = scoped_session(sessionmaker())
register(DBSession)

def setup_engine(settings):
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    return engine

def cleanup_request(event):
    # Event subscriber untuk membersihkan DBSession saat request selesai
    DBSession.remove()

def includeme(config):
    """Initialize the database connection and bind it to the request."""
    settings = config.get_settings()
    engine = setup_engine(settings)

    # Menghubungkan session dengan engine
    DBSession.configure(bind=engine)

    # Menyediakan DBSession sebagai attribute 'db' di request
    config.add_request_method(
        lambda request: DBSession(),
        'db',
        reify=True
    )

    # Daftarkan event subscriber untuk membersihkan session saat request selesai
    config.add_subscriber(cleanup_request, NewRequest)
