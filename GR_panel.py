
!pip install yaml

import streamlit as st
import yaml
import os
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="CMS Data Explorer", layout="wide")

def categorizar_edad(valor):
    #"Asigna el tramo de edad o 'Sin especificar' si es nulo."
    if valor is None or pd.isna(valor): 
        return "Sin especificar"
    if valor <= 2: return "0-2"
    elif valor <= 6: return "2-6"
    elif valor <= 12: return "6-12"
    elif valor <= 18: return "12-18"
    else: return "18+"

@st.cache_data
def cargar_datos(directorio):
    lista_datos = []
    if not os.path.exists(directorio):
        return pd.DataFrame()
    
    for filename in os.listdir(directorio):
        if filename.endswith((".yaml", ".yml")):
            path = os.path.join(directorio, filename)
            with open(path, 'r', encoding='utf-8') as file:
                try:
                    c = yaml.safe_load(file)
                    # Manejo de nulos para Gravedad
                    grav = c.get("gravedad", {}).get("valor")
                    grav = grav.lower() if isinstance(grav, str) else "Sin especificar"
                    
                    # Manejo de nulos para Tratamiento
                    trat = c.get("efectividad_tratamiento", {}).get("existencia")
                    if trat is None:
                        trat_label = "Sin especificar"
                    else:
                        trat_label = "Sí" if trat else "No"

                    registro = {
                        "NBK": c.get("NBK"),
                        "Enfermedad": c.get("ENFERMEDAD"),
                        "HGNC": c.get("HGNC"),
                        "Tramo_Edad": categorizar_edad(c.get("edad", {}).get("valor_raso")),
                        "Gravedad": grav,
                        "Tratamiento": trat_label,
                        "Path": path 
                    }
                    lista_datos.append(registro)
                except Exception as e:
                    st.error(f"Error en {filename}: {e}")
    
    return pd.DataFrame(lista_datos)

# --- Interfaz ---

st.title("🧬 Visualizador CMS con Soporte para Datos Nulos")

df = cargar_datos("YAML_data")

if df.empty:
    st.info("Por favor, asegúrate de que la carpeta 'YAML_data' contenga archivos YAML válidos.")
else:
    # --- Sidebar - Filtros ---
    st.sidebar.header("Filtros de Búsqueda")

    # Filtro Edad (Incluye 'Sin especificar')
    tramos_edad = ["0-2", "2-6", "6-12", "12-18", "18+", "Sin especificar"]
    sel_edad = st.sidebar.multiselect("Edad:", tramos_edad, default=tramos_edad)

    # Filtro Tratamiento (Incluye 'Sin especificar')
    opciones_trat = ["Sí", "No", "Sin especificar"]
    sel_trat = st.sidebar.multiselect("¿Tiene Tratamiento?", opciones_trat, default=opciones_trat)

    # Filtro Gravedad (Incluye 'Sin especificar')
    opciones_grav = ["grave", "moderado", "leve", "Sin especificar"]
    sel_grav = st.sidebar.multiselect("Gravedad:", opciones_grav, default=opciones_grav)

    # Lógica de filtrado
    mask = (
        df['Tramo_Edad'].isin(sel_edad) &
        df['Tratamiento'].isin(sel_trat) &
        df['Gravedad'].isin(sel_grav)
    )
    df_filtrado = df[mask]

    # --- Visualización ---
    m1, m2 = st.columns(2)
    m1.metric("Registros mostrados", len(df_filtrado))
    m2.metric("Campos con nulos detectados", len(df[df.isin(["Sin especificar"]).any(axis=1)]))

    st.dataframe(df_filtrado.drop(columns=["Path"]), use_container_width=True, hide_index=True)

    # Detalle expandible
    if not df_filtrado.empty:
        with st.expander("🔍 Ver código fuente del archivo"):




            # Crear opciones únicas con formato "NBK - HGNC"
            df_unicos = (
                df_filtrado[["NBK", "HGNC", "Path"]]
                .drop_duplicates(subset=["NBK", "HGNC"])
                .copy()
            )

            df_unicos["NBK_HGNC"] = (
                df_unicos["NBK"].astype(str) + " - " + df_unicos["HGNC"].astype(str)
            )

            # Selectbox mostrando "NBK - HGNC"
            sel_nbk_hgnc = st.selectbox(
                "Selecciona un NBK:",
                df_unicos["NBK_HGNC"]
            )

            # Obtener path correspondiente
            path_final = df_unicos[
                df_unicos["NBK_HGNC"] == sel_nbk_hgnc
            ]["Path"].values[0]





            with open(path_final, 'r', encoding='utf-8') as f:
                st.code(f.read(), language='yaml')



