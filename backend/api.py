import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

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

load_dotenv()

app = FastAPI(title="Assistant 2iE API")

# Autoriser le frontend (React/Vite) à communiquer avec l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Accepte toutes les origines pour le dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CHROMA_DB_DIR = "chroma_db"
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

class ChatRequest(BaseModel):
    message: str

# Variable globale pour stocker la chaîne RAG une fois chargée
rag_chain = None

@app.on_event("startup")
def init_assistant():
    global rag_chain
    print("Initialisation de l'API Assistant 2iE...")

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vectorstore = Chroma(
        persist_directory=CHROMA_DB_DIR, 
        embedding_function=embeddings
    )
    
    groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    llm = ChatGroq(model=groq_model, temperature=0.2)

    vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 8})
    
    # Chargement pour le BM25
    print("Chargement des documents locaux pour BM25 (Hybrid Search)...")
    pdf_files = glob.glob(f"docs/*.pdf")
    all_documents = []
    for pdf_file in pdf_files:
        try:
            md_text = pymupdf4llm.to_markdown(pdf_file)
            
            text_lower = md_text.lower()
            cycle_meta = "general"
            if "bachelor" in text_lower and "master" in text_lower:
                cycle_meta = "les_deux"
            elif "bachelor" in text_lower:
                cycle_meta = "bachelor"
            elif "master" in text_lower or "mastère" in text_lower:
                cycle_meta = "master"

            all_documents.append(Document(page_content=md_text, metadata={"source": pdf_file, "cycle": cycle_meta}))
        except Exception as e:
            print(f"Erreur avec le doc {pdf_file}: {e}")
        
    if all_documents:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=250, separators=["\n## ", "\n### ", "\n\n", "\n", " "])
        splits = text_splitter.split_documents(all_documents)
        
        bm25_retriever = BM25Retriever.from_documents(splits)
        bm25_retriever.k = 8
        
        hybrid_retriever = EnsembleRetriever(
            retrievers=[bm25_retriever, vector_retriever], weights=[0.5, 0.5]
        )
    else:
        # Fallback si aucun doc au démarrage: uniquement vectoriel
        hybrid_retriever = vector_retriever

    cross_encoder = HuggingFaceCrossEncoder(model_name="cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")
    compressor = CrossEncoderReranker(model=cross_encoder, top_n=4)
    
    retriever = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=hybrid_retriever
    )

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

    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    print("API opérationnelle et prête à recevoir des requêtes !")

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    if not rag_chain:
        return {"answer": "Erreur : L'assistant est toujours en cours de chargement (ou aucune donnée disponible). Veuillez patienter."}
    
    print(f"Nouvelle question reçue: {request.message}")
    response = rag_chain.invoke({"input": request.message})
    return {"answer": response["answer"]}

if __name__ == "__main__":
    # Lancement du serveur API FastAPI
    uvicorn.run(app, host="0.0.0.0", port=8000)
