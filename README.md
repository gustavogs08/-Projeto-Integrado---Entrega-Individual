# Crescimento Demográfico — Números que Falam

Dashboard Streamlit para analisar a variação populacional dos municípios brasileiros com dados do IBGE.

## Executar no Windows (PowerShell)

```powershell
python -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Se o ambiente virtual já estiver ativado, não é necessário repetir os dois primeiros comandos.

## Dados incluídos
- `dados/crescimento_municipios_2010_2022.csv`: população municipal de 2010 compatibilizada com a Base Territorial 2022 e população do Censo 2022.
- `dados/territorio_municipios_2022.csv`: dados territoriais do Censo 2022.
- `dados/estimativa_populacao_2026.csv`: estimativas municipais do IBGE para 2026, cruzadas pelo código IBGE.

## Funcionalidades
- Upload opcional de uma base censitária CSV/XLSX com UF, município, população de 2010 e população de 2022.
- Upload/atualização da estimativa municipal do IBGE 2026 em CSV/XLSX.
- Filtros por região, UF, município e período (2010–2022 ou 2022–2026 estimado).
- Indicadores: média, mediana, moda aproximada (valores arredondados a duas casas), quartis, IQR, amplitude, variância, desvio padrão e outliers pela regra 1,5 × IQR.
- Visualizações interativas: boxplot, histograma, ranking municipal e comparação regional.
- Tabela filtrada, interpretação para gestores públicos e bloco de contexto com notícia e fontes oficiais.

## Limitações metodológicas
A base municipal incluída possui população total, UF e município. Ela não contém sexo nem faixa etária; portanto, esses filtros não são apresentados como se estivessem disponíveis. Para análises de estrutura etária ou por sexo, é necessário incorporar uma base complementar do IBGE.

A estimativa de 2026 é uma operação estatística distinta do Censo, com referência em 1º de julho de 2026. Não deve ser descrita como resultado censitário. A comparação 2010–2022 usa população de 2010 compatibilizada com a divisão territorial de 2022.

## Bibliotecas
Instale as dependências com `python -m pip install -r requirements.txt`.
