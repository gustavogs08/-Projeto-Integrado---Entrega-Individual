
import re
import unicodedata
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Crescimento Demográfico | IBGE",
    page_icon="📊",
    layout="wide",
)

BASE = Path(__file__).parent
DADOS = BASE / "dados"
ARQUIVO_BASE = DADOS / "crescimento_municipios_2010_2022.csv"
ARQUIVO_2026 = DADOS / "estimativa_populacao_2026.csv"

REGIOES = {
    "Norte": ["AC", "AP", "AM", "PA", "RO", "RR", "TO"],
    "Nordeste": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
    "Centro-Oeste": ["DF", "GO", "MT", "MS"],
    "Sudeste": ["ES", "MG", "RJ", "SP"],
    "Sul": ["PR", "RS", "SC"],
}

UF_REGIAO = {
    uf: regiao
    for regiao, ufs in REGIOES.items()
    for uf in ufs
}


def normalizar(texto):
    texto = unicodedata.normalize(
        "NFKD", str(texto)
    ).encode("ascii", "ignore").decode("ascii")

    return re.sub(
        r"[^a-z0-9]+", "_", texto.lower()
    ).strip("_")


def ler_tabela(arquivo):
    nome = getattr(arquivo, "name", str(arquivo)).lower()

    if nome.endswith((".xlsx", ".xls")):
        return pd.read_excel(arquivo)

    try:
        return pd.read_csv(
            arquivo,
            encoding="utf-8-sig",
            sep=None,
            engine="python",
        )
    except UnicodeDecodeError:
        arquivo.seek(0)
        return pd.read_csv(
            arquivo,
            encoding="latin-1",
            sep=None,
            engine="python",
        )


def preparar_base(bruto):
    df = bruto.copy()
    df.columns = [normalizar(c) for c in df.columns]

    aliases = {
        "codigo_ibge": [
            "codigo_ibge",
            "cod_ibge",
            "codigo_do_municipio",
        ],
        "uf": ["uf", "sigla_uf", "estado"],
        "municipio": [
            "municipio",
            "nome_municipio",
            "nome_do_municipio",
        ],
        "populacao_2010": [
            "populacao_2010",
            "pop_2010",
        ],
        "populacao_2022": [
            "populacao_2022",
            "pop_2022",
        ],
    }

    renomear = {}

    for destino, opcoes in aliases.items():
        encontrado = next(
            (c for c in opcoes if c in df.columns),
            None,
        )

        if encontrado:
            renomear[encontrado] = destino

    df = df.rename(columns=renomear)

    obrigatorias = [
        "uf",
        "municipio",
        "populacao_2010",
        "populacao_2022",
    ]

    faltantes = [
        c for c in obrigatorias
        if c not in df.columns
    ]

    if faltantes:
        raise ValueError(
            "A base precisa conter UF, município, população de 2010 "
            "e população de 2022. "
            f"Colunas ausentes: {', '.join(faltantes)}."
        )

    if "codigo_ibge" not in df.columns:
        if (
            "codigo_uf" in df.columns
            and "codigo_municipio" in df.columns
        ):
            df["codigo_ibge"] = (
                pd.to_numeric(
                    df["codigo_uf"],
                    errors="coerce",
                ) * 100000
                + pd.to_numeric(
                    df["codigo_municipio"],
                    errors="coerce",
                )
            )

    for c in ["populacao_2010", "populacao_2022"]:
        df[c] = pd.to_numeric(
            df[c],
            errors="coerce",
        )

    df["uf"] = (
        df["uf"]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    df["municipio"] = (
        df["municipio"]
        .astype(str)
        .str.strip()
    )

    df = df.dropna(
        subset=["populacao_2010", "populacao_2022"]
    )

    df = df[
        (df["populacao_2010"] > 0)
        & (df["populacao_2022"] >= 0)
    ].copy()

    df["crescimento_absoluto"] = (
        df["populacao_2022"] - df["populacao_2010"]
    )

    df["crescimento_percentual"] = (
        df["crescimento_absoluto"]
        / df["populacao_2010"]
        * 100
    )

    df["taxa_media_anual_percentual"] = (
        (
            df["populacao_2022"]
            / df["populacao_2010"]
        ) ** (1 / 12) - 1
    ) * 100

    df["regiao"] = df["uf"].map(UF_REGIAO)

    return df


@st.cache_data
def carregar_base_padrao():
    return preparar_base(
        pd.read_csv(
            ARQUIVO_BASE,
            encoding="utf-8-sig",
        )
    )


def ler_estimativa_2026(arquivo):
    nome = getattr(
        arquivo,
        "name",
        str(arquivo),
    ).lower()

    if nome.endswith(".csv"):
        bruto = ler_tabela(arquivo)
        bruto.columns = [
            normalizar(c) for c in bruto.columns
        ]

        if not {
            "codigo_ibge",
            "populacao_2026",
        }.issubset(bruto.columns):
            raise ValueError(
                "O CSV de estimativas precisa conter "
                "codigo_ibge e populacao_2026."
            )

        dados = bruto[
            ["codigo_ibge", "populacao_2026"]
        ].copy()

    else:
        bruto = pd.read_excel(
            arquivo,
            sheet_name="MUNICÍPIOS",
            header=1,
            dtype=str,
        )

        colunas = {
            normalizar(c): c
            for c in bruto.columns
        }

        uf_col = next(
            (
                v for k, v in colunas.items()
                if k in ["cod_uf", "codigo_uf"]
            ),
            None,
        )

        mun_col = next(
            (
                v for k, v in colunas.items()
                if k in ["cod_munic", "codigo_municipio"]
            ),
            None,
        )

        pop_col = next(
            (
                v for k, v in colunas.items()
                if "populacao" in k and "estimada" in k
            ),
            None,
        )

        if not all([uf_col, mun_col, pop_col]):
            raise ValueError(
                "Não encontrei COD. UF, COD. MUNIC "
                "e POPULAÇÃO ESTIMADA na aba MUNICÍPIOS."
            )

        dados = bruto[
            [uf_col, mun_col, pop_col]
        ].copy()

        dados["codigo_ibge"] = (
            pd.to_numeric(
                dados[uf_col]
                .astype(str)
                .str.extract(r"(\d{2})", expand=False),
                errors="coerce",
            ) * 100000
            + pd.to_numeric(
                dados[mun_col]
                .astype(str)
                .str.extract(r"(\d{5})", expand=False),
                errors="coerce",
            )
        )

        dados["populacao_2026"] = pd.to_numeric(
            dados[pop_col]
            .astype(str)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False),
            errors="coerce",
        )

        dados = dados[
            ["codigo_ibge", "populacao_2026"]
        ]

    dados["codigo_ibge"] = pd.to_numeric(
        dados["codigo_ibge"],
        errors="coerce",
    )

    dados["populacao_2026"] = pd.to_numeric(
        dados["populacao_2026"],
        errors="coerce",
    )

    dados = (
        dados.dropna()
        .drop_duplicates("codigo_ibge")
    )

    if len(dados) < 5000:
        raise ValueError(
            f"Foram encontrados apenas {len(dados):,} "
            "registros; confira a planilha do IBGE."
        )

    return dados


def fmt_num(valor, casas=0):
    if pd.isna(valor):
        return "—"

    return f"{valor:,.{casas}f}".replace(
        ",", "X"
    ).replace(
        ".", ","
    ).replace(
        "X", "."
    )


# --------------------------------------------------
# CABEÇALHO
# --------------------------------------------------

st.title("📊 Crescimento Demográfico no Brasil")

st.caption(
    "Análise municipal com dados do Censo Demográfico 2010 e 2022 "
    "e estimativas populacionais do IBGE para 2026. "
    "O painel foi desenvolvido para apoiar a leitura territorial "
    "e o planejamento de políticas públicas."
)


# --------------------------------------------------
# CARREGAMENTO DAS BASES
# --------------------------------------------------

try:
    base_padrao = carregar_base_padrao()

except Exception as erro:
    st.error(
        "Não foi possível carregar a base municipal "
        f"incluída no projeto: {erro}"
    )
    st.stop()

base = base_padrao.copy()
est26 = None

if ARQUIVO_2026.exists():
    try:
        est26 = ler_estimativa_2026(ARQUIVO_2026)

    except Exception as erro:
        st.warning(
            "A base local de estimativas de 2026 "
            f"não pôde ser carregada: {erro}"
        )


# --------------------------------------------------
# BARRA LATERAL E FILTROS
# --------------------------------------------------

with st.sidebar:
    st.header("Filtros e dados")

    upload_base = st.file_uploader(
        "Substituir base censitária (CSV/XLSX)",
        type=["csv", "xlsx"],
    )

    if upload_base is not None:
        try:
            base = preparar_base(
                ler_tabela(upload_base)
            )

            st.success(
                f"Base carregada: {len(base):,} municípios."
                .replace(",", ".")
            )

        except Exception as erro:
            st.error(
                f"Não foi possível usar essa base: {erro}"
            )
            base = base_padrao.copy()

    upload_2026 = st.file_uploader(
        "Atualizar estimativa IBGE 2026 (CSV/XLSX)",
        type=["csv", "xlsx"],
    )

    if upload_2026 is not None:
        try:
            est26 = ler_estimativa_2026(upload_2026)

            st.success(
                f"Estimativa carregada: {len(est26):,} registros."
                .replace(",", ".")
            )

        except Exception as erro:
            st.error(str(erro))

    st.divider()

    regioes_disponiveis = [
        r for r in REGIOES
        if r in base["regiao"].dropna().unique()
    ]

    regiao = st.selectbox(
        "Região",
        ["Todas"] + regioes_disponiveis,
    )

    ufs_disponiveis = sorted(
        base["uf"].dropna().unique()
    )

    if regiao != "Todas":
        ufs_disponiveis = [
            u for u in ufs_disponiveis
            if UF_REGIAO.get(u) == regiao
        ]

    uf = st.selectbox(
        "Estado (UF)",
        ["Todos"] + ufs_disponiveis,
    )

    busca = st.text_input("Buscar município")

    periodo_opcoes = ["Censos 2010–2022"]

    if est26 is not None:
        periodo_opcoes.append(
            "Estimativa 2022–2026"
        )

    periodo = st.radio(
        "Período de análise",
        periodo_opcoes,
    )

    ranking_opcao = st.selectbox(
        "Ordenar ranking por",
        [
            "Maior crescimento percentual",
            "Maior crescimento absoluto",
            "Maior redução populacional",
        ],
    )


# --------------------------------------------------
# JUNÇÃO COM ESTIMATIVAS DE 2026
# --------------------------------------------------

if (
    est26 is not None
    and "codigo_ibge" in base.columns
):
    base["codigo_ibge"] = pd.to_numeric(
        base["codigo_ibge"],
        errors="coerce",
    )

    base = base.merge(
        est26,
        on="codigo_ibge",
        how="left",
    )


# --------------------------------------------------
# APLICAÇÃO DOS FILTROS
# --------------------------------------------------

filtrado = base.copy()

if regiao != "Todas":
    filtrado = filtrado[
        filtrado["regiao"] == regiao
    ]

if uf != "Todos":
    filtrado = filtrado[
        filtrado["uf"] == uf
    ]

if busca.strip():
    filtrado = filtrado[
        filtrado["municipio"].str.contains(
            busca.strip(),
            case=False,
            na=False,
        )
    ]


# --------------------------------------------------
# CÁLCULO DA VARIAÇÃO POPULACIONAL
# --------------------------------------------------

if periodo == "Estimativa 2022–2026":

    if "populacao_2026" not in filtrado.columns:
        st.error(
            "A estimativa de 2026 não está disponível. "
            "Carregue o arquivo do IBGE na barra lateral."
        )
        st.stop()

    filtrado = filtrado.dropna(
        subset=["populacao_2026"]
    ).copy()

    filtrado = filtrado[
        filtrado["populacao_2022"] > 0
    ]

    filtrado["variacao_absoluta"] = (
        filtrado["populacao_2026"]
        - filtrado["populacao_2022"]
    )

    filtrado["variacao_percentual"] = (
        filtrado["variacao_absoluta"]
        / filtrado["populacao_2022"]
        * 100
    )

    rotulo_periodo = "2022–2026 (estimativa)"

else:
    filtrado["variacao_absoluta"] = (
        filtrado["populacao_2022"]
        - filtrado["populacao_2010"]
    )

    filtrado["variacao_percentual"] = (
        filtrado["variacao_absoluta"]
        / filtrado["populacao_2010"]
        * 100
    )

    rotulo_periodo = "2010–2022 (Censos)"


if filtrado.empty:
    st.warning(
        "Nenhum município encontrado para os filtros selecionados."
    )
    st.stop()

x = (
    filtrado["variacao_percentual"]
    .replace(
        [float("inf"), -float("inf")],
        pd.NA,
    )
    .dropna()
)

if x.empty:
    st.warning(
        "Não há valores suficientes para calcular "
        "as estatísticas neste recorte."
    )
    st.stop()


# --------------------------------------------------
# VISÃO GERAL
# --------------------------------------------------

pop_inicio = (
    filtrado["populacao_2010"].sum()
    if periodo == "Censos 2010–2022"
    else filtrado["populacao_2022"].sum()
)

pop_fim = (
    filtrado["populacao_2022"].sum()
    if periodo == "Censos 2010–2022"
    else filtrado["populacao_2026"].sum()
)

variacao_total = pop_fim - pop_inicio

variacao_total_pct = (
    variacao_total / pop_inicio * 100
    if pop_inicio
    else 0
)

st.subheader(
    f"Visão geral — {rotulo_periodo}"
)

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "População inicial",
    fmt_num(pop_inicio),
)

k2.metric(
    "População final",
    fmt_num(pop_fim),
)

k3.metric(
    "Variação absoluta",
    f"{fmt_num(variacao_total, 0)} pessoas",
)

k4.metric(
    "Variação total",
    f"{variacao_total_pct:+.2f}%",
)

st.caption(
    f"Municípios no recorte: {len(filtrado):,}."
    .replace(",", ".")
)


# --------------------------------------------------
# ESTATÍSTICA DESCRITIVA
# --------------------------------------------------

st.subheader(
    "Estatística descritiva do crescimento municipal"
)

q1 = x.quantile(0.25)
mediana = x.median()
q3 = x.quantile(0.75)

iqr = q3 - q1

limite_inf = q1 - 1.5 * iqr
limite_sup = q3 + 1.5 * iqr

outliers = filtrado[
    (filtrado["variacao_percentual"] < limite_inf)
    | (filtrado["variacao_percentual"] > limite_sup)
].copy()

modas = x.round(2).mode()

moda_txt = (
    ", ".join(
        f"{v:.2f}%"
        for v in modas.head(3)
    )
    if len(modas)
    else "Não identificada"
)

m1, m2, m3, m4, m5, m6 = st.columns(6)

m1.metric("Média", f"{x.mean():.2f}%")
m2.metric("Mediana", f"{mediana:.2f}%")
m3.metric("Moda aproximada", moda_txt)
m4.metric("Q1", f"{q1:.2f}%")
m5.metric("Q3", f"{q3:.2f}%")

m6.metric(
    "Desvio padrão",
    f"{x.std(ddof=1):.2f}%"
    if len(x) > 1
    else "—",
)

st.info(
    f"IQR: {iqr:.2f} pontos percentuais | "
    f"Amplitude: {x.max() - x.min():.2f} p.p. | "
    f"Variância amostral: {x.var(ddof=1):.2f} | "
    f"Limites de outliers: {limite_inf:.2f}% a "
    f"{limite_sup:.2f}% | "
    f"Municípios atípicos: {len(outliers)}."
)


# --------------------------------------------------
# BOXPLOT E DISTRIBUIÇÃO
# --------------------------------------------------

st.subheader("Distribuição e comparação")

col1, col2 = st.columns(2)

with col1:
    fig_box = px.box(
        filtrado,
        y="variacao_percentual",
        points="outliers",
        title="Boxplot do crescimento percentual municipal",
        labels={
            "variacao_percentual": "Variação populacional (%)"
        },
    )

    fig_box.add_hline(
        y=mediana,
        line_dash="dash",
        annotation_text=f"Mediana: {mediana:.2f}%",
    )

    st.plotly_chart(
        fig_box,
        use_container_width=True,
    )

with col2:
    fig_hist = px.histogram(
        filtrado,
        x="variacao_percentual",
        nbins=35,
        title="Distribuição do crescimento percentual",
        labels={
            "variacao_percentual": "Variação populacional (%)"
        },
    )

    st.plotly_chart(
        fig_hist,
        use_container_width=True,
    )


# --------------------------------------------------
# RANKING DE MUNICÍPIOS
# --------------------------------------------------

col3, col4 = st.columns(2)

with col3:
    ranking = filtrado.copy()

    if ranking_opcao == "Maior crescimento percentual":
        ranking = ranking.sort_values(
            "variacao_percentual",
            ascending=False,
        ).head(15)

    elif ranking_opcao == "Maior crescimento absoluto":
        ranking = ranking.sort_values(
            "variacao_absoluta",
            ascending=False,
        ).head(15)

    else:
        ranking = ranking.sort_values(
            "variacao_absoluta",
            ascending=True,
        ).head(15)

    fig_rank = px.bar(
        ranking.sort_values("variacao_percentual"),
        x="variacao_percentual",
        y="municipio",
        color="uf",
        orientation="h",
        title="Municípios em destaque",
        labels={
            "variacao_percentual": "Variação (%)",
            "municipio": "Município",
            "uf": "UF",
        },
    )

    st.plotly_chart(
        fig_rank,
        use_container_width=True,
    )


# --------------------------------------------------
# GRÁFICO REGIONAL — CORRIGIDO
# --------------------------------------------------

with col4:

    coluna_inicio = (
        "populacao_2010"
        if periodo == "Censos 2010–2022"
        else "populacao_2022"
    )

    coluna_fim = (
        "populacao_2022"
        if periodo == "Censos 2010–2022"
        else "populacao_2026"
    )

    regional = filtrado.dropna(
        subset=[
            "regiao",
            coluna_inicio,
            coluna_fim,
        ]
    ).copy()

    regional = regional[
        (regional[coluna_inicio] > 0)
        & (regional[coluna_fim] >= 0)
    ]

    if not regional.empty:

        regional = regional.groupby(
            "regiao",
            as_index=False,
        ).agg(
            populacao_inicial=(
                coluna_inicio,
                "sum",
            ),
            populacao_final=(
                coluna_fim,
                "sum",
            ),
        )

        regional["crescimento_regional_pct"] = (
            (
                regional["populacao_final"]
                / regional["populacao_inicial"]
            ) - 1
        ) * 100

        fig_reg = px.bar(
            regional.sort_values(
                "crescimento_regional_pct",
                ascending=False,
            ),
            x="regiao",
            y="crescimento_regional_pct",
            title="Crescimento populacional por região",
            labels={
                "regiao": "Região",
                "crescimento_regional_pct": "Variação regional (%)",
            },
            text_auto=".2f",
        )

        fig_reg.update_layout(
            xaxis_title="Região",
            yaxis_title="Crescimento (%)",
            showlegend=False,
        )

        fig_reg.update_traces(
            textposition="outside",
            cliponaxis=False,
        )

        st.plotly_chart(
            fig_reg,
            use_container_width=True,
            config={"responsive": True},
        )

    else:
        st.warning(
            "Não há dados regionais suficientes "
            "para gerar o gráfico."
        )


# --------------------------------------------------
# TABELA DE MUNICÍPIOS
# --------------------------------------------------

st.subheader("Tabela de municípios")

colunas_tabela = [
    "municipio",
    "uf",
    "populacao_2010",
    "populacao_2022",
    "variacao_absoluta",
    "variacao_percentual",
]

if "populacao_2026" in filtrado.columns:
    colunas_tabela.append("populacao_2026")

tabela = filtrado[colunas_tabela].copy()

tabela = tabela.rename(
    columns={
        "municipio": "Município",
        "uf": "UF",
        "populacao_2010": "População 2010",
        "populacao_2022": "População 2022",
        "populacao_2026": "Estimativa 2026",
        "variacao_absoluta": "Variação absoluta",
        "variacao_percentual": "Variação (%)",
    }
)

st.dataframe(
    tabela,
    use_container_width=True,
    hide_index=True,
)


# --------------------------------------------------
# IDENTIFICAÇÃO DE OUTLIERS
# --------------------------------------------------

st.subheader(
    "Outliers identificados pelo critério 1,5 × IQR"
)

if outliers.empty:
    st.success(
        "Nenhum município foi identificado como outlier neste recorte."
    )

else:
    st.write(
        f"Foram identificados {len(outliers)} municípios "
        "fora dos limites estatísticos. Isso não significa "
        "erro nos dados: são casos que merecem investigação contextual."
    )

    st.dataframe(
        outliers[
            [
                "municipio",
                "uf",
                "variacao_percentual",
                "variacao_absoluta",
            ]
        ]
        .sort_values("variacao_percentual")
        .rename(
            columns={
                "municipio": "Município",
                "uf": "UF",
                "variacao_percentual": "Variação (%)",
                "variacao_absoluta": "Variação absoluta",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


# --------------------------------------------------
# INTERPRETAÇÃO PARA GESTORES PÚBLICOS
# --------------------------------------------------

st.subheader("Leitura para gestores públicos")

if variacao_total > 0:

    st.write(
        f"No recorte selecionado, a população agregada "
        f"cresceu {fmt_num(variacao_total)} pessoas "
        f"({variacao_total_pct:.2f}%) em {rotulo_periodo}. "
        "O aumento pode ampliar a demanda por moradia, "
        "mobilidade, saneamento, escolas e unidades de saúde."
    )

elif variacao_total < 0:

    st.write(
        f"No recorte selecionado, a população agregada "
        f"diminuiu {fmt_num(abs(variacao_total))} pessoas "
        f"({abs(variacao_total_pct):.2f}%) em {rotulo_periodo}. "
        "O planejamento deve investigar envelhecimento, "
        "migração, oferta de serviços e possíveis mudanças "
        "na ocupação urbana."
    )

else:
    st.write(
        "A população agregada permaneceu estável "
        "no período selecionado."
    )

if abs(x.mean() - x.median()) > 1:
    st.info(
        "A média e a mediana estão distantes. Isso sugere "
        "assimetria e influência de variações extremas; "
        "a mediana pode representar melhor o município típico."
    )

if not outliers.empty:

    maior_outlier = outliers.loc[
        outliers["variacao_percentual"].abs().idxmax()
    ]

    st.write(
        f"Entre os casos atípicos, "
        f"{maior_outlier['municipio']} "
        f"({maior_outlier['uf']}) apresenta variação de "
        f"{maior_outlier['variacao_percentual']:.2f}%. "
        "O caso deve ser analisado considerando migração, "
        "dinâmica econômica, alterações territoriais "
        "e qualidade da informação."
    )


# --------------------------------------------------
# PERGUNTAS DA CONSULTORIA
# --------------------------------------------------

with st.expander(
    "Perguntas que a consultoria pode responder"
):

    st.markdown(
        "- **Onde a população cresceu mais?** "
        "Consulte o ranking por crescimento percentual ou absoluto.\n"
        "- **Quais municípios exigem investigação?** "
        "Examine os outliers e compare seus contextos locais.\n"
        "- **Como o crescimento afeta o planejamento?** "
        "Relacione a variação populacional à demanda por "
        "habitação, transporte, saneamento, educação e saúde."
    )


# --------------------------------------------------
# CONTEXTO E FONTES
# --------------------------------------------------

st.subheader(
    "Contexto e fontes para a tomada de decisão"
)

st.markdown(
    "O IBGE estimou a população brasileira em "
    "**214,2 milhões de habitantes em 1º de julho de 2026**. "
    "A taxa de crescimento nacional estimada foi de **0,37%** "
    "em relação a 2025. Esses números são um contexto nacional; "
    "não substituem a análise municipal apresentada neste painel."
)

st.markdown(
    "- [Notícia: Crescimento populacional caiu para 0,37% "
    "em 2026 — Agência Brasil (28/08/2026)]"
    "(https://agenciabrasil.ebc.com.br/economia/noticia/"
    "2026-08/crescimento-populacional-caiu-para-037-em-2026-estima-ibge)\n"
    "- [Metodologia e tabelas de estimativas populacionais — IBGE]"
    "(https://www.ibge.gov.br/estatisticas/sociais/populacao/9103)"
)

st.caption(
    "Limitação dos dados: esta base municipal contém população total, "
    "UF e município. Não há variáveis de sexo ou faixa etária; "
    "esses recortes exigem uma base complementar do IBGE "
    "e não são simulados neste painel."
)

st.caption(
    "Metodologia: a comparação 2010–2022 utiliza a população "
    "de 2010 compatibilizada com a Base Territorial 2022. "
    "A estimativa de 2026 é uma operação estatística distinta "
    "do Censo e tem referência em 1º de julho de 2026. "
    "O IBGE não produz estimativas/projeções municipais "
    "por sexo e idade nesta operação."
)

st.caption(
    "Fontes de dados: IBGE — Censo Demográfico 2010, "
    "Censo Demográfico 2022 e Estimativas da População 2026."
)
