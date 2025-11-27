import tkinter as tk
from tkinter import ttk, messagebox
usuarios = {
    "ADMIN": {"senha": "0000", "tipo": "ADMIN"},
    "USER": {"senha": "1234", "tipo": "USER"},
    "ACCESSFULL": {"senha": "0000", "tipo": "ACCESSFULL"},
}
produtos = {
    "Audiovisual e Apresentação": {
        "Projetor": {
            "quantidade": 39,
            "detalhes": [
                {"Nome": "Projetor Epson", "Patrimonio": "AV1001", "Status": "Disponível", "Posse": "-"},
                {"Nome": "Projetor LG", "Patrimonio": "AV1002", "Status": "Em uso", "Posse": "Carlos"},
            ]
        }
    },

    "Mobiliário e Estrutura": {
        "Cadeira": {
            "quantidade": 50,
            "detalhes": [
                {"Nome": "Cadeira Preta", "Patrimonio": "MB2001", "Status": "Disponível", "Posse": "-"},
            ]
        }
    },

    "Papelaria e Escritório": {
        "Caneta": {
            "quantidade": 40,
            "detalhes": [
                {"Nome": "Caneta Azul", "Patrimonio": "PE3001", "Status": "Disponível", "Posse": "-"},
                {"Nome": "Caneta Preta", "Patrimonio": "PE3002", "Status": "Em uso", "Posse": "Pedro"},
            ]
        },
        "Lápis": {
            "quantidade": 20,
            "detalhes": [
                {"Nome": "Lápis HB", "Patrimonio": "PE3101", "Status": "Disponível", "Posse": "-"}
            ]
        }
    }
}


def abrir_secoes():
    janela_secao = tk.Toplevel()
    janela_secao.title("Selecionar Seção")

    tk.Label(janela_secao, text="Selecione uma seção:").pack(pady=5)

    for secao in produtos.keys():
        ttk.Button(janela_secao, text=secao,
                   command=lambda s=secao: abrir_itens(s)).pack(pady=3)


def abrir_itens(secao):
    janela_itens = tk.Toplevel()
    janela_itens.title(f"Itens de {secao}")

    tk.Label(janela_itens, text=f"Itens em {secao}:").pack(pady=5)

    for item, dados in produtos[secao].items():
        texto = f"{item} — {dados['quantidade']}"
        ttk.Button(janela_itens, text=texto,
                   command=lambda i=item, s=secao: abrir_detalhes(s, i)).pack(pady=3)


def abrir_detalhes(secao, item):
    janela_det = tk.Toplevel()
    janela_det.title(f"Detalhes de {item}")

    tk.Label(janela_det, text=f"Resumo: {item}", font=("Open Sans", 12, "bold")).pack(pady=5)

    cols = ("Nome", "Patrimonio", "Status", "Posse")

    tabela = ttk.Treeview(janela_det, columns=cols, show="headings")

    for col in cols:
        tabela.heading(col, text=col)
        tabela.column(col, width=120)

    tabela.pack(padx=10, pady=10)

    for obj in produtos[secao][item]["detalhes"]:
        tabela.insert("", tk.END, values=(
            obj["Nome"],
            obj["Patrimonio"],
            obj["Status"],
            obj["Posse"]
        ))
 
usuario_logado = None
def abrir_menu():
    menu = tk.Tk()
    menu.title("Menu Principal")
    menu.geometry("900x500") 
    menu.configure(bg="white")
    quadro = tk.Frame(menu, width=820, height=420, bg="white", highlightbackground="black",
                      highlightthickness=3)
    quadro.place(relx=0.5, rely=0.5, anchor="center")
    box_user = tk.Frame(quadro, width=100, height=40, highlightbackground="black",
                        highlightthickness=2)
    box_user.place(relx=0.93, rely=0.15, anchor="center")
 
    tk.Label(box_user, text=usuario_logado["tipo"], font=("Arial", 10, "bold")).place(relx=0.5, rely=0.5, anchor="center")
    def criar_botao(text, y):
        frame = tk.Frame(quadro, highlightbackground="black", highlightthickness=2)
        frame.place(relx=0.5, rely=y, anchor="center")
 
        btn = tk.Button(frame, text=text, font=("Arial", 10, "bold"), width=30, height=2, relief="flat")
        btn.pack()
        return btn
 
    criar_botao("CONSULTAR PRODUTOS", 0.30)
    criar_botao("REQUISIÇÕES", 0.45)
    criar_botao("GERAR RELATORIOS", 0.60)
    criar_botao("CRIAÇÃO E EXCLUSÃO DE ITENS", 0.75)
 
    menu.mainloop()
def fazer_login():
    global usuario_logado
 
    user = entrada_usuario.get().upper()
    senha = entrada_senha.get()
 
    if user in usuarios and usuarios[user]["senha"] == senha:
        usuario_logado = usuarios[user]
        login.destroy()
        abrir_menu()
    else:
        messagebox.showerror("Erro", "Usuário ou senha incorretos.")
 
login = tk.Tk()
login.title("Login")
login.geometry("300x200")
login.configure(bg="white")
frame_login = tk.Frame(login, width=260, height=160, bg="white", highlightbackground="black",
                       highlightthickness=3)
frame_login.place(relx=0.5, rely=0.5, anchor="center")
tk.Label(frame_login, text="Usuário:", font=("Arial", 10)).place(x=20, y=30)
entrada_usuario = tk.Entry(frame_login)
entrada_usuario.place(x=100, y=30) 
tk.Label(frame_login, text="Senha:", font=("Arial", 10)).place(x=20, y=70)
entrada_senha = tk.Entry(frame_login, show="*")
entrada_senha.place(x=100, y=70)
frame_btn = tk.Frame(frame_login, highlightbackground="black", highlightthickness=2)
frame_btn.place(x=80, y=110) 
btn_login = tk.Button(frame_btn, text="LOGIN", font=("Arial", 10, "bold"),
                      width=10, relief="flat", command=fazer_login)
btn_login.pack() 
login.mainloop()