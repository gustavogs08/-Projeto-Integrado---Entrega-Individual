# RELATÓRIO DO PROJETO INTEGRADOR
## Números que Falam — Descobrindo o Brasil
### Dashboard de Crescimento Demográfico

**Integrantes:** [Inserir nomes dos integrantes]  
**Instituição:** COTEMIG  
**Tecnologia principal:** Python e Streamlit

### 1. Introdução

O crescimento demográfico é um importante indicador para compreender as transformações populacionais de uma região. Analisar essas mudanças permite identificar municípios que apresentam crescimento ou redução populacional, contribuindo para o planejamento de políticas públicas e para a tomada de decisões.

O projeto **Números que Falam — Descobrindo o Brasil** tem como objetivo desenvolver um dashboard interativo que permita visualizar e analisar o crescimento populacional dos municípios brasileiros, utilizando dados disponibilizados pelo Instituto Brasileiro de Geografia e Estatística (IBGE).

### 2. Desenvolvimento e metodologia

O projeto foi desenvolvido utilizando a linguagem Python, com a biblioteca Streamlit para a construção da interface interativa e Plotly para a criação dos gráficos.

Foram utilizadas bases de dados do IBGE referentes ao Censo Demográfico de 2010 e 2022, além de dados de estimativas populacionais de 2026 e informações territoriais dos municípios.

O desenvolvimento envolveu as seguintes etapas:

- **Coleta de dados:** obtenção das bases populacionais e territoriais do IBGE.
- **Tratamento dos dados (ETL):** organização, padronização, limpeza e preparação das informações para análise.
- **Análise estatística:** cálculo de média, mediana, moda aproximada, quartis, amplitude, desvio padrão e variância.
- **Identificação de valores atípicos:** aplicação do método do intervalo interquartil (IQR), utilizando o critério de 1,5 vezes o IQR.
- **Visualização:** criação de gráficos, tabelas e rankings para facilitar a interpretação dos resultados.

O dashboard também permite filtrar os dados por região, estado e município, além de selecionar diferentes períodos de análise.

### 3. Resultados obtidos

A análise estatística realizada sobre a variação populacional apresentou os seguintes resultados:

| Indicador | Resultado |
|---|---:|
| Média | 2,68% |
| Mediana | 2,69% |
| Moda aproximada | 2,25% |
| Primeiro quartil (Q1) | 1,03% |
| Terceiro quartil (Q3) | 4,11% |
| Desvio padrão | 2,52% |
| Intervalo interquartil | 3,08 p.p. |
| Amplitude | 21,41 p.p. |
| Variância amostral | 6,34 |

A aplicação do método IQR identificou **23 municípios como possíveis valores atípicos (outliers)**, considerando os limites calculados de aproximadamente -3,59% e 8,73%.

Esses resultados demonstram que o crescimento populacional não ocorre de maneira uniforme entre os municípios brasileiros, existindo diferenças relevantes entre as localidades analisadas.

O dashboard permite explorar essas diferenças por meio de gráficos de distribuição, comparação entre regiões, rankings municipais e tabelas detalhadas.

### 4. Conclusão

O desenvolvimento do projeto possibilitou aplicar conhecimentos de programação, manipulação de dados, estatística e visualização de informações em uma situação prática.

A ferramenta desenvolvida facilita a compreensão das mudanças demográficas brasileiras e demonstra como os dados públicos podem ser transformados em informações úteis para a sociedade e para a gestão pública.

Conclui-se que o dashboard atende ao objetivo de apresentar uma análise interativa do crescimento populacional dos municípios, contribuindo para a interpretação dos dados do IBGE e para o desenvolvimento de habilidades técnicas e analíticas dos integrantes do grupo.

### 5. Fontes de dados e tecnologias

**Fonte principal:** Instituto Brasileiro de Geografia e Estatística (IBGE).

**Tecnologias utilizadas:**
- Python;
- Streamlit;
- Pandas;
- Plotly.

**Referência:** [IBGE — Instituto Brasileiro de Geografia e Estatística](https://www.ibge.gov.br/).
