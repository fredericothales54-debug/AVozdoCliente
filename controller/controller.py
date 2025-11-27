import psycopg2
import model
import view

class appcomtroll:
    def __init__(self,model,view,db_conn):
        self.view = None
        self._executar_query = model.clientedb(_db_conn)
        self._executar_query = model.clientedb()
        self._historico = []