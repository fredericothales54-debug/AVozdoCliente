import psycopg2
import model
import view
import datetime
from view import AppView
from model import conexaobanco_model
class appcomtroll:
    def __init__(self,db_model_class,view_instace,db_conn):
        self.db_conn = db_conn
        self.view = view_instace
        self._executar_query = model.conexaobanco_model(db_conn)
        self._executar_query = model.conexaobanco_model()
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
        itens_disponivel = self.db_model.listar_itens_disponivel()
        if not itens_disponivel:
            self.view.mostrar_mensagem("Não há itens disponíveis para empréstimo no momento.")
            return
        self.view.mostrar_mensagem("itens disponiveis:")
        for item in itens_disponiveis:
            self.view.mostar_mensagem(f"ID: {item.id} | Nome: {item.nome} | Patrimonio: {item.patrimonio}")
        try:
            item_id = int(self.view.obter_entrada("digite o ID do item a ser emprestado: ")) 
            usuario_id = int(self.view.obter_entrada("digite o ID o usuario (pessoa que pega o item): "))
            id_local_emprestimo = int(self.view.obter_entrada("Digite o ID do local de destino (ex: 2 para 'Em Uso'): "))
            dias_previstos = int(self.view.obter_entrada("Digite a previsão de dias para devolução (ex: 7): "))
        
        except ValueError:
            self.view.mostar_mensagem("ID ou dias deve ser um numero valido.")
            return
        item_obj = self.db_model.obter_item_por_id(item_id)
        if not item_obj:
            self.view.mostar_mensagem(f"item com ID {item_id} nao encontrado.")
            return
        if item_obj.status != 'DISPONIVEL':
            self.view.mostar_mensagem(f" item '{item_obj.nome}' nao esta disponivel para emprestimo (status: {item_obj.status}.")
            return
        sucesso = self.db_model.emprestar_item(item_id, usuario_id, id_local_emprestimo, dias_previstos)

        if sucesso:
            self.view.mostar_mensagem(f" emprestimo do item '{item_obj.nome}' (patrimonio: {item_obj.patrimonio}) para usuario ID {usuario_id} registrado com sucesso!")
            self._historico.registrar_historico(
                tipo_evento ="EMPRESTIMO" ,
                detalhes={
                    "item_id": item_id,
                    "item_nome": item_obj.nome,
                    "usuario_id": usuario_id,
                    "data_prevista": (datatime.datatime.now() + datetime.timedelta(days=dias_previstos)).strftime("%Y-%m-%d")
                }
            )
        else:
            self.view.mostar_mensagem(f" erro ao registar o emprestimo. transaçao desfeita (rollback).")



    def finalizar_app(self):
        """Fecha a conexão e encerra o aplicativo."""
        self.running = False
        if self.db_conn:
            self.db_conn.close()
        self.view.mostrar_mensagem("Aplicação encerrada. Conexão com o DB fechada.")

class inventarioController:
    def __init__(self,db_conn):
        if db_conn is None:
            raise ValueError("conexao com o banco de dados nao pode ser nula.")
        self.db_conn = db_conn
        self.db_model = conexaobanco_model(self.db_conn)
    
    def autenticar_usuario_controller(conn, matricula: str, senha_digitada: str):
        db_model = conexaobanco_model(conn)
        usuario_row = db_model.autenticar_usuario(matricula)
        if usuario_row:
            id_usuario,nome, matricula_bd, senha_hash_bd =usuario_row
        
        if check_password_hash(senha_hash_bd, senha_digitada):
            usuario = usuario_model(id_usuario, nome, matricula_bd)
            return usuario
        else:
            print("tentativa de login falhou: Matricula nao encontrada.")
            return None
    
    def gerenciar_devoluçao(conn, item_id):
        if not isinstance(item_id, int) or item_id <= 0:
            return {"status": "erro", "mensagem": "ID do item invalido fornecido."}, 400
        db_model = conexaobanco_model(conn)
        sucesso = db_model.devolucao_item(item_id)
        if sucesso:
            return {"status": "sucesso",
                    "mensagem": f"Item {item_id} devolvido e satatus atualido."
                    }, 200
        else:
            return {"status": "erro",
                    "mensagem": f"Nao foi possivelregistrar a devoluçao do item {item_id}. Transaçao desfeita (rollback)."
                    }, 500
    
    def cadastrar_novo_usuario_controller(conn, nome: str,matricula:str,senha_texto_puro:str,usuario_model):
        if not nome or not matricula or not senha_texto_puro:
           return {"status": "erro", "mensagem": "Ttodos os campos (nome, matricula, semha) sao obrigatorios."}, 400
        novo_usuario_obj = usuario_model(
            id_usuario = None,
            nome = nome,
            matricula = matricula
        )
        setattr(novo_usuario_obj, 'senha' , senha_texto_puro)
        db_model = conexaobanco_model(conn)
        sucesso = db_model.cadastrar_usuario(novo_usuario_obj)

        if sucesso:
            return {"status": "sucesso",
                    "mensagem": f"Usuario {nome} cadastrado com sucesso!"
                    }, 201
        else:
            return {"status": "erro",
                    "mensagem": f"Falha ao cadastrar usuario. A matricula {matricula} pode ja estar em uso."
                    }, 409
    def fazer_login(self, matricula: str, senha_digitada: str):

        dados_usuario = self.dal.autenticar_usuario(matricula)
 
        if dados_usuario is None:

            return False, "Matrícula não encontrada."


        senha_armazenada = dados_usuario[3] 


        if senha_digitada == senha_armazenada: 


            usuario_logado = usuario_model(dados_usuario[0], dados_usuario[1], dados_usuario[2])

            historico.registrar_historico(

                tipo_evento="LOGIN",

                detalhes={"matricula": matricula, "nome": usuario_logado.nome}

            )

            return True, usuario_logado

        else:

            return False, "Senha incorreta."
 