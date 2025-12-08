import streamlit as st

from user_service import authenticate_user, create_user


def _hide_native_page_nav() -> None:
    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] div[data-testid="stSidebarNav"] {
            display: none !important;
        }
        button[kind="header"] {
            display: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _go_to_main_page() -> None:
    try:
        st.switch_page("app.py")
    except Exception:
        st.experimental_rerun()


st.set_page_config(page_title="Inventaire — Portail", page_icon="🔐", layout="centered")
_hide_native_page_nav()

if st.session_state.get("auth_user"):
    _go_to_main_page()
    st.stop()


st.title("🔐 Portail Inventaire")
st.caption("Connectez-vous ou créez un compte pour accéder à la vitrine et aux outils.")

login_tab, signup_tab = st.tabs(["Connexion", "Créer un compte"])

with login_tab:
    st.subheader("Accéder à mon espace")
    with st.form("login_form"):
        identifier = st.text_input("Nom d'utilisateur ou e-mail", autocomplete="username")
        password = st.text_input("Mot de passe", type="password", autocomplete="current-password")
        submitted = st.form_submit_button("Se connecter")

    if submitted:

        user = authenticate_user(identifier, password)
        if user:
            st.session_state["auth_user"] = {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "role": user["role"],
            }
            st.success("Connexion réussie. Redirection…")
            _go_to_main_page()
        else:
            st.error("Identifiants incorrects. Vérifiez votre email / mot de passe.")

    st.caption("Mot de passe oublié ? Contactez un administrateur pour déclencher une réinitialisation.")


with signup_tab:
    st.subheader("Créer un nouveau compte")
    with st.form("signup_form"):
        username = st.text_input("Nom d'utilisateur", max_chars=30)
        email = st.text_input("Adresse e-mail", autocomplete="email")
        password = st.text_input("Mot de passe", type="password", help="8 caractères minimum.")
        password_confirm = st.text_input("Confirmer le mot de passe", type="password")
        signup_submitted = st.form_submit_button("Créer mon compte")

    if signup_submitted:
        if password != password_confirm:
            st.error("Les mots de passe ne correspondent pas.")
        else:
            try:
                user = create_user(username, email, password, role="standard")
            except ValueError as exc:
                st.error(str(exc))
            else:
                st.session_state["auth_user"] = {
                    "id": user["id"],
                    "username": user["username"],
                    "email": user["email"],
                    "role": user["role"],
                }
                st.success("Compte créé ! Bienvenue 🎉")
                _go_to_main_page()
