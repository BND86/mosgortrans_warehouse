import psycopg2
from tgbot.create_bot import host, user, password, database, port

def write_photo(id, path):
    drawing = open(path, 'rb').read()
    query = """UPDATE requests SET photo = %s WHERE individual_number = %s"""
    params = (drawing, id)
    cursor.execute(query, params)
    connection.commit()
    connection.close()

try:
    connection = psycopg2.connect(
    host=host,
    user=user,
    password=password,
    database=database,
    port=port
    )
    connection.autocommit = True
    cursor = connection.cursor()
    
    cursor.execute(
        "SELECT version();"
        )

    print(f"Server version: {cursor.fetchone()}")


except psycopg2.InterfaceError as exc:
        print(exc)
        connection = psycopg2.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        port=port
        )
        connection.autocommit = True
        cursor = connection.cursor()

except Exception as _ex:
    print("[INFO] Error while working with PostgreSQL", _ex)

# finally:
#     if connection:
#         connection.close()
#         print("[INFO] PostgreSQL connection closed")
