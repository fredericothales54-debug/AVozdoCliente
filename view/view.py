import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches # Adicionado para legendas no gráfico
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns
import datetime

# -----------------------------------------------------------------
# FUNÇÕES GLOBAIS DE SUPORTE
# Estas funções não precisam de 'self' e são utilities.
# -----------------------------------------------------------------

# Função para obter a data e hora formatadas (necessário para logs/histórico)
def agora_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# --- DECORATOR CORRIGIDO ---
# Este decorator é definido FORA da classe para funcionar corretamente.
def login_required(func):
    """Decorator que verifica se o usuário está logado antes de executar o método."""
    def wrapper(self, *args, **kwargs):
        if self.usuario_logado is None:
            messagebox.showerror("Acesso Negado", "Você deve estar logado para acessar esta função.")
            return
        return func(self, *args, **kwargs)
    return wrapper
# ---------------------------

# -----------------------------------------------------------------
# CLASSE PRINCIPAL DA VIEW (CAMADA DE INTERFACE)
# -----------------------------------------------------------------

class AppView:
    def __init__(self, root_window, controller):
        # 1. Armazena o Controller e a Janela Raiz (Injeção de Dependência)
        self.root = root_window
        self.controller = controller

        # 2. Variáveis de estado da View
        self.usuario_logado = None
        self.login_win = None
        self.menu_win = None
        
        # Variáveis de entrada (Entry)
        self.entry_user = None
        self.entry_pass = None

        # 3. Inicializa a tela de login
        self.tela_login()
        
    # --- UTILS GERAIS ---
    def limpar_frame(self, f):
        """Destrói todos os widgets dentro de um frame."""
        for w in f.winfo_children():
            w.destroy()

    def tela_login(self):
        """Cria e exibe a tela de login."""
        self.login_win = tk.Toplevel(self.root)
        self.login_win.title("Inventário - Login")
        self.login_win.geometry("360x220")
        self.login_win.configure(bg="white")
        self.login_win.protocol("WM_DELETE_WINDOW", self.finalizar_app)

        frm = tk.Frame(self.login_win, bg="white", padx=12, pady=12)
        frm.pack(expand=True, fill="both")

        ttk.Label(frm, text="Usuário:").grid(row=0, column=0, sticky="w", pady=6)
        self.entry_user = ttk.Entry(frm)
        self.entry_user.grid(row=0, column=1, pady=6, sticky="ew")

        ttk.Label(frm, text="Senha:").grid(row=1, column=0, sticky="w", pady=6)
        self.entry_pass = ttk.Entry(frm, show="*")
        self.entry_pass.grid(row=1, column=1, pady=6, sticky="ew")

        # ⚠️ DELEGAÇÃO: Chama o método fazer_login da View
        ttk.Button(frm, text="Entrar", command=self.fazer_login).grid(row=2, column=0, columnspan=2, pady=12)

        frm.columnconfigure(1, weight=1)

    def fazer_login(self):
        """Processa a tentativa de login, delegando ao Controller."""
        user = self.entry_user.get().strip()
        senha = self.entry_pass.get().strip()

        # ⚠️ DELEGAÇÃO: A View chama o Controller para fazer a lógica de autenticação no DB
        sucesso, resposta = self.controller.fazer_login(user, senha)

        if sucesso:
            # Armazena o objeto de usuário retornado pelo Controller
            self.usuario_logado = resposta 
            self.abrir_menu()
        else:
            # Exibe a mensagem de erro do Controller
            messagebox.showerror("Erro de Login", resposta) 

    def abrir_menu(self):
        """Cria e exibe a janela principal da aplicação."""
        self.login_win.withdraw()
        
        if self.menu_win:
             self.menu_win.destroy()
        
        self.menu_win = tk.Toplevel(self.root)
        self.menu_win.title(f"Sistema de Estoque - Logado como: {self.usuario_logado.nome}") # Assumindo que o objeto tem nome e tipo
        self.menu_win.geometry("1000x600")
        self.menu_win.protocol("WM_DELETE_WINDOW", self.finalizar_app)

        main_frame = tk.Frame(self.menu_win)
        main_frame.pack(fill="both", expand=True)

        sidebar = tk.Frame(main_frame, width=200, bg="#f0f0f0")
        sidebar.pack(side="left", fill="y", padx=5, pady=5)

        content = tk.Frame(main_frame, bg="white")
        content.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        ttk.Label(sidebar, text="MENU", font=("Arial", 14, "bold"), background="#f0f0f0").pack(pady=10)

        # ⚠️ Botões de Navegação (Chamando métodos da View)
        ttk.Button(sidebar, text="Consultar Produtos", command=lambda: self.tela_categorias(content)).pack(fill="x", pady=6)
        ttk.Button(sidebar, text="Relatórios", command=lambda: self.tela_relatorios(content)).pack(fill="x", pady=6)
        ttk.Button(sidebar, text="Movimentações", command=lambda: self.tela_movimentacoes(content)).pack(fill="x", pady=6)
        
        if self.usuario_logado.nome in ("TI"):
            ttk.Separator(sidebar, orient="horizontal").pack(fill="x", pady=10)
            ttk.Button(sidebar, text="Gerenciar Usuários", command=lambda: self.tela_usuarios(content)).pack(fill="x", pady=6)
            ttk.Button(sidebar, text="Adicionar Novo Item", command=lambda: self.tela_cadastro_item(content)).pack(fill="x", pady=6)

        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", pady=10)
        ttk.Button(sidebar, text="Logout", command=self.logout).pack(fill="x", pady=6)
        
        # Exibe a tela inicial após abrir o menu
        self.tela_categorias(content)

    def logout(self):
        """Realiza o logout e retorna à tela de login."""
        self.usuario_logado = None
        self.menu_win.destroy()
        self.tela_login()
        
    def finalizar_app(self):
        """Encerra a aplicação e fecha a conexão (delegando ao Controller)."""
        self.controller.finalizar_app() # Chama o método do Controller para fechar a conexão
        self.root.destroy()
        
    # ------------------------------------------------
    # TELAS DE AÇÃO (Requerem login e delegam ao Controller)
    # ------------------------------------------------
        
    @login_required
    def tela_categorias(self, parent):
        """Exibe as categorias e permite navegar para a lista de itens."""
        self.limpar_frame(parent)
        ttk.Label(parent, text="CATEGORIAS DE PRODUTOS", font=("Arial", 16, "bold"), background="white").pack(pady=10)
        
        # ⚠️ DELEGAÇÃO: Pede os dados de categorias ao Controller/Model
        # O Controller deve retornar um dicionário ou lista de nomes de categorias
        categorias = self.controller.obter_categorias()
        
        frm_list = tk.Frame(parent, bg="white")
        frm_list.pack(fill="both", expand=True)

        listbox = tk.Listbox(frm_list, height=15, font=("Arial", 12))
        listbox.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        for nome_categoria in categorias:
            listbox.insert(tk.END, nome_categoria)
            
        def abrir_cat():
            sel = listbox.curselection()
            if not sel:
                messagebox.showinfo("Seleção", "Escolha uma categoria.")
                return
            cat = listbox.get(sel[0])
            self.abrir_itens_categoria(parent, cat)
            
        btn_frm = tk.Frame(frm_list, bg="white")
        btn_frm.pack(side="right", fill="y", padx=10, pady=10)
        
        ttk.Button(btn_frm, text="Abrir Categoria", command=abrir_cat).pack(pady=5, fill="x")

    @login_required
    def abrir_itens_categoria(self, parent, categoria):
        """Exibe todos os exemplares (patrimônios) de uma categoria."""
        self.limpar_frame(parent)
        ttk.Label(parent, text=f"ITENS EM: {categoria.upper()}", font=("Arial", 16, "bold"), background="white").pack(pady=10)
        
        # ⚠️ DELEGAÇÃO: Pede a lista de exemplares ao Controller
        # O Controller deve retornar uma lista de dicionários/objetos de item detalhado
        exemplares = self.controller.listar_exemplares_por_categoria(categoria)

        # Treeview com exemplares
        cols = ("nome", "patrimonio", "status", "em_posse")
        tree = ttk.Treeview(parent, columns=cols, show="headings", selectmode="browse")
        
        tree.heading("nome", text="Nome do Item")
        tree.heading("patrimonio", text="Patrimônio")
        tree.heading("status", text="Status")
        tree.heading("em_posse", text="Em Posse de")
        
        tree.column("nome", width=250)
        tree.column("patrimonio", width=100, anchor="center")
        tree.column("status", width=100, anchor="center")
        tree.column("em_posse", width=150)
        
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Preencher a Treeview
        for ex in exemplares:
             # A chave (iid) é o patrimônio (identificador único)
            chave = ex["patrimonio"] 
            # Garantir que o nome esteja disponível, caso o Controller tenha padronizado
            nome_item = ex.get("nome", "N/A") 
            tree.insert("", tk.END, iid=chave, values=(nome_item, ex["patrimonio"], ex["status"], ex["em_posse"]))


        # --- Lógica de Ação (Requisitar/Devolver) ---
        
        def requisitar_exemplar():
            sel = tree.selection()
            if not sel: return
            patrimonio = sel[0] 

            # ⚠️ DELEGAÇÃO: Envia a ação e os dados para o Controller
            # O Controller fará a validação (status DISPONIVEL) e a transação no DB
            resultado = self.controller.realizar_emprestimo(
                patrimonio, 
                self.usuario_logado.id_usuario # Passa o ID único do usuário
            )
            
            if resultado['status'] == 'sucesso':
                messagebox.showinfo("Sucesso", "Requisição registrada. Status atualizado.")
                # APÓS A REQUISIÇÃO, ATUALIZA A LINHA NA TELA
                # Pede os dados atualizados ao Controller
                item_atualizado = self.controller.obter_item_por_patrimonio(patrimonio) 
                
                if item_atualizado:
                    tree.item(patrimonio, values=(item_atualizado["nome"], item_atualizado["patrimonio"], item_atualizado["status"], item_atualizado["em_posse"]))
            else:
                messagebox.showwarning("Erro", resultado['mensagem'])

        def devolver_exemplar():
            sel = tree.selection()
            if not sel: return
            patrimonio = sel[0]

            # ⚠️ DELEGAÇÃO: Envia a ação para o Controller
            resultado = self.controller.gerenciar_devolucao(patrimonio)

            if resultado['status'] == 'sucesso':
                messagebox.showinfo("Sucesso", "Devolução registrada. Status atualizado para 'Disponível'.")
                # ATUALIZA A LINHA NA TELA
                item_atualizado = self.controller.obter_item_por_patrimonio(patrimonio)
                
                if item_atualizado:
                    tree.item(patrimonio, values=(item_atualizado["nome"], item_atualizado["patrimonio"], item_atualizado["status"], item_atualizado["em_posse"]))
            else:
                messagebox.showwarning("Erro", resultado['mensagem'])
                
        # --- Botões de Ação ---
        action_frm = tk.Frame(parent, bg="white")
        action_frm.pack(pady=10)
        
        ttk.Button(action_frm, text="Requisitar Item", command=requisitar_exemplar).pack(side="left", padx=10)
        ttk.Button(action_frm, text="Devolver Item", command=devolver_exemplar).pack(side="left", padx=10)
        ttk.Button(action_frm, text="Voltar para Categorias", command=lambda: self.tela_categorias(parent)).pack(side="left", padx=10)
    
    # --- Telas de Relatório e Movimentação (Estrutura Mantida, Lógica de Dados Delegada) ---

    @login_required
    def tela_relatorios(self, parent):
        self.limpar_frame(parent)
        ttk.Label(parent, text="RELATÓRIOS DO INVENTÁRIO", font=("Arial", 16, "bold"), background="white").pack(pady=10)

        # ⚠️ DELEGAÇÃO: Obtém os dados resumidos do Controller/Model
        dados_itens_status = self.controller.obter_relatorio_status() # Espera: {'Disponível': 100, 'Em Uso': 50, 'Manutenção': 10}
        
        if not dados_itens_status:
             ttk.Label(parent, text="Nenhum dado de inventário para exibir.", background="white").pack(pady=20)
             return
             
        # Gráfico de Pizza (Status)
        self.relatorio_itens_pizza(parent, dados_itens_status)

    def relatorio_itens_pizza(self, parent, dados_status):
        """Gera e exibe um gráfico de pizza dos status dos itens."""
        fig, ax = plt.subplots(figsize=(6, 6))
        
        labels = dados_status.keys()
        sizes = dados_status.values()
        
        # Cores customizadas
        cores = ['#4CAF50', '#FF9800', '#F44336', '#2196F3'] 
        
        # Filtra cores para os dados existentes
        cores_usadas = [cores[i % len(cores)] for i in range(len(labels))]

        # Criar gráfico de pizza
        wedges, texts, autotexts = ax.pie(
            sizes, 
            autopct=lambda p: '{:.1f}%\n({:d})'.format(p, int(p * sum(sizes) / 100)),
            startangle=90, 
            colors=cores_usadas,
            wedgeprops={'edgecolor': 'black'}
        )
        
        ax.axis('equal') # Garante que o gráfico de pizza seja um círculo.
        ax.set_title('Distribuição de Itens por Status', fontsize=14)

        # Adiciona legenda com patches
        handles = [mpatches.Patch(color=c, label=l) for c, l in zip(cores_usadas, labels)]
        ax.legend(handles=handles, title="Status", loc="lower left", bbox_to_anchor=(0.9, 0, 0.5, 1))

        # Integra o Matplotlib ao Tkinter
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        canvas.draw()
        
    @login_required
    def tela_movimentacoes(self, parent):
        """Exibe o histórico de movimentações (Empréstimos, Devoluções, Cadastro/Exclusão)."""
        self.limpar_frame(parent)
        ttk.Label(parent, text="HISTÓRICO DE MOVIMENTAÇÕES", font=("Arial", 16, "bold"), background="white").pack(pady=10)

        # ⚠️ DELEGAÇÃO: Obtém todos os logs/movimentações do Controller/Model
        movimentacoes = self.controller.obter_historico_movimentacoes()
        
        if not movimentacoes:
             ttk.Label(parent, text="Nenhuma movimentação registrada.", background="white").pack(pady=20)
             return

        # Treeview para exibir os logs
        cols = ("timestamp", "tipo", "detalhes", "usuario")
        tree = ttk.Treeview(parent, columns=cols, show="headings")
        
        tree.heading("timestamp", text="Data/Hora", anchor="center")
        tree.heading("tipo", text="Tipo de Evento", anchor="center")
        tree.heading("detalhes", text="Detalhes", anchor="w")
        tree.heading("usuario", text="Usuário", anchor="center")
        
        tree.column("timestamp", width=150, anchor="center")
        tree.column("tipo", width=120, anchor="center")
        tree.column("detalhes", width=400)
        tree.column("usuario", width=100, anchor="center")
        
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Preencher a Treeview (Movimentações)
        for mov in movimentacoes:
            detalhes_str = mov.get("detalhes", "")
            tree.insert("", tk.END, values=(mov["ts"], mov["tipo"], detalhes_str, mov.get("usuario", "Sistema")))
            
        # ⚠️ DELEGAÇÃO: Obtém dados para o gráfico de movimentação
        dados_tipos_mov = self.controller.obter_contagem_por_tipo_movimentacao()
        self.relatorio_movimentacoes(parent, dados_tipos_mov)

    def relatorio_movimentacoes(self, parent, dados_tipos_mov):
        """Gera e exibe um gráfico de barras da contagem de movimentações."""
        # Cria um Frame para o gráfico
        fig_frame = tk.Frame(parent, bg="white")
        fig_frame.pack(fill="x", pady=10)
        
        if not dados_tipos_mov:
            return

        fig, ax = plt.subplots(figsize=(6, 3))
        
        eventos = dados_tipos_mov.keys()
        contagens = dados_tipos_mov.values()

        sns.barplot(x=list(eventos), y=list(contagens), ax=ax, palette="viridis")
        ax.set_title("Contagem de Eventos de Movimentação", fontsize=12)
        ax.set_ylabel("Contagem")
        ax.set_xlabel("Tipo de Evento")
        
        # Integra o Matplotlib ao Tkinter
        canvas = FigureCanvasTkAgg(fig, master=fig_frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(pady=5)
        canvas.draw()
        
    # --- Telas de Gerenciamento (ADMIN) ---

    @login_required
    def tela_cadastro_item(self, parent):
        """Tela para cadastrar um novo exemplar de item."""
        self.limpar_frame(parent)
        if self.usuario_logado.tipo not in ("ADMIN", "ACCESSFULL"):
            messagebox.showerror("Acesso", "Permissão negada.")
            return

        ttk.Label(parent, text="CADASTRO DE NOVO ITEM", font=("Arial", 16, "bold"), background="white").pack(pady=10)

        form_frame = tk.Frame(parent, bg="white", padx=20, pady=20)
        form_frame.pack(pady=10)

        # ⚠️ DELEGAÇÃO: O Controller deve fornecer os dados para os Combobox
        nomes_itens_disponiveis = self.controller.obter_nomes_itens() # Ex: ['Notebook Core i7', 'Mouse USB']
        locais_disponiveis = self.controller.obter_locais() # Ex: ['SALA-A', 'ALMOXARIFADO']
        status_disponiveis = ['DISPONIVEL', 'MANUTENCAO']
        
        # Variáveis de controle
        nome_item_var = tk.StringVar()
        patrimonio_var = tk.StringVar()
        local_var = tk.StringVar()
        
        def criar_item():
            nome = nome_item_var.get()
            patrimonio = patrimonio_var.get().strip()
            local = local_var.get()
            
            if not nome or not patrimonio or not local:
                messagebox.showwarning("Aviso", "Preencha todos os campos.")
                return

            # ⚠️ DELEGAÇÃO: Chama o Controller para cadastrar o item no DB
            resultado = self.controller.cadastrar_item(
                nome_item=nome,
                numero_patrimonio=patrimonio,
                localizacao=local,
                status="DISPONIVEL" # Novo item sempre inicia DISPONIVEL
            )
            
            if resultado['status'] == 'sucesso':
                messagebox.showinfo("Sucesso", f"Item '{nome}' (Patrimônio: {patrimonio}) cadastrado.")
                # Limpa os campos após sucesso
                patrimonio_var.set("")
            else:
                messagebox.showerror("Erro", resultado['mensagem'])

        # Layout do formulário
        row = 0
        ttk.Label(form_frame, text="Nome/Tipo do Item:", bg="white").grid(row=row, column=0, sticky="w", pady=5, padx=5)
        ttk.Combobox(form_frame, textvariable=nome_item_var, values=nomes_itens_disponiveis, state="readonly").grid(row=row, column=1, sticky="ew", pady=5, padx=5)
        
        row += 1
        ttk.Label(form_frame, text="Nº Patrimônio:", bg="white").grid(row=row, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(form_frame, textvariable=patrimonio_var).grid(row=row, column=1, sticky="ew", pady=5, padx=5)

        row += 1
        ttk.Label(form_frame, text="Local Inicial:", bg="white").grid(row=row, column=0, sticky="w", pady=5, padx=5)
        ttk.Combobox(form_frame, textvariable=local_var, values=locais_disponiveis, state="readonly").grid(row=row, column=1, sticky="ew", pady=5, padx=5)
        
        row += 1
        ttk.Button(form_frame, text="Cadastrar Item", command=criar_item).grid(row=row, column=0, columnspan=2, pady=20)
    
    @login_required
    def tela_usuarios(self, parent):
        """Tela de gerenciamento de usuários (apenas para ADMIN/ACCESSFULL)."""
        self.limpar_frame(parent)
        if self.usuario_logado.tipo not in ("ADMIN", "ACCESSFULL"):
            messagebox.showerror("Acesso", "Permissão negada.")
            return

        ttk.Label(parent, text="GERENCIAMENTO DE USUÁRIOS", font=("Arial", 16, "bold"), background="white").pack(pady=10)

        # ⚠️ DELEGAÇÃO: Obtém a lista de usuários do Controller/Model
        usuarios = self.controller.obter_lista_usuarios() 
        
        if not usuarios:
            ttk.Label(parent, text="Nenhum usuário cadastrado.", background="white").pack(pady=20)
            return

        # Treeview para exibir os usuários
        cols = ("id", "nome", "matricula", "tipo")
        tree = ttk.Treeview(parent, columns=cols, show="headings", selectmode="browse")
        
        tree.heading("id", text="ID")
        tree.heading("nome", text="Nome")
        tree.heading("matricula", text="Matrícula/Usuário")
        tree.heading("tipo", text="Permissão")
        
        tree.column("id", width=50, anchor="center")
        tree.column("nome", width=200)
        tree.column("matricula", width=150, anchor="center")
        tree.column("tipo", width=120, anchor="center")
        
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        for u in usuarios:
            # Assumindo que o Controller retorna objetos/dicionários com 'id', 'nome', 'matricula', 'tipo'
            tree.insert("", tk.END, values=(u["id"], u["nome"], u["matricula"], u["tipo"]))


        def criar_u():
            nome = simpledialog.askstring("Criar Usuário", "Digite o nome completo:")
            matricula = simpledialog.askstring("Criar Usuário", "Digite a matrícula (Usuário):")
            senha = simpledialog.askstring("Criar Usuário", "Digite a senha (texto puro):", show='*')
            
            if nome and matricula and senha:
                # ⚠️ DELEGAÇÃO: Chama o Controller para cadastrar o usuário no DB
                resultado = self.controller.cadastrar_novo_usuario(
                    nome=nome, 
                    matricula=matricula, 
                    senha_texto_puro=senha
                )
                
                if resultado['status'] == 'sucesso':
                    messagebox.showinfo("Sucesso", resultado['mensagem'])
                    # Recarrega a tela após sucesso
                    self.tela_usuarios(parent) 
                else:
                    messagebox.showerror("Erro", resultado['mensagem'])