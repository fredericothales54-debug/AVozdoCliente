import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
import datetime
import sys


sns.set_theme(style="whitegrid")

class AppView:
    def __init__(self, root_window, controller):
        self.controller = controller
        
        self.root = root_window
        self.usuario_logado = None
        self.login_win = None
        self.menu_win = None
        
        self.tela_login()

    def limpar_frame(self, f):
        for w in f.winfo_children():
            w.destroy()

    def exigir_login(self, func):
        def wrapper(*a, **k):
            if self.usuario_logado is None:
                messagebox.showerror("Erro", "Faça login primeiro.")
                return
            return func(*a, **k)
        return wrapper

    def tela_login(self):
        self.login_win = tk.Toplevel(self.root)
        self.login_win.title("Inventário - Login")
        self.login_win.geometry("360x220")
        self.login_win.configure(bg="white")

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

        sucesso, resposta = self.controller.fazer_login(user, senha)

        if sucesso:
            self.usuario_logado = resposta 
            self.abrir_menu()
        else:
            messagebox.showerror("Erro", resposta) 
    def abrir_menu(self):
        self.login_win.withdraw()
        if self.menu_win:
             self.menu_win.destroy()
        
        self.menu_win = tk.Toplevel(self.root)
        self.menu_win.title("Sistema de Estoque")
        
    @exigir_login
    def tela_categorias(self, parent):
        self.limpar_frame(parent)
        categorias = self.controller.obter_categorias()
        
        listbox = tk.Listbox(parent, height=10)
        listbox.pack(fill="x", pady=4)
        for c in categorias.keys():
            listbox.insert(tk.END, c)
            
        def abrir_cat():
            sel = listbox.curselection()
            if not sel:
                messagebox.showinfo("Seleção", "Escolha uma categoria.")
                return
            cat = listbox.get(sel[0])
            self.abrir_itens_categoria(parent, cat)
            
        
    def abrir_itens_categoria(self, parent, categoria):
        self.limpar_frame(parent)
        
        exemplares = self.controller.listar_exemplares_por_categoria(categoria)

        cols = ("nome", "patrimonio", "status", "em_posse")
        tree = ttk.Treeview(parent, columns=cols, show="headings", selectmode="browse")
        
        for ex in exemplares:
            chave = f"{ex['nome']} | {ex['patrimonio']}" 
            tree.insert("", tk.END, iid=chave, values=(ex["nome"], ex["patrimonio"], ex["status"], ex["em_posse"]))

        def requisitar_exemplar():
            sel = tree.selection()
            if not sel: return
            chave = sel[0]
            patrimonio = chave.split(' | ')[1] 

            resultado = self.controller.realizar_emprestimo(
                patrimonio, 
                self.usuario_logado['usuario'] 
            )
            
            if resultado['status'] == 'sucesso':
                messagebox.showinfo("OK", "Requisição registrada.")
                
                item_atualizado = self.controller.obter_item_por_patrimonio(patrimonio) 
                tree.item(chave, values=(item_atualizado["nome"], item_atualizado["patrimonio"], item_atualizado["status"], item_atualizado["em_posse"]))
            else:
                messagebox.showwarning("Erro", resultado['mensagem'])

        def devolver_exemplar():
            sel = tree.selection()
            if not sel: return
            chave = sel[0]
            patrimonio = chave.split(' | ')[1]

            resultado = self.controller.gerenciar_devolucao(patrimonio)

            if resultado['status'] == 'sucesso':
                messagebox.showinfo("OK", "Devolução registrada.")
                item_atualizado = self.controller.obter_item_por_patrimonio(patrimonio)
                tree.item(chave, values=(item_atualizado["nome"], item_atualizado["patrimonio"], item_atualizado["status"], item_atualizado["em_posse"]))
            else:
                messagebox.showwarning("Erro", resultado['mensagem'])
                
        

if __name__ == '__main__':
    class MockController:
        def fazer_login(self, user, senha):
            if user == "teste" and senha == "123":
                return True, {"usuario": "teste", "tipo": "DIRETOR"}
            return False, "Usuário ou senha inválidos."
        
        def obter_categorias(self):
            return {"Ambientes":1, "Tecnologia":2}

        def listar_exemplares_por_categoria(self, cat):
            return [{"nome":"Item A","patrimonio":"0001","status":"Disponível","em_posse":""}]
        
        def realizar_emprestimo(self, pat, user):
             return {'status': 'sucesso'}
             
        def gerenciar_devolucao(self, pat):
             return {'status': 'sucesso'}
             
        def obter_item_por_patrimonio(self, pat):
            return {"nome":"Item A","patrimonio":"0001","status":"Em uso","em_posse":"teste"}
            
    
    root = tk.Tk()
    root.withdraw() 
    
    controller_instance = MockController() 
    
    app_view = AppView(root, controller_instance)
    
    root.mainloop()