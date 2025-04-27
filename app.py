import streamlit as st
import pandas as pd
import glob
import plotly.express as px
from streamlit_option_menu import option_menu
import base64
import requests

# === CONFIGURATION ===
st.set_page_config(page_title="City Fighting", layout="wide")
API_KEY = "a09666d1f639071454ec03d597754735"

# === FONCTIONS DE CHARGEMENT AVEC CACHE ===

@st.cache_data
def load_sante():
    return pd.read_parquet('base_sante.parquet')

@st.cache_data
def load_diplomes():
    return pd.read_parquet('base_diplomes.parquet')

@st.cache_data
def load_crimes():
    return pd.read_parquet('base_delits.parquet')

@st.cache_data
def load_base_complete():
    list_df = [pd.read_parquet(f"base_complete_part_{i}.parquet") for i in range(10)]
    df_base = pd.concat(list_df, ignore_index=True)
    df_base = df_base[df_base["PMUN21"] > 20000]
    df_base['LIBGEO'] = df_base['LIBGEO'].astype(str)
    return df_base

# === CHARGEMENT DES DONNÉES avec Spinner pour joli affichage ===
with st.spinner('📦 Chargement des bases de données...'):
    df_sante = load_sante()
    df_diplomes = load_diplomes()
    df_crimes = load_crimes()
    df_base = load_base_complete()


# === BACKGROUNDS PAR ONGLET ===
backgrounds = {
    "Données générales": "Image/general.jpg",
    "Logement": "Image/logements.jpg",
    "Emploi": "Image/emploi.jpg",
    "Santé": "Image/santé.jpg",
    "Sécurité": "Image/sécurité.jpg",
    "Formation": "Image/formation.jpg"
}

def set_background(image_path):
    with open(image_path, "rb") as img_file:
        b64_img = base64.b64encode(img_file.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{b64_img}");
            background-size: cover;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# === MENU D'ONGLETS ===
selected = option_menu(
    menu_title=None,
    options=["Données générales", "Logement", "Emploi", "Santé", "Sécurité", "Formation"],
    icons=["house", "building", "briefcase", "heart", "shield", "book"],
    orientation="horizontal"
)

set_background(backgrounds.get(selected, "Image/general.jpg"))

# === SÉLECTEURS DE VILLES AU CENTRE ===
st.markdown("""
    <style>
        .centered-select {
            display: flex;
            justify-content: center;
            gap: 50px;
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='centered-select'>", unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    ville1 = st.selectbox("Ville 1", sorted(df_base['LIBGEO'].unique()), key="v1")
with col2:
    ville2 = st.selectbox("Ville 2", sorted(df_base['LIBGEO'].unique()), index=1, key="v2")
st.markdown("</div>", unsafe_allow_html=True)

# === MÉTÉO ===
from datetime import datetime
def get_weather_forecast(ville, api_key, n=5):
    try:
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={ville},FR&appid={api_key}&units=metric&lang=fr"
        response = requests.get(url)
        data = response.json()
        
        if data.get("cod") != "200":
            # API retourne une erreur ➔ on retourne 2 listes vides
            return [], []

        matin, soir = [], []

        for item in data["list"]:
            if "09:00:00" in item["dt_txt"]:
                date = datetime.strptime(item["dt_txt"], "%Y-%m-%d %H:%M:%S").strftime("%A %d %B")
                temp = item["main"]["temp"]
                desc = item["weather"][0]["description"].capitalize()
                icon = item["weather"][0]["icon"]
                icon_url = f"https://openweathermap.org/img/wn/{icon}@2x.png"
                matin.append((date, temp, desc, icon_url))

            elif "18:00:00" in item["dt_txt"]:
                date = datetime.strptime(item["dt_txt"], "%Y-%m-%d %H:%M:%S").strftime("%A %d %B")
                temp = item["main"]["temp"]
                desc = item["weather"][0]["description"].capitalize()
                icon = item["weather"][0]["icon"]
                icon_url = f"https://openweathermap.org/img/wn/{icon}@2x.png"
                soir.append((date, temp, desc, icon_url))

        return matin[:n], soir[:n]
    
    except Exception as e:
        # En cas d'erreur réseau ou autre ➔ on retourne 2 listes vides
        return [], []

def show_logement(data, col):
    # Titre
    col.markdown("### 🏠 Logement")

    # Affichage des données de base
    col.markdown(f"""
    <div style="background-color: rgba(255, 255, 255, 0.8); padding: 15px; border-radius: 15px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px;">
        <h4><strong>🏠 Résidences principales :</strong> {int(data['P21_RP'])}</h4>
        <p><strong>🏚️ Logements vacants :</strong> {int(data['P21_LOGVAC'])}</p>
        <p><strong>🏡 Propriétaires :</strong> {int(data['P21_RP_PROP'])} | <strong>Locataires :</strong> {int(data['P21_RP_LOC'])}</p>
    </div>
    """, unsafe_allow_html=True)

    # Calcul du taux de vacance des logements
    taux_vacance = (int(data['P21_LOGVAC']) / int(data['P21_RP'])) * 100 if data['P21_RP'] else 0

    # Stylisation avec CSS et affichage du taux de vacance
    col.markdown(f"""
        <div style="
            background-color: rgba(255, 255, 255, 0.8);
            padding: 20px;
            border-radius: 15px;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
            font-size: 18px;
            text-align: center;
        ">
            <strong>Taux de logements vacants : </strong>
            <span style="color: { 'red' if taux_vacance > 10 else 'green'}; font-size: 24px; font-weight: bold;">
                {round(taux_vacance, 2)}%
            </span>
        </div>
    """, unsafe_allow_html=True)

    # Graphique de la répartition des logements : Propriétaires vs Locataires
    logement_data = {
        "Propriétaires": int(data['P21_RP_PROP']),
        "Locataires": int(data['P21_RP_LOC'])
    }
    
    fig_logement = px.pie(
    names=list(logement_data.keys()),  # Les catégories (Propriétaires vs Locataires)
    values=list(logement_data.values()),  # Les valeurs correspondantes
    title="Répartition Propriétaires vs Locataires",
    labels={'value': 'Nombre', 'names': 'Type de logement'},  # Renommage des labels
    )

    # Affichage du graphique
    col.plotly_chart(fig_logement, use_container_width=True)


    # Graphique de la répartition entre Maisons et Appartements
    logement_type_data = {
        "Maisons": int(data['P21_MAISON']),
        "Appartements": int(data['P21_APPART'])
    }

    # Création du graphique camembert
    fig_logement_type = px.pie(
        names=list(logement_type_data.keys()),  # Les catégories (Maisons vs Appartements)
        values=list(logement_type_data.values()),  # Les valeurs correspondantes
        title="Répartition Maisons vs Appartements",
        labels={'value': 'Nombre', 'names': 'Type de logement'},  # Renommage des labels
    )

    # Affichage du graphique
    col.plotly_chart(fig_logement_type, use_container_width=True)


    # Graphique pour l'occupation des logements (par nombre de pièces, etc.)
    pieces_data = {
        "1 pièce": int(data['P21_RP_1P']),
        "2 pièces": int(data['P21_RP_2P']),
        "3 pièces": int(data['P21_RP_3P']),
        "4 pièces": int(data['P21_RP_4P']),
        "5 pièces et plus": int(data['P21_RP_5PP'])
    }
    fig_pieces = px.bar(
        x=list(pieces_data.keys()),
        y=list(pieces_data.values()),
        labels={'x': 'Nombre de pièces', 'y': 'Nombre de logements'},
        title="Répartition des logements par nombre de pièces"
    )
    col.plotly_chart(fig_pieces, use_container_width=True)


import plotly.express as px

def show_emploi(data, col):
    # Taux d'emploi
    emploi = data.get('P20_ACTOCC1564', 0)
    chomeurs = data.get('P20_CHOM1564', 0)
    total = data.get('P20_POP1564', 1)
    taux_emploi = round(emploi / total * 100, 1) if total else 0
    taux_chomage = round(chomeurs / total * 100, 1) if total else 0

    # Affichage des taux dans une carte stylisée
    col.markdown(f"""
        <div style="
            background-color: rgba(255, 255, 255, 0.8);
            padding: 20px;
            border-radius: 15px;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
            font-size: 18px;
            text-align: center;
        ">
            <strong>Taux d'emploi (15-64 ans) :</strong>
            <span style="color: green; font-size: 24px; font-weight: bold;">
                {taux_emploi}%
            </span><br>
            <strong>Taux de chômage :</strong>
            <span style="color: red; font-size: 24px; font-weight: bold;">
                {taux_chomage}%
            </span>
        </div>
    """, unsafe_allow_html=True)

    # Graphique de répartition des catégories d'emploi
    emploi_categories = {
        "Emploi": emploi,
        "Chômage": chomeurs,
        "Inactifs": total - emploi - chomeurs
    }

    fig_emploi = px.pie(
        names=list(emploi_categories.keys()),
        values=list(emploi_categories.values()),
        title="Répartition des catégories d'emploi",
        color_discrete_sequence=["#00CC96", "#FF5C8D", "#FFD700"]
    )
    col.plotly_chart(fig_emploi, use_container_width=True)

    # Graphique de répartition des taux d'emploi
    taux_categories = {
        "Actifs occupés (15-64 ans)": emploi,
        "Chômeurs (15-64 ans)": chomeurs,
        "Inactifs (15-64 ans)": total - emploi - chomeurs
    }

    fig_emploi_taux = px.bar(
        x=list(taux_categories.keys()),
        y=list(taux_categories.values()),
        labels={'x': 'Catégories', 'y': 'Nombre de personnes'},
        title="Répartition par statut d'emploi",
        color_discrete_sequence=["#66CDAA", "#FF6347", "#87CEEB"]
    )
    col.plotly_chart(fig_emploi_taux, use_container_width=True)


def show_sante(ville, col):
    try:
        # Obtenir le code de la ville et les données de santé associées
        code = df_sante[df_sante["LIBGEO"] == ville]["CODEGEO"].values[0]
        data = df_sante[df_sante["CODEGEO"] == code]
        
        if not data.empty:
            col.markdown("### 🏥 Équipements de santé")

            # Affichage du nombre total d'établissements de santé
            nombre_etablissements = data['NOMRS'].nunique()  # Comptabilise le nombre d'établissements uniques
            col.write(f"**Nombre d'établissements de santé** : {nombre_etablissements}")
            
        else:
            col.warning(f"Aucune donnée disponible pour {ville}")
        
        # Diagramme à barres pour les équipements de santé
            fig1 = px.bar(data, x='TYPE', y='CAPACITE_D_ACCUEIL', 
                        labels={'TYPE': 'Type d\'équipement', 'CAPACITE_D_ACCUEIL': 'Capacité d\'accueil'},
                        title=f"Capacité d'accueil pour les équipements de santé à {ville}")
            col.plotly_chart(fig1, use_container_width=True)
            
            # Diagramme circulaire pour la répartition des types d'équipements
            fig2 = px.pie(data, names='TYPE', values='CAPACITE_D_ACCUEIL',
                        title=f"Répartition des équipements de santé à {ville}")
            col.plotly_chart(fig2, use_container_width=True)
    
    except Exception as e:
        col.error(f"Erreur : {e}")


def show_delits(ville, col):
    # Filtrer les données pour la ville choisie
    data = df_crimes[df_crimes['LIBGEO'] == ville]

    if not data.empty:
        # Convertir la colonne 'taux_pour_mille' en numérique (en cas de données invalides)
        data['taux_pour_mille'] = pd.to_numeric(data['taux_pour_mille'], errors='coerce')

        # Calcul du total des délits et taux pour 1000 habitants
        total_delits = data['nombre'].sum()
        taux_moyen = data['taux_pour_mille'].mean()

        # Affichage des informations de base dans une carte stylisée
        col.markdown(f"""
            <div style="background-color: rgba(255, 255, 255, 0.8); padding: 15px; border-radius: 15px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px;">
                <h4><strong>🕵️‍♂️ Total des délits</strong> : {total_delits}</h4>
            </div>
        """, unsafe_allow_html=True)

        # Graphique camembert pour la répartition des types de délits
        fig_pie = px.pie(data, names='indicateur', values='nombre', 
                         title=f"Répartition des délits à {ville}", 
                         labels={'indicateur': 'Type de délit', 'nombre': 'Nombre de délits'})
        col.plotly_chart(fig_pie, use_container_width=True)

    else:
        col.warning(f"Aucune donnée disponible pour {ville}.")


def show_diplomes(ville, col):
    try:
        # Récupérer les données pour la ville
        data = df_diplomes[df_diplomes['LIBGEO'] == ville]
        
        if not data.empty:
            col.markdown("### 🎓 Répartition des Diplômes")

            # Diagramme circulaire pour la répartition des diplômes
            niveau_diplome_data = {
                "BEPC": data['P21_NSCOL15P_BEPC'].sum(),
                "CAP/BEP": data['P21_NSCOL15P_CAPBEP'].sum(),
                "Baccalauréat": data['P21_NSCOL15P_BAC'].sum(),
                "Supérieur": data['P21_NSCOL15P_SUP2'].sum(),
                "Autre": data['P21_NSCOL15P_SUP34'].sum(),
            }

            # Pie chart for diplomas distribution
            fig1 = px.pie(names=list(niveau_diplome_data.keys()), 
                          values=list(niveau_diplome_data.values()),
                          title=f"Répartition des diplômes à {ville}")
            col.plotly_chart(fig1, use_container_width=True)

            # Bar chart showing the number of diplomas per category
            fig2 = px.bar(x=list(niveau_diplome_data.keys()), 
                          y=list(niveau_diplome_data.values()), 
                          labels={'x': 'Niveau de diplôme', 'y': 'Nombre'},
                          title=f"Répartition des diplômes par niveau à {ville}")
            col.plotly_chart(fig2, use_container_width=True)
    
    except Exception as e:
        col.error(f"Erreur : {e}")


def show_population(data, col, ville):
    with col:
        st.markdown("### 🌍 Données Générales", unsafe_allow_html=True)

        # Bloc population + densité avec encadré
        st.markdown(
            f"""
            <div style="background-color: rgba(255, 255, 255, 0.8); padding: 15px; border-radius: 15px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px;">
                <h4>👥 Population : {int(data['PMUN21'])}</h4>
            </div>
            """,
            unsafe_allow_html=True
        )

    # --- Affichage de la météo (matin et soir, 5 jours) ---
    meteo_matin, meteo_soir = get_weather_forecast(ville, API_KEY)

    if meteo_matin and meteo_soir:
        col.markdown("#### 🌤️ Prévisions météo (matin et soir – 5 jours)")

        for i in range(len(meteo_matin)):
            date = meteo_matin[i][0]

            col.markdown(
                f"""
                <div style='
                    background: rgba(255, 255, 255, 0.7);
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 15px;
                    box-shadow: 2px 2px 12px rgba(0,0,0,0.1);
                    font-size: 16px;
                '>
                    <h5 style='margin-bottom:10px; text-align:center;'>{date}</h5>
                    <div style='display: flex; justify-content: space-around; align-items: center;'>
                        <div style='text-align:center;'>
                            <strong>🌅 Matin</strong><br>
                            🌡️ {meteo_matin[i][1]}°C<br>
                            {meteo_matin[i][2]}<br>
                            <img src="{meteo_matin[i][3]}" width="50">
                        </div>
                        <div style='text-align:center;'>
                            <strong>🌇 Soir</strong><br>
                            🌡️ {meteo_soir[i][1]}°C<br>
                            {meteo_soir[i][2]}<br>
                            <img src="{meteo_soir[i][3]}" width="50">
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )


def get_data(ville):
    return df_base[df_base['LIBGEO'] == ville].iloc[0]

# === COMPARAISON DES VILLES ===
data1 = get_data(ville1)
data2 = get_data(ville2)
col1, col2 = st.columns(2)

if selected == "Données générales":
    show_population(data1, col1, ville1)
    show_population(data2, col2, ville2)

elif selected == "Logement":
    show_logement(data1, col1)
    show_logement(data2, col2)
elif selected == "Emploi":
    show_emploi(data1, col1)
    show_emploi(data2, col2)
elif selected == "Santé":
    show_sante(ville1, col1)
    show_sante(ville2, col2)
elif selected == "Sécurité":
    show_delits(ville1, col1)
    show_delits(ville2, col2)
elif selected == "Formation":
    show_diplomes(ville1, col1)
    show_diplomes(ville2, col2)

st.markdown("""
---
<center>📈 Données INSEE / OpenWeatherMap | App design by CityFighting™</center>
""", unsafe_allow_html=True)
