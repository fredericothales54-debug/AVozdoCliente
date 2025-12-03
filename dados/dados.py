import os
import psycopg2
from psycopg2 import extras
from typing import List, Dict, Tuple, Any


# Objeto que faz a conexão com o BD


class DatabaseConnector:
    """ Gerencia a conexão e a execução de consultas no PostgreSQL. """
    def __init__(self):
        self.DB_NAME = os.environ.get("DB_NAME", "A_Voz_do_Cliente") 
        self.DB_USER = os.environ.get("DB_USER", "postgres") 
        self.DB_PASS = os.environ.get("DB_PASS", "sua_senha_secreta") # Senha
        self.DB_HOST = os.environ.get("DB_HOST", "localhost")
        self.DB_PORT = os.environ.get("DB_PORT", "5432")

        self._conn = None
        self._cursor = None
        self.connect()

    def connect(self):
        """ Estabelece a conexão com o PostgreSQL. """
        try:
            self._conn = psycopg2.connect(
                dbname=self.DB_NAME,
                user=self.DB_USER,
                password=self.DB_PASS,
                host=self.DB_HOST,
                port=self.DB_PORT
            )
            self._cursor = self._conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            print("INFO: Conexão com o PostgreSQL estabelecida com sucesso!")
        except psycopg2.Error as e:
            print(f"ERRO: Não foi possível conectar ao banco de dados '{self.DB_NAME}'.")
            print(f"Detalhes do erro: {e}")
            self._conn = None 

    def close(self):
        """ Fecha a conexão com o banco de dados. """
        if self._conn:
            self._conn.close()
            print("INFO: Conexão com o banco de dados fechada.")

    def execute(self, query: str, params: Tuple[Any, ...] = None, fetch: str = 'all') -> List[Dict] or Dict or int or None:
        """ 
        Executa uma consulta, manipulando transações e tratando erros. 
        'fetch' pode ser 'all', 'one', 'insert_returning' ou 'none' (para escrita sem retorno).
        """
        if not self._conn:
            return None

        try:
            self._cursor.execute(query, params)
            
            # --- Leitura (SELECT) ---
            if fetch == 'one':
                row = self._cursor.fetchone()
                return dict(row) if row else None
            elif fetch == 'all':
                return [dict(row) for row in self._cursor.fetchall()]
            
            # --- Escrita (INSERT/UPDATE/DELETE) ---
            self._conn.commit()
            
            # Verifica se é um INSERT que precisa retornar o ID
            if fetch == 'insert_returning':
                row = self._cursor.fetchone()
                return row[0] if row else None
                
            return True # Sucesso na escrita (fetch='none' implícito)

        except psycopg2.Error as e:
            self._conn.rollback()
            print(f"ERRO SQL: Falha na execução da query. {e}")
            return None
        except Exception as e:
            print(f"ERRO GERAL: Ocorreu um erro inesperado: {e}")
            return None


# Objeto que faz as consultas e inserções no BD


class Dados:
    """
    O objeto de acesso a dados (DAL) chamado pelo Model.py.
    TODOS os métodos aqui encapsulam a lógica de consulta/escrita SQL.
    """
    def __init__(self):
        self._db = DatabaseConnector()
        
    # Criação de Usuários
    
    def criar_usuario_e_senha(self, nome_usuario: str, senha_usuario: str) -> int or None:
        """
        [Criação de Usuário]
        Insere um novo usuário (nome e senha) na tabela USUARIOS.
        Retorna o id_usuarios gerado pelo banco.
        """
        query = """
            INSERT INTO USUARIOS (nomes_usuarios, senhas_usuarios)
            VALUES (%s, %s)
            RETURNING id_usuarios; 
        """
        return self._db.execute(query, (nome_usuario, senha_usuario), fetch='insert_returning')
    
    def listar_cargos(self) -> List[Dict] or None:
        """ 
        [Listagem de Cargos CORRIGIDA]
        Busca e retorna todos os IDs e nomes de cargos da tabela CARGOS.
        
        Retorna: Lista de dicionários com chaves 'id_cargos' e 'nomes_cargos'.
        """
        query = """
            SELECT id_cargos, nomes_cargos
            FROM CARGOS;
        """
        return self._db.execute(query, fetch='all')
    
    def atribuir_cargo_ao_usuario(self, id_usuario: int, id_juncao_cargos_permissoes: int) -> int or None:
        """
        [Atribuição de Cargo/Permissão CORRIGIDA]
        Cria o vínculo entre um usuário e um cargo/permissão específico.
        
        Retorna o id_juncao_usuario_cp gerado pelo banco.
        """
        query = """
            INSERT INTO JUNCAO_USUARIOS_CP (id_usuarios, id_juncao_cargos_permissoes)
            VALUES (%s, %s)
            RETURNING id_juncao_usuario_cp; 
        """
        return self._db.execute(query, (id_usuario, id_juncao_cargos_permissoes), fetch='insert_returning')
    
    
    def mostrar_usuario_criado(self, id_usuario: int) -> Dict or None:
        """
        [Busca de Usuário Completa CORRIGIDA]
        Busca nome, senha, cargo e o nome do nível de permissão associado ao usuário.

        Retorna um dicionário com os detalhes do usuário.
        """
        query = """
            SELECT
                u.nomes_usuarios,
                u.senhas_usuarios,
                np.nomes_permissoes AS nome_nivel_permissao,
                c.nomes_cargos AS nome_cargo
            FROM
                USUARIOS u
            LEFT JOIN 
                JUNCAO_USUARIOS_CP jucp ON u.id_usuarios = jucp.id_usuarios
            LEFT JOIN 
                JUNCAO_CARGOS_PERMISSOES jcperm ON jucp.id_juncao_cargos_permissoes = jcperm.id_juncao_cargos_permissoes
            LEFT JOIN
                NIVEL_PERMISSOES np ON jcperm.id_nivel_permissoes = np.id_nivel_permissoes
            LEFT JOIN
                CARGOS c ON jcperm.id_cargos = c.id_cargos
            WHERE
                u.id_usuarios = %s;
        """
        return self._db.execute(query, (id_usuario,), fetch='one')
            
    # Geração de Relatórios

    def obter_relatorio_total_inventario(self) -> List[Dict] or None:
        """
        [Relatório Total de Inventário]
        Busca o total de unidades por Nome de Item, agrupado por Categoria.
        Retorna: Lista de dicionários com chaves 'nomes_categorias', 'nomes_itens' e 'total_unidades'.
        """
        query = """
            SELECT
                C.nomes_categorias,
                NI.nomes_itens,
                COUNT(I.id_itens) AS total_unidades
            FROM 
                ITENS I
            JOIN 
                NOMES_ITENS NI ON I.id_nomes_itens = NI.id_nomes_itens
            JOIN 
                CATEGORIAS C ON NI.id_categorias = C.id_categorias
            GROUP BY 
                C.nomes_categorias, NI.nomes_itens
            ORDER BY 
                C.nomes_categorias, NI.nomes_itens;
        """
        return self._db.execute(query, fetch='all')
    
    def obter_relatorio_movimentacoes(self) -> List[Dict] or None:
        """
        [Relatório de Histórico de Movimentações]
        Busca o histórico de movimentação de itens.
        
        ATENÇÃO: Este relatório foi ajustado para usar as colunas existentes no seu DDL:
        - data -> M.data
        - quem moveu -> Usuário associado a M.id_juncao_usuario_cp
        - usuario_origem / usuario_destino -> Indisponíveis no DDL fornecido, 
          portanto, são retornados como N/A.
        
        Retorna: Lista de dicionários com chaves:
        - data_movimentacao
        - numero_patrimonio
        - nomes_itens
        - nomes_status (o novo status do item após a movimentação)
        - usuario_executor
        """
        query = """
            SELECT
                M.data AS data_movimentacao,
                I.numero_patrimonio,
                NI.nomes_itens,
                S.nomes_status, -- Adicionado o status resultante da movimentação
                U.nomes_usuarios AS usuario_executor
            FROM
                MOVIMENTACOES M
            JOIN
                ITENS I ON M.id_itens = I.id_itens
            JOIN
                NOMES_ITENS NI ON I.id_nomes_itens = NI.id_nomes_itens
            JOIN
                STATUS S ON M.id_status = S.id_status
            JOIN
                JUNCAO_USUARIOS_CP JUC ON M.id_juncao_usuario_cp = JUC.id_juncao_usuario_cp
            JOIN
                USUARIOS U ON JUC.id_usuarios = U.id_usuarios
            ORDER BY
                M.data DESC;
        """
        return self._db.execute(query, fetch='all')
    
    def obter_relatorio_disponibilidade_itens(self) -> List[Dict] or None:
        """
        [Relatório de Disponibilidade de Itens]
        Busca o status atual e a contagem de itens, agrupando por Categoria,
        Nome do Item e Status.
        
        Retorna: Lista de dicionários com chaves:
        - nomes_categorias
        - nomes_itens
        - nomes_status
        - total_unidades (quantidade de itens naquele status)
        """
        query = """
            SELECT
                C.nomes_categorias,
                NI.nomes_itens,
                S.nomes_status,
                COUNT(I.id_itens) AS total_unidades
            FROM 
                ITENS I
            JOIN 
                NOMES_ITENS NI ON I.id_nomes_itens = NI.id_nomes_itens
            JOIN 
                CATEGORIAS C ON NI.id_categorias = C.id_categorias
            JOIN 
                STATUS S ON I.id_status = S.id_status -- Junta pelo status atual do item
            GROUP BY 
                C.nomes_categorias, NI.nomes_itens, S.nomes_status
            ORDER BY 
                C.nomes_categorias, NI.nomes_itens, S.nomes_status;
        """
        return self._db.execute(query, fetch='all')