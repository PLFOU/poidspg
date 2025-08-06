import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import gspread
from gspread_dataframe import set_with_dataframe
from google.oauth2.service_account import Credentials
import io
# Nouveaux imports pour Firebase
import firebase_admin
from firebase_admin import credentials, storage

# --- Configuration de la Page ---
st.set_page_config(
    page_title="Dashboard de Suivi de Poids",
    page_icon="🏋️",
    layout="wide"
)

# --- Constantes ---
START_DATE = pd.to_datetime("2025-02-07")
END_DATE = pd.to_datetime("2025-08-31")
START_WEIGHT = 85.5
TARGET_WEIGHT = 70.0

# --- Authentification Google Sheets ---
scopes_gsheets = ["https://www.googleapis.com/auth/spreadsheets"]
creds_gsheets = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=scopes_gsheets
)
gsheets_client = gspread.authorize(creds_gsheets)

# --- Initialisation de Firebase (une seule fois) ---
try:
    firebase_admin.get_app()
except ValueError:
    cred_firebase = credentials.Certificate(dict(st.secrets["firebase_service_account"]))
    firebase_admin.initialize_app(cred_firebase, {
        'storageBucket': st.secrets["firebase_service_account"]["storage_bucket"]
    })

# --- Connexion à Google Sheets ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1J8sfnafYbCUHmgGZML4DTs02rq_vc0J9nHetcvISYRg/edit?gid=0#gid=0" 
WORKSHEET_NAME = "poids"

try:
    spreadsheet = gsheets_client.open_by_url(SHEET_URL)
    worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
except Exception as e:
    st.error(f"Impossible d'ouvrir la feuille de calcul. Vérifiez l'URL et les permissions de partage. Erreur : {e}")
    st.stop()

# --- Fonctions pour Firebase Storage ---
def upload_photo_to_firebase(photo_data):
    """Téléverse une photo sur Firebase Storage."""
    photo_data.seek(0)
    bucket = storage.bucket()
    
    # Créer un nom de dossier basé sur la date du jour
    folder_name = datetime.now().strftime('%Y-%m-%d')
    file_name = f"{folder_name}/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
    
    blob = bucket.blob(file_name)
    blob.upload_from_file(photo_data, content_type='image/jpeg')
    return file_name

# --- Fonctions pour Google Sheets ---
@st.cache_data(ttl=60)
def load_data():
    """Charge les données depuis la feuille Google Sheets."""
    try:
        values = worksheet.get_all_values()
        if not values or len(values) < 2:
            return pd.DataFrame(columns=["Date", "Poids"])

        df = pd.DataFrame(values[1:], columns=values[0])
        df = df.dropna(how="all")
        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
        df['Poids'] = pd.to_numeric(
            df['Poids'].astype(str).str.replace(',', '.', regex=False), 
            errors='coerce'
        )
        df = df.dropna(subset=['Date', 'Poids'])
        df = df.sort_values(by='Date').reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement des données Sheets : {e}")
        return pd.DataFrame(columns=["Date", "Poids"])

def save_data(df_to_save):
    """Met à jour la feuille Google Sheets."""
    try:
        df_to_save['Date'] = pd.to_datetime(df_to_save['Date']).dt.strftime('%d/%m/%Y')
        df_to_save['Poids'] = df_to_save['Poids'].map('{:.2f}'.format).str.replace('.', ',', regex=False)
        worksheet.clear()
        set_with_dataframe(worksheet, df_to_save, include_index=False, resize=True)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde des données Sheets : {e}")

# --- Création des onglets ---
tab1, tab2 = st.tabs(["📊 Dashboard Suivi de Poids", "📸 Ajouter une Photo"])

# --- Contenu de l'Onglet 1 : Dashboard ---
with tab1:
    df = load_data()

    if df is not None and not df.empty:
        st.sidebar.header("📝 Ajouter une nouvelle pesée")
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
            
            df_sorted = df.sort_values(by='Date').reset_index(drop=True)
            save_data(df_sorted)
            st.sidebar.success("Poids enregistré sur Google Sheets !")
            st.rerun()

        st.header("📊 Statistiques Clés")
        
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
            col4.metric(label="� À Perdre (Objectif 70kg)", value=f"{weight_to_target:.2f} kg")

        st.header("📈 Évolution et Tendances")
        df['Moyenne 7 jours'] = df['Poids'].rolling(window=7, min_periods=1).mean()
        df_weekly = df.set_index('Date').resample('W-MON', label='left', closed='left')['Poids'].mean().reset_index()
        df_weekly.rename(columns={'Poids': 'Moyenne Hebdomadaire'}, inplace=True)
        
        df_poids = df[['Date', 'Poids']].copy(); df_poids.rename(columns={'Poids': 'Valeur'}, inplace=True); df_poids['Légende'] = 'Poids Journalier'
        df_moy7j = df[['Date', 'Moyenne 7 jours']].dropna().copy(); df_moy7j.rename(columns={'Moyenne 7 jours': 'Valeur'}, inplace=True); df_moy7j['Légende'] = 'Moyenne 7 jours'
        df_hebdo = df_weekly.copy(); df_hebdo.rename(columns={'Moyenne Hebdomadaire': 'Valeur'}, inplace=True); df_hebdo['Légende'] = 'Moyenne Hebdomadaire'
        df_objectif = pd.DataFrame({'Date': [START_DATE, END_DATE], 'Valeur': [START_WEIGHT, TARGET_WEIGHT]}); df_objectif['Légende'] = 'Objectif'

        df_plot = pd.concat([df_poids, df_moy7j, df_hebdo, df_objectif])

        line_chart = alt.Chart(df_plot).mark_line(interpolate='monotone').encode(
            x=alt.X('Date:T', title='Date'),
            y=alt.Y('Valeur:Q', title='Poids (kg)', scale=alt.Scale(zero=False)),
            color=alt.Color('Légende:N', scale=alt.Scale(domain=['Poids Journalier', 'Moyenne 7 jours', 'Moyenne Hebdomadaire', 'Objectif'], range=['#1f77b4', 'orange', 'green', 'red']), legend=alt.Legend(title=None, orient='top', symbolSize=200, labelFontSize=12)),
            strokeDash=alt.condition(alt.FieldOneOfPredicate(field='Légende', oneOf=['Moyenne 7 jours', 'Moyenne Hebdomadaire']), alt.value([5, 5]), alt.value([0])),
            strokeWidth=alt.condition(alt.datum.Légende == 'Objectif', alt.value(3), alt.value(2)),
            tooltip=[alt.Tooltip('Date:T', format='%A %d %B %Y'), alt.Tooltip('Valeur:Q', title='Poids', format='.2f'), 'Légende:N']
        ).interactive()

        points_chart = alt.Chart(df_poids).mark_point(filled=True, size=50, color='#1f77b4').encode(
            x='Date:T',
            y=alt.Y('Valeur:Q'),
            tooltip=[alt.Tooltip('Date:T', format='%A %d %B %Y'), alt.Tooltip('Valeur:Q', title='Poids', format='.2f')]
        )

        final_chart = (line_chart + points_chart).properties(title="Évolution du Poids vs Objectifs et Moyennes", height=500)
        st.altair_chart(final_chart, use_container_width=True)

        with st.expander("Voir l'historique complet des pesées"):
            st.dataframe(df.sort_values(by='Date', ascending=False).reset_index(drop=True))
    else:
        st.warning("Aucune donnée chargée depuis Google Sheets. Vérifiez que la feuille contient des données et que les permissions de partage sont correctes.")


# --- Contenu de l'Onglet 2 : Photo ---
with tab2:
    st.header("📷 Prenez une photo")
    
    picture = st.camera_input("Prenez une photo pour immortaliser votre progrès :")

    if picture:
        st.image(picture, caption="Photo capturée.")
        
        if st.button("Valider et Enregistrer sur Firebase"):
            with st.spinner("Enregistrement en cours sur Firebase Storage..."):
                try:
                    file_name = upload_photo_to_firebase(picture)
                    st.success(f"Photo enregistrée avec succès sur Firebase sous le nom : {file_name}")
                except Exception as e:
                    st.error(f"Une erreur est survenue lors de l'enregistrement sur Firebase : {e}")
