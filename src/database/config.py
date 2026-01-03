"""
This is the database configuration file and database connection setup file
This file basically is what connects your database to the rest of your python code
So that any logic and what not, requiring changes or working with your database, is
successful because this file allows that connection between the rest of your py code
and your (dev env) sqlite(LOCAL) database or your (prod env) postgresql(CLOUD) database

SQLite (local file) - What you'll use for learning:
 "sqlite:///project_root/data/incident_triage.db"
  ^^^^^^^   ^^^^^^^^^^^^^^^^^^^^
  dialect   path to file

 PostgreSQL (AWS RDS) - What you'll use in production:
 "postgresql://username:password@host:5432/dbname"
  ^^^^^^^^^^   ^^^^^^^^ ^^^^^^^^ ^^^^ ^^^^ ^^^^^^
  dialect      user     pass     host port database

 MySQL - Another option:
 "mysql://username:password@localhost:3306/dbname"
 """

import os                                                       # Operating System interface - so that it can read environment variables (not JUST .env FILE)
from pathlib import Path                                        # Best way to work with file paths - before it would be strings and that is messy ""
from dotenv import load_dotenv                                  # this calls in load_dotenv which reads your .env file
from src.config.project_paths import ENV_FILE, PROJECT_ROOT     # Our own import so that we can very easily pull in file path or project root
from sqlalchemy import create_engine, event, text               # Allows you to create an engine(
from sqlalchemy.pool import StaticPool                          #
from sqlalchemy.orm import sessionmaker, declarative_base       #

load_dotenv(ENV_FILE)   # pointing to the project_root/.env_file


"""
GET_DATABASE_URL():
The purpose of this function is SO THAT IT CAN DETERMINE WHERE our database is
AND if there is no database it creates a default one so that people can try to 
practice in case of pulling this entire code from repo and replicating something

It could be a local SQLite file (dev env)
or a AWS based postgreSQL database (prod env)
or any other mySQL database
"""
def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")    #get the .env variable

    if database_url:
        print(f" Using database from .env file: {database_url}")
        return database_url

    else:                                                   # if there is no database_url then create a local one in a data folder you'll create here
        data_dir = PROJECT_ROOT / "data"
        data_dir.mkdir(exist_ok=True)                       # exist_ok=true means that there will be no error if "data" dir already exists

        database_file = data_dir / "incident_triage.db"     # setting the path to the database file: project_root/data/incident_triage.db [CHANGE NAME IF NEEDED]

        # making the actual database url using the file we make using the above code
        # as_posix() just converts the potential backslashes to front slashes so that it is usable with many db libraries
        database_url = f"sqlite:///{database_file.absolute().as_posix()}"

        print(f"Using local SQLite file: {database_file.absolute()}")   # absolute() just returns the full absolute path of database_file
        return database_url


"""
Create the database engine using "engine = create_engine(database_url, args(comma and more if needed))":
What is an engine?
The engine manages the connection to the database
This connection needs to be made if you want to do anything with your database (Using "Session" to make changes to your db)
This engine opens/closes connections for you to work with your database
"""
DATABASE_URL = get_database_url()

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL,                                # First we create the engine using our db url then include some settings as to how this db connection operates. This is only a connection configuration.
                           connect_args={"check_same_thread": False},   # sqlite by default only allows the thread that made connection to use that connection. Here we say nah other process threads can use that gate/connection too
                           poolclass=StaticPool,                        # staticpool basically allows ONLY one gate/connection to the db and check_same_thread=false allows other threads to also use this one gate/connection
                           echo=False)                                  # echo just shows the query in the terminal when you do anything (if selecting data, it'll show the entire query and the selection you wanted)


    @event.listens_for(engine, "connect")                   # Beside is boilerplate code. Essentially what this VERY crucial code is doing is that it allows for foreign keys to be used in your SQLite db
    def set_sqlite_pragma(dbapi_connection, connection_record):     # By default, SQLite doesn't acknowledge foreign key rules which is VERY dangerous to db integrity (orphan records/ghost records)
        cursor = dbapi_connection.cursor()                          # This code below "hears" for whenever the db engine connects (THE VERY FIRST TIME) and sets the foreign keys rule to ON
        cursor.execute("PRAGMA foreign_keys=ON")                    # You need to understand that as you're not going to be messing with this code block after this. This runs internally through the connection to SQLite db
        cursor.close()

else:                                               # This is for anything that is not SQLite (PostgreSql/MySQL (when you want to use AWS))
    engine = create_engine(DATABASE_URL,
                           pool_size=10,            # Full database servers that are designed for 1000s of connections at a time. We only have 10 open at a time
                           max_overflow=20,         # We can allow for 20 more temporary connections/gates to be opened if the earlier 10 are busy, usually if we see traffic spikes
                           pool_pre_ping=True,      # this just checks the integrity of those connections made so that it doesn't just disconnect, sends a small ping query to check if conn is still alive
                           echo=False)              # same work as echo for sqlite db


"""
Create the session factory using "SessionLocal=sessionmaker(args(comma and more if needed))":
What is this SESSION factory(sessionmaker)?
Essentially this code block is a machine that allows you to create a workspace(session) for your database operations
Each session would allow you to: 
-create new records
-update records
-delete records
-commit all the changes you made to your database
-even rollback if something went wrong
"""
SessionLocal = sessionmaker(bind=engine,                # This connects our sessionmaker to the database engine we make before this
                            autocommit=False,           # This makes it so that changes are not saved without our approval(i.e. automatic. You can make sure you want to commit yourself)
                            autoflush=False,            # Autoflushing writes your data from your recent session but not permanently. Yes you can rollback but these are extra measures that could complicate processes.
                            expire_on_commit=False)     # Essentially saves your ORM model data in Python memory. Why couldn't you just query? Because it is a lot slower than just keeping in your memory.


# Initialize an ORM object type that essentially allows you to work with tables from WITHIN Python.
# It allows you to create tables that you can work with but through python syntax
Base = declarative_base()


"""
GET_DB():
This function is meant to create a database session and then ensure it is closed when the session is done.
How does this work?
FastAPI will call in this function, as a DEPENDENCY, "ability of sorts", and provide it to your API endpoints. 
So for example if one of your endpoints needs to return some data, it would need to open the session, 
do the work, return what it needs to return (or don't return anything if that's what its meant to do),
and then finally close the session. It all does this using the 'yield' keyword.
"""
def get_db():
    db = SessionLocal()
    try:
        yield db        # provide the session to whichever API endpoint that needs it. When the session is yielded, this function is put on hold.
    finally:
        db.close()      # after endpoint is done using the session, this function resumes here at 'finally' and closes the db session.


"""
INIT_DATABASE():
This function does exactly what the name implies. It is meant to initialize the entire database.
How does this work?
You will import ORM models which are python classes that represent tables.
'from src.models import database_models'; database_models would be a file.
Then Base.metadata.create_all(bind=engine) looks at all the tables defined in those models,
gathers their definitions, and creates the tables in the actual database.
"""
def init_database():
    # import here:
    from src.models import database_models

    Base.metadata.create_all(bind=engine)
    print("Database tables created/verified")


"""
TEST_CONNECTION():
We are testing if we can connect to the database.
This is useful for debugging connections.
"""
def test_connection():
    try:
        with engine.connect() as connection:            # 'with' is a special syntax word that has its own context manager
                                                        # -> when entering it enters as engine.connect().__enter__() and opens a connection.
                                                        # It returns the 'connection' object that can be used within the block.

            connection.execute(text("SELECT 1"))        # This is a simple health check query that is UNIVERSALLY USED by all databases to check if connection is good. This is actually when database gets connected
            print("Database connection successful!")
            return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False


if __name__ == "__main__":
    print("Testing database connection...")
    print("-"*40)
    print(f"Database URL: {DATABASE_URL}")
    print("-"*40)
    test_connection()