import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import os

# --- Configuration de la Page ---
st.set_page_config(
    page_title="Dashboard de Suivi de Poids",
    page_icon="🏋️",
    layout="wide"
)

# --- Constantes et Configuration ---
DATA_FILE = "poids.csv"
START_DATE = pd.to_datetime("2025-02-07")
END_DATE = pd.to_datetime("2025-08-31")
START_WEIGHT = 85.5
TARGET_WEIGHT = 70.0

# --- Données Initiales ---
# Ces données seront utilisées pour créer le fichier CSV au premier lancement.
initial_data_string = """Date;Poids
07/02/25;85,50
08/02/25;85,05
09/02/25;85,25
10/02/25;85,40
11/02/25;85,50
12/02/25;85,05
13/02/25;84,90
14/02/25;84,65
15/02/25;84,40
16/02/25;84,25
17/02/25;84,20
18/02/25;84,10
19/02/25;83,90
20/02/25;83,90
21/02/25;83,70
22/02/25;83,45
23/02/25;83,35
24/02/25;83,15
25/02/25;83,25
26/02/25;83,15
27/02/25;82,85
28/02/25;82,70
01/03/25;82,60
02/03/25;82,60
03/03/25;82,60
04/03/25;82,90
05/03/25;82,65
06/03/25;82,25
07/03/25;82,30
08/03/25;81,90
09/03/25;81,60
10/03/25;81,55
11/03/25;81,30
12/03/25;81,10
13/03/25;81,20
14/03/25;81,20
15/03/25;81,25
16/03/25;81,05
17/03/25;80,35
18/03/25;80,85
19/03/25;80,70
20/03/25;80,10
21/03/25;80,30
22/03/25;80,00
23/03/25;80,00
24/03/25;79,90
25/03/25;79,60
26/03/25;79,30
27/03/25;79,55
28/03/25;79,90
29/03/25;79,50
30/03/25;80,05
31/03/25;79,40
01/04/25;79,15
02/04/25;79,10
03/04/25;79,50
04/04/25;79,80
05/04/25;79,60
06/04/25;78,90
07/04/25;78,90
08/04/25;78,95
09/04/25;78,95
10/04/25;78,75
11/04/25;78,95
12/04/25;80,00
13/04/25;79,50
14/04/25;78,80
15/04/25;79,20
16/04/25;79,20
17/04/25;79,35
18/04/25;80,00
19/04/25;79,90
20/04/25;79,20
21/04/25;78,75
22/04/25;79,05
23/04/25;78,50
24/04/25;78,70
25/04/25;78,50
26/04/25;78,50
27/04/25;78,15
28/04/25;79,15
29/04/25;80,10
30/04/25;79,50
01/05/25;77,75
02/05/25;77,35
03/05/25;77,75
04/05/25;77,50
05/05/25;77,85
06/05/25;77,35
07/05/25;77,10
08/05/25;77,20
09/05/25;77,55
10/05/25;77,45
11/05/25;77,15
12/05/25;76,65
13/05/25;77,55
14/05/25;77,10
15/05/25;77,40
16/05/25;77,30
17/05/25;77,25
18/05/25;77,20
19/05/25;76,95
20/05/25;77,80
21/05/25;77,45
22/05/25;76,85
23/05/25;76,85
24/05/25;77,80
25/05/25;76,95
26/05/25;77,00
27/05/25;76,85
28/05/25;77,15
29/05/25;77,15
30/05/25;77,00
31/05/25;76,80
01/06/25;76,50
02/06/25;76,10
03/06/25;75,95
04/06/25;76,85
05/06/25;77,00
06/06/25;76,65
07/06/25;76,65
08/06/25;77,00
09/06/25;77,00
10/06/25;77,00
11/06/25;77,00
12/06/25;77,00
13/06/25;77,00
14/06/25;77,05
15/06/25;77,05
16/06/25;77,00
17/06/25;77,00
18/06/25;77,00
19/06/25;77,00
20/06/25;77,00
21/06/25;77,05
22/06/25;76,60
23/06/25;76,80
24/06/25;77,05
25/06/25;76,85
26/06/25;77,25
27/06/25;77,00
28/06/25;76,50
29/06/25;76,20
30/06/25;76,40
01/07/25;76,40
02/07/25;75,90
03/07/25;75,45
04/07/25;75,20
05/07/25;75,60
06/07/25;76,00
07/07/25;75,40
08/07/25;75,40
09/07/25;75,30
10/07/25;74,75
11/07/25;74,50
12/07/25;75,50
13/07/25;76,00
14/07/25;76,50
15/07/25;77,00
16/07/25;77,00
17/07/25;77,00
18/07/25;77,00
19/07/25;76,90
20/07/25;76,60
21/07/25;76,30
22/07/25;76,60
23/07/25;76,30
24/07/25;76,10
25/07/25;75,90
26/07/25;75,55
27/07/25;75,80
28/07/25;76,10
29/07/25;76,10
30/07/25;75,55
31/07/25;75,65
01/08/25;75,45
02/08/25;74,90
03/08/25;74,90
04/08/25;74,75
05/08/25;74,45
06/08/25;74,30
"""

# --- Fonctions ---

@st.cache_data
def load_data():
    """Charge les données depuis le fichier CSV. Crée le fichier s'il n'existe pas."""
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            f.write(initial_data_string)
    
    try:
        df = pd.read_csv(DATA_FILE, sep=';')
        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%y')
        df['Poids'] = df['Poids'].str.replace(',', '.', regex=False).astype(float)
        df = df.sort_values(by='Date').reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier de données : {e}")
        return pd.DataFrame(columns=["Date", "Poids"])

def save_data(df):
    """Sauvegarde le DataFrame dans le fichier CSV."""
    df_to_save = df.copy()
    df_to_save['Date'] = df_to_save['Date'].dt.strftime('%d/%m/%y')
    df_to_save['Poids'] = df_to_save['Poids'].apply(lambda x: f"{x:.2f}".replace('.', ','))
    df_to_save.to_csv(DATA_FILE, index=False, sep=';')

# --- Interface Utilisateur ---

st.title("🏋️ Dashboard de Suivi de Poids")

# Charger les données
df = load_data()

if not df.empty:
    # --- Barre Latérale pour l'ajout de données ---
    st.sidebar.header("📝 Ajouter une nouvelle pesée")
    # Utiliser la date du jour suivant la dernière entrée comme valeur par défaut
    last_date = df['Date'].max().date()
    default_new_date = last_date + pd.Timedelta(days=1)
    
    new_date = st.sidebar.date_input("Date", value=default_new_date)
    new_weight = st.sidebar.number_input("Poids (kg)", min_value=0.0, step=0.1, format="%.2f")

    if st.sidebar.button("💾 Enregistrer"):
        new_date_dt = pd.to_datetime(new_date)
        if new_date_dt in df['Date'].values:
            st.sidebar.warning("Une entrée existe déjà pour cette date. Elle sera mise à jour.")
            df.loc[df['Date'] == new_date_dt, 'Poids'] = new_weight
        else:
            new_entry = pd.DataFrame([{'Date': new_date_dt, 'Poids': new_weight}])
            df = pd.concat([df, new_entry], ignore_index=True)
        
        df = df.sort_values(by='Date').reset_index(drop=True)
        save_data(df)
        st.sidebar.success("Poids enregistré !")
        st.cache_data.clear() # Nettoyer le cache pour recharger les données
        st.rerun()

    # --- Affichage des métriques clés ---
    st.header("📊 Statistiques Clés")
    
    # S'assurer qu'il y a assez de données pour les calculs
    if len(df) > 1:
        col1, col2, col3, col4 = st.columns(4)
        
        latest_weight = df['Poids'].iloc[-1]
        previous_weight = df['Poids'].iloc[-2]
        starting_weight_actual = df['Poids'].iloc[0]
        weight_lost = starting_weight_actual - latest_weight
        weight_to_target = latest_weight - TARGET_WEIGHT

        col1.metric(label="Poids Actuel", value=f"{latest_weight:.2f} kg", delta=f"{latest_weight - previous_weight:.2f} kg")
        col2.metric(label="Poids de Départ", value=f"{starting_weight_actual:.2f} kg")
        col3.metric(label="✅ Poids Perdu", value=f"{weight_lost:.2f} kg")
        col4.metric(label="🎯 À Perdre (Objectif 70kg)", value=f"{weight_to_target:.2f} kg")

    # --- Calculs pour le graphique ---
    df['Moyenne 7 jours'] = df['Poids'].rolling(window=7, min_periods=1).mean()
    df_weekly = df.set_index('Date').resample('W-MON', label='left', closed='left')['Poids'].mean().reset_index()
    df_weekly.rename(columns={'Poids': 'Moyenne Hebdomadaire'}, inplace=True)

    # --- Création du Graphique ---
    st.header("📈 Évolution et Tendances")

    # 1. Préparer les données dans un format "long" pour une légende automatique
    # Poids journalier
    df_poids = df[['Date', 'Poids']].copy()
    df_poids.rename(columns={'Poids': 'Valeur'}, inplace=True)
    df_poids['Légende'] = 'Poids Journalier'

    # Moyenne 7 jours (on retire les valeurs nulles pour un tracé propre)
    df_moy7j = df[['Date', 'Moyenne 7 jours']].dropna().copy()
    df_moy7j.rename(columns={'Moyenne 7 jours': 'Valeur'}, inplace=True)
    df_moy7j['Légende'] = 'Moyenne 7 jours'

    # Moyenne hebdomadaire
    df_hebdo = df_weekly.copy()
    df_hebdo.rename(columns={'Moyenne Hebdomadaire': 'Valeur'}, inplace=True)
    df_hebdo['Légende'] = 'Moyenne Hebdomadaire'

    # Ligne d'objectif
    df_objectif = pd.DataFrame({
        'Date': [START_DATE, END_DATE],
        'Valeur': [START_WEIGHT, TARGET_WEIGHT]
    })
    df_objectif['Légende'] = 'Objectif'

    # 2. Concaténer toutes les données dans un seul DataFrame
    df_plot = pd.concat([df_poids, df_moy7j, df_hebdo, df_objectif])

    # 3. Créer le graphique de base (lignes)
    line_chart = alt.Chart(df_plot).mark_line(interpolate='monotone').encode(
        x=alt.X('Date:T', title='Date'),
        y=alt.Y('Valeur:Q', title='Poids (kg)', scale=alt.Scale(zero=False)),
        color=alt.Color('Légende:N',
            scale=alt.Scale(
                domain=['Poids Journalier', 'Moyenne 7 jours', 'Moyenne Hebdomadaire', 'Objectif'],
                range=['#1f77b4', 'orange', 'green', 'red']
            ),
            legend=alt.Legend(
                title=None,
                orient='top',
                symbolSize=200,
                labelFontSize=12
            )
        ),
        strokeDash=alt.condition(
            alt.FieldOneOfPredicate(field='Légende', oneOf=['Moyenne 7 jours', 'Moyenne Hebdomadaire']),
            alt.value([5, 5]),
            alt.value([0]),
        ),
        strokeWidth=alt.condition(
            alt.datum.Légende == 'Objectif',
            alt.value(3),
            alt.value(2)
        ),
        tooltip=[
            alt.Tooltip('Date:T', format='%A %d %B %Y'),
            alt.Tooltip('Valeur:Q', title='Poids', format='.2f'),
            'Légende:N'
        ]
    ).interactive()

    # 4. Créer une couche séparée juste pour les points du poids journalier
    points_chart = alt.Chart(df_poids).mark_point(filled=True, size=50, color='#1f77b4').encode(
        x='Date:T',
        y=alt.Y('Valeur:Q'),
        tooltip=[
            alt.Tooltip('Date:T', format='%A %d %B %Y'),
            alt.Tooltip('Valeur:Q', title='Poids', format='.2f')
        ]
    )

    # 5. Combiner les lignes et les points, et ajouter un titre
    final_chart = (line_chart + points_chart).properties(
        title="Évolution du Poids vs Objectifs et Moyennes",
        height=500
    )

    st.altair_chart(final_chart, use_container_width=True)

    # --- Affichage des données brutes ---
    with st.expander("Voir l'historique complet des pesées"):
        st.dataframe(df.sort_values(by='Date', ascending=False).reset_index(drop=True))

else:
    st.info("Le fichier de données est vide ou n'a pas pu être chargé. L'application démarrera une fois les données créées.")
