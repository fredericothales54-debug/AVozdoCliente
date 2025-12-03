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

# ---------- CONFIG ----------
DATA_DIR = "data"
USUARIOS_FILE = os.path.join(DATA_DIR, "usuarios.json")
CATEGORIAS_FILE = os.path.join(DATA_DIR, "categorias.json")
ITENS_FILE = os.path.join(DATA_DIR, "itens.json")
HISTORICO_FILE = os.path.join(DATA_DIR, "historico.json")

# ---------- DADOS PADRÃO ----------
_default_usuarios = [
    {"usuario": "admin", "senha": "0000", "tipo": "CORDENADOR"},
    {"usuario": "user", "senha": "1234", "tipo": "PROFESSOR"},
    {"usuario": "root", "senha": "9999", "tipo": "DIRETOR"}
]

_default_categorias = {
    "Ambientes": {
        "Auditório": 1,
        "Sala de Inovação / Ideação": 1,
        "Laboratório Maker": 1
    },
    "Equipamentos de Tecnologia": {
        "Notebook Core i3": 40,
        "Notebook Core i7": 36,
        "Mouse USB": 60
    },
    "Papelaria e Escritório": {
        "Caneta Azul": 300,
        "Lápis": 500,
        "Borracha": 200
    }
}

# ---------- MEMÓRIA ----------
usuarios = []
categorias = {}
itens_exemplares = {}   # chave -> dict exemplar, chave = "NOME | 0001-0001"
_item_group_counter = defaultdict(int)
movimentacoes = []
criacao_exclusao = []

# ---------- UTILITÁRIOS ----------
def agora_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def salvar_json(path, obj):
    ensure_data_dir()
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
    ensure_data_dir()
    if all(os.path.exists(p) for p in (USUARIOS_FILE, CATEGORIAS_FILE, ITENS_FILE, HISTORICO_FILE)):
        try:
            usuarios = carregar_json(USUARIOS_FILE)
            categorias = carregar_json(CATEGORIAS_FILE)
            itens_exemplares = carregar_json(ITENS_FILE)
            histor = carregar_json(HISTORICO_FILE)
            movimentacoes[:] = histor.get("movimentacoes", [])
            criacao_exclusao[:] = histor.get("criacao_exclusao", [])
            # recomputar counters
            _item_group_counter = defaultdict(int)
            for chave in list(itens_exemplares.keys()):
                try:
                    nome, patr = chave.split(" | ")
                    group = int(patr.split("-")[0])
                    _item_group_counter[nome] = max(_item_group_counter[nome], group)
                except Exception:
                    pass
            return True
        except Exception as e:
            messagebox.showwarning("AVISO", f"Falha ao carregar JSON: {e}\nUsando dados padrão.")
    # fallback: carregar padrões e gerar exemplares
    usuarios = [u.copy() for u in _default_usuarios]
    categorias = {k: v.copy() for k, v in _default_categorias.items()}
    itens_exemplares.clear()
    _item_group_counter.clear()
    movimentacoes.clear()
    criacao_exclusao.clear()
    gerar_exemplares_iniciais()
    salvar_todos()
    return False

# ---------- GERAR EXEMPLARES INICIAIS ----------
def gerar_exemplares_iniciais():
    for categoria, itens in categorias.items():
        for nome, qtd in itens.items():
            # se qtd não for int (quando categorias armazenam dicts), try convert
            try:
                qtd_int = int(qtd)
            except Exception:
                continue
            _item_group_counter[nome] += 1
            group_id = _item_group_counter[nome]
            for i in range(1, qtd_int + 1):
                patrimonio = f"{group_id:04d}-{i:04d}"
                chave = f"{nome} | {patrimonio}"
                itens_exemplares[chave] = {
                    "nome": nome,
                    "patrimonio": patrimonio,
                    "categoria": categoria,
                    "status": "Disponível",
                    "em_posse": ""
                }

# ---------- MOUSE WHEEL BINDINGS (Listbox & Treeview) ----------
def sys_platform_is_mac():
    return os.name == "posix" and getattr(sys, "platform", "").startswith("darwin")

def _bind_mousewheel(widget):
    """
    Binds mouse wheel so that when the cursor is over the widget,
    the mouse wheel scrolls that widget (works for Listbox and Treeview).
    """
    def _on_enter(event):
        if os.name == "nt":
            widget.bind_all("<MouseWheel>", _on_mousewheel_windows)
        elif sys_platform_is_mac():
            widget.bind_all("<MouseWheel>", _on_mousewheel_mac)
        else:
            widget.bind_all("<Button-4>", _on_mousewheel_linux_up)
            widget.bind_all("<Button-5>", _on_mousewheel_linux_down)

    def _on_leave(event):
        try:
            if os.name == "nt":
                widget.unbind_all("<MouseWheel>")
            elif sys_platform_is_mac():
                widget.unbind_all("<MouseWheel>")
            else:
                widget.unbind_all("<Button-4>")
                widget.unbind_all("<Button-5>")
        except Exception:
            pass

    def _on_mousewheel_windows(e):
        # delta is multiples of 120
        try:
            widget.yview_scroll(int(-1 * (e.delta / 120)), "units")
        except Exception:
            pass
        return "break"

    def _on_mousewheel_mac(e):
        try:
            widget.yview_scroll(int(-1 * e.delta), "units")
        except Exception:
            pass
        return "break"

    def _on_mousewheel_linux_up(e):
        try:
            widget.yview_scroll(-1, "units")
        except Exception:
            pass
        return "break"

    def _on_mousewheel_linux_down(e):
        try:
            widget.yview_scroll(1, "units")
        except Exception:
            pass
        return "break"

    widget.bind("<Enter>", _on_enter)
    widget.bind("<Leave>", _on_leave)

# ---------- DECORATOR ----------
def exige_login(func):
    def wrapper(*a, **k):
        if usuario_logado is None:
            messagebox.showerror("ERRO", "FAÇA LOGIN PRIMEIRO.")
            return
        return func(*a, **k)
    return wrapper

# ---------- UI / NEGÓCIO ----------
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
    top.geometry("1000x650")

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

    if usuario_logado["tipo"] in ["CORDENADOR", "DIRETOR", "ACCESSFULL"]:
        ttk.Button(sidebar, text="CRIAR / EXCLUIR ITENS", command=lambda: tela_criar_excluir(content)).pack(fill="x", pady=6)

    if usuario_logado["tipo"] == "ACCESSFULL":
        ttk.Button(sidebar, text="GERENCIAR USUÁRIOS", command=lambda: tela_usuarios(content)).pack(fill="x", pady=6)

    ttk.Button(sidebar, text="SAIR DO APP", command=root.destroy).pack(side="bottom", fill="x", pady=10)

    tela_categorias(content)

# ---------- Helpers de UI ----------
def limpar_frame(f):
    for w in f.winfo_children():
        w.destroy()

def upper_if_text(s):
    try:
        return str(s).upper()
    except Exception:
        return s

# ---------- TELAS ----------
@exige_login
def tela_categorias(parent):
    limpar_frame(parent)
    ttk.Label(parent, text="CATEGORIAS", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(2,8))

    # Use a frame with Listbox + scrollbar
    box_frame = tk.Frame(parent, bg="white")
    box_frame.pack(fill="both", expand=False)
    listbox = tk.Listbox(box_frame, height=10)
    vsb = ttk.Scrollbar(box_frame, orient="vertical", command=listbox.yview)
    listbox.configure(yscrollcommand=vsb.set)
    listbox.pack(side="left", fill="both", expand=True)
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

    cols = ("NOME","PATRIMÔNIO","STATUS","EM_POSSE")
    tree_frame = tk.Frame(parent, bg="white")
    tree_frame.pack(expand=True, fill="both", pady=6)

    tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, width=200, anchor="w")
    vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side="left", expand=True, fill="both")
    vsb.pack(side="right", fill="y")
    _bind_mousewheel(tree)

    # preencher árvore com itens da categoria (case-insensitive)
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
        if ex["status"].lower() != "disponível":
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
        if ex["status"].lower() != "em uso":
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
        # permitir para CORDENADOR/DIRETOR/ACCESSFULL
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

    cols = ("NOME","PATRIMÔNIO","STATUS","EM_POSSE")
    tree_frame = tk.Frame(parent, bg="white")
    tree_frame.pack(expand=True, fill="both")
    tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, width=200)
    vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side="left", expand=True, fill="both")
    vsb.pack(side="right", fill="y")
    _bind_mousewheel(tree)

    for chave, ex in itens_exemplares.items():
        tree.insert("", tk.END, iid=chave, values=(ex["nome"].upper(), ex["patrimonio"], ex["status"].upper(), (ex["em_posse"] or "-").upper()))

    btns = tk.Frame(parent, bg="white")
    btns.pack(fill="x", pady=8)

    def requisitar_sel():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("SELEÇÃO", "ESCOLHA UM EXEMPLAR.")
            return
        chave = sel[0]
        ex = itens_exemplares[chave]
        if ex["status"].lower() != "disponível":
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
        if ex["status"].lower()!="em uso":
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
    total = len(itens_exemplares)
    disp = sum(1 for v in itens_exemplares.values() if v["status"].lower()=="disponível")
    uso = sum(1 for v in itens_exemplares.values() if v["status"].lower()=="em uso")
    info.insert("end", f"USE OS BOTÕES ACIMA PARA VISUALIZAR GRÁFICOS.\nRESUMO RÁPIDO:\nTOTAL EXEMPLARES: {total}\nDISPONÍVEIS: {disp}\nEM USO: {uso}\nMOVIMENTAÇÕES REGISTRADAS: {len(movimentacoes)}\nREGISTROS DE CRIAÇÃO/EXCLUSÃO: {len(criacao_exclusao)}")

# ---------- GRÁFICOS ----------
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

# ---------- CRIAÇÃO / EXCLUSÃO GRUPO / REMOVER N ITENS ----------
@exige_login
def tela_criar_excluir(parent):
    limpar_frame(parent)
    ttk.Label(parent, text="GERENCIAR ITENS", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(2,8))

    frm = tk.Frame(parent, bg="white")
    frm.pack(fill="x", pady=6)
    ttk.Button(frm, text="CRIAR NOVO GRUPO DE ITENS", command=criar_grupo_item).pack(side="left", padx=6)
    ttk.Button(frm, text="EXCLUIR GRUPO (TODOS EXEMPLARES)", command=excluir_grupo_item).pack(side="left", padx=6)
    ttk.Button(frm, text="REMOVER N ITENS DO GRUPO", command=remover_n_itens_grupo).pack(side="left", padx=6)

    cols = ("NOME","PATRIMÔNIO","CATEGORIA","STATUS")
    tree_frame = tk.Frame(parent, bg="white")
    tree_frame.pack(expand=True, fill="both", pady=8)
    tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, width=180)
    vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side="left", expand=True, fill="both")
    vsb.pack(side="right", fill="y")
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
        # adiciona categoria com contador zero (usuário pode preencher depois)
        categorias[cat] = {}
    _item_group_counter[nome] += 1
    group_id = _item_group_counter[nome]
    created = 0
    for i in range(1, qtd+1):
        patrimonio = f"{group_id:04d}-{i:04d}"
        chave = f"{nome} | {patrimonio}"
        itens_exemplares[chave] = {"nome":nome,"patrimonio":patrimonio,"categoria":cat,"status":"Disponível","em_posse":""}
        created += 1
    criacao_exclusao.append({"acao":"CRIACAO","nome":nome,"usuario":usuario_logado["usuario"],"ts":agora_str()})
    salvar_todos()
    messagebox.showinfo("OK", f"{created} EXEMPLARES DE '{nome}' CRIADOS.")

def excluir_grupo_item():
    # PERMISSÃO: apenas DIRETOR
    if usuario_logado["tipo"] != "DIRETOR":
        messagebox.showerror("PERMISSÃO", "APENAS DIRETOR PODE EXCLUIR GRUPOS.")
        return
    nome = simpledialog.askstring("EXCLUIR GRUPO", "NOME DO ITEM (GRUPO) PARA EXCLUIR TOTALMENTE:")
    if not nome:
        return
    removidos = [k for k,v in itens_exemplares.items() if v["nome"].lower() == nome.lower()]
    if not removidos:
        messagebox.showinfo("INFO", "NENHUM EXEMPLAR ENCONTRADO PARA ESSE NOME.")
        return
    # confirmar
    resp = messagebox.askyesno("CONFIRMAR", f"DESEJA REMOVER {len(removidos)} EXEMPLARES DO GRUPO '{nome}'? ESTA AÇÃO NÃO PODE SER DESFEITA.")
    if not resp:
        return
    for k in removidos:
        itens_exemplares.pop(k, None)
    criacao_exclusao.append({"acao":"EXCLUSAO_GRUPO","nome":nome,"usuario":usuario_logado["usuario"],"ts":agora_str(), "qtd": len(removidos)})
    salvar_todos()
    messagebox.showinfo("OK", f"{len(removidos)} EXEMPLARES REMOVIDOS DO GRUPO '{nome}'.")

def remover_n_itens_grupo():
    # PERMISSÃO: apenas DIRETOR
    if usuario_logado["tipo"] != "DIRETOR":
        messagebox.showerror("PERMISSÃO", "APENAS DIRETOR PODE REMOVER ITENS EM MASSA.")
        return
    nome = simpledialog.askstring("REMOVER ITENS", "NOME DO ITEM (GRUPO):")
    if not nome:
        return
    try:
        qtd_raw = simpledialog.askstring("QUANTIDADE", "QUANTOS EXEMPLARES REMOVER (NÚMERO):")
        qtd = int(qtd_raw)
        if qtd <= 0:
            raise ValueError
    except Exception:
        messagebox.showerror("ERRO", "QUANTIDADE INVÁLIDA.")
        return
    # lista exemplares do grupo ordenados por patrimônio decrescente (remove últimos)
    exemplares = sorted([ (k,v) for k,v in itens_exemplares.items() if v["nome"].lower() == nome.lower()],
                        key=lambda kv: kv[1]["patrimonio"], reverse=True)
    if not exemplares:
        messagebox.showinfo("INFO", "NENHUM EXEMPLAR ENCONTRADO PARA ESSE NOME.")
        return
    to_remove = exemplares[:qtd]
    resp = messagebox.askyesno("CONFIRMAR", f"DESEJA REMOVER {len(to_remove)} EXEMPLARES DO GRUPO '{nome}'?")
    if not resp:
        return
    for k,v in to_remove:
        itens_exemplares.pop(k, None)
    criacao_exclusao.append({"acao":"REMOVER_N","nome":nome,"usuario":usuario_logado["usuario"],"ts":agora_str(), "qtd": len(to_remove)})
    salvar_todos()
    messagebox.showinfo("OK", f"{len(to_remove)} EXEMPLARES REMOVIDOS DO GRUPO '{nome}'.")

# ---------- USUÁRIOS ----------
@exige_login
def tela_usuarios(parent):
    limpar_frame(parent)
    ttk.Label(parent, text="GERENCIAR USUÁRIOS (ACESSO: DIRETOR)", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(2,8))

    listbox = tk.Listbox(parent)
    listbox.pack(fill="x", pady=6)
    for u in usuarios:
        listbox.insert(tk.END, f"{u['usuario']} ({u['tipo']})")

    frm = tk.Frame(parent, bg="white")
    frm.pack(fill="x", pady=6)
    def criar_u():
        if usuario_logado["tipo"] != "DIRETOR":
            messagebox.showerror("PERMISSÃO", "APENAS DIRETOR PODE CRIAR USUÁRIOS.")
            return
        nome = simpledialog.askstring("USUÁRIO", "NOME DO USUÁRIO:")
        senha = simpledialog.askstring("SENHA", "SENHA:")
        tipo = simpledialog.askstring("TIPO", "PROFESSOR / CORDENADOR / DIRETOR / ACCESSFULL:")
        if not nome or not senha or not tipo:
            messagebox.showerror("ERRO", "DADOS INCOMPLETOS.")
            return
        usuarios.append({"usuario":nome,"senha":senha,"tipo":tipo})
        criacao_exclusao.append({"acao":"CRIACAO_USUARIO","nome":nome,"usuario":usuario_logado["usuario"],"ts":agora_str()})
        salvar_todos()
        messagebox.showinfo("OK","USUÁRIO CRIADO.")
        tela_usuarios(parent)
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
        for u in usuarios:
            if u["usuario"] == nome:
                usuarios.remove(u)
                criacao_exclusao.append({"acao":"EXCLUSAO_USUARIO","nome":nome,"usuario":usuario_logado["usuario"],"ts":agora_str()})
                salvar_todos()
                messagebox.showinfo("OK","USUÁRIO EXCLUÍDO.")
                tela_usuarios(parent)
                return
        messagebox.showerror("ERRO","USUÁRIO NÃO ENCONTRADO.")

    ttk.Button(frm, text="CRIAR USUÁRIO", command=criar_u).pack(side="left", padx=6)
    ttk.Button(frm, text="EXCLUIR USUÁRIO", command=excluir_u).pack(side="left", padx=6)

# ---------- INÍCIO / LOGIN ----------
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
