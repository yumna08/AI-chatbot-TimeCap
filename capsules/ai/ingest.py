import os
from django.conf import settings
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

def get_vectorstore(user_id):
    persist_directory = os.path.join(settings.BASE_DIR, 'chroma_db')
    collection_name = f"user_{user_id}"
    
    # OpenAIEmbeddings automatically reads OPENAI_API_KEY from the environment
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    
    return Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=persist_directory
    )

def embed_capsule(capsule):
    metadata = {
        "capsule_id": capsule.id,
        "user_id": capsule.user_id,
        "mood": capsule.mood,
        "created_at": capsule.created_at.isoformat(),
        "unlock_date": capsule.unlock_date.isoformat(),
        "title": capsule.title
    }
    # Chroma doesn't like empty lists in metadata, and sometimes doesn't like lists at all depending on version.
    # Joining tags as string or using the list if not empty.
    if capsule.tags:
        metadata["tags"] = capsule.tags
        
    doc = Document(
        page_content=capsule.content,
        metadata=metadata
    )
    
    vectorstore = get_vectorstore(capsule.user_id)
    vectorstore.add_documents(documents=[doc], ids=[str(capsule.id)])

def reindex_user(user):
    vectorstore = get_vectorstore(user.id)
    
    # Get all capsules for the user
    capsules = user.capsules.all()
    
    # Chroma doesn't have a simple 'clear' per collection through the LangChain wrapper 
    # without deleting the collection itself, so we can delete the collection and recreate it.
    try:
        vectorstore.delete_collection()
    except Exception:
        pass
        
    # Recreate the vectorstore
    vectorstore = get_vectorstore(user.id)
    
    if capsules.exists():
        docs = []
        ids = []
        for capsule in capsules:
            metadata = {
                "capsule_id": capsule.id,
                "user_id": capsule.user_id,
                "mood": capsule.mood,
                "created_at": capsule.created_at.isoformat(),
                "unlock_date": capsule.unlock_date.isoformat(),
                "title": capsule.title
            }
            if capsule.tags:
                metadata["tags"] = capsule.tags
                
            docs.append(Document(
                page_content=capsule.content,
                metadata=metadata
            ))
            ids.append(str(capsule.id))
        
        vectorstore.add_documents(documents=docs, ids=ids)
