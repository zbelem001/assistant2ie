import os
from dotenv import load_dotenv

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pymupdf4llm
import glob
import logging

# Charger les clés API (GROQ_API_KEY) et le modèle depuis le .env
load_dotenv()

CHROMA_DB_DIR = "chroma_db"
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2" # Correspondance avec le modèle multilingue


def main():
    print("Initialisation de l'assistant 2iE...")

    # 1. Charger les embeddings et se connecter à la base vectorielle existante
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vectorstore = Chroma(
        persist_directory=CHROMA_DB_DIR, 
        embedding_function=embeddings
    )
    
    # 2. Configurer le LLM
    groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    llm = ChatGroq(
        model=groq_model,
        temperature=0.2
    )

    # --- NOUVELLE METHODE AVANCEE : RECHERCHE HYBRIDE (Vectoriel + BM25) ---
    print("Chargement de la recherche hybride (Vecteurs + Mots-clés exacts) et génération des métadonnées...")
    
    # Retriever 1 : Recherche Vectorielle Classique (Sémantique)
    # On va chercher 8 blocs larges 
    vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 8})
    
    # Retriever 2 : Recherche BM25 (Exact Keyword Match)
    print("Mise à jour du BM25...")
    pdf_files = glob.glob(f"docs/*.pdf")
    all_documents = []
    for pdf_file in pdf_files:
        md_text = pymupdf4llm.to_markdown(pdf_file)
        
        # --- NOUVEAUTÉ : Ajout de Métadonnées ---
        text_lower = md_text.lower()
        cycle_meta = "general"
        if "bachelor" in text_lower and "master" in text_lower:
            cycle_meta = "les_deux"
        elif "bachelor" in text_lower:
            cycle_meta = "bachelor"
        elif "master" in text_lower or "mastère" in text_lower:
            cycle_meta = "master"

        all_documents.append(Document(page_content=md_text, metadata={"source": pdf_file, "cycle": cycle_meta}))
        
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=250, separators=["\n## ", "\n### ", "\n\n", "\n", " "])
    splits = text_splitter.split_documents(all_documents)
    
    bm25_retriever = BM25Retriever.from_documents(splits)
    bm25_retriever.k = 8 # BM25 trouve 8 blocs
    
    # L'Ensemble Retriever combine les deux
    hybrid_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, vector_retriever], weights=[0.5, 0.5]
    )

    # --- NOUVELLE TECHNOLOGIE : RE-RANKING ---
    # Relit les 16 blocs récupérés et ne garde que les 4 VRAIMENT pertinents
    print("Chargement du CrossEncoder (Re-ranker) pour un tri intelligent...")
    cross_encoder = HuggingFaceCrossEncoder(model_name="cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")
    compressor = CrossEncoderReranker(model=cross_encoder, top_n=4)
    
    retriever = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=hybrid_retriever
    )
    print("Recherche hybride & Re-ranking activés !")

    # 3. Créer le Prompt d'instructions pour le LLM (L'étape de génération - Plus naturel !)
    system_prompt = (
        "Tu es l'expert administratif et conseiller privilégié de l'école 2iE. "
        "Tu connais tout sur l'école grâce aux informations ci-dessous, mais tu dois te comporter comme un humain. "
        "\n\nRègles :"
        "\n1. INTERDICTION FORMELLE d'utiliser des expressions comme 'D'après les documents', 'Le texte stipule', 'Le contexte indique'. Réponds directement et naturellement, comme si c'était tes propres connaissances."
        "\n2. Si l'information est présente explicitement, donne-la clairement et avec un ton accueillant."
        "\n3. Si l'information est partielle, déduis logiquement ce qui a du sens, mais suggère toujours à l'étudiant de confirmer avec l'administration."
        "\n4. Si tu ne connais pas la réponse (si ce n'est pas dans le texte), dis simplement et poliment que tu n'as pas cette information pour le moment. Ne dis jamais 'le document ne mentionne pas cela'."
        "\n5. Rédige tes réponses en français."
        "\n\n--- INFORMATIONS ---"
        "\n{context}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    # 4. Construire la chaîne RAG (Retrieval + Augmentation)
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    print("\n" + "="*50)
    print("=== ASSISTANT 2iE OPÉRATIONNEL ===")
    print("Posez vos questions sur la scolarité ou le règlement.")
    print("Tapez 'quit' pour quitter.")
    print("="*50)

    # 5. Boucle pour discuter avec l'assistant
    while True:
        question = input("\nÉtudiant : ")
        if question.lower() in ['quit', 'exit', 'q']:
            print("Au revoir ! Équipe 2iE.")
            break
            
        print("Assistant 2iE (réflexion en cours)...")
        # Exécution de la requête
        response = rag_chain.invoke({"input": question})
        
        print(f"\nAssistant 2iE :\n{response['answer']}")
        
        # Optionnel: on peut afficher d'où vient l'info
        # print("\n--- Sources ---")
        # for doc in response['context']:
        #     print(f" - {doc.metadata.get('source', 'Inconnu')}")

if __name__ == "__main__":
    main()
