import psycopg2
import datetime
from model import conexaobanco_model, item_model, usuario_model, historico 


class AppController:
    def __init__(self, db_model_class, view_instace, db_conn):
        self.db_conn = db_conn
        self.view = view_instace
        self.db_model = db_model_class(self.db_conn) 
        self.historico = historico 
        self.running = True
        
    def fazer_login(self, matricula: str, senha_digitada: str):
        dados_usuario = self.db_model.autenticar_usuario(matricula) 

        if dados_usuario is None:
            return False, "Matrícula não encontrada."

        senha_armazenada = dados_usuario[2]

        if senha_digitada == senha_armazenada: 
            usuario_logado = usuario_model(dados_usuario[0], dados_usuario[1], dados_usuario[2])
            return True, usuario_logado 
        else:
            return False, "Senha incorreta."
    
    def obter_categorias(self):
        return self.db_model.listar_todas_categorias()
        
    def listar_exemplares_por_categoria(self, nome_categoria: str):
        try:
            exemplares_db = self.db_model.listar_exemplares_por_categoria_db(nome_categoria) 
            return exemplares_db 
        except Exception as e:
            print(f"❌ Erro no Controller ao listar exemplares por categoria: {e}")
            return []
    
    def obter_item_por_patrimonio(self, patrimonio):
        return self.db_model.obter_item_por_patrimonio(patrimonio)
    
    def obter_nomes_itens(self):
        query = "SELECT nomes_itens FROM NOMES_ITENS ORDER BY nomes_itens;"
        rows = self.db_model._executar_query(query)
        return [row[0] for row in rows] if rows else []

    def obter_locais(self):
        query = """
            SELECT 
                id_locais,
                CONCAT(numero_sala, ' - ', nome_estrutura, ' - Pos. ', numero_posicao) 
            FROM LOCAIS 
            ORDER BY numero_sala;
        """
        rows = self.db_model._executar_query(query)
        
        if rows:
            return [{'id': row[0], 'descricao': row[1]} for row in rows]
        return []

    def obter_lista_usuarios(self):
        query = """
        SELECT 
            u.id_usuarios, 
            u.nomes_usuarios,
            jucp.id_juncao_usuario_cp,
            np.nomes_permissoes
        FROM 
            USUARIOS u
        JOIN JUNCAO_USUARIOS_CP jucp ON u.id_usuarios = jucp.id_usuarios
        JOIN JUNCAO_CARGOS_PERMISSOES jcp ON jucp.id_juncao_cargos_permissoes = jcp.id_juncao_cargos_permissoes
        JOIN NIVEL_PERMISSOES np ON jcp.id_nivel_permissoes = np.id_nivel_permissoes;
        """
        rows = self.db_model._executar_query(query)
        
        if rows:
            return [{
                "id": row[0],
                "nome": row[1],
                "matricula": row[2],
                "tipo": row[3]
            } for row in rows]
        return []
    
    def cadastrar_item_interface(self, nome_item: str, patrimonio: str, local_id: int):
        try:
            query_nome = "SELECT id_nomes_itens FROM NOMES_ITENS WHERE nomes_itens = %s LIMIT 1;"
            row_nome = self.db_model._executar_query(query_nome, (nome_item,), fetchone=True)
    
            if not row_nome:
                return {"status": "erro", "mensagem": f"Nome de item '{nome_item}' não encontrado no sistema."}
    
            nome_id = row_nome[0]
        
            novo_item = item_model(
                id_produto=None,
                nome_produto=nome_id,
                numero_patrimonio=patrimonio,
                categoria_produto=None,
                localizacao_produto=local_id, 
                status_produto=None
            )
    
            if self.db_model.inserir_produto(novo_item):
                return {
                    "status": "sucesso", 
                    "mensagem": f"Item '{nome_item}' com patrimônio '{patrimonio}' cadastrado com sucesso!"
                }
            else:
                return {
                    "status": "erro", 
                    "mensagem": "Falha ao cadastrar item. O patrimônio pode já estar em uso."
                }
        
        except Exception as e:
            return {"status": "erro", "mensagem": f"Erro ao cadastrar: {str(e)}"}
    
    def realizar_emprestimo(self, patrimonio: str, usuario_id: int):
        item_obj = self.db_model.obter_item_por_patrimonio(patrimonio)
        
        if not item_obj:
            return {"status": "erro", "mensagem": f"Item com patrimônio '{patrimonio}' não encontrado."}, 404
        
        if item_obj.status != 'DISPONÍVEL': 
            return {
                "status": "erro", 
                "mensagem": f"Item '{patrimonio}' não está disponível para empréstimo (status: {item_obj.status})."
            }, 400
            
        id_local_emprestimo = 3 
        dias_previstos = 7 
        
        sucesso = self.db_model.emprestar_item(
            item_id=item_obj.id,
            usuario_id=usuario_id, 
            id_local_emprestimo=id_local_emprestimo, 
            dias_previstos=dias_previstos
        )
        
        if sucesso:
            nome_usuario = self.db_model._obter_nome_usuario_por_id(usuario_id)
            
            self.historico.registrar_historico("EMPRÉSTIMO", {
                "patrimonio": patrimonio,
                "item_nome": item_obj.nome,
                "usuario": nome_usuario
            })
            return {"status": "sucesso", "mensagem": f"Item {patrimonio} emprestado com sucesso."}, 200
        else:
            return {"status": "erro", "mensagem": f"Não foi possível processar o empréstimo do item {patrimonio}."}, 500

    def gerenciar_devolucao(self, patrimonio: str):
        item_obj = self.db_model.obter_item_por_patrimonio(patrimonio)
    
        if not item_obj:
            return {"status": "erro", "mensagem": f"Item com patrimônio '{patrimonio}' não encontrado."}
    
        if item_obj.status not in ['EMPRESTADO', 'EM USO']:
            return {
            "status": "erro", 
            "mensagem": f"Item '{patrimonio}' não pode ser devolvido. Status atual: {item_obj.status}"
            }
    
        item_id = item_obj.id
    
        sucesso = self.db_model.devolucao_item(item_id)
    
        if sucesso:
            nome_usuario = self.view.usuario_logado.nome if self.view.usuario_logado else "Sistema"
            
            self.historico.registrar_historico("DEVOLUÇÃO", {
                "patrimonio": patrimonio,
                "item_nome": item_obj.nome,
                "usuario": nome_usuario
            })
            
            return {"status": "sucesso", "mensagem": f"Item {patrimonio} devolvido e status atualizado."}
        else:
            return {
                "status": "erro", 
                "mensagem": f"Não foi possível registrar a devolução do item {patrimonio}. Transação desfeita (rollback)."
            }
 
    def cadastrar_novo_usuario_controller(self, nome: str, matricula: str, senha_texto_puro: str):
        if not nome or not matricula or not senha_texto_puro:
            return {"status": "erro", "mensagem": "Todos os campos (nome, matrícula, senha) são obrigatórios."}
            
        novo_usuario_obj = usuario_model(
            id_usuarios=None,
            nomes_usuarios=matricula, 
            senhas_usuarios=senha_texto_puro
        )
        setattr(novo_usuario_obj, 'nome', nome) 
        
        sucesso = self.db_model.cadastrar_usuario(novo_usuario_obj)

        if sucesso:
            return {"status": "sucesso", "mensagem": f"Usuário {nome} ({matricula}) cadastrado com sucesso!"}
        else:
            return {"status": "erro", "mensagem": f"Falha ao cadastrar usuário. A matrícula {matricula} pode já estar em uso."}

    def excluir_produto_controller(self, patrimonio: str):
        if not patrimonio:
            return {"status": "erro", "mensagem": "Patrimônio não informado."}
        
        item_obj = self.db_model.obter_item_por_patrimonio(patrimonio)
        
        if not item_obj:
            return {"status": "erro", "mensagem": f"Item com patrimônio '{patrimonio}' não encontrado."}
        
        if item_obj.status == 'EMPRESTADO':
            return {"status": "erro", "mensagem": f"Não é possível excluir o item '{patrimonio}' pois está EMPRESTADO."}
        
        sucesso = self.db_model.deletar_produto(patrimonio)
        
        if sucesso:
            self.historico.registrar_historico("EXCLUSÃO DE ITEM", {
                "patrimonio": patrimonio,
                "item_nome": item_obj.nome
            })
            return {"status": "sucesso", "mensagem": f"Item '{patrimonio}' excluído com sucesso!"}
        else:
            return {"status": "erro", "mensagem": f"Falha ao excluir o item '{patrimonio}'."}
    
    def excluir_usuario_controller(self, usuario_id: int, nome_usuario: str):
        if not usuario_id:
            return {"status": "erro", "mensagem": "ID de usuário não informado."}
        
        if nome_usuario == "TI":
            return {"status": "erro", "mensagem": "Não é possível excluir o usuário TI do sistema."}
        
        sucesso = self.db_model.deletar_usuario(usuario_id)
        
        if sucesso:
            self.historico.registrar_historico("EXCLUSÃO DE USUÁRIO", {
                "usuario_id": usuario_id,
                "usuario_nome": nome_usuario
            })
            return {"status": "sucesso", "mensagem": f"Usuário '{nome_usuario}' excluído com sucesso!"}
        else:
            return {"status": "erro", "mensagem": f"Falha ao excluir o usuário '{nome_usuario}'."}
    
    def verificar_itens_emprestados_usuario(self, usuario_id: int):
        query = """
            SELECT COUNT(*) 
            FROM MOVIMENTACOES m
            JOIN JUNCAO_USUARIOS_CP jucp ON m.id_juncao_usuario_cp = jucp.id_juncao_usuario_cp
            WHERE jucp.id_usuarios = %s AND m.id_status = 2;
        """
        row = self.db_model._executar_query(query, (usuario_id,), fetchone=True)
        return row[0] if row else 0

    def obter_relatorio_status(self):
        query = """
        SELECT s.nomes_status, COUNT(i.id_itens) 
        FROM ITENS i
        JOIN STATUS s ON i.id_status = s.id_status
        GROUP BY s.nomes_status;
        """
        rows = self.db_model._executar_query(query)
        return dict(rows) if rows else {}

    def obter_historico_movimentacoes(self):
        dados_historico = historico.carregar_dados()
        return dados_historico.get('eventos', [])

    def finalizar_app(self):
        self.running = False
        if self.db_conn:
            try:
                self.db_conn.close()
                print("Conexão com DB fechada")
            except Exception as e:
                print(f"Erro ao fechar conexão: {e}")


class inventarioController:
    def __init__(self, db_conn):
        if db_conn is None:
            raise ValueError("Conexão com o banco de dados não pode ser nula.")
        self.db_conn = db_conn
        self.db_model = conexaobanco_model(self.db_conn)