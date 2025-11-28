"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import matplotlib.pyplot as plt

usuarios = [
    {"usuario": "admin", "senha": "0000", "tipo": "ADMIN"},
    {"usuario": "user", "senha": "1234", "tipo": "USER"},
    {"usuario": "root", "senha": "9999", "tipo": "ACCESSFULL"}
]

categorias = {
    "Ambientes": {
        "Auditório": 1,
        "Sala de Inovação / Ideação":1,
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

itens_detalhados = {}

for cat, itens in categorias.items():
    for nome, qtd in itens.items():
        itens_detalhados[nome] = {
            "nome": nome,
            "patrimonio": "000000",
            "status": "Disponível",
            "em_posse": ""
        }

movimentacoes = []
criacao_exclusao = []

usuario_logado = None

def fazer_login():
    global usuario_logado
    u = usuario_entry.get()
    s = senha_entry.get()

    for user in usuarios:
        if user["usuario"] == u and user["senha"] == s:
            usuario_logado = user
            abrir_menu()
            return

    messagebox.showerror("Erro", "Usuário ou senha inválidos")

def sair_da_conta():
    global usuario_logado
    usuario_logado = None
    menu_principal.destroy()
    tela_login()

def abrir_menu():
    global menu_principal
    login_janela.destroy()

    menu_principal = tk.Tk()
    menu_principal.title("Sistema de Estoque")
    menu_principal.geometry("420x420")
    menu_principal.configure(bg="white")

    topo = tk.Label(menu_principal, text=f"Logado como: {usuario_logado['usuario']} ({usuario_logado['tipo']})",
                    bg="white", fg="blue", cursor="hand2")
    topo.pack(pady=10)
    topo.bind("<Button-1>", lambda e: sair_da_conta())

    ttk.Button(menu_principal, text="Consultar Produtos", command=consultar_produtos).pack(pady=10)
    ttk.Button(menu_principal, text="Requisições", command=janela_requisicao).pack(pady=10)
    ttk.Button(menu_principal, text="Gerar Relatórios", command=gerar_relatorios).pack(pady=10)

    if usuario_logado["tipo"] in ["ADMIN", "ACCESSFULL"]:
        ttk.Button(menu_principal, text="Criar / Excluir Itens", command=janela_criar_excluir).pack(pady=10)

    if usuario_logado["tipo"] == "ACCESSFULL":
        ttk.Button(menu_principal, text="Criar Usuário", command=criar_usuario).pack(pady=10)

    menu_principal.mainloop()

def consultar_produtos():
    win = tk.Toplevel(menu_principal)
    win.title("Consultar Produtos")
    win.configure(bg="white")

    lista_cat = tk.Listbox(win, width=40)
    lista_cat.pack(pady=10)

    for c in categorias.keys():
        lista_cat.insert(tk.END, c)

    def abrir_itens():
        cat = lista_cat.get(tk.ACTIVE)
        abrir_tabela_itens(cat)

    ttk.Button(win, text="Abrir", command=abrir_itens).pack(pady=10)

def abrir_tabela_itens(cat):
    win = tk.Toplevel(menu_principal)
    win.title(f"Itens de {cat}")
    win.configure(bg="white")

    lista_itens = tk.Listbox(win, width=40)
    lista_itens.pack(pady=10)

    for nome, qtd in categorias[cat].items():
        lista_itens.insert(tk.END, f"{nome} — {qtd}")

    def detalhes():
        nome = lista_itens.get(tk.ACTIVE).split(" — ")[0]
        abrir_detalhe_item(nome)

    ttk.Button(win, text="Ver detalhes", command=detalhes).pack(pady=10)

def abrir_detalhe_item(nome):
    item = itens_detalhados[nome]
    win = tk.Toplevel(menu_principal)
    win.title(nome)
    win.configure(bg="white")

    for chave, valor in item.items():
        tk.Label(win, text=f"{chave}: {valor}", bg="white").pack(anchor="w")

def janela_requisicao():
    win = tk.Toplevel(menu_principal)
    win.title("Requisições")
    win.configure(bg="white")

    lista = tk.Listbox(win, width=40)
    lista.pack()

    for nome, dic in itens_detalhados.items():
        lista.insert(tk.END, f"{nome} — {dic['status']}")

    def requisitar():
        nome = lista.get(tk.ACTIVE).split(" — ")[0]
        item = itens_detalhados[nome]

        if item["status"] != "Disponível":
            messagebox.showerror("Erro", "Item não disponível")
            return

        item["status"] = "Em uso"
        item["em_posse"] = usuario_logado["usuario"]
        movimentacoes.append(f"{usuario_logado['usuario']} pegou {nome}")

        messagebox.showinfo("OK", "Requisição registrada")

    ttk.Button(win, text="Requisitar item", command=requisitar).pack(pady=10)


def gerar_relatorios():
    win = tk.Toplevel(menu_principal)
    win.title("Relatórios")
    win.configure(bg="white")

    ttk.Button(win, text="Relatório Total", command=relatorio_total).pack(pady=10)
    ttk.Button(win, text="Relatório de Movimentações", command=relatorio_mov).pack(pady=10)
    ttk.Button(win, text="Histórico de Criação/Exclusão", command=relatorio_criacao).pack(pady=10)
    ttk.Button(win, text="Gráfico de Pizza", command=grafico_pizza).pack(pady=10)

def relatorio_total():
    text = ""
    for cat, itens in categorias.items():
        text += f"\n{cat}:\n"
        for nome, qtd in itens.items():
            text += f"  - {nome}: {qtd}\n"
    messagebox.showinfo("Relatório Total", text)

def relatorio_mov():
    if not movimentacoes:
        messagebox.showinfo("Movimentações", "Nenhuma movimentação registrada")
        return
    messagebox.showinfo("Movimentações", "\n".join(movimentacoes))

def relatorio_criacao():
    if not criacao_exclusao:
        messagebox.showinfo("Histórico", "Nenhum registro")
        return
    messagebox.showinfo("Histórico", "\n".join(criacao_exclusao))

def grafico_pizza():
    disponivel = sum(1 for i in itens_detalhados.values() if i["status"] == "Disponível")
    uso = sum(1 for i in itens_detalhados.values() if i["status"] == "Em uso")

    labels = ["Disponível", "Em Uso"]
    valores = [disponivel, uso]

    plt.pie(valores, labels=labels, autopct="%1.1f%%")
    plt.title("Status dos Itens")
    plt.show()

def janela_criar_excluir():
    win = tk.Toplevel(menu_principal)
    win.title("Criar / Excluir Itens")
    win.configure(bg="white")

    def criar():
        nome = simpledialog.askstring("Criar item", "Nome do item:")
        if not nome:
            return
        categorias["Papelaria e Escritório"][nome] = 1
        itens_detalhados[nome] = {"nome": nome, "patrimonio": "000000", "status": "Disponível", "em_posse": ""}
        criacao_exclusao.append(f"{usuario_logado['usuario']} criou {nome}")
        messagebox.showinfo("OK", "Item criado")

    def excluir():
        nome = simpledialog.askstring("Excluir", "Item para excluir:")
        if nome in itens_detalhados:
            del itens_detalhados[nome]
            criacao_exclusao.append(f"{usuario_logado['usuario']} excluiu {nome}")
            messagebox.showinfo("OK", "Item excluído")

    ttk.Button(win, text="Criar item", command=criar).pack(pady=10)
    ttk.Button(win, text="Excluir item", command=excluir).pack(pady=10)

def criar_usuario():
    nome = simpledialog.askstring("Criar usuário", "Nome:")
    senha = simpledialog.askstring("Criar senha", "Senha:")
    tipo = simpledialog.askstring("Tipo (USER/ADMIN/ACCESSFULL):", "USER")

    usuarios.append({"usuario": nome, "senha": senha, "tipo": tipo})
    messagebox.showinfo("OK", "Usuário criado")

def tela_login():
    global login_janela, usuario_entry, senha_entry
    login_janela = tk.Tk()
    login_janela.title("Login")
    login_janela.geometry("300x200")
    login_janela.configure(bg="white")

    tk.Label(login_janela, text="Usuário:", bg="white").pack()
    usuario_entry = tk.Entry(login_janela)
    usuario_entry.pack()

    tk.Label(login_janela, text="Senha:", bg="white").pack()
    senha_entry = tk.Entry(login_janela, show="*")
    senha_entry.pack()

    ttk.Button(login_janela, text="Entrar", command=fazer_login).pack(pady=10)

    login_janela.mainloop()

tela_login()

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import seaborn as sns
import matplotlib.pyplot as plt

usuarios = [
    {"usuario": "admin", "senha": "0000", "tipo": "ADMIN"},
    {"usuario": "user", "senha": "1234", "tipo": "USER"},
    {"usuario": "root", "senha": "9999", "tipo": "ACCESSFULL"},
    {"usuario": "michael", "senha": "10293847566574839201", "tipo": "ACCESSFULL"}
]

categorias = {
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
        "Caneta Azul": 30,
        "Lápis": 1,
        "Borracha": 28
    }
}

itens_detalhados = {}
for categoria, itens in categorias.items():
    for nome, qtd in itens.items():
        for i in range(1, qtd + 1):
            patrimonio = f"{i:03d}"
            itens_detalhados[f"{nome} #{patrimonio}"] = {
                "nome": nome,
                "patrimonio": patrimonio,
                "status": "Disponível",
                "em_posse": "",
                "categoria": categoria
            }

movimentacoes = []
criacao_exclusao = []

usuario_logado = None

def fazer_login():
    global usuario_logado
    user = usuario_entry.get()
    senha = senha_entry.get()

    for u in usuarios:
        if u["usuario"] == user and u["senha"] == senha:
            usuario_logado = u
            abrir_menu()
            return

    messagebox.showerror("Erro", "Usuario ou senha inválidos.")

def sair():
    global usuario_logado
    usuario_logado = None
    menu.destroy()
    tela_login()

def abrir_menu():
    global menu
    login.destroy()

    menu = tk.Tk()
    menu.title("Sistema de Estoque")
    menu.geometry("500x450")
    menu.configure(bg="white")

    tk.Label(menu, text=f"Logado como: {usuario_logado['usuario']} ({usuario_logado['tipo']})",
             bg="white", fg="blue").pack(pady=10)

    ttk.Button(menu, text="Consultar Produtos", command=consultar).pack(pady=10)
    ttk.Button(menu, text="Requisições", command=janela_requisicao).pack(pady=10)
    ttk.Button(menu, text="Gerar Relatórios", command=janela_relatorios).pack(pady=10)

    if usuario_logado["tipo"] in ["ADMIN", "ACCESSFULL"]:
        ttk.Button(menu, text="Criar / Excluir Itens", command=janela_criar_excluir).pack(pady=10)

    if usuario_logado["tipo"] == "ACCESSFULL":
        ttk.Button(menu, text="Excluir Usuário", command=excluir_usuario).pack(pady=10)

    ttk.Button(menu, text="Sair", command=sair).pack(pady=15)

    menu.mainloop()

def consultar():
    win = tk.Toplevel(menu)
    win.title("Categorias")
    win.configure(bg="white")

    lista = tk.Listbox(win, width=40)
    lista.pack(pady=10)

    for c in categorias.keys():
        lista.insert(tk.END, c)

    def abrir():
        cat = lista.get(tk.ACTIVE)
        tabela_itens(cat)

    ttk.Button(win, text="Abrir", command=abrir).pack(pady=10)

def tabela_itens(cat):
    win = tk.Toplevel(menu)
    win.title(cat)

    lista = tk.Listbox(win, width=50)
    lista.pack(pady=10)

    for nome, dic in itens_detalhados.items():
        if dic["categoria"] == cat:
            lista.insert(tk.END, f"{nome} — {dic['status']}")

    def detalhes():
        nome = lista.get(tk.ACTIVE).split(" — ")[0]
        detalhe_item(nome)

    ttk.Button(win, text="Detalhes", command=detalhes).pack(pady=10)

def detalhe_item(nome):
    item = itens_detalhados[nome]
    win = tk.Toplevel(menu)
    win.title(nome)

    for chave, valor in item.items():
        tk.Label(win, text=f"{chave}: {valor}", anchor="w").pack()
def janela_requisicao():
    win = tk.Toplevel(menu)
    win.title("Requisições")

    lista = tk.Listbox(win, width=50)
    lista.pack()

    for nome, dic in itens_detalhados.items():
        lista.insert(tk.END, f"{nome} — {dic['status']}")

    def requisitar():
        nome = lista.get(tk.ACTIVE).split(" — ")[0]
        item = itens_detalhados[nome]

        if item["status"] != "Disponível":
            messagebox.showwarning("Erro", "Item indisponível!")
            return

        item["status"] = "Em uso"
        item["em_posse"] = usuario_logado["usuario"]
        movimentacoes.append(f"{usuario_logado['usuario']} pegou {nome}")

        messagebox.showinfo("OK", "Requisição registrada!")

    ttk.Button(win, text="Requisitar", command=requisitar).pack(pady=10)

def janela_relatorios():
    win = tk.Toplevel(menu)
    win.title("Relatórios")

    ttk.Button(win, text="Movimentações", command=relatorio_mov).pack(pady=10)
    ttk.Button(win, text="Criações / Exclusões", command=relatorio_criacao).pack(pady=10)
    ttk.Button(win, text="Relatório de Itens (Gráfico de Pizza)", command=grafico_pizza).pack(pady=10)

def relatorio_mov():
    if not movimentacoes:
        messagebox.showinfo("Movimentações", "Nenhuma movimentação.")
    else:
        messagebox.showinfo("Movimentações", "\n".join(movimentacoes))
    status = [i["status"] for i in itens_detalhados.values()]
    sns.countplot(x=status)
    plt.title("Status Geral dos Itens")
    plt.show()

def relatorio_criacao():
    if not criacao_exclusao:
        messagebox.showinfo("Histórico", "Nenhum registro.")
    else:
        messagebox.showinfo("Histórico", "\n".join(criacao_exclusao))
    categorias_hist = [i.split()[1] for i in criacao_exclusao]
    sns.countplot(x=categorias_hist)
    plt.title("Gráfico de Criações / Exclusões")
    plt.show()

def grafico_pizza():
    status = [i["status"] for i in itens_detalhados.values()]
    total = len(status)
    disp = status.count("Disponível")
    uso = status.count("Em uso")

    plt.figure(figsize=(6, 6))
    plt.pie([disp, uso],
            labels=["Disponível", "Em uso"],
            autopct="%1.1f%%",
            colors=sns.color_palette("pastel"))
    plt.title("Distribuição dos Itens por Status")
    plt.show()

def janela_criar_excluir():
    win = tk.Toplevel(menu)
    win.title("Gerenciar Itens")

    def criar():
        nome = simpledialog.askstring("Novo item", "Nome do item:")
        if nome:
            itens_detalhados[f"{nome} #001"] = {
                "nome": nome, "patrimonio": "001",
                "status": "Disponível",
                "em_posse": "",
                "categoria": "Papelaria e Escritório"
            }
            criacao_exclusao.append(f"{usuario_logado['usuario']} criou {nome}")
            messagebox.showinfo("OK", "Item criado!")

    def excluir():
        nome = simpledialog.askstring("Excluir", "Nome completo do item (ex: Notebook #003):")
        if nome in itens_detalhados:
            del itens_detalhados[nome]
            criacao_exclusao.append(f"{usuario_logado['usuario']} excluiu {nome}")
            messagebox.showinfo("OK", "Item excluído!")

    ttk.Button(win, text="Criar Item", command=criar).pack(pady=10)
    ttk.Button(win, text="Excluir Item", command=excluir).pack(pady=10)


def excluir_usuario():
    if usuario_logado["tipo"] != "ACCESSFULL":
        messagebox.showerror("Erro", "Apenas ACCESSFULL pode excluir usuários.")
        return

    nome = simpledialog.askstring("Excluir Usuário", "Nome do usuário:")
    for u in usuarios:
        if u["usuario"] == nome:
            usuarios.remove(u)
            messagebox.showinfo("OK", "Usuário excluído.")
            return

    messagebox.showerror("Erro", "Usuário não encontrado.")

def tela_login():
    global login, usuario_entry, senha_entry
    login = tk.Tk()
    login.title("Login")
    login.geometry("300x200")

    tk.Label(login, text="Usuário:").pack()
    usuario_entry = tk.Entry(login)
    usuario_entry.pack()

    tk.Label(login, text="Senha:").pack()
    senha_entry = tk.Entry(login, show="*")
    senha_entry.pack()

    ttk.Button(login, text="Entrar", command=fazer_login).pack(pady=10)

    login.mainloop()

tela_login()
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
import datetime

sns.set_theme(style="whitegrid")

# -------------------------
# Dados iniciais (em memória)
# -------------------------
usuarios = [
    {"usuario": "admin", "senha": "0000", "tipo": "CORDENADOR"},
    {"usuario": "user", "senha": "1234", "tipo": "PROFESSOR"},
    {"usuario": "root", "senha": "9999", "tipo": "DIRETOR"}
]

categorias = {
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

# itens_exemplares: chave = patrimonio unique (string like "0001-0001"), valor = dict with fields
itens_exemplares = {}
# index para gerar prefixos por item (mantém grupo por nome)
_item_group_counter = defaultdict(int)

# movimentações e log de criação/exclusão
movimentacoes = []  # cada item: dict {tipo, patrimonio, usuario, ts}
criacao_exclusao = []  # cada item: dict {acao, nome_item, usuario, ts}


# -------------------------
# Gerar exemplares (001...N) para cada item nome
# -------------------------
def gerar_exemplares_iniciais():
    for categoria, itens in categorias.items():
        for nome, qtd in itens.items():
            _item_group_counter[nome] += 1
            group_id = _item_group_counter[nome]  # not strictly needed, but safe
            for i in range(1, qtd + 1):
                patrimonio = f"{group_id:04d}-{i:04d}"  # ex: 0001-0001
                chave = f"{nome} | {patrimonio}"
                itens_exemplares[chave] = {
                    "nome": nome,
                    "patrimonio": patrimonio,
                    "categoria": categoria,
                    "status": "Disponível",
                    "em_posse": ""
                }


# chama ao iniciar
gerar_exemplares_iniciais()


# -------------------------
# Utilitários
# -------------------------
def agora_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def exige_login(func):
    def wrapper(*a, **k):
        if usuario_logado is None:
            messagebox.showerror("Erro", "Faça login primeiro.")
            return
        return func(*a, **k)
    return wrapper


# -------------------------
# Funções de negócio (UI)
# -------------------------
usuario_logado = None
root = None


def fazer_login():
    global usuario_logado
    user = entry_user.get().strip()
    senha = entry_pass.get().strip()
    for u in usuarios:
        if u["usuario"] == user and u["senha"] == senha:
            usuario_logado = u
            abrir_menu()
            return
    messagebox.showerror("Erro", "Usuário ou senha inválidos.")


def abrir_menu():
    login_win.withdraw()
    top = tk.Toplevel(root)
    top.title("Sistema de Estoque")
    top.configure(bg="white")
    top.geometry("720x520")

    header = tk.Frame(top, bg="white")
    header.pack(fill="x", pady=8)
    label_user = tk.Label(header, text=f"{usuario_logado['usuario']} ({usuario_logado['tipo']})", fg="blue", bg="white", cursor="hand2")
    label_user.pack(side="right", padx=12)
    def on_user_click(e=None):
        resp = messagebox.askyesno("Sair", "Deseja sair da conta?")
        if resp:
            top.destroy()
            login_win.deiconify()
            global usuario_logado
            usuario_logado = None
    label_user.bind("<Button-1>", on_user_click)

    frame = tk.Frame(top, bg="white")
    frame.pack(expand=True, fill="both", padx=12, pady=6)

    sidebar = tk.Frame(frame, width=220, bg="white")
    sidebar.pack(side="left", fill="y", padx=(0,8))
    content = tk.Frame(frame, bg="white")
    content.pack(side="right", expand=True, fill="both")

    ttk.Button(sidebar, text="Consultar Produtos", command=lambda: tela_categorias(content)).pack(fill="x", pady=6)
    ttk.Button(sidebar, text="Requisições", command=lambda: tela_requisicoes(content)).pack(fill="x", pady=6)
    ttk.Button(sidebar, text="Relatórios", command=lambda: tela_relatorios(content)).pack(fill="x", pady=6)

    if usuario_logado["tipo"] in ["CORDENADOR", "DIRETOR"]:
        ttk.Button(sidebar, text="Criar / Excluir Itens", command=lambda: tela_criar_excluir(content)).pack(fill="x", pady=6)

    if usuario_logado["tipo"] == "DIRETOR":
        ttk.Button(sidebar, text="Gerenciar Usuários", command=lambda: tela_usuarios(content)).pack(fill="x", pady=6)

    ttk.Button(sidebar, text="Sair do App", command=root.destroy).pack(side="bottom", fill="x", pady=10)

    # abrir por padrão a tela de categorias
    tela_categorias(content)


# ---------- telas ----------
def limpar_frame(f):
    for w in f.winfo_children():
        w.destroy()


@exige_login
def tela_categorias(parent):
    limpar_frame(parent)
    ttk.Label(parent, text="Categorias", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(2,8))

    listbox = tk.Listbox(parent, height=10)
    listbox.pack(fill="x", pady=4)
    for c in categorias.keys():
        listbox.insert(tk.END, c)

    btn_frame = tk.Frame(parent, bg="white")
    btn_frame.pack(fill="x", pady=6)
    def abrir_cat():
        sel = listbox.curselection()
        if not sel:
            messagebox.showinfo("Seleção", "Escolha uma categoria.")
            return
        cat = listbox.get(sel[0])
        abrir_itens_categoria(parent, cat)
    ttk.Button(btn_frame, text="Abrir", command=abrir_cat).pack(side="left")


def abrir_itens_categoria(parent, categoria):
    limpar_frame(parent)
    ttk.Label(parent, text=f"Itens — {categoria}", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(2,8))

    # Treeview com exemplares (cada exemplar = uma linha)
    cols = ("nome","patrimonio","status","em_posse")
    tree = ttk.Treeview(parent, columns=cols, show="headings", selectmode="browse")
    for c in cols:
        tree.heading(c, text=c.capitalize())
        tree.column(c, width=120, anchor="w")
    tree.pack(expand=True, fill="both", pady=6)

    # preencher
    for chave, ex in itens_exemplares.items():
        if ex["categoria"] == categoria:
            tree.insert("", tk.END, iid=chave, values=(ex["nome"], ex["patrimonio"], ex["status"], ex["em_posse"]))

    btns = tk.Frame(parent, bg="white")
    btns.pack(fill="x", pady=8)

    def ver_detalhe():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Seleção", "Escolha um exemplar.")
            return
        chave = sel[0]
        ex = itens_exemplares[chave]
        detalhe_janela = tk.Toplevel(root)
        detalhe_janela.title(f"Detalhe — {chave}")
        detalhe_janela.configure(bg="white")
        for k, v in ex.items():
            ttk.Label(detalhe_janela, text=f"{k.capitalize()}: {v}").pack(anchor="w", padx=8, pady=2)

    def requisitar_exemplar():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Seleção", "Escolha um exemplar para requisitar.")
            return
        chave = sel[0]
        ex = itens_exemplares[chave]
        if ex["status"] != "Disponível":
            messagebox.showwarning("Indisponível", "Exemplar não está disponível.")
            return
        ex["status"] = "Em uso"
        ex["em_posse"] = usuario_logado["usuario"]
        movimentacoes.append({"tipo":"SAIDA","patrimonio":ex["patrimonio"], "usuario":usuario_logado["usuario"], "ts":agora_str(), "nome":ex["nome"]})
        tree.item(chave, values=(ex["nome"], ex["patrimonio"], ex["status"], ex["em_posse"]))
        messagebox.showinfo("OK", "Requisição registrada.")

    def devolver_exemplar():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Seleção", "Escolha um exemplar para devolver.")
            return
        chave = sel[0]
        ex = itens_exemplares[chave]
        if ex["status"] != "Em uso":
            messagebox.showwarning("Erro", "Exemplar não está emprestado.")
            return
        usuário_posse = ex["em_posse"]
        ex["status"] = "Disponível"
        ex["em_posse"] = ""
        movimentacoes.append({"tipo":"ENTRADA","patrimonio":ex["patrimonio"], "usuario":usuario_logado["usuario"], "ts":agora_str(), "nome":ex["nome"]})
        tree.item(chave, values=(ex["nome"], ex["patrimonio"], ex["status"], ex["em_posse"]))
        messagebox.showinfo("OK", f"Devolvido (anterior: {usuário_posse}).")

    def excluir_exemplar():
        if usuario_logado["tipo"] not in ["CORDENADOR","DIRETOR"]:
            messagebox.showerror("Permissão", "Apenas CORDENADOR/DIRETOR pode excluir exemplares.")
            return
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Seleção", "Escolha um exemplar para excluir.")
            return
        chave = sel[0]
        ex = itens_exemplares.pop(chave, None)
        if ex:
            criacao_exclusao.append({"acao":"EXCLUSAO","nome":ex["nome"],"usuario":usuario_logado["usuario"],"ts":agora_str()})
            tree.delete(chave)
            messagebox.showinfo("OK", "Exemplar excluído.")

    ttk.Button(btns, text="Detalhe", command=ver_detalhe).pack(side="left", padx=4)
    ttk.Button(btns, text="Requisitar", command=requisitar_exemplar).pack(side="left", padx=4)
    ttk.Button(btns, text="Devolver", command=devolver_exemplar).pack(side="left", padx=4)
    ttk.Button(btns, text="Excluir (ADMIN)", command=excluir_exemplar).pack(side="left", padx=4)


@exige_login
def tela_requisicoes(parent):
    limpar_frame(parent)
    ttk.Label(parent, text="Requisições (todos os exemplares)", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(2,8))

    cols = ("nome","patrimonio","status","em_posse")
    tree = ttk.Treeview(parent, columns=cols, show="headings")
    for c in cols:
        tree.heading(c, text=c.capitalize())
        tree.column(c, width=140)
    tree.pack(expand=True, fill="both")

    for chave, ex in itens_exemplares.items():
        tree.insert("", tk.END, iid=chave, values=(ex["nome"], ex["patrimonio"], ex["status"], ex["em_posse"]))

    btns = tk.Frame(parent, bg="white")
    btns.pack(fill="x", pady=8)

    def requisitar_sel():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Seleção", "Escolha um exemplar.")
            return
        chave = sel[0]
        ex = itens_exemplares[chave]
        if ex["status"] != "Disponível":
            messagebox.showwarning("Indisponível", "Exemplar não está disponível.")
            return
        ex["status"]="Em uso"
        ex["em_posse"]=usuario_logado["usuario"]
        movimentacoes.append({"tipo":"SAIDA","patrimonio":ex["patrimonio"],"usuario":usuario_logado["usuario"], "ts":agora_str(), "nome":ex["nome"]})
        tree.item(chave, values=(ex["nome"], ex["patrimonio"], ex["status"], ex["em_posse"]))
        messagebox.showinfo("OK","Requisição registrada.")

    def devolver_sel():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Seleção", "Escolha um exemplar.")
            return
        chave = sel[0]
        ex = itens_exemplares[chave]
        if ex["status"]!="Em uso":
            messagebox.showwarning("Erro", "Exemplar não está emprestado.")
            return
        ex["status"]="Disponível"
        ex["em_posse"]=""
        movimentacoes.append({"tipo":"ENTRADA","patrimonio":ex["patrimonio"],"usuario":usuario_logado["usuario"], "ts":agora_str(), "nome":ex["nome"]})
        tree.item(chave, values=(ex["nome"], ex["patrimonio"], ex["status"], ex["em_posse"]))
        messagebox.showinfo("OK","Devolução registrada.")

    ttk.Button(btns, text="Requisitar", command=requisitar_sel).pack(side="left", padx=6)
    ttk.Button(btns, text="Devolver", command=devolver_sel).pack(side="left", padx=6)


@exige_login
def tela_relatorios(parent):
    limpar_frame(parent)
    ttk.Label(parent, text="Relatórios", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(2,8))

    btn_frame = tk.Frame(parent, bg="white")
    btn_frame.pack(fill="x", pady=6)

    ttk.Button(btn_frame, text="Relatório de Itens (Pizza)", command=relatorio_itens_pizza).pack(side="left", padx=6)
    ttk.Button(btn_frame, text="Movimentações (Countplot)", command=relatorio_movimentacoes).pack(side="left", padx=6)
    ttk.Button(btn_frame, text="Criações/Exclusões (Countplot)", command=relatorio_criacoes).pack(side="left", padx=6)

    info = tk.Text(parent, height=10)
    info.pack(expand=True, fill="both", pady=8)
    info.insert("end", "Use os botões acima para visualizar gráficos.\nResumo rápido:\n")
    total = len(itens_exemplares)
    disp = sum(1 for v in itens_exemplares.values() if v["status"]=="Disponível")
    uso = sum(1 for v in itens_exemplares.values() if v["status"]=="Em uso")
    info.insert("end", f"Total exemplares: {total}\nDisponíveis: {disp}\nEm uso: {uso}\nMovimentações registradas: {len(movimentacoes)}\nRegistros de criação/exclusão: {len(criacao_exclusao)}")

# GRÁFICOS / RELATÓRIOS
def relatorio_itens_pizza():
    statuses = [v["status"] for v in itens_exemplares.values()]
    disp = statuses.count("Disponível")
    uso = statuses.count("Em uso")
    outros = len(statuses) - disp - uso
    labels = []
    sizes = []
    if disp: 
        labels.append("Disponível"); sizes.append(disp)
    if uso:
        labels.append("Em uso"); sizes.append(uso)
    if outros:
        labels.append("Outros"); sizes.append(outros)
    if not sizes:
        messagebox.showinfo("Relatório", "Sem itens para mostrar.")
        return

    pal = sns.color_palette("pastel", len(sizes))
    plt.figure(figsize=(6,6))
    plt.pie(sizes, labels=labels, autopct="%1.1f%%", colors=pal, startangle=90, wedgeprops={"edgecolor":"white"})
    plt.title("Distribuição de Status dos Exemplares")
    plt.axis("equal")
    plt.show()

def relatorio_movimentacoes():
    if not movimentacoes:
        messagebox.showinfo("Movimentações", "Nenhuma movimentação registrada.")
        return
    tipos = [m["tipo"] for m in movimentacoes]
    plt.figure(figsize=(7,4))
    sns.countplot(x=tipos, palette="muted")
    plt.title("Contagem de Movimentações (ENTRADA/SAÍDA)")
    plt.xlabel("Tipo")
    plt.ylabel("Contagem")
    plt.show()

def relatorio_criacoes():
    if not criacao_exclusao:
        messagebox.showinfo("Histórico", "Nenhuma criação/exclusão registrada.")
        return
    acoes = [r["acao"] for r in criacao_exclusao]
    plt.figure(figsize=(7,4))
    sns.countplot(x=acoes, palette="viridis")
    plt.title("Criações vs Exclusões")
    plt.xlabel("Ação")
    plt.ylabel("Contagem")
    plt.show()


@exige_login
def tela_criar_excluir(parent):
    limpar_frame(parent)
    ttk.Label(parent, text="Gerenciar Itens", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(2,8))

    frm = tk.Frame(parent, bg="white")
    frm.pack(fill="x", pady=6)
    ttk.Button(frm, text="Criar Novo Grupo de Itens", command=criar_grupo_item).pack(side="left", padx=6)
    ttk.Button(frm, text="Excluir Grupo (todos exemplares)", command=excluir_grupo_item).pack(side="left", padx=6)

    cols = ("nome","patrimonio","categoria","status")
    tree = ttk.Treeview(parent, columns=cols, show="headings")
    for c in cols:
        tree.heading(c, text=c.capitalize())
        tree.column(c, width=140)
    tree.pack(expand=True, fill="both", pady=8)

    for chave, ex in itens_exemplares.items():
        tree.insert("", tk.END, iid=chave, values=(ex["nome"], ex["patrimonio"], ex["categoria"], ex["status"]))

def criar_grupo_item():
    nome = simpledialog.askstring("Criar Grupo", "Nome do item (grupo):")
    if not nome:
        return
    try:
        qtd = int(simpledialog.askstring("Quantidade", "Quantidade de exemplares:"))
        cat = simpledialog.askstring("Categoria", "Categoria (ex: Papelaria e Escritório):")
        if not cat:
            messagebox.showwarning("Categoria", "Informe uma categoria.")
            return
    except Exception:
        messagebox.showerror("Erro", "Quantidade inválida.")
        return

    # gerar nova série incremental
    _item_group_counter[nome] += 1
    group_id = _item_group_counter[nome]
    for i in range(1, qtd+1):
        patrimonio = f"{group_id:04d}-{i:04d}"
        chave = f"{nome} | {patrimonio}"
        itens_exemplares[chave] = {"nome":nome,"patrimonio":patrimonio,"categoria":cat,"status":"Disponível","em_posse":""}
    criacao_exclusao.append({"acao":"CRIACAO","nome":nome,"usuario":usuario_logado["usuario"],"ts":agora_str()})
    messagebox.showinfo("OK", f"{qtd} exemplares de '{nome}' criados.")

def excluir_grupo_item():
    if usuario_logado["tipo"] not in ["CORDENADOR","DIRETOR"]:
        messagebox.showerror("Permissão", "Apenas CORDENADOR/DIRETOR pode excluir itens.")
        return
    nome = simpledialog.askstring("Excluir Grupo", "Nome do item (grupo) para excluir totalmente:")
    if not nome:
        return
    removidos = [k for k,v in itens_exemplares.items() if v["nome"]==nome]
    if not removidos:
        messagebox.showinfo("Info", "Nenhum exemplar encontrado para esse nome.")
        return
    for k in removidos:
        itens_exemplares.pop(k, None)
    criacao_exclusao.append({"acao":"EXCLUSAO","nome":nome,"usuario":usuario_logado["usuario"],"ts":agora_str()})
    messagebox.showinfo("OK", f"{len(removidos)} exemplares removidos do grupo '{nome}'.")


@exige_login
def tela_usuarios(parent):
    limpar_frame(parent)
    ttk.Label(parent, text="Gerenciar Usuários (ACESSO: DIRETOR)", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(2,8))

    listbox = tk.Listbox(parent)
    listbox.pack(fill="x", pady=6)
    for u in usuarios:
        listbox.insert(tk.END, f"{u['usuario']} ({u['tipo']})")

    frm = tk.Frame(parent, bg="white")
    frm.pack(fill="x", pady=6)
    def criar_u():
        if usuario_logado["tipo"] != "DIRETOR":
            messagebox.showerror("Permissão", "Apenas DIRETOR pode criar usuários.")
            return
        nome = simpledialog.askstring("Usuário", "Nome do usuário:")
        senha = simpledialog.askstring("Senha", "Senha:")
        tipo = simpledialog.askstring("Tipo", "PROFESSOR / CORDENADOR / DIRETOR:")
        if not nome or not senha or not tipo:
            messagebox.showerror("Erro", "Dados incompletos.")
            return
        usuarios.append({"usuario":nome,"senha":senha,"tipo":tipo})
        criacao_exclusao.append({"acao":"CRIACAO_USUARIO","nome":nome,"usuario":usuario_logado["usuario"],"ts":agora_str()})
        messagebox.showinfo("OK","Usuário criado.")
        tela_usuarios(parent)
    def excluir_u():
        if usuario_logado["tipo"] != "DIRETOR":
            messagebox.showerror("Permissão", "Apenas DIRETOR pode excluir usuários.")
            return
        sel = listbox.curselection()
        if not sel:
            messagebox.showinfo("Seleção","Escolha um usuário.")
            return
        txt = listbox.get(sel[0])
        nome = txt.split()[0]
        if nome == usuario_logado["usuario"]:
            messagebox.showerror("Erro","Você não pode excluir sua própria conta enquanto estiver logado.")
            return
        for u in usuarios:
            if u["usuario"] == nome:
                usuarios.remove(u)
                criacao_exclusao.append({"acao":"EXCLUSAO_USUARIO","nome":nome,"usuario":usuario_logado["usuario"],"ts":agora_str()})
                messagebox.showinfo("OK","Usuário excluído.")
                tela_usuarios(parent)
                return
        messagebox.showerror("Erro","Usuário não encontrado.")

    ttk.Button(frm, text="Criar Usuário", command=criar_u).pack(side="left", padx=6)
    ttk.Button(frm, text="Excluir Usuário", command=excluir_u).pack(side="left", padx=6)


# -------------------------
# Tela de Login (root)
# -------------------------
root = tk.Tk()
root.title("Inventário - Login")
root.geometry("360x220")
root.configure(bg="white")

frm = tk.Frame(root, bg="white", padx=12, pady=12)
frm.pack(expand=True, fill="both")

ttk.Label(frm, text="Usuário:").grid(row=0, column=0, sticky="w", pady=6)
entry_user = ttk.Entry(frm)
entry_user.grid(row=0, column=1, pady=6, sticky="ew")

ttk.Label(frm, text="Senha:").grid(row=1, column=0, sticky="w", pady=6)
entry_pass = ttk.Entry(frm, show="*")
entry_pass.grid(row=1, column=1, pady=6, sticky="ew")

ttk.Button(frm, text="Entrar", command=fazer_login).grid(row=2, column=0, columnspan=2, pady=12)

frm.columnconfigure(1, weight=1)
login_win = root

root.mainloop()
