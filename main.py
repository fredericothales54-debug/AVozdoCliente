from model import *
from view import *
from controller import *
import tkinter as tk
import sys
import psycopg2
DB_HOST="localhost"
DB_NAME="A_Voz_do_Cliente"
DB_USER="postgres"
DB_PASS="1234"
DB_PORT="5432"
def main():
    db_conn=True
    try:
        db_conn=psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        print("Conexão bd deu certo")
    except psycopg2.OperationalError as e:
        print("erro ao conectar ao banco de dados")
        sys.exit(1)
    root=tk.Tk()
    root.withdraw()
    appcontroler=AppController(
        db_model_class=conexaobanco_model,
        view_instace=None,
        db_conn=db_conn
    )
    app_view= AppView(
        root_window=root,
        controller=appcontroler
    )
    appcontroler.view=app_view
    root.mainloop()
    if db_conn:
        db_conn.close()
        print("conexão db fechada")
if __name__ == "__main__":
    main()