import os
import psycopg2
from psycopg2 import extras
from typing import List, Dict, Tuple, Any, Optional
from datetime import datetime


# ==============================================================================================================================# 
# Objeto que faz a conexão com o BD
# ==============================================================================================================================# 


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


# ==============================================================================================================================# 
# Objeto que faz as consultas e inserções no BD
# ==============================================================================================================================# 


class Dados:
    """
    O objeto de acesso a dados (DAL) chamado pelo Model.py.
    TODOS os métodos aqui encapsulam a lógica de consulta/escrita SQL.
    """
    def __init__(self):
        self._db = DatabaseConnector()
     
    # ==============================================================================================================================#   
    # Criação de Usuários
    # ==============================================================================================================================#
    
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

    # ==============================================================================================================================#    
    # Geração de Relatórios
    # ==============================================================================================================================# 

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
    
    # ==============================================================================================================================# 
    # Realizar Consultas
    # ==============================================================================================================================# 
    
    def listar_categorias(self) -> List[Dict] or None:
        """
        [Passo 1: Listar Categorias]
        Busca todos os nomes e IDs da tabela CATEGORIAS.
        Usado para a primeira tela de seleção.

        Retorna: Lista de dicionários (id_categorias, nomes_categorias).
        """
        query = """
            SELECT
                id_categorias, nomes_categorias
            FROM 
                CATEGORIAS
            ORDER BY 
                nomes_categorias;
        """
        return self._db.execute(query, fetch='all')

    def listar_itens_por_categoria(self, id_categoria: int) -> List[Dict] or None:
        """
        [Passo 2: Listar Itens por Categoria com Quantidade]
        Busca o nome e a contagem total de unidades (ITENS) para uma Categoria específica.
        
        Parâmetros:
        - id_categoria: ID da categoria selecionada pelo usuário.

        Retorna: Lista de dicionários (id_nomes_itens, nomes_itens, total_unidades).
        """
        query = """
            SELECT
                NI.id_nomes_itens,
                NI.nomes_itens,
                COUNT(I.id_itens) AS total_unidades
            FROM 
                NOMES_ITENS NI
            JOIN 
                ITENS I ON NI.id_nomes_itens = I.id_nomes_itens
            WHERE 
                NI.id_categorias = %s
            GROUP BY 
                NI.id_nomes_itens, NI.nomes_itens
            ORDER BY 
                NI.nomes_itens;
        """
        return self._db.execute(query, (id_categoria,), fetch='all')

    def listar_detalhes_itens_por_nome(self, id_nomes_itens: int) -> Optional[List[Dict]]:
        """
        [Passo 3: Listar Detalhes de Unidades]
        Busca todos os detalhes de cada unidade física (ITENS), incluindo status e localização atual.
        
        NOTA: A query foi simplificada para usar o campo ITENS.id_locais para a localização atual,
        o que é mais eficiente do que recalcular a localização a partir do histórico MOVIMENTACOES.

        Retorna: Lista de dicionários (numero_patrimonio, nomes_status, local_atual_completo).
        """
        query = """
            SELECT
                I.numero_patrimonio,
                S.nomes_status,
                -- Usa o estado atual (ITENS.id_locais). Se for NULL (item 'EM USO'),
                -- exibe uma mensagem indicando que está com um usuário.
                COALESCE(
                    L.nome_estrutura || ' - Sala ' || L.numero_sala || ' - Pos. ' || L.numero_posicao,
                    CASE WHEN S.nomes_status = 'EM USO' THEN 'Com Usuário (Movimentado)' ELSE 'Local Desconhecido' END
                ) AS local_atual_completo
            FROM 
                ITENS I
            JOIN
                NOMES_ITENS NI ON I.id_nomes_itens = NI.id_nomes_itens
            JOIN
                STATUS S ON I.id_status = S.id_status
            LEFT JOIN -- LEFT JOIN necessário pois id_locais pode ser NULL
                LOCAIS L ON I.id_locais = L.id_locais
            WHERE 
                I.id_nomes_itens = %s
            ORDER BY 
                I.numero_patrimonio;
        """
        return self._db.execute(query, (id_nomes_itens,), fetch='all')
    
    # ==============================================================================================================================# 
    # Realizar Movimentações
    # ==============================================================================================================================#  

    def _obter_id_status(self, nome_status: str) -> Optional[int]:
        """
        [Função Auxiliar]
        Busca o ID de um status pelo seu nome (ex: 'EM USO' ou 'DISPONÍVEL').
        """
        query = "SELECT id_status FROM STATUS WHERE nomes_status = %s;"
        resultado = self._db.execute(query, (nome_status,), fetch='one')
        return resultado['id_status'] if resultado else None

    def listar_itens_por_categorias_disponivel(self, id_categoria: int) -> List[Dict] or None:
        """
        [Passo 1] Lista todos os Nomes de Itens (agrupados) de uma categoria
        que possuam pelo menos uma unidade com o status 'DISPONÍVEL'.

        Parâmetros:
        - id_categoria: ID da categoria selecionada.

        Retorna: Lista de dicionários (id_nomes_itens, nomes_itens, total_disponivel).
        """
        id_disponivel = self._obter_id_status('DISPONÍVEL')
        if id_disponivel is None:
            print("ERRO: Status 'DISPONÍVEL' não encontrado.")
            return []

        query = """
            SELECT
                NI.id_nomes_itens,
                NI.nomes_itens,
                COUNT(I.id_itens) AS total_disponivel
            FROM
                ITENS I
            JOIN
                NOMES_ITENS NI ON I.id_nomes_itens = NI.id_nomes_itens
            WHERE
                NI.id_categorias = %s AND I.id_status = %s
            GROUP BY
                NI.id_nomes_itens, NI.nomes_itens
            ORDER BY
                NI.nomes_itens;
        """
        return self._db.execute(query, (id_categoria, id_disponivel), fetch='all')

    def listar_itens_por_nome_e_disponivel(self, id_nomes_itens: int) -> List[Dict] or None:
        """
        [Passo 2] Lista as unidades físicas (patrimônio) de um Nome de Item
        que estão com o status 'DISPONÍVEL', mostrando sua localização atual.
        
        O usuário seleciona um item específico para a movimentação.

        Parâmetros:
        - id_nomes_itens: ID do nome do item (ex: 'Notebook Core i3').

        Retorna: Lista de dicionários (id_itens, numero_patrimonio, local_atual_completo).
        """
        id_disponivel = self._obter_id_status('DISPONÍVEL')
        if id_disponivel is None:
            print("ERRO: Status 'DISPONÍVEL' não encontrado.")
            return []
            
        query = """
            SELECT
                I.id_itens,
                I.numero_patrimonio,
                CONCAT(L.nome_estrutura, ' - ', L.numero_sala, ' - Pos. ', L.numero_posicao) AS local_atual_completo
            FROM
                ITENS I
            LEFT JOIN
                LOCAIS L ON I.id_locais = L.id_locais
            WHERE
                I.id_nomes_itens = %s AND I.id_status = %s
            ORDER BY
                I.numero_patrimonio;
        """
        return self._db.execute(query, (id_nomes_itens, id_disponivel), fetch='all')
        
    def listar_usuarios(self) -> List[Dict] or None:
        """
        [Passo 3] Lista todos os usuários e seus cargos para seleção do receptor.
        
        O usuário seleciona para quem o item será movimentado.

        Retorna: Lista de dicionários (id_juncao_usuario_cp, nomes_usuarios, nomes_cargos).
        """
        query = """
            SELECT
                JUC.id_juncao_usuario_cp,
                U.nomes_usuarios,
                C.nomes_cargos
            FROM
                JUNCAO_USUARIOS_CP JUC
            JOIN
                USUARIOS U ON JUC.id_usuarios = U.id_usuarios
            JOIN
                JUNCAO_CARGOS_PERMISSOES JCP ON JUC.id_juncao_cargos_permissoes = JCP.id_juncao_cargos_permissoes
            JOIN
                CARGOS C ON JCP.id_cargos = C.id_cargos
            ORDER BY
                U.nomes_usuarios;
        """
        return self._db.execute(query, fetch='all')
        
    def mostrar_movimentacao_preview(self, id_item: int, id_juncao_cp_receptor: int) -> Dict[str, Any] or None:
        """
        [Passo 4] Busca os detalhes dos IDs selecionados para que o usuário possa revisar
        a movimentação antes de confirmá-la.

        Parâmetros:
        - id_item: ID da unidade física do item (id_itens).
        - id_juncao_cp_receptor: ID da junção do usuário que receberá o item.

        Retorna: Dicionário com (item_nome, patrimonio_numero, receptor_nome_completo) ou None.
        """
        preview_data = {}
        
        # Detalhes do Item
        item_query = """
            SELECT
                NI.nomes_itens,
                I.numero_patrimonio
            FROM
                ITENS I
            JOIN
                NOMES_ITENS NI ON I.id_nomes_itens = NI.id_nomes_itens
            WHERE
                I.id_itens = %s;
        """
        item_data = self._db.execute(item_query, (id_item,), fetch='one')
        if item_data:
            preview_data['item_nome'] = item_data['nomes_itens']
            preview_data['patrimonio_numero'] = item_data['numero_patrimonio']
        else:
            return None
            
        # Detalhes do Receptor
        receptor_query = """
            SELECT
                U.nomes_usuarios,
                C.nomes_cargos
            FROM
                JUNCAO_USUARIOS_CP JUC
            JOIN
                USUARIOS U ON JUC.id_usuarios = U.id_usuarios
            JOIN
                JUNCAO_CARGOS_PERMISSOES JCP ON JUC.id_juncao_cargos_permissoes = JCP.id_juncao_cargos_permissoes
            JOIN
                CARGOS C ON JCP.id_cargos = C.id_cargos
            WHERE
                JUC.id_juncao_usuario_cp = %s;
        """
        receptor_data = self._db.execute(receptor_query, (id_juncao_cp_receptor,), fetch='one')
        if receptor_data:
            preview_data['receptor_nome_completo'] = f"{receptor_data['nomes_usuarios']} ({receptor_data['nomes_cargos']})"
        else:
            preview_data['receptor_nome_completo'] = "Usuário/Cargo Desconhecido"
            
        return preview_data

    def realizar_movimentacao(self, executor_id_juncao_cp: int, id_item_movido: int, id_juncao_cp_receptor: int) -> bool:
        """
        [Passo 5 - Transação Lógica] Executa a movimentação final:
        1. Atualiza o status do item na tabela ITENS para 'EM USO' e define id_locais = NULL.
        2. Insere um novo registro na tabela MOVIMENTACOES (log de auditoria) com status 'EM USO'.

        Retorna: True se a movimentação for bem-sucedida (ambas as queries), False caso contrário.
        """
        
        # 1. Obter o ID do Status 'EM USO'
        id_em_uso = self._obter_id_status('EM USO')
        if id_em_uso is None:
            print("ERRO: Status 'EM USO' não encontrado. Não é possível mover o item.")
            return False
            
        # 2. Atualizar o status e a localização do item na tabela ITENS (Estado Atual)
        update_item_query = """
            UPDATE ITENS
            SET id_status = %s, id_locais = NULL
            WHERE id_itens = %s;
        """
        sucesso_update = self._db.execute(update_item_query, (id_em_uso, id_item_movido), fetch='none')
        
        if not sucesso_update:
            print(f"ERRO: Falha ao atualizar o status/local do item ID {id_item_movido}.")
            return False

        # 3. Inserir o registro de movimentação (Saída) na MOVIMENTACOES (Histórico)
        insert_movimentacao_query = """
            INSERT INTO MOVIMENTACOES 
                (id_itens, id_status, id_juncao_usuario_cp, data, id_locais)
            VALUES 
                (%s, %s, %s, %s, NULL);
        """
        
        data_movimentacao = datetime.now()
        
        # Aqui, o id_juncao_cp_receptor é usado como o 'executor' do movimento, 
        # que na prática representa o novo responsável pelo item.
        sucesso_insert = self._db.execute(insert_movimentacao_query, 
                                          (id_item_movido, id_em_uso, id_juncao_cp_receptor, data_movimentacao), 
                                          fetch='none')
                                          
        if sucesso_insert:
            print(f"INFO: Item ID {id_item_movido} movimentado com sucesso para o receptor JUC ID {id_juncao_cp_receptor}.")
            return True
        else:
            print(f"ERRO: Falha ao registrar a movimentação do item ID {id_item_movido}. Estado do item pode estar inconsistente.")
            return False
        
    # ==============================================================================================================================#     
    # Criação e Exclusão de Itens
    # ==============================================================================================================================#  

    def inserir_nome_item(self, nome_item: str, id_categoria: int) -> int or None:
        """
        [PASSO 1/3: NOME/CATEGORIA]
        Insere o tipo de item na tabela NOMES_ITENS ou retorna o ID se já existir.
        
        Retorna: id_nomes_itens ou None.
        """
        # 1. Tenta buscar o ID existente
        query_select = "SELECT id_nomes_itens FROM NOMES_ITENS WHERE nomes_itens = %s;"
        existing_id = self._db.execute(query_select, (nome_item,), fetch='one')
        
        if existing_id:
            print(f"INFO: Tipo de item '{nome_item}' já existe. ID: {existing_id['id_nomes_itens']}")
            return existing_id['id_nomes_itens']
            
        # 2. Se não existir, insere
        query_insert = """
            INSERT INTO NOMES_ITENS (nomes_itens, id_categorias) 
            VALUES (%s, %s) 
            RETURNING id_nomes_itens;
        """
        result = self._db.execute(query_insert, (nome_item, id_categoria), fetch='one')
        
        if result:
            print(f"INFO: Novo tipo de item '{nome_item}' inserido. ID: {result['id_nomes_itens']}")
            return result['id_nomes_itens']
        return None

    def registrar_patrimonio(self, id_nomes_itens: int, numero_patrimonio: str, id_status_inicial: int) -> int or None:
        """
        [PASSO 2/3: PATRIMÔNIO]
        Insere o item patrimonial na tabela ITENS.
        
        ATENÇÃO: id_status_inicial deve ser o ID que você definiu para o status
        inicial do item (Ex: 1 - DISPONÍVEL, 2 - EM USO).
        
        Retorna: id_itens do novo item ou None.
        """
        query = """
            INSERT INTO ITENS (id_nomes_itens, numero_patrimonio, id_status) 
            VALUES (%s, %s, %s) 
            RETURNING id_itens;
        """
        result = self._db.execute(query, (id_nomes_itens, numero_patrimonio, id_status_inicial), fetch='one')
        
        if result:
            print(f"INFO: Item patrimonial '{numero_patrimonio}' inserido. ID: {result['id_itens']}")
            return result['id_itens']
        
        print(f"ERRO: Falha ao inserir item com patrimônio {numero_patrimonio}. Patrimônio pode ser duplicado.")
        return None

    def registrar_movimentacao_inicial(self, id_itens: int, id_local_destino: int, id_juncao_usuario_cp: int) -> int or None:
        """
        [PASSO 3/3: LOCALIZAÇÃO INICIAL]
        Insere a primeira movimentação do item na tabela MOVIMENTACOES.
        
        * O status é fixado em 1 (DISPONÍVEL) conforme sua regra.
        * id_local_origem é NULL (pois o item está sendo criado).
        
        Retorna: id_movimentacoes do registro criado ou None.
        """
        # Status fixo em 1 (DISPONÍVEL) conforme a regra do usuário
        STATUS_DISPONIVEL_ID = 1 
        
        query = """
            INSERT INTO MOVIMENTACOES (id_itens, id_local_origem, id_local_destino, id_status, id_juncao_usuario_cp, data) 
            VALUES (%s, NULL, %s, %s, %s, NOW()) 
            RETURNING id_movimentacoes;
        """
        params = (id_itens, id_local_destino, STATUS_DISPONIVEL_ID, id_juncao_usuario_cp)
        result = self._db.execute(query, params, fetch='one')
        
        if result:
            print(f"INFO: Movimentação inicial registrada. Item ID: {id_itens}. Local ID: {id_local_destino}")
            return result['id_movimentacoes']
        
        print(f"ERRO: Falha ao registrar movimentação inicial para item {id_itens}.")
        return None