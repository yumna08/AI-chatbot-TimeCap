from typing import Optional
import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)


def generate_caption(image_path: str) -> Optional[str]:
    """Generate a short, warm one-sentence caption for the photo at image_path.
    Returns the caption string, or None on error.
    """
    try:
        # Read the image bytes (the model supports multimodal input)
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        # The user instruction for the model
        user_template = (
            "Write a single warm, reflective one-sentence caption for this photo, "
            "as if describing it to someone looking back at it as a memory. Do not "
            "describe technical details, just the feeling/moment. Keep it under 25 words."
        )

        prompt = ChatPromptTemplate.from_template("{instruction}")

        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)

        chain = prompt | llm

        response = chain.invoke({
            "instruction": user_template,
            "image": image_bytes,
        })

        caption = None
        if response and getattr(response, "content", None):
            caption = response.content.strip()

        return caption
    except Exception as e:
        logger.exception(f"Failed to generate caption for {image_path}: {e}")
        return None
