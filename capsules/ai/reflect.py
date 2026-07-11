from django.utils import timezone
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from capsules.models import Capsule
from .search import smart_search

def generate_reflection(user, question: str):
    # Escape question immediately
    escaped_question = question.replace("{", "{{").replace("}", "}}")
    
    # 1. Retrieve relevant capsules via smart_search
    search_results = smart_search(user, question, k=10)
    
    capsules_data = []
    seen_ids = set()
    
    for res in search_results:
        # Escape content from smart_search
        if res.get("content"):
            res["content"] = res["content"].replace("{", "{{").replace("}", "}}")
        capsules_data.append(res)
        seen_ids.add(res["capsule_id"])
        
    # If fewer than 3 results, backfill with recent unlocked capsules
    if len(capsules_data) < 3:
        recent_capsules = Capsule.objects.filter(
            user=user,
            unlock_date__lte=timezone.now()
        ).order_by('-unlock_date')[:10]
        
        for cap in recent_capsules:
            if cap.id not in seen_ids:
                content = cap.content
                truncated_content = content[:300] + ('...' if len(content) > 300 else '')
                # Escape literal curly braces
                escaped_content = truncated_content.replace("{", "{{").replace("}", "}}")
                capsules_data.append({
                    "capsule_id": cap.id,
                    "title": cap.title,
                    "content": escaped_content,
                    "mood": cap.mood,
                    "created_at": cap.created_at.isoformat(),
                    "unlock_date": cap.unlock_date.isoformat(),
                    "tags": cap.tags
                })
                seen_ids.add(cap.id)
                
    # Sort chronologically by created_at
    capsules_data.sort(key=lambda x: x["created_at"])
    
    # Format capsules for the prompt
    formatted_capsules_list = []
    for cap in capsules_data:
        formatted = f"[{cap['created_at']}, mood: {cap['mood']}] \"{cap['content']}\""
        formatted_capsules_list.append(formatted)
        
    capsules_formatted = "\n\n".join(formatted_capsules_list)
    
    # EXACT SYSTEM PROMPT
    system_prompt = """You are an AI companion helping {user_name} reflect on their own life, using
entries they wrote to their future self. You are NOT role-playing as them —
you are a warm, observant companion speaking TO them, referencing what past-them
wrote.

STRICT RULES:
1. Only reference facts and feelings actually present in the CAPSULES below.
   Never invent achievements, events, or emotions that weren't written.
2. When comparing past and present, be specific with dates ("Five years ago,
   on {{date}}, you wrote...") rather than vague ("a while back").
3. Frame any pattern or projection as an observation, never a guarantee. Use
   language like "it looks like," "you've consistently," "if this continues" —
   not "you will."
4. Keep tone warm and encouraging but grounded — avoid generic motivational-
   poster language. Let the specifics of what they wrote carry the emotional
   weight.
5. If asked something the capsules don't cover, say so honestly rather than
   filling the gap with generic advice.

RELEVANT CAPSULES (chronological):
{capsules_formatted}

QUESTION FROM {user_name}:
{question}

Respond in 3-6 sentences, referencing specific capsules by date where relevant."""

    prompt = ChatPromptTemplate.from_template(system_prompt)
    
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)
    
    chain = prompt | llm
    
    # Execute the chain
    response = chain.invoke({
        "user_name": user.username,
        "capsules_formatted": capsules_formatted,
        "question": escaped_question
    })
    
    # Return the reflection text and the list of capsule IDs that were provided to the LLM
    return {
        "reflection": response.content,
        "referenced_capsules": list(seen_ids)
    }
