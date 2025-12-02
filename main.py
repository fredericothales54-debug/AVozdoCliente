import tkinter as tk
import psycopg2
import sys
from model import conexaobanco_model
from controller import AppController 
from view import AppView 
DB_HOST = "localhost"
DB_NAME = "seu_banco_de_dados"
DB_USER = "seu_usuario"
DB_PASS = "sua_senha"
DB_PORT = "5432"

def main():
    """Função principal para inicializar e executar a aplicação MVC."""
    db_conn = None
    
  
    try:
        db_conn = psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        print("✅ Conexão com o PostgreSQL estabelecida com sucesso.")
        
    except psycopg2.OperationalError as e:
        print(f"❌ Erro ao conectar ao banco de dados: {e}")
        print("Certifique-se de que o PostgreSQL está rodando e as credenciais estão corretas.")
        sys.exit(1)

    
    
    
    root = tk.Tk()
    root.withdraw() 
    
    
    app_controller = AppController(
        db_model_class=conexaobanco_model, 
        view_instace=None,                  
        db_conn=db_conn                    
    )
    
   
   
    app_view = AppView(
        root_window=root,
        controller=app_controller
    )
    
   
    app_controller.view = app_view 
    
   
    root.mainloop()

    if db_conn:
        db_conn.close()
        print("Conexão com o DB fechada ao sair do aplicativo.")

if __name__ == "__main__":
    main()