# create_tables.py
from db import engine, Base  # type: ignore
import models  # noqa: F401 - import all models so metadata is available
assert models  # mark as used for linters

def create():
    Base.metadata.create_all(bind=engine)
    print("Tables created")

if __name__ == "__main__":
    create()
