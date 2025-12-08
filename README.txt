MANUAL DE INSTALAÇÃO E EXECUÇÃO (README)

### Guia de Configuração e Execução do Sistema de Estoque

Este documento descreve os passos necessários para configurar o ambiente de banco de dados e rodar o aplicativo SistemaEstoque.exe.

---

### 1. Pré-requisito Único

O único software externo necessário para rodar o projeto é o **PostgreSQL Server**, que deve estar instalado e em execução na sua máquina.

---

### 2. Configuração do Banco de Dados

O sistema utiliza um banco de dados PostgreSQL. A configuração é feita em duas etapas simples.

#### 2.1. Criação do Banco de Dados

Primeiro, crie o banco de dados principal. Copie e execute o comando abaixo no seu console SQL (como psql ou pgAdmin):

CREATE DATABASE A_Voz_do_Cliente
    WITH OWNER = postgres
           ENCODING = 'UTF8'
           TEMPLATE = template0;

#### 2.2. Criação do Esquema e População de Dados

Após a criação, **conecte-se** ao banco de dados A_Voz_do_Cliente. Em seguida, execute todo o código SQL do arquivo **dados.txt**.

Este script é o responsável por criar todas as tabelas (DDL), inserir os dados iniciais de controle e popular o sistema com aproximadamente 4729 itens de patrimônio para teste (DML), prontos para uso.

#### 2.3. Configuração de Credenciais (.env)

Por padrão, o projeto espera conectar-se ao usuário **postgres** com a senha **1234**.

Se o usuário precisar utilizar outras credenciais (outra senha, por exemplo), deve criar um arquivo chamado **.env** na mesma pasta do executável e preencher com os dados corretos:

DB_NAME="A_Voz_do_Cliente"
DB_USER="postgres"
DB_PASS="sua_senha_aqui" 
DB_HOST="localhost"
DB_PORT="5432"

---

### 3. Execução do Programa

Com o banco de dados configurado e populado, basta executar o programa.

* Execute o arquivo principal: **SistemaEstoque.exe**.

#### Credenciais de Acesso para Teste

Utilize as seguintes credenciais de teste, que foram cadastradas no passo 2.2:

* Usuário Administrador (TI): Nome: **TI** | Senha: **0000**
* Usuário Operacional (Almoxarifado): Nome: **ALMOXARIFADO** | Senha: **0000**

---

### 4. Detalhamento de Funcionalidades do Programa

O sistema é uma aplicação gráfica desenvolvida para gerenciar o ciclo de vida e a localização dos itens de patrimônio e estoque.

#### 4.1. Módulos Principais

* **Login de Usuário**: Tela inicial que valida o Nome e Senha. Define o nível de acesso do usuário com base na tabela USUARIOS e no nível de permissão associado (JUNCAO_USUARIOS_CP).
* **Controle de Itens**: Permite buscar, visualizar e gerenciar todos os itens do patrimônio (tabela ITENS).
* **Movimentações**: Módulo responsável por registrar o fluxo do item (empréstimo, devolução ou baixa), atualizando seu STATUS e registrando cada transação na tabela MOVIMENTACOES.
* **Relatórios e Gráficos**: Exibe visualizações gráficas (utilizando matplotlib/seaborn) sobre a distribuição atual dos itens por status (DISPONÍVEL, EM USO, EXTRAVIADO).
* **Histórico**: Permite a consulta detalhada de todas as operações. As movimentações são registradas tanto no banco de dados quanto no arquivo de log historico.json.

#### 4.2. Ações dos Botões de Controle

* **Adicionar Item (Cadastro)**:
    * O que faz: Cria um novo item no patrimônio.
    * Detalhes: Gera um novo numero_patrimonio e registra sua primeira movimentação com STATUS='DISPONÍVEL' para um local no Almoxarifado. (Função: controller.registrar_item()).

* **Emprestar Item**:
    * O que faz: Registra a saída de um item.
    * Detalhes: Altera o status do item para "EM USO" e insere um novo registro na MOVIMENTACOES, associando o item ao usuário logado e à sua nova localização. (Função: controller.registrar_movimentacao_emprestimo()).

* **Devolver Item**:
    * O que faz: Registra o retorno de um item.
    * Detalhes: Altera o status do item de volta para "DISPONÍVEL" e registra a devolução, geralmente para um local de estoque no Almoxarifado. (Função: controller.registrar_movimentacao_devolucao()).

* **Excluir Item**:
    * O que faz: Remove permanentemente um item do patrimônio.
    * Detalhes: Remove o registro do item e todas as suas movimentações históricas. É crucial que as chaves estrangeiras do banco (FOREIGN KEY) estejam configuradas com ON DELETE CASCADE para a exclusão completa, ou o sistema fará a exclusão manual em sequência. (Função: controller.deletar_item()).

* **Gerenciar Usuários (Criar/Excluir)**:
    * O que faz: Permite a gestão de contas de acesso.
    * Detalhes: Usuários com permissão adequada podem criar ou excluir outras contas. O sistema inclui uma verificação de segurança: um usuário não pode ser excluído se tiver itens emprestados. (Funções: controller.criar_usuario(), controller.apagar_usuario(), controller.verificar_itens_emprestados_usuario()).