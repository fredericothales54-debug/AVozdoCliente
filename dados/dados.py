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
    
    def verificar_credenciais(self, nome_usuario: str, senha: str) -> Optional[Dict[str, Any]]:
        """
        [Verificação de Credenciais para Login]
        Verifica se existe um usuário com o nome E a senha fornecidos.

        Retorna: 
        - Um dicionário com os dados essenciais do usuário (ex: ID e nome) se as credenciais forem válidas.
        - None (simulando "linha de erro") se o usuário/senha não for encontrado.
        """
        query = """
            SELECT 
                id_usuarios, nomes_usuarios
            FROM 
                USUARIOS
            WHERE 
                nomes_usuarios = %s AND senhas_usuarios = %s;
        """
        # Usamos fetch='one' para buscar apenas uma linha.
        usuario_encontrado = self._db.execute(query, (nome_usuario, senha), fetch='one')
        
        if usuario_encontrado:
            # Retorna os dados do usuário encontrado.
            return dict(usuario_encontrado)
        else:
            # Retorna None se não houver match.
            print(f"ERRO: Tentativa de login falhou para o usuário '{nome_usuario}'.")
            return None

    def listar_cargos(self) -> Optional[List[Dict[str, Any]]]:
        """
        [Listagem de Cargos]
        Busca apenas os nomes e IDs da tabela CARGOS para exibir uma lista limpa.
        O ID retornado é o id_cargos, que é mapeado para id_juncao_cargos_permissoes 
        na função de atribuição, usando a suposição de que eles são os mesmos neste contexto.
        """
        query = """
            SELECT id_cargos, nomes_cargos 
            FROM CARGOS;
        """
        return self._db.execute(query, fetch='all')

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
    
    def atribuir_cargo_ao_usuario(self, id_usuario: int, id_juncao_cargos_permissoes: int) -> int or None:
        """
        [Atribuição de Cargo/Permissão]
        Recebe o ID do Usuário (automático da função de criação) e o ID de Junção de Cargos/Permissões.
        Insere o id_juncao_cargos_permissoes diretamente na tabela JUNCAO_USUARIOS_CP.

        Parâmetros:
        - id_usuario: O ID do usuário RECÉM-CRIADO.
        - id_juncao_cargos_permissoes: O ID da junção (obtido da lista de cargos simples ou de uma etapa de mapeamento anterior).

        Retorna o id_juncao_usuario_cp gerado após a inserção.
        """
        
        # O valor recebido (id_juncao_cargos_permissoes) é usado diretamente na query.
        query = """
            INSERT INTO JUNCAO_USUARIOS_CP (id_usuarios, id_juncao_cargos_permissoes)
            VALUES (%s, %s)
            RETURNING id_juncao_usuario_cp; 
        """
        return self._db.execute(query, (id_usuario, id_juncao_cargos_permissoes), fetch='insert_returning')
    
    def mostrar_usuario_criado(self, id_usuario: int) -> Dict or None:
        """
        [Busca de Usuário Completa]
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
    
    # Realizar Movimentações

    def nomear_item_novo(self, nome_item: str, id_categoria: int) -> int or str or None:
        """
        [Criação de Itens com Validação]
        1. Verifica se o nome do item já existe.
        2. Se existir, retorna a mensagem "JÁ EXISTE".
        3. Se não existir, insere o novo nome de item e o ID da categoria.

        Retorna: O id_nomes_itens (int) gerado se for sucesso, a string "JÁ EXISTE" se o nome já existir, 
                 ou None em caso de outro erro SQL.
        """
        # 1. VERIFICAÇÃO DE EXISTÊNCIA
        check_query = """
            SELECT id_nomes_itens
            FROM NOMES_ITENS 
            WHERE nomes_itens = %s;
        """
        item_existente = self._db.execute(check_query, (nome_item,), fetch='one')
        
        if item_existente:
            # 2. Se existir, retorna a mensagem de erro específica
            print(f"AVISO: O nome do item '{nome_item}' já existe no banco de dados.")
            return "JÁ EXISTE"

        # 3. INSERÇÃO SE NÃO EXISTE
        insert_query = """
            INSERT INTO NOMES_ITENS (nomes_itens, id_categorias)
            VALUES (%s, %s)
            RETURNING id_nomes_itens; 
        """
        return self._db.execute(insert_query, (nome_item, id_categoria), fetch='insert_returning')
    
    def listar_categorias(self) -> List[Dict] or None:
        """
        [Busca de Categorias]
        Busca e retorna todos os IDs e nomes das categorias.

        Retorna: Lista de dicionários com chaves 'id_categorias' e 'nomes_categorias'.
        O ID é necessário para vincular o novo item à categoria no BD.
        """
        query = """
            SELECT id_categorias, nomes_categorias
            FROM CATEGORIAS;
        """
        return self._db.execute(query, fetch='all')
    
    def atribuir_categoria(self, id_nomes_itens: int, id_categorias: int) -> int or str or None:
        """
        [Atualização de Categoria de Item]
        Atualiza o campo id_categorias de um item específico na tabela NOMES_ITENS.

        Parâmetros:
        - id_nomes_itens (int): O ID do nome do item a ser atualizado.
        - id_categorias (int): O ID da nova categoria a ser atribuída.

        Retorna: O número de linhas afetadas (int > 0) se for sucesso, 
                 ou None / string de erro se falhar (ex: FOREIGN_KEY_ERROR).
        """
        query = """
            UPDATE NOMES_ITENS
            SET id_categorias = %s
            WHERE id_nomes_itens = %s;
        """
        return self._db.execute(query, (id_categorias, id_nomes_itens), fetch='none')
    
    def atribuir_patrimonio(self, numero_patrimonio: str, id_nomes_itens: int) -> int or str or None:
        """
        [Criação de Item Físico (Patrimônio)]
        Insere um novo item físico na tabela ITENS com o número de patrimônio e 
        vinculado a um Nome de Item, definindo o status inicial como 'DISPONÍVEL' (id_status=1).
        
        OBS: Pressupõe que o ID 1 na tabela STATUS é 'DISPONÍVEL'.

        Retorna: O id_itens (int) gerado se for sucesso, ou string de erro.
        """
        # O status inicial é 1 (DISPONÍVEL), o local inicial é 1 (ESTOQUE)
        # Note que a coluna id_locais na tabela ITENS não é NOT NULL no seu esquema, mas a id_status é.
        query = """
            INSERT INTO ITENS (id_nomes_itens, numero_patrimonio, id_status)
            VALUES (%s, %s, 1) 
            RETURNING id_itens; 
        """
        return self._db.execute(query, (id_nomes_itens, numero_patrimonio), fetch='insert_returning')
    
    def listar_status(self) -> List[Dict] or None:
        """ 
        [Listagem de Status]
        Busca e retorna todos os IDs e nomes de status de itens da tabela STATUS.
        
        Retorna: Lista de dicionários com chaves 'id_status' e 'nomes_status'.
        """
        query = """
            SELECT id_status, nomes_status
            FROM STATUS;
        """
        return self._db.execute(query, fetch='all')
    
    def atribuir_status(self, id_itens: int, id_status: int) -> int or str or None:
        """
        [Atualização de Status de Item Físico]
        Atualiza o campo id_status de um item específico na tabela ITENS.

        Retorna: O número de linhas afetadas (int > 0) se for sucesso, 
                 ou None / string de erro se falhar (ex: FOREIGN_KEY_ERROR).
        """
        query = """
            UPDATE ITENS
            SET id_status = %s
            WHERE id_itens = %s;
        """
        return self._db.execute(query, (id_status, id_itens), fetch='none')