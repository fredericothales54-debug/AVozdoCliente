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
        
    def _executar_query(self, query, params=None, fetchone=False, commit=False):
        c = None
        try:
            c = self.conn.cursor()
            c.execute(query, params or ())
            
            if commit:
                self.conn.commit()
                return True
            
            q_upper = query.strip().upper()
            
            if q_upper.startswith(('INSERT', 'UPDATE', 'DELETE')):
                if 'RETURNING' in q_upper:
                    if fetchone:
                        return c.fetchone()
                    else:
                        return c.fetchall()
                else:
                    return True
            
            if fetchone:
                r = c.fetchone()
                return r
            else:
                r = c.fetchall()
                return r
                
        except Exception as e:
            if commit and self.conn:
                self.conn.rollback()
            print(f"erro query: {e}")
            return None if fetchone else []
        finally:
            if c:
                c.close()

    def _obter_juncao_cp(self, id_usuarios: int):
        q = "SELECT id_juncao_usuario_cp FROM JUNCAO_USUARIOS_CP WHERE id_usuarios = %s LIMIT 1;"
        r = self._executar_query(q, (id_usuarios,), fetchone=True)
        return r[0] if r else None
        
    def _obter_item_id_por_patrimonio(self, patrimonio: str):
        q = "SELECT id_itens FROM ITENS WHERE numero_patrimonio = %s LIMIT 1;"
        r = self._executar_query(q, (patrimonio,), fetchone=True)
        return r[0] if r else None
    
    def _obter_id_status(self, nome_status: str):
        q = "SELECT id_status FROM STATUS WHERE nomes_status = %s LIMIT 1;"
        r = self._executar_query(q, (nome_status.upper(),), fetchone=True)
        return r[0] if r else None
    
    def obter_item_por_patrimonio(self, patrimonio: str):
        query = """
            SELECT
                i.id_itens,
                ni.nomes_itens,
                i.numero_patrimonio,
                c.nomes_categorias,
                CONCAT(l.numero_sala, ' - ', l.numero_posicao, ' (', l.nome_estrutura, ')'),
                s.nomes_status
            FROM ITENS i
            JOIN NOMES_ITENS ni ON i.id_nomes_itens = ni.id_nomes_itens
            JOIN STATUS s ON i.id_status = s.id_status
            LEFT JOIN LATERAL (
                SELECT id_locais
                FROM MOVIMENTACOES
                WHERE id_itens = i.id_itens
                ORDER BY id_movimentacoes DESC
                LIMIT 1
            ) AS latest_loc ON TRUE
            JOIN LOCAIS l ON latest_loc.id_locais = l.id_locais
            JOIN CATEGORIAS c ON ni.id_categorias = c.id_categorias
            WHERE i.numero_patrimonio = %s;
        """
        r = self._executar_query(query, (patrimonio,), fetchone=True)
        if r:
            return item_model.from_db_row(r)
        return None
    
    def obter_item_por_id(self, id_interno: int):
        query = """
            SELECT i.id_itens, ni.nomes_itens, i.numero_patrimonio, 'N/A',
                CONCAT(l.numero_sala, ' - ', l.numero_posicao), s.nomes_status
            FROM ITENS i
            JOIN NOMES_ITENS ni ON i.id_nomes_itens = ni.id_nomes_itens 
            JOIN STATUS s ON i.id_status = s.id_status
            LEFT JOIN LATERAL (
                SELECT id_locais 
                FROM MOVIMENTACOES 
                WHERE id_itens = i.id_itens 
                ORDER BY id_movimentacoes DESC 
                LIMIT 1
            ) AS latest_loc ON TRUE
            JOIN LOCAIS l ON latest_loc.id_locais = l.id_locais
            WHERE i.id_itens = %s;
        """
        r = self._executar_query(query, (id_interno,), fetchone=True)
        if r:
            return item_model.from_db_row(r)
        return "item nao achado"
        
    def devolucao_item(self,item_id: int):
        almox_jucp = 2 
        almox_local = 1 
        
        try:
            q1 = """
            INSERT INTO MOVIMENTACOES (id_itens, id_status, id_juncao_usuario_cp, data, id_locais)
            VALUES (%s, 1, %s, NOW(), %s);
            """
            self._executar_query(q1, (item_id, almox_jucp, almox_local), commit=False)
            
            q2 = "UPDATE ITENS SET id_status = 1 WHERE id_itens = %s;"
            self._executar_query(q2,(item_id,),commit=False)
            
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"erro devolucao: {e}")
            return False

    def autenticar_usuario(self,usuarios:str):
        q = """
            SELECT id_usuarios, nomes_usuarios, senhas_usuarios
            FROM USUARIOS 
            WHERE nomes_usuarios= %s; 
        """
        r = self._executar_query(q, (usuarios,), fetchone=True)
        if r:
            return (r)
        return None
    
    def _obter_nome_usuario_por_id(self, id_usuarios: int):
        q = "SELECT nomes_usuarios FROM USUARIOS WHERE id_usuarios = %s LIMIT 1;"
        r = self._executar_query(q, (id_usuarios,), fetchone=True)
        return r[0] if r else "desconhecido"
        
    def inserir_produto(self,item_obj):
        almox_jucp = 2 
        
        q_item="""
            INSERT INTO ITENS(id_nomes_itens, numero_patrimonio, id_status) 
            VALUES (%s, %s, %s) RETURNING id_itens;
        """
        params_item=(item_obj.nome, item_obj.patrimonio, 1)
        
        q_mov="""
            INSERT INTO MOVIMENTACOES (id_itens, id_status, id_juncao_usuario_cp, data, id_locais) 
            VALUES (%s, %s, %s, NOW(), %s);
        """
        
        try:
            r = self._executar_query(q_item, params_item, fetchone=True, commit=False)
            if not r:
                raise Exception("falhou inserir item")
            id_novo = r[0]
            
            params_mov = (id_novo, 1, almox_jucp, item_obj.localizacao)
            self._executar_query(q_mov , params_mov, commit=False)

            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"erro insercao: {e}")
            return False
            
    def deletar_produto(self, patrimonio: str):
        try:
            q1 = "SELECT id_itens FROM ITENS WHERE numero_patrimonio = %s;"
            r = self._executar_query(q1, (patrimonio,), fetchone=True)
            
            if not r:
                print(f"item {patrimonio} nao existe")
                return False
            
            item_id = r[0]
            
            q2 = "DELETE FROM MOVIMENTACOES WHERE id_itens = %s;"
            self._executar_query(q2, (item_id,), commit=False)
            print(f"movimentacoes do {patrimonio} apagadas")
            
            q3 = "DELETE FROM ITENS WHERE numero_patrimonio = %s;"
            self._executar_query(q3, (patrimonio,), commit=False)
            print(f"item {patrimonio} apagado")
            
            self.conn.commit()
            return True
            
        except Exception as e:
            self.conn.rollback()
            print(f"erro deletar produto: {e}")
            return False
    
    def deletar_usuario(self, usuario_id: int):
        try:
            q1 = "SELECT nomes_usuarios FROM USUARIOS WHERE id_usuarios = %s;"
            r = self._executar_query(q1, (usuario_id,), fetchone=True)
            
            if not r:
                print(f"usuario id {usuario_id} nao existe")
                return False
            
            nome = r[0]
            
            if nome == 'TI':
                print(f"nao da pra apagar o TI")
                return False
            
            q2 = "SELECT id_juncao_usuario_cp FROM JUNCAO_USUARIOS_CP WHERE id_usuarios = %s;"
            juncao_r = self._executar_query(q2, (usuario_id,), fetchone=True)
            
            if juncao_r:
                juncao_id = juncao_r[0]
                
                q3 = "DELETE FROM MOVIMENTACOES WHERE id_juncao_usuario_cp = %s;"
                self._executar_query(q3, (juncao_id,), commit=False)
                print(f"movimentacoes do {nome} apagadas")
            
            q4 = "DELETE FROM JUNCAO_USUARIOS_CP WHERE id_usuarios = %s;"
            self._executar_query(q4, (usuario_id,), commit=False)
            print(f"juncao CP do {nome} apagada")
            
            q5 = "DELETE FROM USUARIOS WHERE id_usuarios = %s;"
            self._executar_query(q5, (usuario_id,), commit=False)
            print(f"usuario {nome} apagado")
            
            self.conn.commit()
            return True
            
        except Exception as e:
            self.conn.rollback()
            print(f"erro deletar usuario: {e}")
            return False
            
    def cadastrar_usuario(self, usuario_obj):
        c = self.conn.cursor()
    
        try:
            c.execute("""
                INSERT INTO USUARIOS(nomes_usuarios, senhas_usuarios)
                VALUES(%s, %s)
                RETURNING id_usuarios;
            """, (usuario_obj.nome, usuario_obj.senha))
        
            id_novo = c.fetchone()[0]
            print(f"usuario criado id: {id_novo}")
       
            c.execute("""
                SELECT id_juncao_cargos_permissoes 
                FROM JUNCAO_CARGOS_PERMISSOES 
                WHERE id_cargos = 1 
                LIMIT 1;
            """)
        
            r = c.fetchone()
            if not r:
                raise Exception("cargo padrao nao existe")
        
            id_jcp_padrao = r[0]
            print(f"cargo padrao: {id_jcp_padrao}")
        
            c.execute("""
                INSERT INTO JUNCAO_USUARIOS_CP(id_usuarios, id_juncao_cargos_permissoes)
                VALUES(%s, %s)
                RETURNING id_juncao_usuario_cp;
            """, (id_novo, id_jcp_padrao))
            
            id_juncao = c.fetchone()[0]
            print(f"juncao criada id: {id_juncao}")
        
            self.conn.commit()
            c.close()
            
            print(f"usuario {usuario_obj.nome} cadastrado ok!")
            return True
        
        except Exception as e:
            self.conn.rollback()
            c.close()
            print(f"erro cadastrar: {e}")
            return False
            
    def emprestar_item(self, item_id: int, usuario_id: int, id_local_emprestimo: int, dias_previstos: int = 7):
        id_jcp = self._obter_juncao_cp(usuario_id)
        
        if not id_jcp:
            print(f"ERRO: nao achou JUNCAO_USUARIOS_CP pro usuario: {usuario_id}")
            print(f"verifica se o usuario foi cadastrado direito")
            return False
        
        print(f"juncao achada: {id_jcp} pro usuario {usuario_id}")
            
        agora = datetime.datetime.now()
        
        q_mov = """
            INSERT INTO MOVIMENTACOES (id_itens, id_status, id_juncao_usuario_cp, data, id_locais)
            VALUES (%s, 2, %s, %s, %s);
        """
        params_mov = (item_id, id_jcp, agora, id_local_emprestimo)

        q_status = "UPDATE ITENS SET id_status = 2 WHERE id_itens = %s;"
        params_status = (item_id,)
        
        try:
            self._executar_query(q_mov, params_mov, commit=False)
            print(f"movimentacao registrada item {item_id}")
            
            self._executar_query(q_status, params_status, commit=False)
            print(f"status item {item_id} virou EMPRESTADO")
            
            self.conn.commit()
            print(f"emprestimo ok!")
            return True
            
        except Exception as e:
            self.conn.rollback()
            print(f"erro emprestimo: {e}")
            return False

    def listar_todas_categorias(self):
        q = "SELECT id_categorias, nomes_categorias FROM CATEGORIAS ORDER BY nomes_categorias;"
        
        try:
            rows = self._executar_query(q)
            if rows:
                return [{"id": r[0], "nome": r[1]} for r in rows]
            return []
        except Exception as e:
            print(f"erro listar categorias: {e}")
            return []

    def listar_itens_disponiveis(self):
        query = """
            SELECT i.id_itens, ni.nomes_itens, i.numero_patrimonio,
                c.nomes_categorias, 
                CONCAT(l.numero_sala, ' - ', l.numero_posicao, ' (', l.nome_estrutura, ')'), 
                s.nomes_status
            FROM ITENS i
            JOIN NOMES_ITENS ni ON i.id_nomes_itens = ni.id_nomes_itens 
            JOIN STATUS s ON i.id_status = s.id_status
            LEFT JOIN LATERAL (
                SELECT id_locais 
                FROM MOVIMENTACOES 
                WHERE id_itens = i.id_itens 
                ORDER BY id_movimentacoes DESC 
                LIMIT 1
            ) AS latest_loc ON TRUE
            JOIN LOCAIS l ON latest_loc.id_locais = l.id_locais
            JOIN CATEGORIAS c ON ni.id_categorias = c.id_categorias 
            WHERE i.id_status = 1;
        """
        
        rows = self._executar_query(query)
        
        if rows:
            return [item_model.from_db_row(r) for r in rows]
        return []
        
    def listar_exemplares_por_categoria_db(self, nome_categoria: str):
        query = """
            SELECT i.id_itens, ni.nomes_itens, i.numero_patrimonio,
                s.nomes_status, u.nomes_usuarios
            FROM ITENS i
            JOIN NOMES_ITENS ni ON i.id_nomes_itens = ni.id_nomes_itens 
            JOIN STATUS s ON i.id_status = s.id_status
            JOIN CATEGORIAS c ON ni.id_categorias = c.id_categorias
            LEFT JOIN LATERAL (
                SELECT jucp.id_usuarios 
                FROM MOVIMENTACOES m
                JOIN JUNCAO_USUARIOS_CP jucp ON m.id_juncao_usuario_cp = jucp.id_juncao_usuario_cp
                WHERE m.id_itens = i.id_itens AND m.id_status IN (2, 3)
                ORDER BY m.data DESC
                LIMIT 1
            ) AS ultima_mov ON TRUE
            LEFT JOIN USUARIOS u ON ultima_mov.id_usuarios = u.id_usuarios
            WHERE c.nomes_categorias = %s
            ORDER BY i.numero_patrimonio;
        """
        
        rows = self._executar_query(query, (nome_categoria,))
        
        if rows:
            result = []
            for r in rows:
                stat = r[3]
                
                if stat in ('EMPRESTADO', 'EM USO') and r[4]:
                    posse = r[4]
                else:
                    posse = 'Ninguém'
                    
                result.append({
                    "id": r[0],
                    "nome": r[1],
                    "patrimonio": r[2],
                    "status": stat,
                    "em_posse": posse
                })
            return result 
        return []

class Historico:
    ARQUIVO = 'historico.json'

    @staticmethod
    def carregar_dados():
        try:
            with open(Historico.ARQUIVO, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"eventos": []}
            
    @staticmethod
    def registrar_historico(tipo_evento: str, detalhes: dict):
        dados = Historico.carregar_dados()

        if 'eventos' not in dados:
            dados['eventos'] = []
       
        novo = {
            "ts": datetime.datetime.now().isoformat(),
            "tipo": tipo_evento,
            "detalhes": detalhes
        }
        
        dados["eventos"].append(novo)
        dados["ultima_atualizacao"] = datetime.datetime.now().isoformat()
        
        try:
            with open(Historico.ARQUIVO, 'w', encoding='utf-8') as f:
                json.dump(dados, f, indent=4)
                return True
        except Exception as e:
            print(f"erro salvar historico: {e}")
            return False

historico = Historico()