import psycopg2
import datetime
from model import conexaobanco_model, item_model, usuario_model
from model import conexaobanco_model
from model import item_model, usuario_model, historico 



class AppController:
    def __init__(self, db_model_class, view_instace, db_conn):
        self.db_conn = db_conn
        self.view = view_instace
        
       
        self.db_model = db_model_class(self.db_conn) 
        
        
        self.historico = historico 
        
        self.running = True
    def fazer_login(self, matricula: str, senha_digitada: str):
        """Método de login que a View estava procurando."""
        dados_usuario = self.db_model.autenticar_usuario(matricula) 

        if dados_usuario is None:
            return False, "Matrícula não encontrada."

        senha_armazenada = dados_usuario[2]

        if senha_digitada == senha_armazenada: 
            
            usuario_logado = usuario_model(dados_usuario[0], dados_usuario[1], dados_usuario[2])

            return True, usuario_logado 

        else:
            return False, "Senha incorreta."
    
   

    def iniciar_app(self):
        self.view.mostrar_mensagem("Bem-vindo ao sistema de Inventário!")

        while self.running:
            escolha = self.view.mostrar_menu_principal()

            if escolha == '1':
                self.cadastrar_item()
            elif escolha == '2':
                self.realizar_emprestimo()
            elif escolha == '0':
                self.finalizar_app()
            else:
                self.view.mostrar_mensagem("Opção inválida. Tente novamente.")

    def cadastrar_item(self):
        self.view.mostrar_mensagem("\n--- Novo Item Cadastrado ---")
        
        try:
            nome_id = int(self.view.obter_entrada("Digite o ID do Nome do item (Tabela NOMES_ITENS): "))
            patrimonio = self.view.obter_entrada("Digite o número do patrimônio: ")
            status_id = int(self.view.obter_entrada("Digite o ID do Status (Geralmente 1 para DISPONIVEL): "))
            local_id = int(self.view.obter_entrada("Digite o ID do Local (Tabela LOCAIS): "))
        except ValueError:
            self.view.mostrar_mensagem("❌ Erro: ID, Status ou Local devem ser números válidos.")
            return

        try:
            novo_item = item_model(
                id_produto=None, 
                nome_produto=nome_id, 
                numero_patrimonio=patrimonio, 
                categoria_produto=None, 
                localizacao_produto=local_id, 
                status_produto=status_id
            )
            
            if self.db_model.inserir_produto(novo_item):
                self.view.mostrar_mensagem(f"Item com Patrimônio '{patrimonio}' cadastrado com sucesso!")
            else:
                self.view.mostrar_mensagem(f"❌ Erro ao cadastrar item. Transação desfeita.")
        except Exception as e:
            self.view.mostrar_mensagem(f"❌ Erro na operação de cadastro: {e}")

    def realizar_emprestimo(self):
        self.view.mostrar_mensagem("\n--- Realizar Empréstimo ---")
        
        itens_disponiveis = self.db_model.listar_itens_disponiveis()
        if not itens_disponiveis:
            self.view.mostrar_mensagem("Não há itens disponíveis para empréstimo no momento.")
            return

        self.view.mostrar_mensagem("Itens disponíveis:")
        for item in itens_disponiveis:
            self.view.mostrar_mensagem(f"ID: {item.id} | Nome: {item.nome} | Patrimônio: {item.patrimonio} | Status: {item.status}")
            
        try:
            item_id = int(self.view.obter_entrada("Digite o ID do item a ser emprestado: "))
            usuario_id = int(self.view.obter_entrada("Digite o ID do usuário (pessoa que pega o item): "))
            id_local_emprestimo = int(self.view.obter_entrada("Digite o ID do local de destino (ex: 2 para 'Em Uso'): "))
            dias_previstos = int(self.view.obter_entrada("Digite a previsão de dias para devolução (ex: 7): "))
        except ValueError:
            self.view.mostrar_mensagem("❌ ID, Local ou dias deve ser um número válido.")
            return

        item_obj = self.db_model.obter_item_por_id(item_id)
        
        if isinstance(item_obj, str) or not item_obj:
            self.view.mostrar_mensagem(f"❌ Item com ID {item_id} não encontrado.")
            return
            
        if item_obj.status != 'DISPONIVEL':
            self.view.mostrar_mensagem(f"❌ Item '{item_obj.nome}' não está disponível para empréstimo (status: {item_obj.status}).")
            return
            
        sucesso = self.db_model.emprestar_item(item_id, usuario_id, id_local_emprestimo, dias_previstos)

        if sucesso:
            self.view.mostrar_mensagem(f"✅ Empréstimo do item '{item_obj.nome}' (Patrimônio: {item_obj.patrimonio}) registrado com sucesso!")
            
            self.historico.registrar_historico(
                tipo_evento="EMPRESTIMO",
                detalhes={
                    "item_id": item_id,
                    "item_nome": item_obj.nome,
                    "usuario_id": usuario_id,
                    # Correção do erro de digitação de datetime
                    "data_prevista": (datetime.datetime.now() + datetime.timedelta(days=dias_previstos)).strftime("%Y-%m-%d")
                }
            )
        else:
            self.view.mostrar_mensagem("❌ Erro ao registrar o empréstimo. Transação desfeita (rollback).")

    def finalizar_app(self):
        """Fecha a conexão e encerra o aplicativo."""
        self.running = False
        if self.db_conn:
            self.db_conn.close()
        self.view.mostrar_mensagem("Aplicação encerrada. Conexão com o DB fechada.")
   
    def obter_categorias(self):
        return self.db_model.listar_todas_categorias() 

    def obter_item_por_patrimonio(self, patrimonio):
        return self.db_model.obter_item_por_patrimonio(patrimonio)
    

class inventarioController:
    def __init__(self, db_conn):
        if db_conn is None:
            raise ValueError("Conexão com o banco de dados não pode ser nula.")
        self.db_conn = db_conn
        # Inicializa o Model de persistência
        self.db_model = conexaobanco_model(self.db_conn)
        
    def autenticar_usuario_controller(self, matricula: str, senha_digitada: str):
        usuario_row = self.db_model.autenticar_usuario(matricula)

        if usuario_row:
            id_usuario, nome, matricula_bd, senha_hash_bd = usuario_row

            if senha_hash_bd == senha_digitada: 
                usuario = usuario_model(id_usuario, nome, matricula_bd)
                return usuario
            else:
                print("Tentativa de login falhou: Senha incorreta.") 
                return None
        else:
            print("Tentativa de login falhou: Matrícula não encontrada.")
            return None

    
    def gerenciar_devolucao(self, item_id):
        if not isinstance(item_id, int) or item_id <= 0:
            return {"status": "erro", "mensagem": "ID do item inválido fornecido."}, 400
            
        
        sucesso = self.db_model.devolucao_item(item_id)
        
        if sucesso:
            return {"status": "sucesso",
                    "mensagem": f"Item {item_id} devolvido e status atualizado."
                    }, 200
        else:
            return {"status": "erro",
                    "mensagem": f"Não foi possível registrar a devolução do item {item_id}. Transação desfeita (rollback)."
                    }, 500

    def cadastrar_novo_usuario_controller(self, nome: str, matricula: str, senha_texto_puro: str):
        if not nome or not matricula or not senha_texto_puro:
            return {"status": "erro", "mensagem": "Todos os campos (nome, matrícula, senha) são obrigatórios."}, 400
            
        novo_usuario_obj = usuario_model(
            id_usuario=None,
            nome=nome,
            matricula=matricula
        )
        setattr(novo_usuario_obj, 'senha', senha_texto_puro)
        
        sucesso = self.db_model.cadastrar_usuario(novo_usuario_obj)

        if sucesso:
            return {"status": "sucesso",
                    "mensagem": f"Usuário {nome} cadastrado com sucesso!"
                    }, 201
        else:
            return {"status": "erro",
                    "mensagem": f"Falha ao cadastrar usuário. A matrícula {matricula} pode já estar em uso."
                    }, 409