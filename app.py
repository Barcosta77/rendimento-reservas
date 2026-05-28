import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os
from pathlib import Path

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Rendimento das Reservas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.kpi-box {
    background: #fff; border: 1px solid #e5e7eb; border-radius: 12px;
    padding: 16px 20px; text-align: left;
}
.kpi-label { font-size: 11px; font-weight: 600; color: #9ca3af;
    text-transform: uppercase; letter-spacing: .05em; margin-bottom: 4px; }
.kpi-value { font-size: 22px; font-weight: 700; color: #1a1a2e; }
.kpi-value.up { color: #059669; }
.kpi-value.down { color: #dc2626; }
.kpi-sub { font-size: 11px; color: #6b7280; margin-top: 2px; }
div[data-testid="stMetric"] { background:#fff; border:1px solid #e5e7eb; border-radius:12px; padding:14px; }
</style>
""", unsafe_allow_html=True)

# ── Dados ─────────────────────────────────────────────────────────────────────
UNIDADES = ["GV 402","GV 306","GV 305","PJ 204","CR 408",
            "T 801","T 3103","T 2807","Mercure","Puerto de Vilas","Puerto Bilbao"]

GRUPOS = {
    "Gildo Vilaça":  ["GV 402","GV 306","GV 305"],
    "Transamerica":  ["T 801","T 3103","T 2807"],
    "Outros":        ["PJ 204","CR 408","Mercure","Puerto de Vilas","Puerto Bilbao"],
}

CORES = {
    "GV 402":"#6366f1","GV 306":"#818cf8","GV 305":"#a5b4fc",
    "PJ 204":"#f59e0b","CR 408":"#10b981",
    "T 801":"#ef4444","T 3103":"#f97316","T 2807":"#fb923c",
    "Mercure":"#8b5cf6","Puerto de Vilas":"#06b6d4","Puerto Bilbao":"#0ea5e9",
}

CORES_ANOS = {2022:"#94a3b8", 2024:"#f59e0b", 2025:"#34d399", 2026:"#6366f1"}
MESES_PT = ["","Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]

@st.cache_data
def carregar_dados():
    caminho = Path(__file__).parent / "data.json"
    with open(caminho, encoding="utf-8") as f:
        raw = json.load(f)
    df = pd.DataFrame(raw)
    df = df.fillna(0)
    df["chave"] = df["ano"] * 100 + df["n"]
    df["label"] = df["mes"] + "/" + df["ano"].astype(str)
    return df

df_todos = carregar_dados()

def fmt(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def fmtk(v):
    return f"R$ {v/1000:.1f}k"

def cor_ano(ano):
    return CORES_ANOS.get(int(ano), "#6366f1")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 Rendimento das Reservas")
    st.markdown("---")

    # Unidades
    st.markdown("### Unidades")
    col_g1, col_g2, col_g3 = st.columns(3)
    with col_g1:
        if st.button("Todas", use_container_width=True):
            st.session_state["unidades"] = UNIDADES.copy()
    with col_g2:
        if st.button("Nenhuma", use_container_width=True):
            st.session_state["unidades"] = []
    with col_g3:
        if st.button("Reset", use_container_width=True):
            st.session_state["unidades"] = UNIDADES.copy()

    for grupo, ids in GRUPOS.items():
        if st.button(f"🔷 {grupo}", use_container_width=True):
            atual = st.session_state.get("unidades", UNIDADES.copy())
            todas_on = all(u in atual for u in ids)
            if todas_on:
                st.session_state["unidades"] = [u for u in atual if u not in ids]
            else:
                st.session_state["unidades"] = list(set(atual) | set(ids))

    if "unidades" not in st.session_state:
        st.session_state["unidades"] = UNIDADES.copy()

    unidades_sel = []
    for u in UNIDADES:
        checked = u in st.session_state["unidades"]
        val = st.checkbox(u, value=checked, key=f"chk_{u}")
        if val:
            unidades_sel.append(u)
    st.session_state["unidades"] = unidades_sel

    st.markdown("---")

    # Período
    st.markdown("### Período")
    anos_disp = sorted(df_todos["ano"].unique())
    meses_disp = sorted(df_todos["chave"].unique())

    primeiro = df_todos.iloc[0]
    ultimo   = df_todos.iloc[-1]

    preset = st.selectbox("Atalho rápido", [
        "Período completo", "Últimos 12 meses", "Últimos 6 meses",
        "2022", "2024", "2025", "2026",
    ])

    def get_preset_range(p):
        if p == "Período completo":
            return (int(primeiro["ano"]), int(primeiro["n"]),
                    int(ultimo["ano"]), int(ultimo["n"]))
        elif p == "Últimos 12 meses":
            m, a = int(ultimo["n"]) - 11, int(ultimo["ano"])
            if m <= 0: m += 12; a -= 1
            return a, m, int(ultimo["ano"]), int(ultimo["n"])
        elif p == "Últimos 6 meses":
            m, a = int(ultimo["n"]) - 5, int(ultimo["ano"])
            if m <= 0: m += 12; a -= 1
            return a, m, int(ultimo["ano"]), int(ultimo["n"])
        else:
            ano = int(p)
            sub = df_todos[df_todos["ano"] == ano]
            if sub.empty: return (int(primeiro["ano"]), int(primeiro["n"]),
                                  int(ultimo["ano"]), int(ultimo["n"]))
            return ano, int(sub["n"].min()), ano, int(sub["n"].max())

    ai, mi, af, mf = get_preset_range(preset)

    col_de, col_ate = st.columns(2)
    with col_de:
        st.markdown("**De**")
        ano_ini = st.selectbox("Ano ini", anos_disp, index=list(anos_disp).index(ai), label_visibility="collapsed", key="ano_ini")
        mes_ini = st.selectbox("Mês ini", list(range(1,13)), index=mi-1,
                               format_func=lambda x: MESES_PT[x], label_visibility="collapsed", key="mes_ini")
    with col_ate:
        st.markdown("**Até**")
        ano_fim = st.selectbox("Ano fim", anos_disp, index=list(anos_disp).index(af), label_visibility="collapsed", key="ano_fim")
        mes_fim = st.selectbox("Mês fim", list(range(1,13)), index=mf-1,
                               format_func=lambda x: MESES_PT[x], label_visibility="collapsed", key="mes_fim")

    st.markdown("---")

    # Tipo de gráfico
    st.markdown("### Visualização")
    view = st.radio("Modo", ["Barras", "Linha", "Por Ano", "Comparar Mês"],
                    label_visibility="collapsed")

    if view == "Comparar Mês":
        mes_comp = st.selectbox("Escolha o mês",
                                list(range(1, 13)),
                                index=3,
                                format_func=lambda x: MESES_PT[x])

    st.markdown("---")
    st.caption("Atualizado automaticamente via `atualizar_dados.py`")

# ── Filtro de dados ───────────────────────────────────────────────────────────
chave_ini = ano_ini * 100 + mes_ini
chave_fim = ano_fim * 100 + mes_fim
if chave_ini > chave_fim:
    chave_ini, chave_fim = chave_fim, chave_ini

df = df_todos[(df_todos["chave"] >= chave_ini) & (df_todos["chave"] <= chave_fim)].copy()

if not unidades_sel:
    st.warning("Selecione ao menos uma unidade na barra lateral.")
    st.stop()

if df.empty:
    st.warning("Nenhum dado para o período selecionado.")
    st.stop()

df["total"] = df[unidades_sel].sum(axis=1)

# ── Cabeçalho ─────────────────────────────────────────────────────────────────
label_u = ("todas" if len(unidades_sel) == len(UNIDADES)
           else unidades_sel[0] if len(unidades_sel) == 1
           else f"{len(unidades_sel)} unidades")
d0, d1 = df.iloc[0], df.iloc[-1]
st.title("📊 Rendimento das Reservas")
st.caption(f"Receita líquida · {label_u} · {d0['mes']}/{d0['ano']} – {d1['mes']}/{d1['ano']}")

# ── KPIs ──────────────────────────────────────────────────────────────────────
if view != "Comparar Mês":
    total_p = df["total"].sum()
    media   = df["total"].mean()
    idx_max = df["total"].idxmax()
    melhor  = df.loc[idx_max]
    delta_pct = ((df["total"].iloc[-1] - df["total"].iloc[-2]) / df["total"].iloc[-2] * 100
                 if len(df) > 1 else 0)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total do período",  fmt(total_p), f"{len(df)} meses")
    c2.metric("Média mensal",      fmtk(media))
    c3.metric("Melhor mês",        fmtk(melhor["total"]), f"{melhor['mes']}/{int(melhor['ano'])}")
    c4.metric("Último vs anterior",f"{delta_pct:+.1f}%",
              f"{d1['mes']}/{int(d1['ano'])}", delta_color="normal")
else:
    df_mes = df_todos[df_todos["n"] == mes_comp].copy()
    df_mes["total"] = df_mes[unidades_sel].sum(axis=1)
    if not df_mes.empty:
        idx_max = df_mes["total"].idxmax()
        idx_min = df_mes["total"].idxmin()
        media_m = df_mes["total"].mean()
        delta_ano = ((df_mes["total"].iloc[-1] - df_mes["total"].iloc[-2]) / df_mes["total"].iloc[-2] * 100
                     if len(df_mes) > 1 else 0)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Melhor ano", fmtk(df_mes.loc[idx_max,"total"]), str(int(df_mes.loc[idx_max,"ano"])))
        c2.metric("Pior ano",   fmtk(df_mes.loc[idx_min,"total"]), str(int(df_mes.loc[idx_min,"ano"])))
        c3.metric("Média",      fmtk(media_m), f"{len(df_mes)} anos")
        c4.metric("Último vs anterior", f"{delta_ano:+.1f}%", delta_color="normal")

st.markdown("---")

# ── Gráfico ───────────────────────────────────────────────────────────────────
fig = go.Figure()

if view == "Comparar Mês":
    df_mes = df_todos[df_todos["n"] == mes_comp].copy()
    df_mes["total"] = df_mes[unidades_sel].sum(axis=1)
    anos_labels = df_mes["ano"].astype(str).tolist()

    if len(unidades_sel) == 1:
        fig.add_trace(go.Bar(
            x=anos_labels,
            y=df_mes["total"],
            marker_color=[cor_ano(a) for a in df_mes["ano"]],
            text=[fmtk(v) for v in df_mes["total"]],
            textposition="outside",
            name=unidades_sel[0],
        ))
    else:
        for u in unidades_sel:
            fig.add_trace(go.Bar(
                x=anos_labels, y=df_mes[u].fillna(0),
                name=u, marker_color=CORES[u], marker_line_width=0,
            ))
        fig.update_layout(barmode="stack")

    titulo = f"{MESES_PT[mes_comp]} — comparação por ano"

elif view == "Por Ano":
    anos = sorted(df["ano"].unique())
    for ano in anos:
        sub = df[df["ano"] == ano]
        vals = [None] * 12
        for _, row in sub.iterrows():
            vals[int(row["n"]) - 1] = row["total"]
        fig.add_trace(go.Scatter(
            x=MESES_PT[1:], y=vals,
            mode="lines+markers", name=str(ano),
            line=dict(color=cor_ano(ano), width=2.5),
            marker=dict(size=5),
            connectgaps=False,
        ))
    titulo = "Rendimento por ano"

elif view == "Linha":
    fig.add_trace(go.Scatter(
        x=df["label"], y=df["total"],
        mode="lines+markers",
        line=dict(color="#6366f1", width=2.5),
        marker=dict(size=5),
        fill="tozeroy", fillcolor="rgba(99,102,241,0.08)",
        name="Rendimento",
    ))
    titulo = f"Rendimento mensal — {label_u}"

else:  # Barras
    if len(unidades_sel) == 1:
        fig.add_trace(go.Bar(
            x=df["label"], y=df["total"],
            marker_color=[cor_ano(a) for a in df["ano"]],
            marker_line_width=0,
            name=unidades_sel[0],
        ))
    else:
        for u in unidades_sel:
            fig.add_trace(go.Bar(
                x=df["label"], y=df[u].fillna(0),
                name=u, marker_color=CORES[u], marker_line_width=0,
            ))
        fig.update_layout(barmode="stack")
    titulo = f"Rendimento mensal — {label_u}"

fig.update_layout(
    title=titulo,
    height=380,
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=dict(family="sans-serif", size=12, color="#374151"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    margin=dict(l=10, r=10, t=60, b=10),
    xaxis=dict(showgrid=False, tickfont=dict(size=11, color="#9ca3af")),
    yaxis=dict(gridcolor="#f3f4f6", tickfont=dict(size=11, color="#9ca3af"),
               tickformat=",.0f", tickprefix="R$ "),
    hovermode="x unified",
)
fig.update_traces(
    hovertemplate="<b>%{x}</b><br>%{y:,.2f}<extra>%{fullData.name}</extra>"
)
st.plotly_chart(fig, use_container_width=True)

# ── Tabela ────────────────────────────────────────────────────────────────────
st.markdown("---")

if view == "Comparar Mês":
    st.markdown(f"#### {MESES_PT[mes_comp]} por ano")
    df_tab = df_todos[df_todos["n"] == mes_comp].copy()
    df_tab["total"] = df_tab[unidades_sel].sum(axis=1)
    df_tab["Δ ano ant."] = df_tab["total"].pct_change() * 100
    df_tab["Período"] = MESES_PT[mes_comp] + " " + df_tab["ano"].astype(str)
    df_tab["Rendimento"] = df_tab["total"].apply(fmt)
    df_tab["Δ ano ant."] = df_tab["Δ ano ant."].apply(
        lambda x: f"+{x:.1f}%" if pd.notna(x) and x >= 0 else (f"{x:.1f}%" if pd.notna(x) else "—")
    )
    cols_show = ["Período", "Rendimento", "Δ ano ant."]
    if len(unidades_sel) > 1:
        for u in unidades_sel:
            df_tab[u + " (k)"] = df_tab[u].apply(lambda v: f"{v/1000:.1f}k")
            cols_show.append(u + " (k)")
    st.dataframe(df_tab[cols_show].iloc[::-1].reset_index(drop=True),
                 use_container_width=True, hide_index=True)
else:
    st.markdown("#### Histórico completo")
    df_tab = df.copy()
    df_tab["Δ mês ant."] = df_tab["total"].pct_change() * 100
    df_tab["Período"] = df_tab["label"]
    df_tab["Rendimento"] = df_tab["total"].apply(fmt)
    df_tab["Δ mês ant."] = df_tab["Δ mês ant."].apply(
        lambda x: f"+{x:.1f}%" if pd.notna(x) and x >= 0 else (f"{x:.1f}%" if pd.notna(x) else "—")
    )
    cols_show = ["Período", "Rendimento", "Δ mês ant."]
    if len(unidades_sel) > 1:
        for u in unidades_sel:
            df_tab[u + " (k)"] = df_tab[u].apply(lambda v: f"{v/1000:.1f}k")
            cols_show.append(u + " (k)")
    st.dataframe(df_tab[cols_show].iloc[::-1].reset_index(drop=True),
                 use_container_width=True, hide_index=True)

# ── Rodapé ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("Para adicionar novos meses: execute `atualizar_dados.py` na pasta dos arquivos xlsx e faça push para o GitHub.")
