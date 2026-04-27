import streamlit as st
import fitz  # PyMuPDF
import anthropic
import json
import re

st.set_page_config(page_title="Générateur de fiches démembrement", layout="wide")

st.title("Générateur de fiches — Démembrement de propriété")
st.markdown("Téléversez le PDF de la fiche produit pour extraire les données et générer la publication.")

# --- Clé API ---
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Clé API Anthropic", type="password", help="Votre clé API Claude")
    st.markdown("---")
    st.markdown("**Champs extraits automatiquement :**")
    st.markdown("""
- Nom du programme & ville
- Prix minimum (avec parking)
- Décote (%)
- Durée du démembrement
- Date de livraison
- Nombre de lots
- Région / Département
- Neuf ou Ancien
- Type de bien
- Promoteur & Bailleur
- Description localisation
- Description programme
""")

def extract_text_from_pdf(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_data_with_claude(text, api_key):
    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""Tu es un expert en immobilier spécialisé dans le démembrement de propriété.

Voici le texte brut extrait d'une fiche produit PDF d'un programme en démembrement.
Extrais les informations suivantes et retourne-les en JSON strict (sans markdown, sans explication).

Champs à extraire :
- nom_programme : nom du programme (ex: "Les Aiguinards")
- ville : ville (ex: "Meylan")
- departement : nom complet du département en toutes lettres (ex: "Isère", "Paris", "Bouches-du-Rhône") — jamais le numéro
- adresse : adresse complète du programme (numéro, rue, code postal, ville) si mentionnée dans le PDF
- region : région (ex: "Auvergne-Rhône-Alpes")
- type_bien : "Appartement" | "Maison" | "Résidence de tourisme" | "Résidence étudiante"
- neuf_ou_ancien : "Neuf" | "Ancien"
- prix_minimum : prix minimum en nue-propriété avec parking, en euros (nombre entier, ex: 130000)
- decote : pourcentage de décote (nombre entier, ex: 39)
- duree_demembrement : durée en années (nombre entier, ex: 16)
- date_livraison : date ou trimestre de livraison (ex: "T1 2028")
- nombre_lots : nombre de lots disponibles en démembrement (nombre entier, ex: 6)
- promoteur : nom du promoteur (ex: "Edifim")
- bailleur : nom du bailleur usufruitier (ex: "Erilia")
- description_localisation : texte brut décrivant la localisation et l'environnement (extrait du PDF)
- description_programme : texte brut décrivant le programme (types d'appartements, prestations, équipements)
- acces_transports : texte brut sur les accès et transports

Si une information n'est pas disponible, mets null.

Texte du PDF :
{text}

Retourne uniquement le JSON, sans aucun autre texte."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.content[0].text.strip()
    # Nettoyer si markdown code block
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"^```\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


def generate_fiche_and_seo(data, api_key):
    """Génère la fiche ET le SEO en un seul appel pour garantir la cohérence."""
    client = anthropic.Anthropic(api_key=api_key)

    decote = str(data.get("decote", ""))
    duree = str(data.get("duree_demembrement", ""))
    prix_min = str(data.get("prix_minimum", ""))

    prompt = f"""Tu es un rédacteur et expert SEO spécialisé en investissement immobilier et démembrement de propriété.

Tu dois générer en une seule fois : la fiche de publication ET les éléments SEO associés.

Voici les données du programme :
{json.dumps(data, ensure_ascii=False, indent=2)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ÉTAPE 1 — Choisis d'abord l'expression clé
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Choisis une expression clé longue traîne de 3 à 5 mots (ex: "nue-propriété appartement Meylan Isère").
Cette expression doit ensuite apparaître :
- Dans le titre SEO (méta-titre)
- Dans la méta-description
- Au moins 2 fois dans les 3 blocs de texte (dont obligatoirement dans le premier paragraphe)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ÉTAPE 2 — Rédige les 3 blocs H2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Règles de rédaction STRICTES :
1. Exactement 3 blocs, chacun avec un titre H2
2. Phrases de 20 mots maximum
3. Voix active uniquement
4. Mots de transition variés (ainsi, de plus, par ailleurs, en outre, également, qui plus est, à cela s'ajoute, c'est pourquoi, dès lors...)
5. Chaque bloc : 80 à 130 mots
6. Texte naturel, commercial sans excès
7. Dans chaque bloc, entoure 2 ou 3 phrases/groupes clés avec <strong>...</strong>
8. L'expression clé (ou un synonyme très proche) doit apparaître dans le PREMIER paragraphe et au moins une 2ème fois dans les blocs suivants

Bloc 1 — Environnement et localisation : ville, quartier, transports, commerces, dynamique économique
Bloc 2 — Le programme : bâtiment, typologies (T2, T3...), prestations, nombre de lots, promoteur
Bloc 3 — L'investissement : décote de {decote}%, durée {duree} ans, prix à partir de {prix_min} €, bailleur, avantages

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ÉTAPE 3 — Génère les éléments SEO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- titre_seo : 60 à 65 caractères max, contient tous les mots de l'expression clé
- meta_description : 150 à 160 caractères max, contient l'expression clé, se termine par un appel à l'action

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FORMAT DE SORTIE — JSON strict uniquement, sans markdown, sans explication
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{{
  "expression_cle": "...",
  "titre_seo": "...",
  "meta_description": "...",
  "html": "<h2>...</h2>\\n<p>...</p>\\n\\n<h2>...</h2>\\n<p>...</p>\\n\\n<h2>...</h2>\\n<p>...</p>"
}}"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2500,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.content[0].text.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"^```\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)

def format_price(val):
    if val is None:
        return "—"
    try:
        return f"{int(val):,} €".replace(",", " ")
    except:
        return str(val)

# --- Interface principale ---
uploaded_file = st.file_uploader("Téléverser la fiche produit PDF", type=["pdf"])

if uploaded_file and api_key:
    pdf_bytes = uploaded_file.read()

    with st.spinner("Extraction du texte PDF..."):
        text = extract_text_from_pdf(pdf_bytes)

    if not text.strip():
        st.error("Impossible d'extraire le texte du PDF. Le fichier est peut-être un scan image.")
        st.stop()

    with st.expander("Texte brut extrait (debug)", expanded=False):
        st.text(text[:3000])

    with st.spinner("Analyse des données par Claude..."):
        try:
            data = extract_data_with_claude(text, api_key)
        except Exception as e:
            st.error(f"Erreur lors de l'extraction : {e}")
            st.stop()

    st.success("Données extraites avec succès !")

    # --- Affichage et édition des données ---
    st.markdown("## Vérification et correction des données")
    st.markdown("Vérifie les informations extraites avant de générer la fiche.")

    col1, col2, col3 = st.columns(3)

    with col1:
        data["nom_programme"] = st.text_input("Nom du programme", value=data.get("nom_programme") or "")
        data["adresse"] = st.text_input("Adresse complète", value=data.get("adresse") or "")
        data["ville"] = st.text_input("Ville", value=data.get("ville") or "")
        data["departement"] = st.text_input("Département", value=data.get("departement") or "")
        data["region"] = st.text_input("Région", value=data.get("region") or "")
        data["neuf_ou_ancien"] = st.selectbox("Neuf ou Ancien", ["Neuf", "Ancien"],
            index=0 if data.get("neuf_ou_ancien") == "Neuf" else 1)

    with col2:
        data["type_bien"] = st.selectbox("Type de bien",
            ["Appartement", "Maison", "Résidence de tourisme", "Résidence étudiante"],
            index=["Appartement", "Maison", "Résidence de tourisme", "Résidence étudiante"].index(
                data.get("type_bien", "Appartement")) if data.get("type_bien") in
                ["Appartement", "Maison", "Résidence de tourisme", "Résidence étudiante"] else 0)
        data["prix_minimum"] = st.number_input("Prix minimum avec parking (€)",
            value=int(data.get("prix_minimum") or 0), step=1000)
        data["decote"] = st.number_input("Décote (%)", value=int(data.get("decote") or 0), step=1)
        data["duree_demembrement"] = st.number_input("Durée (ans)",
            value=int(data.get("duree_demembrement") or 0), step=1)
        data["date_livraison"] = st.text_input("Date de livraison", value=data.get("date_livraison") or "")

    with col3:
        data["nombre_lots"] = st.number_input("Nombre de lots",
            value=int(data.get("nombre_lots") or 0), step=1)
        data["promoteur"] = st.text_input("Promoteur", value=data.get("promoteur") or "")
        data["bailleur"] = st.text_input("Bailleur", value=data.get("bailleur") or "")

    st.markdown("---")
    st.markdown("**Descriptions**")
    data["description_localisation"] = st.text_area("Description localisation",
        value=data.get("description_localisation") or "", height=120)
    data["description_programme"] = st.text_area("Description programme",
        value=data.get("description_programme") or "", height=120)
    data["acces_transports"] = st.text_area("Accès & transports",
        value=data.get("acces_transports") or "", height=80)

    st.markdown("---")

    if st.button("Générer la fiche de publication", type="primary", use_container_width=True):
        with st.spinner("Génération de la fiche et des éléments SEO..."):
            try:
                result = generate_fiche_and_seo(data, api_key)
                fiche_html = result.get("html", "")
                seo = {
                    "expression_cle": result.get("expression_cle", ""),
                    "titre_seo": result.get("titre_seo", ""),
                    "meta_description": result.get("meta_description", ""),
                }
            except Exception as e:
                st.error(f"Erreur lors de la génération : {e}")
                st.stop()

        st.success("Fiche générée !")

        # --- Récapitulatif des métadonnées ---
        st.markdown("## Métadonnées WordPress")
        meta_col1, meta_col2, meta_col3, meta_col4 = st.columns(4)
        with meta_col1:
            st.metric("Prix minimum", format_price(data.get("prix_minimum")))
            st.metric("Décote", f"{data.get('decote', '—')} %")
        with meta_col2:
            st.metric("Durée", f"{data.get('duree_demembrement', '—')} ans")
            st.metric("Livraison", data.get("date_livraison") or "—")
        with meta_col3:
            st.metric("Lots disponibles", data.get("nombre_lots") or "—")
            st.metric("Type", data.get("type_bien") or "—")
        with meta_col4:
            st.metric("Promoteur", data.get("promoteur") or "—")
            st.metric("Bailleur", data.get("bailleur") or "—")

        # --- Champs SEO ---
        st.markdown("## SEO")
        seo_col1, seo_col2 = st.columns([1, 2])
        with seo_col1:
            expr = seo.get("expression_cle", "")
            st.markdown("**Expression clé principale**")
            st.code(expr, language=None)
            expr_len = len(expr)
            st.caption(f"{expr_len} caractères")
        with seo_col2:
            titre_seo = seo.get("titre_seo", "")
            st.markdown("**Titre SEO / Méta-titre**")
            st.code(titre_seo, language=None)
            t_len = len(titre_seo)
            color = "green" if t_len <= 65 else "red"
            st.markdown(f":{color}[{t_len} / 65 caractères]")

        meta_desc = seo.get("meta_description", "")
        st.markdown("**Méta-description**")
        st.code(meta_desc, language=None)
        md_len = len(meta_desc)
        color_md = "green" if md_len <= 160 else "red"
        st.markdown(f":{color_md}[{md_len} / 160 caractères]")

        st.markdown("---")

        # --- Contenu HTML ---
        st.markdown("## Contenu HTML à copier dans WordPress")

        # Aperçu visuel
        with st.expander("Aperçu visuel", expanded=True):
            st.markdown(fiche_html, unsafe_allow_html=True)

        # Code brut à copier
        st.markdown("**Code HTML (à coller dans l'éditeur WordPress ► Vue code)**")
        st.code(fiche_html, language="html")

        # Bouton copie via JS
        st.markdown(f"""
<textarea id="html_to_copy" style="position:absolute;left:-9999px">{fiche_html}</textarea>
<button onclick="navigator.clipboard.writeText(document.getElementById('html_to_copy').value);this.innerText='✓ Copié !'"
style="background:#0073aa;color:white;border:none;padding:10px 24px;border-radius:6px;cursor:pointer;font-size:15px">
📋 Copier le HTML
</button>
""", unsafe_allow_html=True)

        # Fiche complète JSON pour référence
        with st.expander("Données JSON complètes", expanded=False):
            st.json(data)

elif uploaded_file and not api_key:
    st.warning("Entre ta clé API Anthropic dans la barre latérale pour continuer.")
elif not uploaded_file:
    st.info("Téléverse un PDF pour commencer.")
