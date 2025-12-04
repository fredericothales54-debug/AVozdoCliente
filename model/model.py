import json
import datetime
ARQUIVO="historico.json"
class usuario_model:
    
    def __init__(self,id_usuarios,nomes_usuarios, senhas_usuarios):
        self.id = id_usuarios
        self.nome = nomes_usuarios
        self.senha=senhas_usuarios
class item_model:
    
    def __init__(self, id_produto, nome_produto, numero_patrimonio, categoria_produto, localizacao_produto,status_produto ):
       
        self.id = id_produto
        self.nome = nome_produto
        self.patrimonio = numero_patrimonio
        self.tipo = categoria_produto
        self.localizacao = localizacao_produto
        self.status = status_produto
    @classmethod
    def from_db_row(cls, row):
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
        self.conn = conn
    def _executar_query(self, query, params=None, fetchone=False,commit=False):
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
    def autenticar_usuario(self,usuarios:str):
        query = """
            SELECT id_usuarios, nomes_usuarios,  senhas_usuarios
            FROM USUARIOS 
            WHERE  nomes_usuarios= %s; 
        """
        row = self._executar_query(query, (usuarios,), fetchone=True)
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
    def deletar_produto(self,item_obj):
        query="""
            DELETE FROM ITENS WHERE numero_patrimonio =%s;
            """
        parametros=(
            item_obj.patrimonio
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

    def listar_todas_categorias(self):
        
        query = "SELECT id_categorias, nomes_categorias FROM CATEGORIAS ORDER BY nomes_categorias;"
        
        try:
            rows = self._executar_query(query)
            
            if rows:
                return [{"id": row[0], "nome": row[1]} for row in rows]
            
            return []
            
        except Exception as e:
            print(f"❌ Erro de query ao listar categorias: {e}")
            return []

    def listar_itens_disponiveis(self):
        query = """
            SELECT
                i.id_itens,
                ni.nomes_itens, 
                i.numero_patrimonio,
                c.nome_categoria,
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
            JOIN 
                CATEGORIAS c ON ni.id_categorias = c.id_categorias 
            WHERE
                i.id_status = 1; -- Filtra apenas por 'DISPONÍVEL'
        """
        
        rows = self._executar_query(query)
        
        if rows:
            return [item_model.from_db_row(row) for row in rows]
            
        return []
    def listar_exemplares_por_categoria_db(self, nome_categoria: str):
        query = """
            SELECT
                i.id_itens,
                ni.nomes_itens, 
                i.numero_patrimonio,
                c.nomes_categorias, 
                CONCAT(l.numero_sala, ' - ', l.numero_posicao), 
                s.nomes_status,
                COALESCE(u.nomes_usuarios, 'N/A') AS em_posse_por -- Nome do usuário em posse
            FROM
                ITENS i
            JOIN NOMES_ITENS ni ON i.id_nomes_itens = ni.id_nomes_itens -- CORRIGIDO
            JOIN CATEGORIAS c ON ni.id_categorias = c.id_categorias
            JOIN STATUS s ON i.id_status = s.id_status
            JOIN LOCAIS l ON i.id_locais = l.id_locais -- Assumindo id_locais em ITENS
            -- Buscar o último status de movimentação: Status 2 é 'EM USO'
            LEFT JOIN MOVIMENTACOES m ON i.id_itens = m.id_itens AND m.id_status = 2 
            -- Busca o usuário em posse através das tabelas de junção (DDL)
            LEFT JOIN JUNCAO_USUARIOS_CP jucp ON m.id_juncao_usuario_cp = jucp.id_juncao_usuario_cp
            LEFT JOIN USUARIOS u ON jucp.id_usuarios = u.id_usuarios
            WHERE
                c.nomes_categorias = %s
            ORDER BY
                i.numero_patrimonio;
        """
        rows = self._executar_query(query, (nome_categoria,))
        
        if rows:
            return [{
                "id": row[0],
                "nome": row[1],
                "patrimonio": row[2],
                "categoria": row[3],
                "localizacao": row[4],
                "status": row[5],
                "em_posse": row[6] 
            } for row in rows]
        return []
ARQUIVO = 'historico.json'
class Historico:
    @staticmethod
    def carregar_dados():
        try:
            with open(ARQUIVO, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

historico = Historico()

def registrar_historico(tipo_evento: str, detalhes: dict):
    dados = historico.carregar_dados()

   
    if 'eventos' not in dados:
        dados['eventos'] = []
    
    novo_registro = {
        "timestamp": datetime.datetime.now().isoformat(),
        "tipo": tipo_evento,
        "detalhes": detalhes
    }
    
    dados["eventos"].append(novo_registro)
    
    dados["ultima_atualizacao"] = datetime.datetime.now().isoformat()
    
    try:
        with open(ARQUIVO, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=4)
            return True
    except Exception as e:
        print(f"Erro ao salvar histórico: {e}")
        return False