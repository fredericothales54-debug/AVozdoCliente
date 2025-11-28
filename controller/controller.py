import psycopg2
import model
import view
import datetime
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
    def realizar_emprestimo(self):
        """Lógica para registrar um empréstimo."""
        # Implementação futura: 
        # 1. Obter ID do item e ID do usuário via View.
        # 2. Chamar o Model para criar um registro na tabela Movimentacao.
        self.view.mostrar_mensagem("Função de Empréstimo a ser implementada...")
    
    def finalizar_app(self):
        """Fecha a conexão e encerra o aplicativo."""
        self.running = False
        if self.db_conn:
            self.db_conn.close()
        self.view.mostrar_mensagem("Aplicação encerrada. Conexão com o DB fechada.")

class inventarioContrller:
    def __init__(self,db_conn):
        if db_conn is None:
            raise ValueError("conexao com o banco de dados nao pode ser nula.")
        self.db_conn = db_conn
        self.db_model = conexaobanco_model(self.db_conn)
    def autenticar_usuario(self,matricula:str):
        query = """
            SELECT id_usuario, nome, matricula, senha
            FROM usuario
            WHERE matricula = %s;
        """
        row = self._executar_query(query, (matricula,), fetchone=True)
        if row:
            return (row)
        return None     