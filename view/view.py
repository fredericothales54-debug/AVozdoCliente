import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches 
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns
import datetime

def agora_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def login_required(func):
    def wrapper(self, *args, **kwargs):
        if self.usuario_logado is None:
            messagebox.showerror("Acesso Negado", "Você deve estar logado.")
            return
        return func(self, *args, **kwargs)
    return wrapper


class AppView:
    def __init__(self, root_window, controller):
        self.root = root_window
        self.controller = controller

        self.usuario_logado = None
        self.login_win = None
        self.menu_win = None
        
        self.entry_user = None
        self.entry_pass = None

        self.tela_login()
        
    def limpar_frame(self, f):
        for w in f.winfo_children():
            w.destroy()

    def tela_login(self):
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

        ttk.Button(frm, text="Entrar", command=self.fazer_login).grid(row=2, column=0, columnspan=2, pady=12)

        frm.columnconfigure(1, weight=1)

    def fazer_login(self):
        user = self.entry_user.get().strip()
        senha = self.entry_pass.get().strip()

        ok, resp = self.controller.fazer_login(user, senha)

        if ok:
            self.usuario_logado = resp 
            self.abrir_menu()
        else:
            messagebox.showerror("Erro de Login", resp)

    def abrir_menu(self):
        self.login_win.withdraw()
        
        if self.menu_win:
             self.menu_win.destroy()
        
        self.menu_win = tk.Toplevel(self.root)
        self.menu_win.title(f"Sistema de Estoque - Logado como: {self.usuario_logado.nome}") 
        self.menu_win.geometry("1000x600")
        self.menu_win.protocol("WM_DELETE_WINDOW", self.finalizar_app)

        main_frame = tk.Frame(self.menu_win)
        main_frame.pack(fill="both", expand=True)

        sidebar = tk.Frame(main_frame, width=200, bg="#f0f0f0")
        sidebar.pack(side="left", fill="y", padx=5, pady=5)

        content = tk.Frame(main_frame, bg="white")
        content.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        ttk.Label(sidebar, text="MENU", font=("Arial", 14, "bold"), background="#f0f0f0").pack(pady=10)

        ttk.Button(sidebar, text="Consultar Produtos", command=lambda: self.tela_categorias(content)).pack(fill="x", pady=6)
        ttk.Button(sidebar, text="Relatórios", command=lambda: self.tela_relatorios(content)).pack(fill="x", pady=6)
        ttk.Button(sidebar, text="Movimentações", command=lambda: self.tela_movimentacoes(content)).pack(fill="x", pady=6)
        
        if self.usuario_logado.nome in ("TI"):
            ttk.Separator(sidebar, orient="horizontal").pack(fill="x", pady=10)
            ttk.Button(sidebar, text="Gerenciar Usuários", command=lambda: self.tela_usuarios(content)).pack(fill="x", pady=6)
            ttk.Button(sidebar, text="Adicionar Novo Item", command=lambda: self.tela_cadastro_item(content)).pack(fill="x", pady=6)

        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", pady=10)
        ttk.Button(sidebar, text="Logout", command=self.logout).pack(fill="x", pady=6)
        
        self.tela_categorias(content)

    def logout(self):
        self.usuario_logado = None
        self.menu_win.destroy()
        self.tela_login()
        
    def finalizar_app(self):
        try:
            self.controller.finalizar_app() 
        except Exception as e:
            print("erro finalizar")
        try:
            if self.menu_win and self.menu_win.winfo_exists():
                self.menu_win.destroy()
        except:
            pass
        try:
            if self.login_win and self.login_win.winfo_exists():
                self.login_win.destroy()
        except:
            pass
        try:
            self.root.quit()
            self.root.destroy()
        except:
            pass

    @login_required
    def tela_categorias(self, parent):
        self.limpar_frame(parent)
        ttk.Label(parent, text="CATEGORIAS DE PRODUTOS", font=("Arial", 16, "bold"), background="white").pack(pady=10)
        
        cats = self.controller.obter_categorias()
        
        frm_list = tk.Frame(parent, bg="white")
        frm_list.pack(fill="both", expand=True)

        listbox = tk.Listbox(frm_list, height=15, font=("Arial", 12))
        listbox.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        for cat_obj in cats: 
            listbox.insert(tk.END, cat_obj['nome']) 
            
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
        self.limpar_frame(parent)
        ttk.Label(parent, text=f"ITENS EM: {categoria.upper()}", font=("Arial", 16, "bold"), background="white").pack(pady=10)
        
        tree_frame = tk.Frame(parent, bg="white")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        tree_container = {'tree': None}
        
        def carregar_treeview():
            for w in tree_frame.winfo_children():
                w.destroy()
                
            exemplares = self.controller.listar_exemplares_por_categoria(categoria)

            cols = ("nome", "patrimonio", "status", "em_posse")
            tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
            
            tree.heading("nome", text="Nome do Item")
            tree.heading("patrimonio", text="Patrimônio")
            tree.heading("status", text="Status")
            tree.heading("em_posse", text="Em Posse de")
            
            tree.column("nome", width=250)
            tree.column("patrimonio", width=100, anchor="center")
            tree.column("status", width=100, anchor="center")
            tree.column("em_posse", width=150)
            
            tree.pack(fill="both", expand=True) 
            
            for ex in exemplares:
                chave = ex["patrimonio"] 
                nome_item = ex.get("nome", "N/A") 
                
                tree.insert("", tk.END, iid=chave, values=(nome_item, ex["patrimonio"], ex["status"], ex.get("em_posse", "N/A")))
            
            tree_container['tree'] = tree
            return tree 

        carregar_treeview()

        def requisitar_exemplar():
            tree = tree_container['tree']
            if tree is None:
                return
            sel = tree.selection()
            if not sel: 
                messagebox.showwarning("Seleção", "Selecione um item.")
                return
            pat = sel[0] 
            
            resultado, _ = self.controller.realizar_emprestimo(
                pat, 
                self.usuario_logado.id 
            )
            
            if resultado['status'] == 'sucesso':
                messagebox.showinfo("Sucesso", resultado['mensagem'])
                carregar_treeview() 
            else:
                messagebox.showerror("Erro", resultado['mensagem'])
            
        def devolver_exemplar():
            tree = tree_container['tree']
            if tree is None:
                return
            sel = tree.selection()
            if not sel: 
                messagebox.showwarning("Seleção", "Selecione um item.")
                return
            pat = sel[0]

            resultado = self.controller.gerenciar_devolucao(pat)

            if resultado['status'] == 'sucesso':
                messagebox.showinfo("Sucesso", resultado['mensagem'])
                carregar_treeview()
            else:
                messagebox.showwarning("Erro", resultado['mensagem'])
        
        def excluir_item():
            if self.usuario_logado.nome not in ("TI"):
                messagebox.showerror("Acesso Negado", "Só TI pode excluir.")
                return
            
            tree = tree_container['tree']
            if tree is None:
                return
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Seleção", "Selecione um item.")
                return
            
            pat = sel[0]
            
            conf = messagebox.askyesno(
                "Confirmar Exclusão",
                f"Excluir item?\n\nPatrimônio: {pat}\n\nNão tem volta!"
            )
            
            if not conf:
                return
            
            resultado = self.controller.excluir_produto_controller(pat)
            
            if resultado['status'] == 'sucesso':
                messagebox.showinfo("Sucesso", resultado['mensagem'])
                carregar_treeview()
            else:
                messagebox.showerror("Erro", resultado['mensagem'])
                
        action_frm = tk.Frame(parent, bg="white")
        action_frm.pack(pady=10)
        
        ttk.Button(action_frm, text="Requisitar Item", command=requisitar_exemplar).pack(side="left", padx=10)
        ttk.Button(action_frm, text="Devolver Item", command=devolver_exemplar).pack(side="left", padx=10)
        
        if self.usuario_logado.nome in ("TI"):
            ttk.Button(action_frm, text=" Excluir", command=excluir_item).pack(side="left", padx=10)
        
        ttk.Button(action_frm, text="Voltar", command=lambda: self.tela_categorias(parent)).pack(side="left", padx=10)
    
    @login_required
    def tela_relatorios(self, parent):
        self.limpar_frame(parent)
        ttk.Label(parent, text="RELATÓRIOS DO INVENTÁRIO", font=("Arial", 16, "bold"), background="white").pack(pady=10)

        dados = self.controller.obter_relatorio_status()
        
        if not dados:
             ttk.Label(parent, text="Sem dados.", background="white").pack(pady=20)
             return
             
        self.relatorio_itens_pizza(parent, dados)

    def relatorio_itens_pizza(self, parent, dados):
        fig, ax = plt.subplots(figsize=(10, 7))
        
        labels = list(dados.keys())
        sizes = list(dados.values())
        
        cores_map = {
            'DISPONÍVEL': '#4CAF50',
            'EMPRESTADO': '#FF9800',
            'EM USO': '#2196F3',
            'MANUTENÇÃO': '#F44336',
            'DANIFICADO': '#9C27B0',
            'DESCARTADO': '#607D8B'
        }
        
        cores = [cores_map.get(l, '#999999') for l in labels]
        
        def fmt(pct, vals):
            absolute = int(round(pct/100.*sum(vals)))
            return f'{pct:.1f}%\n({absolute:,})'
        
        explode = [0.05 if (size/sum(sizes))*100 < 5 else 0 for size in sizes]
        
        wedges, texts, autotexts = ax.pie(
            sizes, 
            labels=labels,
            autopct=lambda pct: fmt(pct, sizes),
            startangle=90,
            colors=cores,
            explode=explode,
            shadow=True,
            wedgeprops={'edgecolor': 'white', 'linewidth': 2}
        )
        
        for text in texts:
            text.set_fontsize(11)
            text.set_fontweight('bold')
            text.set_color('white')
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(10)
            autotext.set_fontweight('bold')
        
        ax.axis('equal')
        
        plt.title('Distribuição de Itens por Status', 
                  fontsize=16, 
                  fontweight='bold',
                  pad=20)
        
        ax.legend(
            wedges, 
            [f'{l}: {s:,} itens' for l, s in zip(labels, sizes)],
            title="Status",
            loc="center left",
            bbox_to_anchor=(1, 0, 0.5, 1),
            fontsize=10,
            title_fontsize=12
        )
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        canvas.draw()
        
    @login_required
    def tela_movimentacoes(self, parent):
        self.limpar_frame(parent)
        ttk.Label(parent, text="HISTÓRICO DE MOVIMENTAÇÕES", font=("Arial", 16, "bold"), background="white").pack(pady=10)

        movs = self.controller.obter_historico_movimentacoes()
        
        if not movs:
             ttk.Label(parent, text="Sem movimentações.", background="white").pack(pady=20)
             return

        cols = ("timestamp", "tipo", "patrimonio", "item", "usuario")
        tree = ttk.Treeview(parent, columns=cols, show="headings")
        
        tree.heading("timestamp", text="Data/Hora", anchor="center")
        tree.heading("tipo", text="Tipo", anchor="center")
        tree.heading("patrimonio", text="Patrimônio", anchor="center")
        tree.heading("item", text="Item", anchor="w")
        tree.heading("usuario", text="Usuário", anchor="center")
        
        tree.column("timestamp", width=150, anchor="center")
        tree.column("tipo", width=100, anchor="center")
        tree.column("patrimonio", width=100, anchor="center")
        tree.column("item", width=300, anchor="w")
        tree.column("usuario", width=120, anchor="center")
        
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        for mov in movs:
            det = mov.get("detalhes", {})
            
            if isinstance(det, dict):
                pat = det.get("patrimonio", "N/A")
                item_nome = det.get("item_nome", "N/A")
                usr = det.get("usuario", "Sistema")
            else:
                pat = "N/A"
                item_nome = str(det)
                usr = "Sistema"
            
            tree.insert("", tk.END, values=(
                mov["ts"], 
                mov["tipo"], 
                pat,
                item_nome,
                usr
            ))
            
    @login_required
    def tela_cadastro_item(self, parent):
        self.limpar_frame(parent)
        if self.usuario_logado.nome not in ("TI"):
            messagebox.showerror("Acesso", "Sem permissão.")
            return

        ttk.Label(parent, text="CADASTRO DE NOVO ITEM", font=("Arial", 16, "bold"), background="white").pack(pady=10)

        form_frame = tk.Frame(parent, bg="white", padx=20, pady=20)
        form_frame.pack(pady=10)

        nomes = self.controller.obter_nomes_itens()
        locais_dados = self.controller.obter_locais()
        
        locais_map = {loc['descricao']: loc['id'] for loc in locais_dados}
        locais_desc = list(locais_map.keys())
        
        nome_var = tk.StringVar()
        pat_var = tk.StringVar()
        local_var = tk.StringVar()
        
        def criar():
            nome = nome_var.get()
            pat = pat_var.get().strip()
            local_desc = local_var.get()
    
            if not nome or not pat or not local_desc:
                messagebox.showwarning("Aviso", "Preencha tudo.")
                return

            local_id = locais_map.get(local_desc)
            
            if not local_id:
                messagebox.showerror("Erro", "Local inválido.")
                return
    
            resultado = self.controller.cadastrar_item_interface(nome, pat, local_id)
    
            if resultado['status'] == 'sucesso':
                messagebox.showinfo("Sucesso", resultado['mensagem'])
                nome_var.set('')
                pat_var.set('')
                local_var.set('')
            else:
                messagebox.showerror("Erro", resultado['mensagem'])

        row = 0
        tk.Label(form_frame, text="Nome/Tipo:", bg="white").grid(row=row, column=0, sticky="w", pady=5, padx=5)
        ttk.Combobox(form_frame, textvariable=nome_var, values=nomes, state="readonly").grid(row=row, column=1, sticky="ew", pady=5, padx=5)
        
        row += 1
        tk.Label(form_frame, text="Nº Patrimônio:", bg="white").grid(row=row, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(form_frame, textvariable=pat_var).grid(row=row, column=1, sticky="ew", pady=5, padx=5)

        row += 1
        tk.Label(form_frame, text="Local:", bg="white").grid(row=row, column=0, sticky="w", pady=5, padx=5)
        ttk.Combobox(form_frame, textvariable=local_var, values=locais_desc, state="readonly").grid(row=row, column=1, sticky="ew", pady=5, padx=5)
        
        row += 1
        ttk.Button(form_frame, text="Cadastrar", command=criar).grid(row=row, column=0, columnspan=2, pady=20)
    
    @login_required
    def tela_usuarios(self, parent):
        self.limpar_frame(parent)
        if self.usuario_logado.nome not in ("TI"):
            messagebox.showerror("Acesso", "Sem permissão.")
            return

        ttk.Label(parent, text="GERENCIAMENTO DE USUÁRIOS", font=("Arial", 16, "bold"), background="white").pack(pady=10)

        usuarios = self.controller.obter_lista_usuarios()
        
        if not usuarios:
            ttk.Label(parent, text="Sem usuários.", background="white").pack(pady=20)
            return

        cols = ("id", "nome", "matricula", "tipo")
        tree = ttk.Treeview(parent, columns=cols, show="headings", selectmode="browse")
        
        tree.heading("id", text="ID")
        tree.heading("nome", text="Nome")
        tree.heading("matricula", text="Matrícula")
        tree.heading("tipo", text="Permissão")
        
        tree.column("id", width=50, anchor="center")
        tree.column("nome", width=200)
        tree.column("matricula", width=150, anchor="center")
        tree.column("tipo", width=120, anchor="center")
        
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        for u in usuarios:
            tree.insert("", tk.END, values=(u["id"], u["nome"], u["matricula"], u["tipo"]))

        def criar():
            nome = simpledialog.askstring("Criar", "Nome completo:")
            if not nome:
                return
                
            mat = simpledialog.askstring("Criar", "Matrícula:")
            if not mat:
                return
                
            senha = simpledialog.askstring("Criar", "Senha:", show='*')
            if not senha:
                return
            
            resultado = self.controller.cadastrar_novo_usuario_controller(
                nome=nome, 
                matricula=mat, 
                senha_texto_puro=senha
            )
            
            if resultado['status'] == 'sucesso':
                messagebox.showinfo("Sucesso", resultado['mensagem'])
                self.tela_usuarios(parent)
            else:
                messagebox.showerror("Erro", resultado['mensagem'])
        
        def excluir():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Seleção", "Selecione um usuário.")
                return
            
            item = tree.item(sel[0])
            vals = item['values']
            user_id = vals[0]
            nome = vals[1]
            
            if nome == "TI":
                messagebox.showerror("Erro", "Não pode apagar TI.")
                return
            
            itens_emp = self.controller.verificar_itens_emprestados_usuario(user_id)
            
            if itens_emp > 0:
                messagebox.showerror(
                    "Erro", 
                    f"Usuario '{nome}' tem {itens_emp} item(ns) emprestado(s)."
                )
                return
            
            conf = messagebox.askyesno(
                "Confirmar",
                f"Excluir usuário:\n\n{nome}\n\nNão tem volta!"
            )
            
            if not conf:
                return
            
            resultado = self.controller.excluir_usuario_controller(user_id, nome)
            
            if resultado['status'] == 'sucesso':
                messagebox.showinfo("Sucesso", resultado['mensagem'])
                self.tela_usuarios(parent)
            else:
                messagebox.showerror("Erro", resultado['mensagem'])
                    
        btn_frm = tk.Frame(parent, bg="white")
        btn_frm.pack(pady=10)
        ttk.Button(btn_frm, text="➕ Cadastrar", command=criar).pack(side="left", padx=10)
        ttk.Button(btn_frm, text="🗑️ Excluir", command=excluir).pack(side="left", padx=10)