# Assistant Virtuel 2iE - Backend (RAG)

Ce projet backend implémente le système d'intelligence artificielle (IA) de l'assistant virtuel de l'école **2iE** (Institut International d'Ingénierie de l'Eau et de l'Environnement). Il repose sur une architecture **RAG (Retrieval-Augmented Generation)** avancée, permettant à l'assistant de répondre de manière précise et naturelle aux questions des étudiants et prospects en se basant sur une base de connaissances documentaire (PDF) et web.

## 🎯 Objectif du Projet

Fournir des réponses fiables concernant :
- Les règlements internes et la discipline.
- Les tarifs, frais de scolarité et modalités d'inscription.
- Les formations (Bachelor, Master, Mastère Spécialisé).
- L'historique, la gouvernance et les laboratoires de recherche de 2iE.

L'assistant est conçu pour agir comme un conseiller privilégié de 2iE, offrant des réponses humainement fluides sans exposer la mécanique sous-jacente (ex: il ne dira jamais "d'après le document fourni...").

## 🛠️ Technologies et Architecture

Le système utilise les technologies suivantes pour assurer une extraction, une recherche et une génération d'excellente qualité :

- **LangChain** : Framework principal pour l'orchestration du RAG.
- **ChromaDB** : Base de données vectorielle locale (`chroma_db/`) pour le stockage des embeddings.
- **Modèles d'Embeddings et Re-Ranking (HuggingFace)** :
  - *Embeddings* : `paraphrase-multilingual-MiniLM-L12-v2` (optimisé pour le multilingue).
  - *Cross-Encoder (Re-ranker)* : `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` pour un tri intelligent des résultats.
- **LLM (Génération de texte)** : Propulsé par **Groq** (modèle `llama-3.1-8b-instant` par défaut), garantissant des inférences extrêmement rapides via l'API.
- **Traitement Documentaire** :
  - *PyMuPDF4LLM* : Extraction intelligente des PDFs (`docs/`) au format Markdown (préservant la structure, les tableaux et les listes).
  - *WebBaseLoader* : Scraping des pages institutionnelles du site web de 2iE.

## 🚀 Fonctionnalités Clés

1. **Recherche Hybride Avancée** :
   Le système combine deux méthodes de recherche via un `EnsembleRetriever` (poids 50/50) :
   - *Recherche Sémantique (Vectorielle)* : Comprend le sens et le contexte de la question en utilisant ChromaDB.
   - *Recherche par Mots-Clés (BM25)* : Assure de ne pas rater les correspondances exactes (ex: sigles, montants spécifiques).

2. **Re-Ranking Contextuel** :
   Les documents récupérés par la recherche hybride (les 16 meilleurs) sont relus et reclassés par un modèle Cross-Encoder qui ne conserve que les 4 extraits *les plus pertinents* avant de les envoyer au LLM. Cela réduit drastiquement les hallucinations.

3. **Filtrage par Métadonnées** :
   Lors de l'ingestion, le système analyse le texte et attribue des étiquettes intelligentes aux documents :
   - *Cycle* : `bachelor`, `master`, `les_deux`, `general`.
   - *Type de document* : `reglement`, `tarifs`, `info`, `page_web`.

## 📁 Structure des Fichiers

- `ingestion_v2.py` : Script responsable de la lecture des PDFs (dossier `docs/`), du scraping web, du découpage (Chunking intelligent ciblant le Markdown), de la création des vecteurs et de l'enregistrement dans la base ChromaDB.
- `assistant.py` : Script principal chargeant la base vectorielle, configurant la recherche hybride, le re-ranker, et initialisant la chaîne de discussion avec le LLM Groq.
- `docs/` : Dossier contenant les documents sources (PDF) de l'école.
- `chroma_db/` : Dossier généré automatiquement contenant la base de données vectorielle locale SQLite.

## ⚙️ Configuration et Installation

1. **Environnement** : Assurez-vous d'avoir Python installé. Recommandation : utiliser un environnement virtuel.
2. **Variables d'environnement** :
   Vous devez créer un fichier `.env` à la racine de `backend/` avec au minimum votre clé API Groq :
   ```env
   GROQ_API_KEY=votre_cle_api_groq_ici
   GROQ_MODEL=llama-3.1-8b-instant
   ```
3. **Mise à jour de la base de données** :
   Si vous ajoutez de nouveaux PDFs dans `docs/`, relancez le script d'ingestion :
   ```bash
   python ingestion_v2.py
   ```
4. **Lancement de l'assistant** :
   ```bash
   python assistant.py
   ```