import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# ─── CONFIG ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard IESS · Establecimientos de Salud",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── ESTILO CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .kpi-card {
        background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
        border-radius: 12px; padding: 20px 24px; color: white;
        box-shadow: 0 4px 15px rgba(37,99,235,0.3);
    }
    .kpi-card .value { font-size: 2rem; font-weight: 700; line-height: 1.1; }
    .kpi-card .label { font-size: 0.78rem; opacity: 0.85; margin-top: 4px; letter-spacing: 0.5px; text-transform: uppercase; }
    .kpi-card .delta { font-size: 0.85rem; margin-top: 8px; }
    .section-title { font-size: 1.1rem; font-weight: 600; color: #1e3a5f;
                     border-left: 4px solid #2563eb; padding-left: 10px; margin: 1.5rem 0 0.8rem; }
    div[data-testid="stMetricValue"] { font-size: 1.6rem !important; }
    .stSelectbox label, .stMultiSelect label { font-weight: 600; color: #374151; }
</style>
""", unsafe_allow_html=True)

# ─── CARGA DE DATOS ───────────────────────────────────────────────────────────
@st.cache_data
def cargar_datos():
    df = pd.read_csv("BASE.csv", sep=";", encoding="utf-8", on_bad_lines="skip")
    df.columns = df.columns.str.strip()

    # Limpiar y convertir métricas numéricas
    num_cols = [
        "ATENCIONES_CONSULTA_EXTERNA", "ATENCIONES_EMERGENCIA",
        "EGRESOS_HOSPITALARIO", "ATENCIONES_DE_AMBULANCIA", "CIRUGIAS",
        "CAMAS_CENSABLES_DOTACION",
        "NUMERO_DE_PROFESIONALES_ACTUALES_OPERATIVO",
        "NUMERO_DE_PROFESIONALES_ACTUALES_ADMINISTRATIVO",
        "NUMERO_DE_PROFESIONALES_ACTUALES_ESPECIALIDAD",
    ]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Porcentajes: quitar % y coma → punto
    pct_cols = [c for c in df.columns if "%" in c or "INDICE" in c or "ABASTECIMIENTO" in c]
    for col in pct_cols:
        if df[col].dtype == object:
            df[col] = (
                df[col].astype(str)
                .str.replace("%", "", regex=False)
                .str.replace(",", ".", regex=False)
                .str.strip()
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Orden de meses
    orden_meses = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
                   "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
    df["MES"] = pd.Categorical(df["MES"], categories=orden_meses, ordered=True)

    # Coordenadas
    for coord in ["COORDENADAS_X", "COORDENADAS_Y"]:
        if coord in df.columns:
            df[coord] = df[coord].astype(str).str.replace(",", ".").str.strip()
            df[coord] = pd.to_numeric(df[coord], errors="coerce")

    return df

df_raw = cargar_datos()

# ─── SIDEBAR FILTROS ──────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/f/f7/IESS_logo.svg/320px-IESS_logo.svg.png", width=160)
    st.markdown("## 🔍 Filtros")

    años = sorted(df_raw["AÑO"].dropna().unique())
    año_sel = st.multiselect("Año", años, default=años)

    meses_disp = list(df_raw["MES"].cat.categories)
    mes_sel = st.multiselect("Mes", meses_disp, default=meses_disp)

    provincias = sorted(df_raw["PROVINCIA"].dropna().unique())
    prov_sel = st.multiselect("Provincia", provincias, default=provincias)

    niveles = sorted(df_raw["NIVEL_DE_ATENCION"].dropna().unique())
    nivel_sel = st.multiselect("Nivel de atención", niveles, default=niveles)

    st.markdown("---")
    st.caption("📊 Fuente: MSP · IESS · 2024-2025")

# ─── FILTRADO ─────────────────────────────────────────────────────────────────
df = df_raw[
    df_raw["AÑO"].isin(año_sel) &
    df_raw["MES"].isin(mes_sel) &
    df_raw["PROVINCIA"].isin(prov_sel) &
    df_raw["NIVEL_DE_ATENCION"].isin(nivel_sel)
].copy()

if df.empty:
    st.warning("No hay datos con los filtros seleccionados.")
    st.stop()

# ─── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("# 🏥 Dashboard · Establecimientos de Salud IESS")
st.markdown(f"**{len(df):,} registros** · {df['NOMBRE_OFICIAL'].nunique()} establecimientos · "
            f"{df['PROVINCIA'].nunique()} provincias")
st.markdown("---")

# ─── KPIs ─────────────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)

total_consultas   = int(df["ATENCIONES_CONSULTA_EXTERNA"].sum())
total_emergencias = int(df["ATENCIONES_EMERGENCIA"].sum())
total_cirugias    = int(df["CIRUGIAS"].sum())
total_egresos     = int(df["EGRESOS_HOSPITALARIO"].sum())
total_profesional = int(df["NUMERO_DE_PROFESIONALES_ACTUALES_OPERATIVO"].sum())

with col1:
    st.metric("🩺 Consultas Externas", f"{total_consultas:,}")
with col2:
    st.metric("🚨 Atenciones Emergencia", f"{total_emergencias:,}")
with col3:
    st.metric("🔪 Cirugías", f"{total_cirugias:,}")
with col4:
    st.metric("🛏 Egresos Hospitalarios", f"{total_egresos:,}")
with col5:
    st.metric("👨‍⚕️ Profesionales Operativos", f"{total_profesional:,}")

st.markdown("---")

# ─── FILA 1: Atenciones por provincia | Tendencia mensual ─────────────────────
st.markdown('<p class="section-title">📍 Atenciones por Provincia</p>', unsafe_allow_html=True)

col_left, col_right = st.columns([1.2, 1])

with col_left:
    prov_agg = (
        df.groupby("PROVINCIA")[["ATENCIONES_CONSULTA_EXTERNA", "ATENCIONES_EMERGENCIA"]]
        .sum().reset_index()
        .sort_values("ATENCIONES_CONSULTA_EXTERNA", ascending=True)
        .tail(15)
    )
    fig_prov = go.Figure()
    fig_prov.add_bar(
        y=prov_agg["PROVINCIA"], x=prov_agg["ATENCIONES_CONSULTA_EXTERNA"],
        name="Consulta Externa", orientation="h",
        marker_color="#2563eb"
    )
    fig_prov.add_bar(
        y=prov_agg["PROVINCIA"], x=prov_agg["ATENCIONES_EMERGENCIA"],
        name="Emergencia", orientation="h",
        marker_color="#f97316"
    )
    fig_prov.update_layout(
        barmode="stack", height=420, margin=dict(l=0,r=10,t=10,b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        xaxis_title="Atenciones", yaxis_title="",
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
    )
    st.plotly_chart(fig_prov, use_container_width=True)

with col_right:
    st.markdown('<p class="section-title">📅 Tendencia Mensual</p>', unsafe_allow_html=True)
    mes_agg = (
        df.groupby("MES")[["ATENCIONES_CONSULTA_EXTERNA", "ATENCIONES_EMERGENCIA", "CIRUGIAS"]]
        .sum().reset_index()
    )
    fig_mes = go.Figure()
    fig_mes.add_scatter(x=mes_agg["MES"].astype(str), y=mes_agg["ATENCIONES_CONSULTA_EXTERNA"],
                        name="Consulta", mode="lines+markers", line=dict(color="#2563eb", width=2.5))
    fig_mes.add_scatter(x=mes_agg["MES"].astype(str), y=mes_agg["ATENCIONES_EMERGENCIA"],
                        name="Emergencia", mode="lines+markers", line=dict(color="#f97316", width=2.5))
    fig_mes.add_scatter(x=mes_agg["MES"].astype(str), y=mes_agg["CIRUGIAS"],
                        name="Cirugías", mode="lines+markers", line=dict(color="#10b981", width=2.5),
                        yaxis="y2")
    fig_mes.update_layout(
        height=390, margin=dict(l=0,r=30,t=10,b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        plot_bgcolor="white", paper_bgcolor="white",
        yaxis=dict(showgrid=True, gridcolor="#f1f5f9", title="Atenciones"),
        yaxis2=dict(overlaying="y", side="right", title="Cirugías", showgrid=False),
        xaxis=dict(tickangle=-45),
    )
    st.plotly_chart(fig_mes, use_container_width=True)

# ─── FILA 2: Distribución por nivel | Cirugías top 10 establecimientos ─────────
st.markdown('<p class="section-title">🏗 Distribución por Nivel de Atención</p>', unsafe_allow_html=True)

col_a, col_b, col_c = st.columns([1, 1, 1])

with col_a:
    nivel_agg = df.groupby("NIVEL_DE_ATENCION")["ATENCIONES_CONSULTA_EXTERNA"].sum().reset_index()
    fig_pie = px.pie(nivel_agg, names="NIVEL_DE_ATENCION", values="ATENCIONES_CONSULTA_EXTERNA",
                     color_discrete_sequence=["#2563eb","#f97316","#10b981"],
                     hole=0.45)
    fig_pie.update_layout(height=300, margin=dict(l=10,r=10,t=30,b=10),
                          legend=dict(orientation="h", y=-0.15))
    fig_pie.update_traces(textposition="outside", textinfo="percent+label")
    st.plotly_chart(fig_pie, use_container_width=True)

with col_b:
    top_est = (
        df.groupby("NOMBRE_OFICIAL")["CIRUGIAS"].sum().reset_index()
        .sort_values("CIRUGIAS", ascending=False).head(10)
    )
    top_est["NOMBRE_CORTO"] = top_est["NOMBRE_OFICIAL"].str[:35] + "…"
    fig_top = px.bar(top_est, x="CIRUGIAS", y="NOMBRE_CORTO", orientation="h",
                     color="CIRUGIAS", color_continuous_scale="Blues",
                     labels={"CIRUGIAS":"Cirugías","NOMBRE_CORTO":""})
    fig_top.update_layout(height=300, margin=dict(l=0,r=10,t=10,b=10),
                          coloraxis_showscale=False, plot_bgcolor="white")
    fig_top.update_yaxes(autorange="reversed")
    st.markdown("**Top 10 establecimientos por cirugías**")
    st.plotly_chart(fig_top, use_container_width=True)

with col_c:
    prof_agg = df.groupby("NIVEL_DE_ATENCION")[
        ["NUMERO_DE_PROFESIONALES_ACTUALES_OPERATIVO",
         "NUMERO_DE_PROFESIONALES_ACTUALES_ADMINISTRATIVO",
         "NUMERO_DE_PROFESIONALES_ACTUALES_ESPECIALIDAD"]
    ].sum().reset_index()
    prof_melt = prof_agg.melt(id_vars="NIVEL_DE_ATENCION", var_name="Tipo", value_name="N")
    prof_melt["Tipo"] = prof_melt["Tipo"].str.replace("NUMERO_DE_PROFESIONALES_ACTUALES_","")
    fig_prof = px.bar(prof_melt, x="NIVEL_DE_ATENCION", y="N", color="Tipo",
                      color_discrete_sequence=["#2563eb","#f97316","#10b981"],
                      barmode="group", labels={"N":"Profesionales","NIVEL_DE_ATENCION":""})
    fig_prof.update_layout(height=300, margin=dict(l=0,r=10,t=10,b=10),
                           legend=dict(orientation="h", y=1.15, font=dict(size=10)),
                           plot_bgcolor="white")
    st.markdown("**Profesionales por nivel de atención**")
    st.plotly_chart(fig_prof, use_container_width=True)

# ─── FILA 3: Mapa + Abastecimiento ─────────────────────────────────────────────
st.markdown('<p class="section-title">🗺 Mapa de Establecimientos</p>', unsafe_allow_html=True)

col_map, col_abas = st.columns([1.5, 1])

with col_map:
    df_geo = df.dropna(subset=["COORDENADAS_X","COORDENADAS_Y"]).copy()
    df_geo = df_geo[(df_geo["COORDENADAS_X"] < 0) & (df_geo["COORDENADAS_Y"].between(-6, 2))]
    df_geo_agg = (
        df_geo.groupby(["NOMBRE_OFICIAL","COORDENADAS_Y","COORDENADAS_X","NIVEL_DE_ATENCION"])
        ["ATENCIONES_CONSULTA_EXTERNA"].sum().reset_index()
    )
    color_map = {"I NIVEL":"#10b981","II NIVEL":"#f97316","III NIVEL":"#ef4444"}
    fig_map = px.scatter_mapbox(
        df_geo_agg,
        lat="COORDENADAS_Y", lon="COORDENADAS_X",
        color="NIVEL_DE_ATENCION",
        size="ATENCIONES_CONSULTA_EXTERNA",
        size_max=20,
        hover_name="NOMBRE_OFICIAL",
        hover_data={"ATENCIONES_CONSULTA_EXTERNA":":,.0f"},
        color_discrete_map=color_map,
        mapbox_style="carto-positron",
        zoom=5.5, center={"lat": -1.5, "lon": -78.5},
        height=380,
    )
    fig_map.update_layout(margin=dict(l=0,r=0,t=0,b=0),
                          legend=dict(orientation="h", y=1.0))
    st.plotly_chart(fig_map, use_container_width=True)

with col_abas:
    st.markdown("**Índice de Abastecimiento de Medicamentos (%)**")
    abas_cols = {
        "General Medicamentos":   "% _ABASTECIMIENTO >1MES_GENERAL_MEDIC",
        "Esenciales":             "%_ABASTECIMIENTO >1MES_ESENCIALES_MEDIC",
        "Vitales":                "%_ABASTECIMIENTO >1MES_VITALES_MEDIC",
        "Dispositivos Médicos":   "%_ABASTECIMIENTO >1MES_GENERAL_(DISPOSITIVOS_MEDICOS)",
    }
    abas_prov = df.groupby("PROVINCIA")[list(abas_cols.values())].mean().reset_index()
    abas_prov = abas_prov.sort_values(abas_cols["General Medicamentos"], ascending=False).head(12)

    fig_abas = go.Figure()
    colors = ["#2563eb","#10b981","#f97316","#8b5cf6"]
    for (label, col), clr in zip(abas_cols.items(), colors):
        if col in abas_prov.columns:
            fig_abas.add_bar(x=abas_prov["PROVINCIA"], y=abas_prov[col],
                             name=label, marker_color=clr)
    fig_abas.update_layout(
        barmode="group", height=380, margin=dict(l=0,r=10,t=10,b=60),
        plot_bgcolor="white", paper_bgcolor="white",
        yaxis=dict(showgrid=True, gridcolor="#f1f5f9", title="%"),
        xaxis=dict(tickangle=-45),
        legend=dict(orientation="h", y=1.05, font=dict(size=10)),
    )
    st.plotly_chart(fig_abas, use_container_width=True)

# ─── FILA 4: Satisfacción + Ausentismo ─────────────────────────────────────────
st.markdown('<p class="section-title">📈 Indicadores de Calidad</p>', unsafe_allow_html=True)

col_s1, col_s2 = st.columns(2)

with col_s1:
    sat_col = "%_INDICE_DE_SATISFACCION_DEL_PACIENTE"
    if sat_col in df.columns:
        sat_prov = df.groupby("PROVINCIA")[sat_col].mean().reset_index().sort_values(sat_col, ascending=False)
        fig_sat = px.bar(sat_prov, x="PROVINCIA", y=sat_col,
                         color=sat_col, color_continuous_scale="RdYlGn",
                         labels={sat_col:"Satisfacción (%)","PROVINCIA":""},
                         title="Índice de Satisfacción del Paciente por Provincia")
        fig_sat.update_layout(height=320, margin=dict(l=0,r=10,t=40,b=60),
                              plot_bgcolor="white", coloraxis_showscale=False,
                              xaxis=dict(tickangle=-45))
        st.plotly_chart(fig_sat, use_container_width=True)

with col_s2:
    aus_col = "INDICE_DE_AUSENTISMO_PACIENTE"
    if aus_col in df.columns:
        aus_mes = df.groupby("MES")[aus_col].mean().reset_index()
        fig_aus = px.area(aus_mes, x="MES", y=aus_col,
                          color_discrete_sequence=["#ef4444"],
                          labels={aus_col:"Ausentismo (%)","MES":""},
                          title="Índice de Ausentismo Mensual Promedio")
        fig_aus.update_layout(height=320, margin=dict(l=0,r=10,t=40,b=10),
                              plot_bgcolor="white", paper_bgcolor="white",
                              xaxis=dict(tickangle=-45))
        st.plotly_chart(fig_aus, use_container_width=True)

# ─── TABLA DETALLE ─────────────────────────────────────────────────────────────
with st.expander("📋 Ver tabla de datos filtrados"):
    cols_tabla = [
        "AÑO","MES","NOMBRE_OFICIAL","PROVINCIA","CANTON","NIVEL_DE_ATENCION",
        "ATENCIONES_CONSULTA_EXTERNA","ATENCIONES_EMERGENCIA","EGRESOS_HOSPITALARIO",
        "CIRUGIAS","NUMERO_DE_PROFESIONALES_ACTUALES_OPERATIVO",
        "%_INDICE_DE_SATISFACCION_DEL_PACIENTE"
    ]
    cols_tabla = [c for c in cols_tabla if c in df.columns]
    st.dataframe(
        df[cols_tabla].sort_values(["AÑO","MES"]).reset_index(drop=True),
        use_container_width=True, height=320
    )
    csv_out = df[cols_tabla].to_csv(index=False, sep=";").encode("utf-8")
    st.download_button("⬇ Descargar datos filtrados (.csv)", csv_out,
                       "datos_filtrados.csv", "text/csv")

st.caption("Dashboard · Establecimientos de Salud IESS Ecuador · 2024-2025")
