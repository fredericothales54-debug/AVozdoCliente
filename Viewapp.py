import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
import datetime
import json
import os
import sys

sns.set_theme(style="whitegrid")

# ---------- ARQUIVOS JSON ----------
USUARIOS_FILE = "usuarios.json"
CATEGORIAS_FILE = "categorias.json"
ITENS_FILE = "itens.json"
HISTORICO_FILE = "historico.json"

# -------------------------
# Dados iniciais (em memória)
# -------------------------
_default_usuarios = [
    {"usuario": "admin", "senha": "0000", "tipo": "CORDENADOR"},
    {"usuario": "user", "senha": "1234", "tipo": "PROFESSOR"},
    {"usuario": "root", "senha": "9999", "tipo": "DIRETOR"}
]

_default_categorias = {
    "Ambientes": {
        "Auditório": 1,
        "Sala de Inovação / Ideação": 1,
        "Laboratório Maker": 1,
        "Laboratório de Informática 1": 1,
        "Laboratório de Informática 2": 1,
        "Laboratório de Informática 3": 1,
        "Laboratório de Informática 4": 1
    },
    "Equipamentos de Tecnologia": {
        "Notebook Core i3": 40,
        "Notebook Core i7": 36,
        "Computador Desktop Completo": 20,
        "Monitor 24 polegadas": 25,
        "Mouse USB": 60,
        "Teclado USB": 55,
        "Headset com Microfone": 35,
        "Pen Drive 32GB": 40,
        "Tablet 10\"": 15,
        "Leitor de código de barras": 10,
        "Impressora Laser": 6,
        "Multifuncional": 4,
        "Scanner": 2
    },
    "Infraestrutura e Conectividade": {
        "Roteador Wi-Fi": 8,
        "Switch 24 portas": 6,
        "Patch Cords diversos": 50,
        "Cabo HDMI 1.8m": 30,
        "Cabo VGA 1.5m": 15,
        "Adaptador USB-C → HDMI": 12,
        "Nobreak 1400VA": 5,
        "Estabilizador 500VA": 18,
        "Extensão elétrica 5 tomadas": 40
    },
    "Audiovisual e Apresentação": {
        "Datashow Projetor": 4,
        "Projetor portátil mini": 2,
        "Caixa de Som Amplificada": 3,
        "Microfone sem fio": 4,
        "Tripé para projetor": 4
    },
    "Mobiliário e Estrutura": {
        "Mesa de Professor": 15,
        "Mesa de Escritório": 10,
        "Cadeira Giratória": 25,
        "Cadeira Escolar": 120,
        "Armário de Aço 2 portas": 8,
        "Estante de Livros": 6,
        "Ar-Condicionado 12.000 BTU": 10,
        "Ar-Condicionado 18.000 BTU": 4,
        "Quadro Branco pequeno": 20,
        "Caixa organizadora plástica": 60,
        "Câmera de segurança": 12
    },
    "Papelaria e Escritório": {
        "Resma de Papel A4": 200,
        "Caneta Azul": 300,
        "Caneta Preta": 300,
        "Caneta Vermelha": 150,
        "Lápis": 500,
        "Borracha": 200,
        "Apontador": 120,
        "Grampeador": 20,
        "Caixa de Grampos": 150,
        "Cola Bastão": 200,
        "Cola Líquida": 80,
        "Post-it bloco pequeno": 90,
        "Caderno 96 folhas": 180,
        "Pasta catálogo": 70,
        "Pasta L": 500,
        "Envelope pardo": 300,
        "Marcador de Quadro Branco": 200,
        "Tesoura escolar": 120,
        "Régua 30cm": 150,
        "Fita adesiva": 100,
        "Fita dupla face": 60
    }
}

# memória (serão carregadas do JSON ou geradas inicialmente)
usuarios = []
categorias = {}
itens_exemplares = {}   # chave -> dict exemplar
_item_group_counter = defaultdict(int)
movimentacoes = []
criacao_exclusao = []

# -------------------------
# Utilitários de data e IO
# -------------------------
def agora_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def salvar_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def carregar_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_todos():
    try:
        salvar_json(USUARIOS_FILE, usuarios)
        salvar_json(CATEGORIAS_FILE, categorias)
        salvar_json(ITENS_FILE, itens_exemplares)
        salvar_json(HISTORICO_FILE, {"movimentacoes": movimentacoes, "criacao_exclusao": criacao_exclusao})
    except Exception as e:
        messagebox.showerror("ERRO AO SALVAR", f"Não foi possível salvar: {e}")

def carregar_todos():
    global usuarios, categorias, itens_exemplares, movimentacoes, criacao_exclusao, _item_group_counter
    if os.path.exists(USUARIOS_FILE) and os.path.exists(CATEGORIAS_FILE) and os.path.exists(ITENS_FILE) and os.path.exists(HISTORICO_FILE):
        try:
            usuarios = carregar_json(USUARIOS_FILE)
            categorias = carregar_json(CATEGORIAS_FILE)
            itens_exemplares = carregar_json(ITENS_FILE)
            histor = carregar_json(HISTORICO_FILE)
            movimentacoes = histor.get("movimentacoes", [])
            criacao_exclusao = histor.get("criacao_exclusao", [])
            _item_group_counter = defaultdict(int)
            for chave in itens_exemplares.keys():
                try:
                    nome, patr = chave.split(" | ")
                    group = int(patr.split("-")[0])
                    _item_group_counter[nome] = max(_item_group_counter[nome], group)
                except Exception:
                    pass
            return True
        except Exception as e:
            messagebox.showwarning("AVISO", f"Falha ao carregar arquivos JSON: {e}\nGerando dados padrão.")
    usuarios = [u.copy() for u in _default_usuarios]
    categorias = {k: v.copy() for k, v in _default_categorias.items()}
    itens_exemplares.clear()
    _item_group_counter.clear()
    movimentacoes.clear()
    criacao_exclusao.clear()
    gerar_exemplares_iniciais()
    salvar_todos()
    return False

# -------------------------
# Gerar exemplares (001...N) para cada item nome
# -------------------------
def gerar_exemplares_iniciais():
    for categoria, itens in categorias.items():
        for nome, qtd in itens.items():
            _item_group_counter[nome] += 1
            group_id = _item_group_counter[nome]
            for i in range(1, qtd + 1):
                patrimonio = f"{group_id:04d}-{i:04d}"
                chave = f"{nome} | {patrimonio}"
                itens_exemplares[chave] = {
                    "nome": nome,
                    "patrimonio": patrimonio,
                    "categoria": categoria,
                    "status": "Disponível",
                    "em_posse": ""
                }

# -------------------------
# Helpers para scroll com mouse wheel (bind local ao widget)
# -------------------------
def _bind_mousewheel(widget):
    # Bind wheel events directly on widget (avoids global bind_all)
    if os.name == "nt":
        widget.bind("<MouseWheel>", lambda e: widget.yview_scroll(int(-1*(e.delta/120)), "units"))
    elif sys_platform_is_mac():
        widget.bind("<MouseWheel>", lambda e: widget.yview_scroll(int(-1*(e.delta)), "units"))
    else:
        widget.bind("<Button-4>", lambda e: widget.yview_scroll(-1, "units"))
        widget.bind("<Button-5>", lambda e: widget.yview_scroll(1, "units"))

def sys_platform_is_mac():
    return os.name == "posix" and getattr(sys, 'platform', '').startswith('darwin')

# -------------------------
# Decorator exige login
# -------------------------
def exige_login(func):
    def wrapper(*a, **k):
        if usuario_logado is None:
            messagebox.showerror("ERRO", "FAÇA LOGIN PRIMEIRO.")
            return
        return func(*a, **k)
    return wrapper

# -------------------------
# Funções de negócio (UI)
# -------------------------
usuario_logado = None
root = None
login_win = None
entry_user = None
entry_pass = None

def fazer_login():
    global usuario_logado
    user = entry_user.get().strip()
    senha = entry_pass.get().strip()
    for u in usuarios:
        if u["usuario"] == user and u["senha"] == senha:
            usuario_logado = u
            abrir_menu()
            return
    messagebox.showerror("ERRO", "USUÁRIO OU SENHA INVÁLIDOS.")

def abrir_menu():
    login_win.withdraw()
    top = tk.Toplevel(root)
    top.title("SISTEMA DE ESTOQUE")
    top.configure(bg="white")
    top.geometry("920x600")

    header = tk.Frame(top, bg="white")
    header.pack(fill="x", pady=8)
    label_user = tk.Label(header, text=f"{usuario_logado['usuario']} ({usuario_logado['tipo']})", fg="blue", bg="white", cursor="hand2")
    label_user.pack(side="right", padx=12)
    def on_user_click(e=None):
        resp = messagebox.askyesno("SAIR", "DESEJA SAIR DA CONTA?")
        if resp:
            top.destroy()
            login_win.deiconify()
            global usuario_logado
            usuario_logado = None
    label_user.bind("<Button-1>", on_user_click)

    frame = tk.Frame(top, bg="white")
    frame.pack(expand=True, fill="both", padx=12, pady=6)

    sidebar = tk.Frame(frame, width=260, bg="white")
    sidebar.pack(side="left", fill="y", padx=(0,8))
    content = tk.Frame(frame, bg="white")
    content.pack(side="right", expand=True, fill="both")

    ttk.Button(sidebar, text="CONSULTAR PRODUTOS", command=lambda: tela_categorias(content)).pack(fill="x", pady=6)
    ttk.Button(sidebar, text="REQUISIÇÕES", command=lambda: tela_requisicoes(content)).pack(fill="x", pady=6)
    ttk.Button(sidebar, text="RELATÓRIOS", command=lambda: tela_relatorios(content)).pack(fill="x", pady=6)

    # permissões: CORDENADOR/DIRETOR/ACCESSFULL podem criar/excluir itens
    if usuario_logado["tipo"] in ["CORDENADOR", "DIRETOR", "ACCESSFULL"]:
        ttk.Button(sidebar, text="CRIAR / EXCLUIR ITENS", command=lambda: tela_criar_excluir(content)).pack(fill="x", pady=6)

    # GERENCIAR USUÁRIOS apenas para DIRETOR (você confirmou "sim" para permitir criar outros DIRETORES)
    if usuario_logado["tipo"] == "DIRETOR":
        ttk.Button(sidebar, text="GERENCIAR USUÁRIOS", command=lambda: tela_usuarios(content)).pack(fill="x", pady=6)

    ttk.Button(sidebar, text="SAIR DO APP", command=root.destroy).pack(side="bottom", fill="x", pady=10)

    tela_categorias(content)

# ---------- telas ----------
def limpar_frame(f):
    for w in f.winfo_children():
        w.destroy()

@exige_login
def tela_categorias(parent):
    limpar_frame(parent)
    ttk.Label(parent, text="CATEGORIAS", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(2,8))

    listbox_frame = tk.Frame(parent, bg="white")
    listbox_frame.pack(fill="both", expand=False)
    listbox = tk.Listbox(listbox_frame, height=10)
    listbox.pack(side="left", fill="both", expand=True, pady=4)
    vsb = ttk.Scrollbar(listbox_frame, orient="vertical", command=listbox.yview)
    listbox.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")

    for c in categorias.keys():
        listbox.insert(tk.END, c.upper())

    _bind_mousewheel(listbox)

    btn_frame = tk.Frame(parent, bg="white")
    btn_frame.pack(fill="x", pady=6)
    def abrir_cat():
        sel = listbox.curselection()
        if not sel:
            messagebox.showinfo("SELEÇÃO", "ESCOLHA UMA CATEGORIA.")
            return
        cat = listbox.get(sel[0])
        abrir_itens_categoria(parent, cat)
    ttk.Button(btn_frame, text="ABRIR", command=abrir_cat).pack(side="left")

def abrir_itens_categoria(parent, categoria):
    limpar_frame(parent)
    ttk.Label(parent, text=f"ITENS — {categoria}", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(2,8))

    # colocar tree + scrollbar dentro de frame para scrollbar maior
    tree_frame = tk.Frame(parent, bg="white")
    tree_frame.pack(expand=True, fill="both", pady=6)

    cols = ("NOME","PATRIMÔNIO","STATUS","EM_POSSE")
    tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, width=160, anchor="w")
    tree.pack(side="left", expand=True, fill="both")

    vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y", padx=(0,4))
    _bind_mousewheel(tree)

    # preencher
    for chave, ex in itens_exemplares.items():
        if ex["categoria"].upper() == categoria.upper():
            tree.insert("", tk.END, iid=chave, values=(ex["nome"].upper(), ex["patrimonio"], ex["status"].upper(), (ex["em_posse"] or "-").upper()))

    btns = tk.Frame(parent, bg="white")
    btns.pack(fill="x", pady=8)

    def ver_detalhe():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("SELEÇÃO", "ESCOLHA UM EXEMPLAR.")
            return
        chave = sel[0]
        ex = itens_exemplares[chave]
        detalhe_janela = tk.Toplevel(root)
        detalhe_janela.title(f"DETALHE — {chave}")
        detalhe_janela.configure(bg="white")
        for k, v in ex.items():
            ttk.Label(detalhe_janela, text=f"{k.upper()}: {str(v).upper()}").pack(anchor="w", padx=8, pady=2)

    def requisitar_exemplar():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("SELEÇÃO", "ESCOLHA UM EXEMPLAR PARA REQUISITAR.")
            return
        chave = sel[0]
        ex = itens_exemplares[chave]
        if ex["status"] != "Disponível":
            messagebox.showwarning("INDISPONÍVEL", "EXEMPLAR NÃO ESTÁ DISPONÍVEL.")
            return
        ex["status"] = "Em uso"
        ex["em_posse"] = usuario_logado["usuario"]
        movimentacoes.append({"tipo":"SAIDA","patrimonio":ex["patrimonio"], "usuario":usuario_logado["usuario"], "ts":agora_str(), "nome":ex["nome"]})
        tree.item(chave, values=(ex["nome"].upper(), ex["patrimonio"], ex["status"].upper(), ex["em_posse"].upper()))
        salvar_todos()
        messagebox.showinfo("OK", "REQUISIÇÃO REGISTRADA.")

    def devolver_exemplar():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("SELEÇÃO", "ESCOLHA UM EXEMPLAR PARA DEVOLVER.")
            return
        chave = sel[0]
        ex = itens_exemplares[chave]
        if ex["status"] != "Em uso":
            messagebox.showwarning("ERRO", "EXEMPLAR NÃO ESTÁ EMPRESTADO.")
            return
        usuario_posse = ex["em_posse"]
        ex["status"] = "Disponível"
        ex["em_posse"] = ""
        movimentacoes.append({"tipo":"ENTRADA","patrimonio":ex["patrimonio"], "usuario":usuario_logado["usuario"], "ts":agora_str(), "nome":ex["nome"]})
        tree.item(chave, values=(ex["nome"].upper(), ex["patrimonio"], ex["status"].upper(), "-"))
        salvar_todos()
        messagebox.showinfo("OK", f"DEVOLVIDO (ANTERIOR: {usuario_posse}).")

    def excluir_exemplar():
        if usuario_logado["tipo"] not in ["CORDENADOR","DIRETOR","ACCESSFULL"]:
            messagebox.showerror("PERMISSÃO", "APENAS CORDENADOR/DIRETOR/ACCESSFULL PODEM EXCLUIR EXEMPLARES.")
            return
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("SELEÇÃO", "ESCOLHA UM EXEMPLAR PARA EXCLUIR.")
            return
        chave = sel[0]
        ex = itens_exemplares.pop(chave, None)
        if ex:
            criacao_exclusao.append({"acao":"EXCLUSAO","nome":ex["nome"],"usuario":usuario_logado["usuario"],"ts":agora_str()})
            tree.delete(chave)
            salvar_todos()
            messagebox.showinfo("OK", "EXEMPLAR EXCLUÍDO.")

    ttk.Button(btns, text="DETALHE", command=ver_detalhe).pack(side="left", padx=4)
    ttk.Button(btns, text="REQUISITAR", command=requisitar_exemplar).pack(side="left", padx=4)
    ttk.Button(btns, text="DEVOLVER", command=devolver_exemplar).pack(side="left", padx=4)
    ttk.Button(btns, text="EXCLUIR (ADMIN)", command=excluir_exemplar).pack(side="left", padx=4)

@exige_login
def tela_requisicoes(parent):
    limpar_frame(parent)
    ttk.Label(parent, text="REQUISIÇÕES (TODOS OS EXEMPLARES)", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(2,8))

    tree_frame = tk.Frame(parent, bg="white")
    tree_frame.pack(expand=True, fill="both")

    cols = ("NOME","PATRIMÔNIO","STATUS","EM_POSSE")
    tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, width=180)
    tree.pack(side="left", expand=True, fill="both")

    for chave, ex in itens_exemplares.items():
        tree.insert("", tk.END, iid=chave, values=(ex["nome"].upper(), ex["patrimonio"], ex["status"].upper(), (ex["em_posse"] or "-").upper()))

    vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y", padx=(0,4))
    _bind_mousewheel(tree)

    btns = tk.Frame(parent, bg="white")
    btns.pack(fill="x", pady=8)

    def requisitar_sel():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("SELEÇÃO", "ESCOLHA UM EXEMPLAR.")
            return
        chave = sel[0]
        ex = itens_exemplares[chave]
        if ex["status"] != "Disponível":
            messagebox.showwarning("INDISPONÍVEL", "EXEMPLAR NÃO ESTÁ DISPONÍVEL.")
            return
        ex["status"]="Em uso"
        ex["em_posse"]=usuario_logado["usuario"]
        movimentacoes.append({"tipo":"SAIDA","patrimonio":ex["patrimonio"],"usuario":usuario_logado["usuario"], "ts":agora_str(), "nome":ex["nome"]})
        tree.item(chave, values=(ex["nome"].upper(), ex["patrimonio"], ex["status"].upper(), ex["em_posse"].upper()))
        salvar_todos()
        messagebox.showinfo("OK","REQUISIÇÃO REGISTRADA.")

    def devolver_sel():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("SELEÇÃO", "ESCOLHA UM EXEMPLAR.")
            return
        chave = sel[0]
        ex = itens_exemplares[chave]
        if ex["status"]!="Em uso":
            messagebox.showwarning("ERRO", "EXEMPLAR NÃO ESTÁ EMPRESTADO.")
            return
        ex["status"]="Disponível"
        ex["em_posse"]=""
        movimentacoes.append({"tipo":"ENTRADA","patrimonio":ex["patrimonio"],"usuario":usuario_logado["usuario"], "ts":agora_str(), "nome":ex["nome"]})
        tree.item(chave, values=(ex["nome"].upper(), ex["patrimonio"], ex["status"].upper(), "-"))
        salvar_todos()
        messagebox.showinfo("OK","DEVOLUÇÃO REGISTRADA.")

    ttk.Button(btns, text="REQUISITAR", command=requisitar_sel).pack(side="left", padx=6)
    ttk.Button(btns, text="DEVOLVER", command=devolver_sel).pack(side="left", padx=6)

@exige_login
def tela_relatorios(parent):
    limpar_frame(parent)
    ttk.Label(parent, text="RELATÓRIOS", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(2,8))

    btn_frame = tk.Frame(parent, bg="white")
    btn_frame.pack(fill="x", pady=6)

    ttk.Button(btn_frame, text="RELATÓRIO DE ITENS (PIZZA)", command=relatorio_itens_pizza).pack(side="left", padx=6)
    ttk.Button(btn_frame, text="MOVIMENTAÇÕES (COUNTPLOT)", command=relatorio_movimentacoes).pack(side="left", padx=6)
    ttk.Button(btn_frame, text="CRIAÇÕES/EXCLUSÕES (COUNTPLOT)", command=relatorio_criacoes).pack(side="left", padx=6)

    info = tk.Text(parent, height=10)
    info.pack(expand=True, fill="both", pady=8)
    info.insert("end", "USE OS BOTÕES ACIMA PARA VISUALIZAR GRÁFICOS.\nRESUMO RÁPIDO:\n")
    total = len(itens_exemplares)
    disp = sum(1 for v in itens_exemplares.values() if v["status"].lower()=="disponível")
    uso = sum(1 for v in itens_exemplares.values() if v["status"].lower()=="em uso")
    info.insert("end", f"TOTAL EXEMPLARES: {total}\nDISPONÍVEIS: {disp}\nEM USO: {uso}\nMOVIMENTAÇÕES REGISTRADAS: {len(movimentacoes)}\nREGISTROS DE CRIAÇÃO/EXCLUSÃO: {len(criacao_exclusao)}")

# GRÁFICOS / RELATÓRIOS
def relatorio_itens_pizza():
    statuses = [v["status"] for v in itens_exemplares.values()]
    disp = sum(1 for s in statuses if s.lower() == "disponível")
    uso = sum(1 for s in statuses if s.lower() == "em uso")
    outros = len(statuses) - disp - uso
    labels = []
    sizes = []
    if disp:
        labels.append("DISPONÍVEL"); sizes.append(disp)
    if uso:
        labels.append("EM USO"); sizes.append(uso)
    if outros:
        labels.append("OUTROS"); sizes.append(outros)
    if not sizes:
        messagebox.showinfo("RELATÓRIO", "SEM ITENS PARA MOSTRAR.")
        return

    pal = sns.color_palette("pastel", len(sizes))
    plt.figure(figsize=(6,6))
    plt.pie(sizes, labels=labels, autopct="%1.1f%%", colors=pal, startangle=90, wedgeprops={"edgecolor":"white"})
    plt.title("DISTRIBUIÇÃO DE STATUS DOS EXEMPLARES")
    plt.axis("equal")
    plt.show()

def relatorio_movimentacoes():
    if not movimentacoes:
        messagebox.showinfo("MOVIMENTAÇÕES", "NENHUMA MOVIMENTAÇÃO REGISTRADA.")
        return
    tipos = [m["tipo"] for m in movimentacoes]
    plt.figure(figsize=(7,4))
    sns.countplot(x=tipos, palette="muted")
    plt.title("CONTAGEM DE MOVIMENTAÇÕES (ENTRADA/SAÍDA)")
    plt.xlabel("TIPO")
    plt.ylabel("CONTAGEM")
    plt.show()

def relatorio_criacoes():
    if not criacao_exclusao:
        messagebox.showinfo("HISTÓRICO", "NENHUMA CRIAÇÃO/EXCLUSÃO REGISTRADA.")
        return
    acoes = [r["acao"] for r in criacao_exclusao]
    plt.figure(figsize=(7,4))
    sns.countplot(x=acoes, palette="viridis")
    plt.title("CRIAÇÕES VS EXCLUSÕES")
    plt.xlabel("AÇÃO")
    plt.ylabel("CONTAGEM")
    plt.show()

@exige_login
def tela_criar_excluir(parent):
    limpar_frame(parent)
    ttk.Label(parent, text="GERENCIAR ITENS", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(2,8))

    frm = tk.Frame(parent, bg="white")
    frm.pack(fill="x", pady=6)
    ttk.Button(frm, text="CRIAR NOVO GRUPO DE ITENS", command=criar_grupo_item).pack(side="left", padx=6)
    ttk.Button(frm, text="EXCLUIR GRUPO (TODOS EXEMPLARES)", command=excluir_grupo_item).pack(side="left", padx=6)
    ttk.Button(frm, text="EXCLUIR ITENS (QUANTIDADE)", command=excluir_itens_quantidade).pack(side="left", padx=6)

    tree_frame = tk.Frame(parent, bg="white")
    tree_frame.pack(expand=True, fill="both", pady=8)

    cols = ("NOME","PATRIMÔNIO","CATEGORIA","STATUS")
    tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, width=180)
    tree.pack(side="left", expand=True, fill="both")

    vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y", padx=(0,4))
    _bind_mousewheel(tree)

    for chave, ex in itens_exemplares.items():
        tree.insert("", tk.END, iid=chave, values=(ex["nome"].upper(), ex["patrimonio"], ex["categoria"].upper(), ex["status"].upper()))

def criar_grupo_item():
    nome = simpledialog.askstring("CRIAR GRUPO", "NOME DO ITEM (GRUPO):")
    if not nome:
        return
    try:
        qtd_raw = simpledialog.askstring("QUANTIDADE", "QUANTIDADE DE EXEMPLARES:")
        qtd = int(qtd_raw)
        cat = simpledialog.askstring("CATEGORIA", "CATEGORIA (EX: PAPELARIA E ESCRITÓRIO):")
        if not cat:
            messagebox.showwarning("CATEGORIA", "INFORME UMA CATEGORIA.")
            return
    except Exception:
        messagebox.showerror("ERRO", "QUANTIDADE INVÁLIDA.")
        return

    if cat not in categorias:
        categorias[cat] = {}
    _item_group_counter[nome] += 1
    group_id = _item_group_counter[nome]
    for i in range(1, qtd+1):
        patrimonio = f"{group_id:04d}-{i:04d}"
        chave = f"{nome} | {patrimonio}"
        itens_exemplares[chave] = {"nome":nome,"patrimonio":patrimonio,"categoria":cat,"status":"Disponível","em_posse":""}
    criacao_exclusao.append({"acao":"CRIACAO","nome":nome,"usuario":usuario_logado["usuario"],"ts":agora_str()})
    salvar_todos()
    messagebox.showinfo("OK", f"{qtd} EXEMPLARES DE '{nome}' CRIADOS.")

def excluir_grupo_item():
    # EXCLUSÃO DE GRUPO APENAS PARA DIRETOR (EXATO)
    if usuario_logado["tipo"] != "DIRETOR":
        messagebox.showerror("PERMISSÃO", "APENAS DIRETOR PODE EXCLUIR GRUPOS.")
        return
    nome = simpledialog.askstring("EXCLUIR GRUPO", "NOME DO ITEM (GRUPO) PARA EXCLUIR TOTALMENTE:")
    if not nome:
        return
    removidos = [k for k,v in list(itens_exemplares.items()) if v["nome"].lower() == nome.lower()]
    if not removidos:
        messagebox.showinfo("INFO", "NENHUM EXEMPLAR ENCONTRADO PARA ESSE NOME.")
        return
    confirm = messagebox.askyesno("CONFIRMAR", f"REMOVER {len(removidos)} EXEMPLARES DO GRUPO '{nome}'? ESTA AÇÃO NÃO PODE SER DESFEITA.")
    if not confirm:
        return
    for k in removidos:
        itens_exemplares.pop(k, None)
    criacao_exclusao.append({"acao":"EXCLUSAO_GRUPO","nome":nome,"usuario":usuario_logado["usuario"],"ts":agora_str()})
    salvar_todos()
    messagebox.showinfo("OK", f"{len(removidos)} EXEMPLARES REMOVIDOS DO GRUPO '{nome}'.")

def excluir_itens_quantidade():
    # remover N exemplares de um grupo (apenas DIRETOR ou CORDENADOR/ACCESSFULL allowed)
    if usuario_logado["tipo"] not in ["DIRETOR","CORDENADOR","ACCESSFULL"]:
        messagebox.showerror("PERMISSÃO", "APENAS DIRETOR/CORDENADOR/ACCESSFULL PODEM REMOVER ITENS.")
        return
    nome = simpledialog.askstring("EXCLUIR ITENS", "NOME DO ITEM (GRUPO) PARA REMOVER EXEMPLARES:")
    if not nome:
        return
    # listar exemplares do grupo
    exemplares = sorted([k for k,v in itens_exemplares.items() if v["nome"].lower() == nome.lower()])
    if not exemplares:
        messagebox.showinfo("INFO", "NENHUM EXEMPLAR ENCONTRADO PARA ESSE NOME.")
        return
    qtd_raw = simpledialog.askstring("QUANTIDADE", f"ENCONTRADOS {len(exemplares)} EXEMPLARES. QUANTOS DESEJA REMOVER?")
    try:
        qtd = int(qtd_raw)
    except Exception:
        messagebox.showerror("ERRO", "QUANTIDADE INVÁLIDA.")
        return
    if qtd <= 0:
        messagebox.showinfo("INFO", "NENHUMA REMOÇÃO REALIZADA.")
        return
    qtd = min(qtd, len(exemplares))
    confirm = messagebox.askyesno("CONFIRMAR", f"REMOVER {qtd} EXEMPLARES DO GRUPO '{nome}'?")
    if not confirm:
        return
    # remove os últimos exemplares (ou primeiros) — escolhi remover os últimos para manter menores patrimonios
    to_remove = exemplares[-qtd:]
    for k in to_remove:
        itens_exemplares.pop(k, None)
    criacao_exclusao.append({"acao":"EXCLUSAO_PARCIAL","nome":nome,"usuario":usuario_logado["usuario"],"quantidade":qtd,"ts":agora_str()})
    salvar_todos()
    messagebox.showinfo("OK", f"{qtd} EXEMPLARES REMOVIDOS DO GRUPO '{nome}'.")

@exige_login
def tela_usuarios(parent):
    limpar_frame(parent)
    ttk.Label(parent, text="GERENCIAR USUÁRIOS (ACESSO: DIRETOR)", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(2,8))

    list_frame = tk.Frame(parent, bg="white")
    list_frame.pack(fill="both", expand=False)
    listbox = tk.Listbox(list_frame, height=8)
    listbox.pack(side="left", fill="both", expand=True, pady=6)
    vsb = ttk.Scrollbar(list_frame, orient="vertical", command=listbox.yview)
    listbox.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")
    _bind_mousewheel(listbox)

    def refresh_list():
        listbox.delete(0, tk.END)
        for u in usuarios:
            listbox.insert(tk.END, f"{u['usuario']} ({u['tipo']})")

    refresh_list()

    frm = tk.Frame(parent, bg="white")
    frm.pack(fill="x", pady=6)
    def criar_u():
        if usuario_logado["tipo"] != "DIRETOR":
            messagebox.showerror("PERMISSÃO", "APENAS DIRETOR PODE CRIAR USUÁRIOS.")
            return
        nome = simpledialog.askstring("USUÁRIO", "NOME DO USUÁRIO:")
        if not nome: return
        senha = simpledialog.askstring("SENHA", "SENHA:")
        if senha is None: return
        tipo = simpledialog.askstring("TIPO", "PROFESSOR / CORDENADOR / DIRETOR / ACCESSFULL:")
        if not tipo:
            messagebox.showerror("ERRO", "TIPO INVÁLIDO.")
            return
        usuarios.append({"usuario":nome,"senha":senha,"tipo":tipo})
        criacao_exclusao.append({"acao":"CRIACAO_USUARIO","nome":nome,"usuario":usuario_logado["usuario"],"ts":agora_str()})
        salvar_todos()
        messagebox.showinfo("OK","USUÁRIO CRIADO.")
        refresh_list()

    def excluir_u():
        if usuario_logado["tipo"] != "DIRETOR":
            messagebox.showerror("PERMISSÃO", "APENAS DIRETOR PODE EXCLUIR USUÁRIOS.")
            return
        sel = listbox.curselection()
        if not sel:
            messagebox.showinfo("SELEÇÃO","ESCOLHA UM USUÁRIO.")
            return
        txt = listbox.get(sel[0])
        nome = txt.split()[0]
        if nome == usuario_logado["usuario"]:
            messagebox.showerror("ERRO","VOCÊ NÃO PODE EXCLUIR SUA PRÓPRIA CONTA ENQUANTO ESTIVER LOGADO.")
            return
        # impedir excluir outro DIRETOR sem confirmação
        for u in list(usuarios):
            if u["usuario"] == nome:
                if u["tipo"] == "DIRETOR":
                    # confirmar exclusão de DIRETOR
                    conf = messagebox.askyesno("CONFIRMAR", "O USUÁRIO É DIRETOR. TEM CERTEZA QUE DESEJA EXCLUIR?")
                    if not conf:
                        return
                usuarios.remove(u)
                criacao_exclusao.append({"acao":"EXCLUSAO_USUARIO","nome":nome,"usuario":usuario_logado["usuario"],"ts":agora_str()})
                salvar_todos()
                messagebox.showinfo("OK","USUÁRIO EXCLUÍDO.")
                refresh_list()
                return
        messagebox.showerror("ERRO","USUÁRIO NÃO ENCONTRADO.")

    ttk.Button(frm, text="CRIAR USUÁRIO", command=criar_u).pack(side="left", padx=6)
    ttk.Button(frm, text="EXCLUIR USUÁRIO", command=excluir_u).pack(side="left", padx=6)

# -------------------------
# Tela de Login (root)
# -------------------------
def iniciar_app():
    global root, login_win, entry_user, entry_pass
    carregar_todos()

    root = tk.Tk()
    root.title("INVENTÁRIO - LOGIN")
    root.geometry("420x260")
    root.configure(bg="white")

    frm = tk.Frame(root, bg="white", padx=12, pady=12)
    frm.pack(expand=True, fill="both")

    ttk.Label(frm, text="USUÁRIO:").grid(row=0, column=0, sticky="w", pady=6)
    entry_user = ttk.Entry(frm)
    entry_user.grid(row=0, column=1, pady=6, sticky="ew")

    ttk.Label(frm, text="SENHA:").grid(row=1, column=0, sticky="w", pady=6)
    entry_pass = ttk.Entry(frm, show="*")
    entry_pass.grid(row=1, column=1, pady=6, sticky="ew")

    ttk.Button(frm, text="ENTRAR", command=fazer_login).grid(row=2, column=0, columnspan=2, pady=12)

    frm.columnconfigure(1, weight=1)
    login_win = root
    root.mainloop()

if __name__ == "__main__":
    iniciar_app()
