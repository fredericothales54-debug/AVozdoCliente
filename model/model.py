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
    def _executar_query(self, query, params=None, fetchone=False,commit=False):
        """Função auxiliar para executar consultas."""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, params)
                if commit:
                    self.conn.commit()
                    return True
                if fetchone:
                    return cursor.fetchone()
                else:
                    return cursor.fetchall()
        except Exception as e:
            if commit:
                self.conn.rollback()
            print(f" Erro de query: {e}")
            return None 
    def obter_item_por_id(self, id_interno: int):
        query = """
            SELECT
                i.id_itens,
                ni.nomes_itens, -- nome_produto
                i.numero_patrimonio,
                'N/A', -- categoria_produto (placeholder)
                CONCAT(l.numero_sala, ' - ', l.numero_posicao), -- localizacao_produto
                s.nome_status -- status_produto
            FROM
                ITENS i
            JOIN
                NOMES_ITENS ni ON i.id_nomes = ni.id_nomes
            JOIN
                STATUS s ON i.id_status = s.id_status
            JOIN
                LOCAIS l ON i.id_locais = l.id_locais
            WHERE
                i.id_itens = %s;
            """
        row = self._executar_query(query, (id_interno,), fetchone=True)
        if row:
            return item_model.from_db_row(row)
        return "Item não encontrado"
    def devolucao_item(self,item_id):
        try:
            query_fechar = """
            UPDATE MOVIMENTACOES 
            SET data_devolucao_real = NOW() 
            WHERE id_itens = %s AND data_devolucao_real IS NULL;
            """
            self._executar_query(query_fechar,(item_id,),commit=False)
            query_status_item= """
                UPDATE ITENS 
                SET id_status = 1, id_locais = 1 
                WHERE id_itens = %s;
            """
            self._executar_query(query_status_item,(item_id,),commit=False)
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            return False
    def autenticar_usuario(self,matricula:str):
        query = """
            SELECT id_usuario, nome, matricula, senha
            FROM USUARIOS 
            WHERE matricula = %s; 
        """
        row = self._executar_query(query, (matricula,), fetchone=True)
        if row:
            return (row)
        return None
    def inserir_produto(self,item_obj):
        query="""
            INSERT INTO ITENS(
                id_nomes, 
                numero_patrimonio, 
                id_status,
                id_locais
                ) VALUES (%s, %s, %s, %s);
            """
        parametros=(
            item_obj.nome,
            item_obj.patrimonio,
            item_obj.status,
            item_obj.localizacao
            )
        try:
            self._executar_query(query , parametros, fetchone=False,commit=True)
            return True
        except Exception as e:
            self.conn.rollback()
            return False
    def cadastrar_usuario(self,usuario_obj):
        query="""
            INSERT INTO USUARIOS(
            nome,matricula,senha
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
    def emprestar_item(self, item_id: int, usuario_id: int, id_local_emprestimo: int, dias_previstos: int = 7):
        data_emprestimo = datetime.datetime.now()
        data_devolucao_prevista = data_emprestimo + datetime.timedelta(days=dias_previstos)
        
        query_movimentacao = """
            INSERT INTO MOVIMENTACOES (id_itens, id_usuarios, data, data_devolucao_prevista)
            VALUES (%s, %s, %s, %s);
        """
        params_movimentacao = (item_id, usuario_id, data_emprestimo, data_devolucao_prevista)

       
        query_status_item = """
            UPDATE ITENS
            SET id_status = 2, 
                id_locais = %s 
            WHERE id_itens = %s;
        """
        params_status_item = (id_local_emprestimo, item_id)
        
        try:
            self._executar_query(query_movimentacao, params_movimentacao, commit=False)
            
            self._executar_query(query_status_item, params_status_item, commit=False)
            
            self.conn.commit()
            return True
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Erro na transação de empréstimo: {e}")
            return False
    def listar_itens_disponiveis(self):
        query = """
            SELECT
                i.id_itens,
                ni.nomes_itens, 
                i.numero_patrimonio,
                'N/A', -- Categoria Produto (Placeholder)
                CONCAT(l.numero_sala, ' - ', l.numero_posicao, ' (', l.nome_estrutura, ')'), 
                s.nome_status
            FROM
                ITENS i
            JOIN
                NOMES_ITENS ni ON i.id_nomes = ni.id_nomes
            JOIN
                STATUS s ON i.id_status = s.id_status
            JOIN
                LOCAIS l ON i.id_locais = l.id_locais
            WHERE
                i.id_status = 1; -- Filtra apenas por 'DISPONÍVEL'
        """
        
        rows = self._executar_query(query)
        
        if rows:
            return [item_model.from_db_row(row) for row in rows]
            
        return [] 
        


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