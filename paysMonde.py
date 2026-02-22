import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import random
import json
import os

# Configuration de la page
st.set_page_config(layout="wide", page_title="Tracker de Pays Visités")

# --- 1. GESTION DES DONNÉES GÉOGRAPHIQUES ---
@st.cache_data
def load_geodata():
    url = "https://raw.githubusercontent.com/python-visualization/folium/main/examples/data/world-countries.json"
    try:
        world = gpd.read_file(url)
        return world
    except Exception as e:
        st.error(f"Erreur de chargement GeoJSON : {e}")
        return gpd.GeoDataFrame()

world_data = load_geodata()

if world_data.empty:
    st.stop()

# --- 2. GESTION DU JSON (VISITED / NOT VISITED) ---
JSON_FILE = "pays_status.json"

def load_user_data(all_countries):
    """Charge le JSON ou le crée s'il n'existe pas"""
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        # Initialisation par défaut : tout le monde à "not visited"
        default_data = {country: "not visited" for country in all_countries}
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(default_data, f)
        return default_data

def save_user_data(data):
    """Sauvegarde l'état dans le fichier JSON"""
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# Liste de référence des pays
liste_pays_entree = world_data['name'].unique().tolist()
liste_pays_entree.sort()

# Chargement des statuts (Visited / Not Visited)
pays_status = load_user_data(liste_pays_entree)

# --- 3. INTERFACE UTILISATEUR ---
st.title("🌍 Carte du Monde - Suivi des visites")

# Initialisation de l'état de session pour le pays sélectionné
if 'selected_country' not in st.session_state:
    st.session_state['selected_country'] = None

col1, col2 = st.columns([1, 4])

with col1:
    st.markdown("### 🎮 Contrôles")
    
    # Bouton aléatoire
    if st.button("🎲 Tirer un pays au sort", use_container_width=True):
        st.session_state['selected_country'] = random.choice(liste_pays_entree)

    # Zone d'interaction pour le pays sélectionné
    if st.session_state['selected_country']:
        current_country = st.session_state['selected_country']
        current_status = pays_status.get(current_country, "not visited")
        
        st.divider()
        st.markdown(f"### 📍 {current_country}")
        
        # Affichage de l'état actuel avec couleur
        if current_status == "visited":
            st.success("Statut : ✅ VISITED")
        else:
            st.warning("Statut : ❌ NOT VISITED")

        # Boutons pour changer le statut
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Marquer Vu", key="btn_vu"):
                pays_status[current_country] = "visited"
                save_user_data(pays_status)
                st.rerun() # Recharge la page pour mettre à jour la carte
        with c2:
            if st.button("Marquer Pas Vu", key="btn_pasvu"):
                pays_status[current_country] = "not visited"
                save_user_data(pays_status)
                st.rerun()

    # Petites stats
    nb_visited = list(pays_status.values()).count("visited")
    st.markdown(f"**Progression :** {nb_visited} / {len(liste_pays_entree)} pays.")

# --- 4. AFFICHAGE DE LA CARTE ---
with col2:
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB positron")

    # --- A. FONCTION DE STYLE (LA PARTIE IMPORTANTE) ---
    def function_couleur_pays(feature):
        nom_pays = feature['properties']['name']
        statut = pays_status.get(nom_pays, "not visited")
        
        if statut == "visited":
            return {
                'fillColor': '#2ecc71', # VERT
                'color': 'black',
                'weight': 1,
                'fillOpacity': 0.7
            }
        else:
            return {
                'fillColor': 'transparent', # RIEN CHANGÉ (Transparent)
                'color': '#cccccc',         # Gris très clair pour les frontières
                'weight': 1,
                'fillOpacity': 0.0
            }

    # --- B. AJOUT DE TOUS LES PAYS AVEC LE STYLE ---
    folium.GeoJson(
        world_data,
        style_function=function_couleur_pays,
        tooltip=folium.GeoJsonTooltip(fields=['name'], aliases=['Pays:'])
    ).add_to(m)

    # --- C. ZOOM SUR LE PAYS SÉLECTIONNÉ (Optionnel : Contour Rouge) ---
    if st.session_state['selected_country']:
        country_name = st.session_state['selected_country']
        pays_geo = world_data[world_data.name == country_name]
        
        if not pays_geo.empty:
            # On ajoute juste un contour rouge épais pour montrer lequel est sélectionné
            # sans remplir, pour ne pas cacher la couleur verte si visité
            folium.GeoJson(
                pays_geo,
                style_function=lambda x: {
                    'fillColor': 'transparent',
                    'color': '#FF0000', # ROUGE (Sélection active)
                    'weight': 3,
                    'fillOpacity': 0
                }
            ).add_to(m)

            # Zoom
            minx, miny, maxx, maxy = pays_geo.total_bounds
            m.fit_bounds([[miny, minx], [maxy, maxx]], padding=(30, 30))

    st_folium(m, width="100%", height=700)