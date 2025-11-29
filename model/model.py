import json
import datetime
ARQUIVO="historico.json"
class usuario_model:
    """Representa a pessoa que pega o item ."""
    
    def __init__(self, id_usuario, nome, matricula):
        self.id = id_usuario
        self.nome = nome
        self.matricula = matricula
class item_model:
    """Classe que representa um filme no sistema de cinema"""
    
    def __init__(self, id_produto, nome_produto, numero_patrimonio, categoria_produto, localizacao_produto,status_produto ):
        """
        Inicializa um objeto Filme.
        Note que agora recebe 'sala_nome' diretamente da consulta SQL (JOIN).
        """
        self.id = id_produto
        self.nome = nome_produto
        self.patrimonio = numero_patrimonio
        self.tipo = categoria_produto
        self.localizacao = localizacao_produto
        self.status = status_produto
    @classmethod
    def from_db_row(cls, row):
        """Cria um objeto Filme a partir de uma tupla do banco de dados"""
        return cls(
            id_produto=row[0],
            nome_produto=row[1],
            numero_patrimonio=row[2],
            categoria_produto=row[3],
            localizacao_produto=row[4],
            status_produto=row[5]
        )
class movimentacaomodel:
    def __init__(self, id_movimentacao, item_id, usuario_id, data_emprestimo: datetime, data_devolucao_prevista: datetime, data_devolucao_real: datetime = None):
        self.id = id_movimentacao
        self.item_id = item_id      
        self.usuario_id = usuario_id
        self.data_emprestimo = data_emprestimo
        self.data_devolucao_prevista = data_devolucao_prevista
        self.data_devolucao_real = data_devolucao_real
     
class conexaobanco_model:
    def __init__(self,conn):
        """Recebe uma conexão com o banco de dados."""
        self.conn = conn
    def _executar_query(self, query, params=None, fetchone=False):
        """Função auxiliar para executar consultas."""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, params)
                if fetchone:
                    return cursor.fetchone()
                else:
                    return cursor.fetchall()
        except Exception as e:
            print(f"❌ Erro ao executar query: {e}")
            return None
    def obter_item_por_id(self, id_interno: int):
        """Retorna um objeto ItemModel específico pelo ID interno."""
        query = """
            SELECT id_produto, nome_produto, numero_patrimonio, categoria_produto, localizacao_produto, status_produto
            FROM produtos 
            WHERE id_produto = %s; 
        """
        row = self._executar_query(query, (id_interno,), fetchone=True)
        if row:
            return item_model.from_db_row(row)
        return "Item não encontrado"
    def devolucao_item(self,item_id):
        try:
            query_fechar = """
            UPDATE movimentacoes 
            SET data_devolucao_real = NOW() 
            WHERE item_id = %s AND data_devolucao_real IS NULL;
            """
            self._executar_query(query_fechar,(item_id,),commit=False)
            query_status_item= "UPDATE itens SET status = 'Disponível',localizacao_atual='Estoque' WHERE id=%s;"
            self._executar_query(query_status_item,(item_id,),commit=False)
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            return False
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
    def inserir_produto(self,item_obj):
        query="""
            INSERT INTO produtos(
                nome_produto,numero_patrimonio,categoria_produto,localizacao_produto,status_produto
                ) (VALUES %s,%s,%s,%s,%s);
            """
        parametros=(
            item_obj.nome,
            item_obj.patrimonio,
            item_obj.tipo,
            item_obj.localizacao,
            item_obj.status
            )
        try:
            self._executar_query(query , parametros, fetchone=False,commit=True)
            return True
        except Exception as e:
            self.conn.rollback()
            return False
    def cadastrar_usuario(self,usuario_obj):
        query="""
            INSERT INTO usuarios(
            usuario,matricula,senha
            ) VALUES(%s,%s,%s);
            """
        parametros=(
            usuario_obj.nome,
            usuario_obj.matricula,
            usuario_obj.senha
            )
        try:
            self._executar_query(query,parametros,fetchone=False,commit=True)
            return True
        except Exception as e:
            self.conn.rollback()
            return False

        


class historico:
    def __init__(self):
        pass
    @staticmethod
    def carregar_dados():
        dados_iniciais= {
            "eventos":[],
            "ultima_atualizacao":None
           }
        try:
            with open(ARQUIVO, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return dados_iniciais
        
        except json.JSONDecodeError:
            print ("erro")
            return dados_iniciais
           
    @staticmethod
    def registrar_historico(tipo_evento:str,detalhes:dict):
        dados=historico.carregar_dados()
        novo_registro={
            "timestamp": datetime.datetime.now().isoformat(),
            "tipo": tipo_evento,
            "detalhes": detalhes
        }
        dados["eventos"].append(novo_registro)
        dados["ultima_atualizacao"]=datetime.datetime.now().isoformat()
        try:
            with open (ARQUIVO,'w',encoding='utf-8') as f:
                json.dump(dados,f,indent=4)
                return True
        except Exception as e:
            print("erro",e)
            return False