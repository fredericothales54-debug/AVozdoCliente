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
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import seaborn as sns
import matplotlib.pyplot as plt

usuarios = [
    {"usuario": "admin", "senha": "0000", "tipo": "ADMIN"},
    {"usuario": "user", "senha": "1234", "tipo": "USER"},
    {"usuario": "root", "senha": "9999", "tipo": "ACCESSFULL"}
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
        "Caneta Azul": 300,
        "Lápis": 500,
        "Borracha": 200
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
