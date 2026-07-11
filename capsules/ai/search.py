from django.utils import timezone
from dateutil.parser import parse
from .ingest import get_vectorstore

def smart_search(user, query: str, k=8):
    vectorstore = get_vectorstore(user.id)
    results = vectorstore.similarity_search(query, k=k)
    
    now = timezone.now()
    filtered_results = []
    
    for doc in results:
        metadata = doc.metadata
        unlock_date_str = metadata.get('unlock_date')
        
        if not unlock_date_str:
            continue
            
        unlock_date = parse(unlock_date_str)
        
        if now >= unlock_date:
            content = doc.page_content
            truncated_content = content[:300] + ('...' if len(content) > 300 else '')
            
            filtered_results.append({
                "capsule_id": metadata.get("capsule_id"),
                "title": metadata.get("title"),
                "content": truncated_content,
                "mood": metadata.get("mood"),
                "created_at": metadata.get("created_at"),
                "unlock_date": unlock_date_str,
                "tags": metadata.get("tags", []),
            })
            
    return filtered_results
