import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# 1. Carregar o Dataset de Exemplo (Iris)
# Este dataset é muito comum e é usado para classificação de flores.
df = sns.load_dataset("iris")

# 2. Verificar se o DataFrame foi carregado
if df is None or df.empty:
    print("Erro: O dataset 'iris' não foi carregado corretamente.")
    exit()

# 3. Criar o Gráfico de Dispersão (Scatterplot)
# Vamos plotar o comprimento da sépala vs. a largura da sépala,
# colorindo os pontos de acordo com a espécie da flor.
sns.scatterplot(
    data=df,
    x="sepal_length",     # Eixo X: Comprimento da Sépala
    y="sepal_width",      # Eixo Y: Largura da Sépala
    hue="species",        # Cor dos pontos: Espécie da flor
    palette="viridis",    # Paleta de cores moderna
    s=80,                 # Tamanho dos pontos
    alpha=0.7             # Transparência
)

# 4. Adicionar Detalhes e Exibir
plt.title("Relação entre Comprimento e Largura da Sépala por Espécie (Dataset Iris)", fontsize=14)
plt.xlabel("Comprimento da Sépala (cm)")
plt.ylabel("Largura da Sépala (cm)")
plt.legend(title="Espécie")

# Exibe o gráfico na tela
plt.show()