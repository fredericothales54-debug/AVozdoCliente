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
        dados = self.db_model.autenticar_usuario(matricula) 

        if dados is None:
            return False, "Matrícula não encontrada."

        senha_db = dados[2]

        if senha_digitada == senha_db: 
            usr = usuario_model(dados[0], dados[1], dados[2])
            return True, usr 
        else:
            return False, "Senha incorreta."
    
    def obter_categorias(self):
        return self.db_model.listar_todas_categorias()
        
    def listar_exemplares_por_categoria(self, nome_cat: str):
        try:
            ex = self.db_model.listar_exemplares_por_categoria_db(nome_cat) 
            return ex 
        except Exception as e:
            print(f"erro listar exemplares: {e}")
            return []
    
    def obter_item_por_patrimonio(self, pat):
        return self.db_model.obter_item_por_patrimonio(pat)
    
    def obter_nomes_itens(self):
        q = "SELECT nomes_itens FROM NOMES_ITENS ORDER BY nomes_itens;"
        r = self.db_model._executar_query(q)
        return [row[0] for row in r] if r else []

    def obter_locais(self):
        q = """
            SELECT 
                id_locais,
                CONCAT(numero_sala, ' - ', nome_estrutura, ' - Pos. ', numero_posicao) 
            FROM LOCAIS 
            ORDER BY numero_sala;
        """
        r = self.db_model._executar_query(q)
        
        if r:
            return [{'id': row[0], 'descricao': row[1]} for row in r]
        return []

    def obter_lista_usuarios(self):
        q = """
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
        r = self.db_model._executar_query(q)
        
        if r:
            return [{
                "id": row[0],
                "nome": row[1],
                "matricula": row[2],
                "tipo": row[3]
            } for row in r]
        return []
    
    def cadastrar_item_interface(self, nome_item: str, pat: str, local_id: int):
        try:
            q = "SELECT id_nomes_itens FROM NOMES_ITENS WHERE nomes_itens = %s LIMIT 1;"
            r = self.db_model._executar_query(q, (nome_item,), fetchone=True)
    
            if not r:
                return {"status": "erro", "mensagem": f"Nome '{nome_item}' nao existe."}
    
            nome_id = r[0]
        
            item_novo = item_model(
                id_produto=None,
                nome_produto=nome_id,
                numero_patrimonio=pat,
                categoria_produto=None,
                localizacao_produto=local_id, 
                status_produto=None
            )
    
            if self.db_model.inserir_produto(item_novo):
                return {
                    "status": "sucesso", 
                    "mensagem": f"Item '{nome_item}' patrimonio '{pat}' cadastrado!"
                }
            else:
                return {
                    "status": "erro", 
                    "mensagem": "Falhou. Patrimonio ja existe?"
                }
        
        except Exception as e:
            return {"status": "erro", "mensagem": f"Erro: {str(e)}"}
    
    def realizar_emprestimo(self, pat: str, user_id: int):
        item = self.db_model.obter_item_por_patrimonio(pat)
        
        if not item:
            return {"status": "erro", "mensagem": f"Item '{pat}' nao achado."}, 404
        
        if item.status != 'DISPONÍVEL': 
            return {
                "status": "erro", 
                "mensagem": f"Item '{pat}' nao disponivel (status: {item.status})."
            }, 400
            
        local_emp = 3 
        dias = 7 
        
        ok = self.db_model.emprestar_item(
            item_id=item.id,
            usuario_id=user_id, 
            id_local_emprestimo=local_emp, 
            dias_previstos=dias
        )
        
        if ok:
            nome = self.db_model._obter_nome_usuario_por_id(user_id)
            
            self.historico.registrar_historico("EMPRÉSTIMO", {
                "patrimonio": pat,
                "item_nome": item.nome,
                "usuario": nome
            })
            return {"status": "sucesso", "mensagem": f"Item {pat} emprestado!"}, 200
        else:
            return {"status": "erro", "mensagem": f"Nao deu pra emprestar {pat}."}, 500

    def gerenciar_devolucao(self, pat: str):
        item = self.db_model.obter_item_por_patrimonio(pat)
    
        if not item:
            return {"status": "erro", "mensagem": f"Item '{pat}' nao achado."}
    
        if item.status not in ['EMPRESTADO', 'EM USO']:
            return {
            "status": "erro", 
            "mensagem": f"Item '{pat}' nao pode devolver. Status: {item.status}"
            }
    
        ok = self.db_model.devolucao_item(item.id)
    
        if ok:
            nome = self.view.usuario_logado.nome if self.view.usuario_logado else "Sistema"
            
            self.historico.registrar_historico("DEVOLUÇÃO", {
                "patrimonio": pat,
                "item_nome": item.nome,
                "usuario": nome
            })
            
            return {"status": "sucesso", "mensagem": f"Item {pat} devolvido!"}
        else:
            return {
                "status": "erro", 
                "mensagem": f"Nao deu pra devolver {pat}."
            }
 
    def cadastrar_novo_usuario_controller(self, nome: str, mat: str, senha: str):
        if not nome or not mat or not senha:
            return {"status": "erro", "mensagem": "Preencha tudo."}
            
        usr_novo = usuario_model(
            id_usuarios=None,
            nomes_usuarios=mat, 
            senhas_usuarios=senha
        )
        setattr(usr_novo, 'nome', nome) 
        
        ok = self.db_model.cadastrar_usuario(usr_novo)

        if ok:
            return {"status": "sucesso", "mensagem": f"Usuario {nome} ({mat}) cadastrado!"}
        else:
            return {"status": "erro", "mensagem": f"Falhou. Matricula {mat} ja existe?"}

    def excluir_produto_controller(self, pat: str):
        if not pat:
            return {"status": "erro", "mensagem": "Sem patrimonio."}
        
        item = self.db_model.obter_item_por_patrimonio(pat)
        
        if not item:
            return {"status": "erro", "mensagem": f"Item '{pat}' nao existe."}
        
        if item.status == 'EMPRESTADO':
            return {"status": "erro", "mensagem": f"Item '{pat}' emprestado, nao da pra apagar."}
        
        ok = self.db_model.deletar_produto(pat)
        
        if ok:
            self.historico.registrar_historico("EXCLUSÃO DE ITEM", {
                "patrimonio": pat,
                "item_nome": item.nome
            })
            return {"status": "sucesso", "mensagem": f"Item '{pat}' apagado!"}
        else:
            return {"status": "erro", "mensagem": f"Falhou apagar '{pat}'."}
    
    def excluir_usuario_controller(self, user_id: int, nome: str):
        if not user_id:
            return {"status": "erro", "mensagem": "Sem ID."}
        
        if nome == "TI":
            return {"status": "erro", "mensagem": "Nao da pra apagar TI."}
        
        ok = self.db_model.deletar_usuario(user_id)
        
        if ok:
            self.historico.registrar_historico("EXCLUSÃO DE USUÁRIO", {
                "usuario_id": user_id,
                "usuario_nome": nome
            })
            return {"status": "sucesso", "mensagem": f"Usuario '{nome}' apagado!"}
        else:
            return {"status": "erro", "mensagem": f"Falhou apagar '{nome}'."}
    
    def verificar_itens_emprestados_usuario(self, user_id: int):
        q = """
            SELECT COUNT(*) 
            FROM MOVIMENTACOES m
            JOIN JUNCAO_USUARIOS_CP jucp ON m.id_juncao_usuario_cp = jucp.id_juncao_usuario_cp
            WHERE jucp.id_usuarios = %s AND m.id_status = 2;
        """
        r = self.db_model._executar_query(q, (user_id,), fetchone=True)
        return r[0] if r else 0

    def obter_relatorio_status(self):
        q = """
        SELECT s.nomes_status, COUNT(i.id_itens) 
        FROM ITENS i
        JOIN STATUS s ON i.id_status = s.id_status
        GROUP BY s.nomes_status;
        """
        r = self.db_model._executar_query(q)
        return dict(r) if r else {}

    def obter_historico_movimentacoes(self):
        dados = historico.carregar_dados()
        return dados.get('eventos', [])

    def finalizar_app(self):
        self.running = False
        if self.db_conn:
            try:
                self.db_conn.close()
                print("db fechado")
            except Exception as e:
                print(f"erro fechar: {e}")


class inventarioController:
    def __init__(self, db_conn):
        if db_conn is None:
            raise ValueError("db nao pode ser None")
        self.db_conn = db_conn
        self.db_model = conexaobanco_model(self.db_conn)