from app.database import create_tables
import app.sneeze_app


def startup() -> None:
    # this function is called before the first request
    create_tables()

    # Initialize the sneeze tracking application
    app.sneeze_app.create()
