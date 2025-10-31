import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables for API keys
load_dotenv() 

# --- LLM Configuration (Flexible Client Setup) ---
LLM_PROVIDER_NAME = os.getenv("LLM_PROVIDER_NAME", "Groq")
API_KEY = os.getenv(f"{LLM_PROVIDER_NAME.upper()}_API_KEY")

# Set base URL and model based on provider
if LLM_PROVIDER_NAME.lower() == "groq":
    BASE_URL = "https://api.groq.com/openai/v1"
    # Using the fast, capable Llama 3.1 8B model as planned
    MODEL_NAME = "llama-3.1-8b-instant" 

TREATMENT_DOCUMENTS = {
    # ------------------------------------------------------------------------
    # --- CORE ENTRIES (Ensure 31 unique entries are present) ---
    # ------------------------------------------------------------------------
    "Healthy": 
        "Cultural: Maintain optimal soil moisture and nutrient balance. Prevention: Monitor weekly for pests. General: Apply neem oil every two weeks.",
    
    # --- Example 1 (Tomato Disease - Use your exact class name) ---
    "Tomato Leaf Mold": 
        "Treatment: Apply protective fungicides like Chlorothalonil or Mancozeb. Cultural: **CRITICAL: Increase ventilation**, reduce humidity to below 85%, space plants farther apart, and water at the base, not overhead.",
        
    # --- Example 2 (Potato Disease - Use your exact class name) ---
    "Potato Late Blight": 
        "Treatment: **Systemic fungicides** (metalaxyl) immediately. Protective: Apply **Copper products** (organic). Cultural: Destroy all infected foliage/cull piles. Use resistant varieties next season.",

    # --- Example 3 (Viral/Incurable Disease - Use your exact class name) ---
    "Tomato Yellow Leaf Curl Virus": 
        "CURE IS NONE. The plant cannot be cured. Action: **IMMEDIATELY remove and destroy** the infected plant. Control the vector (silverleaf whitefly) with chemical rotation (e.g., neonicotinoids).",
        
    # ------------------------------------------------------------------------
    # Placeholder for the remaining 27 diseases from your dataset
    # You must insert your specific data here:
    # "Your_Disease_Name_X": "Treatment: [Chemical/Organic]. Cultural: [Sanitation/Prevention].",
    # ... CONTINUE ADDING ALL 31 DISEASE ENTRIES HERE ...
}

# --- RAG Retrieval and Prompt Generation Functions ---

def get_treatment_context(disease_name: str, severity: int) -> str:
    """Retrieves and augments context for the LLM based on disease and severity."""
    base_treatment = TREATMENT_DOCUMENTS.get(disease_name, 
                                            "No verified treatment data. Seek local agricultural extension advice.")
    
    severity_note = ""
    if 1 <= severity <= 2:
        severity_note = "The infection is **minor/early**. Focus on organic methods, sanitation, and monitoring."
    elif 3 <= severity <= 4:
        severity_note = "The infection is **established**. Immediate and consistent application of the recommended chemical or organic treatment is required."
    elif severity == 5:
        severity_note = "The infection is **CRITICAL/SEVERE**. The critical rule MUST be returned."
        
    return f"Disease: {disease_name}. Severity: Level {severity}/5. Treatment Data: {base_treatment}. Instructions: {severity_note}"

def generate_recommendation(disease_name: str, severity: int, language_code: str = 'en') -> str:
    """Generates a farmer-friendly, translated recommendation using the LLM and RAG context."""
    if not API_KEY:
        return f"LLM service ({LLM_PROVIDER_NAME}) API Key missing. Please set the {LLM_PROVIDER_NAME.upper()}_API_KEY in .env."

    try:
        # Initialize client using flexible configuration
        client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
        rag_context = get_treatment_context(disease_name, severity)
        
        # --- Prompt Engineering: System Instructions ---
        system_prompt = f"""
        You are SmartCropDoc-AI, an expert agricultural advisor. Your response must be farmer-friendly and translated entirely into the language code: **{language_code}**.
        
        RULES:
        1. Base the answer **only** on the CONTEXT provided. Do not use external knowledge.
        2. If the severity is Level 5, the response MUST ONLY state: '🚨 This is a severe infection. Immediate professional lab diagnosis is required. Please check the Nearest Labs section for contact information.'
        3. Structure the response into a clear section for **Sanitation/Cultural Advice** and another for **Treatment/Pesticide**.
        4. Include a general safety precaution (e.g., wear gloves/mask).

        CONTEXT:
        ---
        {rag_context}
        ---
        """
        
        # --- LLM Call ---
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Provide the treatment plan for {disease_name} (Severity {severity}) in language code {language_code}."}
            ],
            temperature=0.3, # Low temperature for factual, reliable output
        )

        return response.choices[0].message.content
        
    except Exception as e:
        print(f"LLM API Error: {e}")
        return f"Could not connect to the recommendation engine ({LLM_PROVIDER_NAME}). Check API key/connection."