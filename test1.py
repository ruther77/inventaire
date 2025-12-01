# app.py (au même niveau que le 'with pos_tab:')

import os
import io
import math
import re
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from functools import lru_cache 
import streamlit_authenticator as stauth 
import plotly.express as px # Import crucial pour les graphiques

# Imports pour le Scanner et la Vidéo (Dépendances : opencv-python, pyzbar, streamlit-webrtc)
import cv2 
from pyzbar.pyzbar import decode
from PIL import Image
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, WebRtcMode, RTCConfiguration

# Importation des fonctions de gestion de la BDD et du chargeur 
from core.data_repository import query_df, exec_sql, exec_sql_return_id, get_engine # NOUVEAU: exec_sql n'est plus appelé ici
from core.inventory_service import * # NOUVEAU: Import du service 
from core import products_loader

# --- FONCTION POUR CHARGER LE CSS EXTERNE (style.css) ---
def local_css(file_name):
    """Charge un fichier CSS externe et l'injecte dans l'application Streamlit."""
    
    # Construction du chemin absolu en utilisant le répertoire du script courant
    file_path = os.path.join(os.path.dirname(__file__), file_name)
    
    try:
        with open(file_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        # Affiche un message de débogage pour vérifier le CWD (Current Working Directory)
        current_dir = os.getcwd()
        st.error(f"Erreur: Le fichier de style '{file_name}' est introuvable. Chemin relatif tenté (CWD): {current_dir}/{file_name}. Le fichier n'est PAS dans le conteneur ou le CWD est incorrect.")
        
        
# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Inventaire Épicerie", layout="wide", page_icon="📦")

# --- CHARGEMENT DU STYLE CSS PERSONNALISÉ ---
# Ceci remplace l'ancien bloc de CSS en ligne
local_css("style.css")

# --- Initialisation des Variables de Session ---
if "last_barcode" not in st.session_state:
    st.session_state["last_barcode"] = None
if "current_frame_count" not in st.session_state:
    st.session_state["current_frame_count"] = 0
if "cart" not in st.session_state:
    st.session_state["cart"] = []
    
# --- Configuration de l'Authentification ---
# Utilisez une clé secrète forte pour la production !
SECRET_KEY = '__auth_token_inventaire_secure_2025' 

# Définition des rôles et hachage
hashed_passwords = stauth.Hasher(['jemmysev', 'userpass']).generate()

credentials = {
    "usernames": {
        "admin": {
            "email": "ulrich@inventaire.fr",
            "name": "ulrich",
            "password": hashed_passwords[0], 
            "role": "admin"
        },
        "user": {
            "email": "user@inventaire.fr",
            "name": "user",
            "password": hashed_passwords[1], 
            "role": "standard"
        }
    }
}

authenticator = stauth.Authenticate(
    credentials,
    'inventaire_cookie', 
    SECRET_KEY,          
    cookie_expiry_days=30
)

# --- Fonctions Utilitaires et Caching ---

def to_float(x, default=0.0, minv=None, maxv=None):
    """Convertit une chaîne en float en gérant les formats monétaires et les NaN."""
    if x is None:
        return default
    try:
        if isinstance(x, float) and math.isnan(x):
            return default
    except Exception:
        pass
    s = str(x).replace("€","").replace("\xa0","").replace(" ","").replace(",", ".").strip()
    try:
        v = float(s)
        if minv is not None:
            v = max(v, minv)
        if maxv is not None:
            v = min(v, maxv) # Correction de l'erreur maxv
        return round(v, 4)
    except Exception:
        return default

@st.cache_data(ttl=60)
def load_products_list():
    # Requête optimisée utilisant le stock matérialisé (O(1))
    sql_query = """
        SELECT
            p.id,
            p.nom,
            p.prix_vente,
            p.tva,
            p.stock_actuel AS quantite_stock, -- Stock Actuel (O(1))
            CASE
                WHEN p.stock_actuel <= 0 THEN '❌ Rupture'
                WHEN p.stock_actuel < 5 THEN '⚠️ Faible'
                ELSE '✅ OK'
            END AS statut_stock
        FROM
            produits p
        LEFT JOIN
            produits_barcodes pb ON p.id = pb.produit_id
        GROUP BY
            p.id, p.nom, p.prix_vente, p.tva, p.stock_actuel
        ORDER BY
            p.nom;
    """
    # ... (Appel à query_df) ...
    try:
        # On charge toutes les infos importantes, y compris la TVA pour le PoS
        df = query_df(sql_query)
        # Ajout d'une colonne de statut pour le dashboard et l'inventaire
        df['statut_stock'] = df['quantite_stock'].apply(lambda x: 'Stock OK' if x > 5 else ('Alerte Basse' if x > 0 else 'Épuisé'))
        return df
    except Exception as e:
        st.error(f"Erreur critique de chargement des produits: {e}. Vérifiez la vue 'v_stock_produits'.")
        return pd.DataFrame()


# --- Classe Barcode Detector (pour le Scanner) ---
class BarcodeDetector(VideoTransformerBase):
    """Détecte les codes-barres dans chaque frame vidéo. Déclenche le Rerun Streamlit."""
    
    SKIP_FRAMES = 5 # Ne vérifie qu'une frame sur 5 pour optimiser
    
    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        st.session_state["current_frame_count"] += 1
        
        if st.session_state["current_frame_count"] % self.SKIP_FRAMES == 0:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # Utilisation de la détection Pyzbar
            barcodes = decode(gray)
            
            for barcode in barcodes:
                barcode_data = barcode.data.decode("utf-8")
                
                # Vérifie si un nouveau code-barres a été scanné
                if st.session_state["last_barcode"] != barcode_data:
                    st.session_state["last_barcode"] = barcode_data
                    # Déclenche une mise à jour Streamlit pour traiter le code
                    st.rerun() 
                
                # Dessiner le rectangle autour du code-barres (Feedback visuel)
                (x, y, w, h) = barcode.rect
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                text = f"{barcode_data}"
                cv2.putText(img, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return img


# ==============================================================================
# --- DÉBUT DU FLUX PRINCIPAL (CONTRÔLE D'ACCÈS) ---
# ==============================================================================

name, authentication_status, username = authenticator.login('Connexion à l\'Inventaire', 'main')

if authentication_status:
    
    # --- UI Setup et Définition des Onglets (LES 7 ONGLETS SONT ICI) ---
    st.session_state["user_role"] = credentials["usernames"][username]["role"]

    st.title("📦 Inventaire — Gestion Complète")
    st.sidebar.caption(f'Bienvenue, **{name}** (Rôle: **{st.session_state["user_role"]}**)')
    authenticator.logout('Déconnexion', 'sidebar')

    # CORRECTION CRITIQUE : Définition des 7 onglets
    pos_tab, catalog_tab, mvt_tab, dash_tab, scanner_tab, import_tab, admin_tab = st.tabs([
        "Vente (PoS)", "Catalogue", "Stock & Mvt", "Dashboard", "Scanner", "Importation", "Maintenance (Admin)"
    ])
    
    # Chargement des données (en cache)
    df_products = load_products_list()
   

# ---------------- Vente (PoS) ----------------
with pos_tab:
    st.header("Terminal Point de Vente (PoS)")

    col_input, col_cart = st.columns([1, 2])

    with col_cart:
        st.markdown('<div class="app-tile">', unsafe_allow_html=True)
        st.subheader("🛒 Panier Actuel")
        
        # 1. Vérifiez si le panier existe et n'est pas vide
        if 'cart' not in st.session_state or not st.session_state.cart:
            st.info("Le panier est vide. Veuillez ajouter des produits.")
        else:
            # 2. Création d'un DataFrame pour l'affichage (plus clair)
            cart_df = pd.DataFrame(st.session_state.cart)
            
            # 3. Calcul du sous-total TTC et de la TVA par ligne
            cart_df['prix_total'] = cart_df['prix_vente'] * cart_df['qty']
            cart_df['total_tva'] = cart_df['prix_total'] * (cart_df['tva'] / 100)
            
            # 4. Affichage du tableau
            st.dataframe(
                cart_df[['nom', 'qty', 'prix_vente', 'prix_total']],
                column_config={
                    "nom": "Produit",
                    "qty": "Quantité",
                    "prix_vente": st.column_config.NumberColumn("P.U. (€)", format="%.2f €"),
                    "prix_total": st.column_config.NumberColumn("Total Ligne (€)", format="%.2f €")
                },
                hide_index=True,
                use_container_width=True
            )
            
            # 5. Calcul des totaux
            total_ttc = cart_df['prix_total'].sum()
            total_tva = cart_df['total_tva'].sum()
            total_ht = total_ttc - total_tva
            
            col_tva, col_ht, col_ttc = st.columns(3)
            
            col_ht.metric("Total HT", f"{total_ht:.2f} €")
            col_tva.metric("Total TVA", f"{total_tva:.2f} €")
            col_ttc.metric("Total TTC", f"{total_ttc:.2f} €", delta_color="off")
            
            # 6. Bouton pour Vider le Panier
            if st.button("Vider le Panier", help="Annule la transaction en cours.", key="clear_cart_btn"):
                st.session_state.cart = [] # Réinitialise le panier
                st.rerun() # Rafraîchit l'application
        
        # Bouton de Validation de Vente (Placez-le ici car il est lié au panier)
            st.divider()
            if st.session_state.cart:
                # La logique pour finaliser la vente doit être ici
                if st.button("Finaliser la Vente", key="btn_finalize_sale", type="primary"):
                    st.success("Vente Finalisée (Logique de mouvements de stock à implémenter ici)!")
                    # TODO: Ajouter process_sale_transaction(st.session_state.cart, username)
                    st.session_state.cart = []
                    st.rerun()

            st.markdown('</div>', unsafe_allow_html=True) # Fermeture de la tile de la colonne col_cart
    
    with col_input:
        st.markdown('<div class="app-tile">', unsafe_allow_html=True) 
    
        st.subheader("🛒 Saisie Produit")

        # --- 1. CHARGEMENT DYNAMIQUE DES PRODUITS ---
        # On assume que la table des produits a les colonnes 'id' et 'nom'
        try:
            # Assurez-vous que query_df est accessible (importé de db_manager)
            products_df = query_df("SELECT id, nom FROM produits ORDER BY nom")
        
            # Création du mapping Nom -> ID et de la liste pour le selectbox
            product_options = {row['nom']: row['id'] for index, row in products_df.iterrows()}
            # Ajout d'une option par défaut non sélectionnable
            product_names = ["-- Sélectionner un produit --"] + list(product_options.keys())
        
            # Gérer l'ancienne logique de code-barres (pour la pré-sélection si nécessaire)
            # NOTE : Cette logique n'est plus compatible directement avec un selectbox,
            #        mais elle est conservée pour réinitialiser la session state.
            initial_input = st.session_state.get("last_barcode", "")
            if st.session_state.get("last_barcode"):
                st.session_state["last_barcode"] = None

        except Exception as e:
            st.error(f"Erreur lors du chargement des produits: {e}")
            # Si échec, on vide la liste pour éviter le plantage
            product_names = ["-- Erreur de chargement --"]
            product_options = {}

        # --- 2. REMPLACEMENT DU TEXT_INPUT PAR LE SELECTBOX ---
        with st.form("pos_input_form", clear_on_submit=False):
        
            # REMPLACEMENT de st.text_input par st.selectbox
            selected_product_name = st.selectbox(
            "Sélectionner un Produit (Nom)", 
            options=product_names,
            index=0, 
            key="pos_product_selectbox"
            )
        
            qty_to_add = st.number_input("Quantité", min_value=1, value=1, step=1, key='pos_qty_add')
            add_button = st.form_submit_button("Ajouter au Panier")
        
            # --- 3. LOGIQUE D'AJOUT ADAPTÉE ---
            if add_button and selected_product_name != "-- Sélectionner un produit --":
                # L'ID est maintenant récupéré à partir du nom sélectionné
                selected_product_id = product_options.get(selected_product_name)
            
                if selected_product_id:
                    # ******************************************************************
                    # REMPLACER CES LIGNES PAR VOTRE VRAIE LOGIQUE D'AJOUT AU PANIER
                    # (qui utilisait avant `product_input` pour la recherche BDD)
                    # Maintenant, vous avez directement l'ID (`selected_product_id`) et la quantité (`qty_to_add`).
                    #
                    # Exemple de ce que votre ancienne fonction de recherche de produit doit maintenant faire :
                    # product_found = fetch_product_by_id(selected_product_id)
                    # add_to_cart(product_found, qty_to_add)
                    # ******************************************************************
                
                    # Dans cet exemple, nous allons forcer un rerun pour simuler l'ajout
                    # Vous devez remplacer ceci par votre code existant pour ajouter l'article au panier
                    # en utilisant selected_product_id et qty_to_add.
                
                    st.session_state["product_to_add_id"] = selected_product_id
                    st.session_state["product_to_add_qty"] = qty_to_add
                    st.session_state["add_to_cart_triggered"] = True
                    #st.rerun()
                else:
                    st.error("Erreur: ID produit non trouvé après sélection.")

            elif add_button:
                st.warning("Veuillez sélectionner un produit pour l'ajouter au panier.")
        # --------------------------------------------------------------------------------
# NOUVEAU BLOC D'EXÉCUTION DU PANIER (À insérer sous le formulaire)
# --------------------------------------------------------------------------------
if st.session_state.get("add_to_cart_triggered", False):
    
    product_id = st.session_state.get("product_to_add_id")
    quantity = st.session_state.get("product_to_add_qty")
    
    if product_id and quantity > 0:
        # 1. Chercher les détails du produit dans le DataFrame chargé (df_products)
        try:
            # df_products est le DataFrame chargé par load_products_list() au début du script
            product_row = df_products[df_products['id'] == product_id].iloc[0]

            # 2. Créer l'objet produit pour le panier
            product_data = {
                'id': int(product_row['id']),
                'nom': product_row['nom'],
                'prix_vente': float(product_row['prix_vente']),
                'tva': float(product_row['tva']),
                'qty': quantity 
            }

            # 3. Mettre à jour le panier (Logique d'ajout/incrémentation)
            found = False
            for item in st.session_state.cart:
                if item['id'] == product_id:
                    item['qty'] += quantity
                    found = True
                    break
                    
            if not found:
                st.session_state.cart.append(product_data)
            
            st.toast(f"✅ {quantity} x {product_data['nom']} ajouté(s) au panier !", icon='🛒')
            
        except IndexError:
            st.error(f"Erreur : Produit ID {product_id} non trouvé dans le catalogue.")
        except Exception as e:
            st.error(f"Erreur inattendue lors de l'ajout au panier : {e}")

    # 4. Réinitialiser les variables de session pour éviter l'exécution répétée
    if "product_to_add_id" in st.session_state:
        del st.session_state["product_to_add_id"]
    if "product_to_add_qty" in st.session_state:
        del st.session_state["product_to_add_qty"]
    if "add_to_cart_triggered" in st.session_state:
        del st.session_state["add_to_cart_triggered"]

        st.markdown('</div>', unsafe_allow_html=True)

    pass # fin du bloc pos_tab

# ---------------- Catalogue ----------------
with catalog_tab:
    st.header("Catalogue Produits et Administration")
    
    # --- LOGIQUE DE DÉSACTIVATION DES COLONNES ---
    non_editable_columns = ['id', 'quantite_stock', 'statut_stock',"codes_barres"]
    if st.session_state.get("user_role") == "admin":
        # Admin peut éditer tout sauf l'ID, le Stock et le Statut
        disabled_cols = non_editable_columns 
    else:
        # Utilisateur standard ne peut rien éditer
        disabled_cols = ['nom', 'prix_vente', 'tva', 'quantite_stock', 'statut_stock'] 
        
        st.caption("Le stock ne peut être modifié que via les mouvements (ventes/ajustements), pas ici.")
        
        if df_products.empty:
            st.info("Aucun produit n'est actuellement enregistré.")
            
        else:
            # Affichage du catalogue (editable seulement pour les admins)
            editable_df = st.data_editor(
                df_products,
                key="catalog_editor",
                hide_index=True,
                width='stretch', # Correction Streamlit
                num_rows="dynamic" if st.session_state.get("user_role") == "admin" else "fixed",
                
                disabled=disabled_cols, 
                
                column_config={
                    "id": "ID",
                    "nom": "Nom du Produit",
                    "prix_vente": st.column_config.NumberColumn("Prix Vente (€)", format="%.2f"),
                    "tva": st.column_config.NumberColumn("TVA (%)", format="%.2f"),
                    "quantite_stock": st.column_config.NumberColumn("Stock Actuel", format="%.2f"),
                    "codes_barres": st.column_config.TextColumn("Codes-barres (Séparés par ', ')"),
                    "statut_stock": st.column_config.TextColumn("Statut Stock")
                }
            )

            # Logique de persistance des modifications et suppression
            if st.session_state.get("user_role") == "admin":
                
                col_save, col_delete = st.columns([1, 1])
                
                # --- Enregistrement des modifications ---
                if col_save.button("Enregistrer les modifications du Catalogue", key="save_catalog_changes", type="primary"):
                    try:
                        changes = st.session_state["catalog_editor"]["edited_rows"]
                        
                        if changes:
                            updates_count = 0
                            for index, row_changes in changes.items():
                                product_id = df_products.loc[index, 'id']
                                
                                # Construction dynamique de la requête de mise à jour
                                set_clauses = [f"{col}=:{col}" for col in row_changes.keys() if col not in non_editable_columns]
                                
                                if set_clauses:
                                    sql = f"UPDATE produits SET {', '.join(set_clauses)} WHERE id = :id"
                                    params = row_changes
                                    params['id'] = product_id
                                    exec_sql(text(sql).bindparams(**params))
                                    updates_count += 1

                            st.success(f"{updates_count} produit(s) mis à jour avec succès!")
                            load_products_list.clear() 
                            st.rerun()
                        else:
                            st.info("Aucune modification n'a été détectée dans le tableau.")
                            
                    except Exception as e:
                        st.error(f"Erreur lors de l'enregistrement: {e}")
                        
                # --- Suppression de produits (Nouvelle fonctionnalité) ---
                product_to_delete = col_delete.selectbox(
                    "Sélectionner un produit à supprimer", 
                    df_products['nom'], 
                    index=None
                )
                if product_to_delete:
                    id_to_delete = df_products[df_products['nom'] == product_to_delete]['id'].iloc[0]
                    if col_delete.button(f"Confirmer la Suppression de {product_to_delete}", key="confirm_delete"):
                        try:
                            # Suppression CASCADE (supprime aussi les codes-barres et mouvements associés)
                            exec_sql(text("DELETE FROM produits WHERE id = :pid").bindparams(pid=id_to_delete))
                            st.toast(f"✅ Produit '{product_to_delete}' et données associées supprimés.", icon='🗑️')
                            load_products_list.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erreur lors de la suppression: {e}. Des contraintes de BDD peuvent bloquer.")

            st.divider()

        # Bloc d'ajout rapide de produit (pour les administrateurs)
        if st.session_state.get("user_role") == "admin":
            st.subheader("Ajout Rapide de Produit")
            
            with st.form("add_product_form", clear_on_submit=True):
                colA, colB = st.columns(2)
                with colA:
                    new_nom = st.text_input("Nom du Produit", max_chars=100)
                    new_prix = st.number_input("Prix de Vente (€)", min_value=0.01, format="%.2f", value=1.0)
                with colB:
                    new_tva = st.number_input("TVA (%)", min_value=0.0, max_value=100.0, value=20.0, format="%.2f")
                    new_codes = st.text_input("Codes-barres (séparés par ;) [Optionnel]", max_chars=255)
                
                if st.form_submit_button("Ajouter le Produit au Catalogue"):
                    if new_nom and new_prix > 0:
                        try:
                            # 1. Insertion du produit de base
                            sql_prod = text("INSERT INTO produits (nom, prix_vente, tva) VALUES (:nom, :prix, :tva) RETURNING id")
                            product_id = exec_sql_return_id(sql_prod.bindparams(nom=new_nom, prix=new_prix, tva=new_tva))
                            
                            # 2. Insertion des codes-barres (si fournis)
                            if new_codes:
                                codes_list = [c.strip() for c in new_codes.split(';') if c.strip()]
                                for code in codes_list:
                                    sql_code = text("INSERT INTO produits_barcodes (produit_id, code_barres) VALUES (:pid, :code) ON CONFLICT (code_barres) DO NOTHING")
                                    exec_sql(sql_code.bindparams(pid=product_id, code=code))

                            st.success(f"Produit '{new_nom}' ajouté avec succès!")
                            load_products_list.clear() 
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erreur lors de l'ajout: {e}")
                    else:
                        st.warning("Veuillez entrer un nom et un prix de produit valide (> 0).")

    pass

# ---------------- Stock & Mvt ----------------
# Bloc legacy désactivé pour éviter les erreurs d'indentation (à remettre en forme si besoin)
if False:
    pass
