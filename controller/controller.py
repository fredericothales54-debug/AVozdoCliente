import psycopg2
import model
import view
from model import clientedb
from view import AppView
class appcomtroll:
    def __init__(self,db_model_class,view_instace,db_conn):
        self.db_conn = db_conn
        self.view = view_instace
        self._executar_query = model.clientedb(_db_conn)
        self._executar_query = model.clientedb()
        self._historico = []
        self.db_model = db_model_class(self.db_conn)
        self.running = True
    
    def iniciar_app(self):
        self.view.mostrar_mensagem("Bem-vindo ao sistema!")

        while self.running:
            escolha = self.view.mostrar_menu_principal()

            if escolha == '1':
                self.cadastar_item()
            elif escolha == '2':
                self.realizar_emprestimo()
            elif escolha == '0':
                self.finalizar_app()
            else:
                self.view.mostrar_mensagem("Opçao invalida. Tente novamente.")

    def cadastrar_item(self):
        self.view.mostrar_mensagem("\n--- Novo item cadastrado ---")
        none = self.view.obter_entrada("Digite o nome do item")
        patrimonio = self.view.obter_entrada("Digite o numero do patrimonio: ")
        try:
            self.db_model.inserir_item( nome, patrimonio)
            self.view.mostar_mensagem(f" item '{nome}' cadastrado com sucesso!")
        except Exception as e:
            self.view.mostar_menssagem(f" erro cadastrar produto ")
