import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import random
import json
import os

# --- CONFIGURATION GLOBALE (Doit être au tout début) ---
st.set_page_config(layout="wide", page_title="Tracker de Pays Visités")

# ==========================================
# 0. GESTION DE L'ÉTAT (INTRO vs APP)
# ==========================================
if 'app_started' not in st.session_state:
    st.session_state['app_started'] = False

def start_app():
    """Fonction appelée lors du clic sur le coeur"""
    st.session_state['app_started'] = True

# ==========================================
# 1. ÉCRAN D'INTRODUCTION (Le Coeur Battant)
# ==========================================
def show_splash_screen():
    st.markdown("""
        <style>
        /* Fond noir complet et on cache la barre du haut */
        .stApp {
            background-color: black !important;
        }
        header {visibility: hidden;}

        /* On centre le conteneur du bouton Streamlit */
        div[data-testid="stButton"] {
            display: flex;
            justify-content: center;
            margin-top: 15vh;
            position : relative;
            left : -50px
        }

        /* On centre le contenu à l'intérieur du bouton lui-même */
        div[data-testid="stButton"] button {
             border: none !important;
             background-color: transparent !important;
             box-shadow: none !important;
             display: flex;
             justify-content: center;
             align-items: center;
        }
        
        /* Retrait de l'effet de survol gris par défaut de Streamlit */
        div[data-testid="stButton"] button:hover, 
        div[data-testid="stButton"] button:focus,
        div[data-testid="stButton"] button:active {
             background-color: transparent !important;
             border: none !important;
             color: inherit !important;
             transform: none !important; 
        }
        
        /* On cible l'emoji coeur à l'intérieur du bouton */
        div[data-testid="stButton"] button p {
            font-size: 250px !important;
            animation: heartbeat 1.5s infinite ease-in-out;
            margin: 0;
            padding: 0;
            line-height: 1;
        }

        /* L'animation de battement */
        @keyframes heartbeat {
            0% { transform: scale(1); }
            15% { transform: scale(1.15); filter: drop-shadow(0 0 30px red); }
            30% { transform: scale(1); }
            45% { transform: scale(1.1); }
            60% { transform: scale(1); }
        }
        
        /* Le texte en dessous */
        .enter-text {
            color: white;
            text-align: center;
            font-family: 'Arial', sans-serif;
            font-size:40px;
            margin-top: 20px;
            font-weight: lighter;
            letter-spacing: 4px;
            opacity: 0.8;
            animation: pulse-text 2s infinite; /* Petit effet clignotant ajouté */
        }

        @keyframes pulse-text {
            0% { opacity: 0.6; }
            50% { opacity: 1; }
            100% { opacity: 0.6; }
        }
        </style>
        """, unsafe_allow_html=True)

    # On utilise 3 colonnes de taille égale pour forcer le contenu parfaitement au centre
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col2:
        st.button("❤️", on_click=start_app, key="heart_btn")
        st.markdown('<p class="enter-text">IL FAUT CLIQUER SUR MON COEUR ici </p>', unsafe_allow_html=True)

# ==========================================
# 2. VOTRE APPLICATION PRINCIPALE
# ==========================================
def main_app_logic():
    # --- FONCTIONS DE CHARGEMENT ---
    @st.cache_data
    def load_geodata():
        url = "https://raw.githubusercontent.com/python-visualization/folium/main/examples/data/world-countries.json"
        try:
            world = gpd.read_file(url)
            return world
        except Exception as e:
            st.error(f"Erreur GeoJSON : {e}")
            return gpd.GeoDataFrame()

    world_data = load_geodata()
    if world_data.empty: st.stop()

    JSON_FILE = "pays_status.json"

    def load_user_data(all_countries):
        if os.path.exists(JSON_FILE):
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            default_data = {country: "not visited" for country in all_countries}
            with open(JSON_FILE, "w", encoding="utf-8") as f:
                json.dump(default_data, f)
            return default_data

    def save_user_data(data):
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    # Initialisation des données
    liste_pays_entree = world_data['name'].unique().tolist()
    liste_pays_entree.sort()
    pays_status = load_user_data(liste_pays_entree)

    # --- INTERFACE ---
    if st.sidebar.button("🔙 Revenir à l'accueil"):
        st.session_state['app_started'] = False
        st.rerun()

    st.title("🌍 Carte du Monde - Suivi des visites")

    if 'selected_country' not in st.session_state:
        st.session_state['selected_country'] = None

    col1, col2 = st.columns([1, 4])

    with col1:
        st.markdown("### 🎮 Contrôles")
        if st.button("🎲 Tirer un pays au sort", use_container_width=True):
            st.session_state['selected_country'] = random.choice(liste_pays_entree)

        if st.session_state['selected_country']:
            current_country = st.session_state['selected_country']
            current_status = pays_status.get(current_country, "not visited")
            
            st.divider()
            st.markdown(f"### 📍 {current_country}")
            
            if current_status == "visited":
                st.success("Statut : ✅ VISITED")
            else:
                st.warning("Statut : ❌ NOT VISITED")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("Marquer Vu", key="btn_vu"):
                    pays_status[current_country] = "visited"
                    save_user_data(pays_status)
                    st.rerun()
            with c2:
                if st.button("Marquer Pas Vu", key="btn_pasvu"):
                    pays_status[current_country] = "not visited"
                    save_user_data(pays_status)
                    st.rerun()

        nb_visited = list(pays_status.values()).count("visited")
        st.markdown(f"**Progression :** {nb_visited} / {len(liste_pays_entree)} pays.")

    with col2:
        m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB positron")

        def function_couleur_pays(feature):
            nom_pays = feature['properties']['name']
            statut = pays_status.get(nom_pays, "not visited")
            
            if statut == "visited":
                return {'fillColor': '#2ecc71', 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}
            else:
                return {'fillColor': 'transparent', 'color': '#cccccc', 'weight': 1, 'fillOpacity': 0.0}

        folium.GeoJson(
            world_data,
            style_function=function_couleur_pays,
            tooltip=folium.GeoJsonTooltip(fields=['name'], aliases=['Pays:'])
        ).add_to(m)

        if st.session_state['selected_country']:
            country_name = st.session_state['selected_country']
            pays_geo = world_data[world_data.name == country_name]
            
            if not pays_geo.empty:
                folium.GeoJson(
                    pays_geo,
                    style_function=lambda x: {'fillColor': 'transparent', 'color': '#FF0000', 'weight': 3, 'fillOpacity': 0}
                ).add_to(m)
                minx, miny, maxx, maxy = pays_geo.total_bounds
                m.fit_bounds([[miny, minx], [maxy, maxx]], padding=(30, 30))

        st_folium(m, width="100%", height=700)

# ==========================================
# 3. LOGIQUE PRINCIPALE (Le chef d'orchestre)
# ==========================================
if not st.session_state['app_started']:
    show_splash_screen()
else:
    main_app_logic()