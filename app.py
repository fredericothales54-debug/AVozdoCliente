import tkinter as tk
from tkinter import ttk

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

root = tk.Tk()
root.title("Sistema de Controle")

ttk.Button(root, text="CONSULTAR PRODUTOS", command=abrir_secoes, width=30).pack(pady=10)
ttk.Button(root, text="REQUISIÇÕES", command=abrir_secoes, width=30).pack(pady=10)
ttk.Button(root, text="GERAR RELATÓRIOS", command=abrir_secoes, width=30).pack(pady=10)
ttk.Button(root, text="CRIAÇÃO E EXCLUSÃO DE ITENS", command=abrir_secoes, width=30).pack(pady=10)
root.mainloop()
