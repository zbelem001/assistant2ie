import os
from dotenv import load_dotenv
import pymupdf4llm
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import WebBaseLoader
import glob
import logging

load_dotenv()

# Reduce spam from loaders/splitters
logging.getLogger("httpx").setLevel(logging.WARNING)

DOCS_DIR = "docs"
CHROMA_DB_DIR = "chroma_db"
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

def ingest_documents():
    print(f"1. Extraction (Markdown) via PyMuPDF4LLM depuis '{DOCS_DIR}'...")
    pdf_files = glob.glob(f"{DOCS_DIR}/*.pdf")
    all_documents = []

    for pdf_file in pdf_files:
        print(f"   -> Lecture de {pdf_file}...")
        # L'outil extrait intelligemment sous forme de Markdown (tableaux, listes...)
        md_text = pymupdf4llm.to_markdown(pdf_file)
        
        # --- NOUVEAUTÉ : Ajout de Métadonnées (Filtrage) ---
        text_lower = md_text.lower()
        cycle_meta = "general"
        if "bachelor" in text_lower and "master" in text_lower:
            cycle_meta = "les_deux"
        elif "bachelor" in text_lower:
            cycle_meta = "bachelor"
        elif "master" in text_lower or "mastère" in text_lower:
            cycle_meta = "master"
            
        doc_type_meta = "info"
        if "règlement" in text_lower or "sanction" in text_lower or "discipline" in text_lower:
            doc_type_meta = "reglement"
        elif "fcfa" in text_lower or "frais" in text_lower or "tarif" in text_lower:
            doc_type_meta = "tarifs"

        doc = Document(
            page_content=md_text, 
            metadata={
                "source": pdf_file,
                "cycle": cycle_meta,
                "type": doc_type_meta
            }
        )
        all_documents.append(doc)

    print("\n1b. Extraction Web (Scraping du site de 2iE)...")
    urls_to_scrape = [
        "https://www.2ie-edu.org/formations/",
        "https://www.2ie-edu.org/international/", 
        "https://www.2ie-edu.org/tarifs/#1718030146941-eee7c2a2-b4b5",
        "https://www.2ie-edu.org/tarifs/#1716914657015-9205d785-2de4",
        "https://www.2ie-edu.org/tarifs/#1716914657036-d5f3492d-121d", 
        "https://www.2ie-edu.org/tarifs/#1718181967668-e5cc5b32-7fce",
        "https://www.2ie-edu.org/inscription/#1716232730092-e3627213-0512",
        "https://www.2ie-edu.org/a-propos/historique/", 
        "https://www.2ie-edu.org/a-propos/gouvernance-organisation/#1715868580997-b72d1025-b35b",
        "https://www.2ie-edu.org/contact-admissions/",
        "https://www.2ie-edu.org/recherche/laboratoire-eaux-hydrosystemes-et-agriculture-lehsa/",
        "https://www.2ie-edu.org/recherche/laboratoire-eco-materiaux-habitats-durables-lemhad/"
    ]
    
    try:
        web_loader = WebBaseLoader(urls_to_scrape)
        web_docs = web_loader.load()
        for doc in web_docs:
            print(f"   -> Page web lue : {doc.metadata.get('source')}")
            # On ajoute un metadata "web" pour les différencier des PDF
            doc.metadata["type"] = "page_web"
            doc.metadata["cycle"] = "general"
            all_documents.append(doc)
    except Exception as e:
        print(f"Erreur lors du scraping web: {e}")

    print("\n2. Découpage des documents (Markdown Splitting)...")
    # Puisqu'on a du Markdown, on peut découper un peu plus grand
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=250,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "]
    )
    chunks = text_splitter.split_documents(all_documents)
    print(f" -> Découpé en {len(chunks)} morceaux intelligents.")

    print(f"\n3. Recréation de la Base ChromaDB...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    
    # On vide proprement avant
    if os.path.exists(CHROMA_DB_DIR):
        import shutil
        shutil.rmtree(CHROMA_DB_DIR)

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DB_DIR
    )
    
    print("\nTerminé ! La NOUVELLE base vectorielle Markdown est prête.")

if __name__ == "__main__":
    ingest_documents()
