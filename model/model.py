import json
import datetime
ARQUIVO="historico.json"
class usuario_model:
    """Classe que representa um filme no sistema de cinema"""
    def __init__(self, id_produto, nome_produto):
        self.id = id_produto
        self.nome = nome_produto
class usuario_model:
    """Representa a pessoa que pega o item emprestado (Professor)."""
    
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
        self.staus = status_produto
    @classmethod
    def from_db_row(cls, row):
        """Cria um objeto Filme a partir de uma tupla do banco de dados"""
        # (id_produto, nome_produto, numero_patrimonio, categoria_produto, localizacao_produto, status_produto)
        return cls(
            id_produto=row[0],
            nome_produto=row[1],
            numero_patrimonio=row[2],
            categoria_produto=row[3],
            localizacao_produto=row[4],
            status_produto=row[5]
        )
class MovimentacaoModel:
    def __init__(self, id_movimentacao, item_id, usuario_id, data_emprestimo: datetime, data_devolucao_prevista: datetime, data_devolucao_real: datetime = None):
        self.id = id_movimentacao
        self.item_id = item_id      
        self.usuario = usuario_id
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
    def obter_produto(self, id_produto):
        """Retorna um objeto Filme específico pelo ID, buscando do BD."""
        query = """
            SELECT f.id_produto, f.nome_produto, f.numero_patrimonio, f.categoria_produto, f.localizacao_produto, f.status_produto
            FROM produtos f
            JOIN dados s ON f.localizacao_produto = s.id
            WHERE f.id = %s;
        """
        row = self._executar_query(query, (id_produto,), fetchone=True)
        if row:
            return item_model.from_db_row(row)
        return "produto nao encontrado"
