import os
from openai import OpenAI
from dotenv import load_dotenv

# ------------------------------------------------------------------------
# Load Environment Variables
# ------------------------------------------------------------------------
load_dotenv()

# --- LLM Configuration ---
LLM_PROVIDER_NAME = os.getenv("LLM_PROVIDER_NAME", "Groq")
API_KEY = os.getenv(f"{LLM_PROVIDER_NAME.upper()}_API_KEY")

if LLM_PROVIDER_NAME.lower() == "groq":
    BASE_URL = "https://api.groq.com/openai/v1"
    MODEL_NAME = "llama-3.1-8b-instant"
else:
    BASE_URL = "https://api.openai.com/v1"
    MODEL_NAME = "gpt-4-turbo"

# ------------------------------------------------------------------------
# TREATMENT KNOWLEDGE BASE (RAG CONTEXT)
# Matches your 31 DISEASE_CLASSES exactly
# ------------------------------------------------------------------------

TREATMENT_DOCUMENTS = {
    "Apple_Black_rot": 
        "Treatment: Apply fungicides such as Captan or Thiophanate-methyl at bloom and petal-fall. Cultural: Remove mummified fruits and prune dead wood. Ensure good air circulation.",
    
    "Apple_scab": 
        "Treatment: Use Mancozeb or Captan fungicide at early leaf emergence. Cultural: Remove fallen leaves and avoid overhead watering. Use resistant varieties when possible.",

    "Apple_Cedar_apple_rust": 
        "Treatment: Apply Myclobutanil or Propiconazole at early leaf stage. Cultural: Remove nearby juniper trees that host rust spores.",

    "Apple_healthy": 
        "Cultural: Maintain balanced fertilization, prune regularly, and spray neem oil every 2 weeks as preventive pest control.",

    "Banana_Panama": 
        "CURE IS NONE. This is Fusarium wilt. Cultural: Destroy infected plants and avoid replanting bananas in the same soil for 5 years. Use resistant varieties like 'Gros Michel'.",

    "Banana_Fusarium_wilt": 
        "CURE IS NONE. Remove infected plants, sterilize soil with lime, and improve drainage. Use resistant cultivars such as 'Cavendish'.",

    "Banana_Sigatoka": 
        "Treatment: Spray Mancozeb or Propiconazole weekly during infection period. Cultural: Prune lower leaves and increase airflow between plants.",

    "Banana_Healthy": 
        "Cultural: Maintain spacing, good drainage, and regular potassium fertilization. Apply Trichoderma-based biocontrol for root health.",

    "Cauliflower_Black_Rot": 
        "Treatment: No chemical cure once infected. Prevent by using hot-water-treated seeds. Cultural: Avoid overhead watering and rotate crops every 3 years.",

    "Cauliflower_Bacterial_spot_rot": 
        "Treatment: Copper oxychloride or Streptocycline spray at early spotting. Cultural: Use clean seed and maintain field hygiene.",

    "Cauliflower_Downy_Mildew": 
        "Treatment: Apply Metalaxyl or Mancozeb at first symptom. Cultural: Maintain low humidity and ensure good spacing.",

    "Cauliflower_Healthy": 
        "Cultural: Maintain 6.5 pH soil, adequate nitrogen, and consistent watering. Use neem-based sprays preventively.",

    "Corn_(maize)_Cercospora_leaf_spot": 
        "Treatment: Apply Mancozeb or Azoxystrobin. Cultural: Rotate with legumes and use resistant maize hybrids.",

    "Corn_(maize)_Northern_Leaf_Blight": 
        "Treatment: Use Propiconazole or Mancozeb spray. Cultural: Avoid monocropping and ensure residue management.",

    "Corn_(maize)_Common_rust": 
        "Treatment: Apply Triazole fungicides at first pustule appearance. Cultural: Grow rust-resistant hybrids and irrigate properly.",

    "Corn_(maize)_healthy": 
        "Cultural: Use disease-free certified seeds, balanced fertilization, and pest monitoring weekly.",

    "Grape_Black_rot": 
        "Treatment: Use Captan or Myclobutanil spray at pre-bloom and post-bloom. Cultural: Prune infected vines and avoid leaf wetness.",

    "Grape_Esca_(Black_Measles)": 
        "No chemical cure. Cultural: Prune infected vines below affected area, disinfect tools, and apply Trichoderma biofungicide to wounds.",

    "Grape_Leaf_blight_(Isariopsis_Leaf_Spot)": 
        "Treatment: Spray Mancozeb or Copper oxychloride. Cultural: Avoid excessive nitrogen and remove infected leaves.",

    "Grape_healthy": 
        "Cultural: Maintain canopy airflow, proper irrigation, and apply sulfur or neem oil preventively.",

    "Mango_Gall_Midge": 
        "Treatment: Spray Imidacloprid or Lambda-cyhalothrin at flowering. Cultural: Remove inflorescences showing galls. Plow under fallen debris.",

    "Mango_Anthracnose": 
        "Treatment: Apply Carbendazim or Copper oxychloride during flowering and fruit set. Cultural: Prune dense canopies and ensure air circulation.",

    "Mango_Powdery Mildew": 
        "Treatment: Apply wettable sulfur or Triazole fungicides early. Cultural: Remove infected inflorescences and avoid overhead irrigation.",

    "Mango_Healthy": 
        "Cultural: Apply balanced fertilizer, prune after harvest, and use organic compost and neem sprays monthly.",

    "Potato_Early_blight": 
        "Treatment: Mancozeb or Azoxystrobin every 10 days. Cultural: Avoid overhead watering and rotate with cereals.",

    "Potato_Late_blight": 
        "Treatment: Metalaxyl + Mancozeb alternately. Cultural: Destroy infected foliage immediately and avoid waterlogging.",

    "Potato_healthy": 
        "Cultural: Use certified seed potatoes, maintain spacing, and apply neem oil weekly as preventive measure.",

    "Tomato_Bacterial_spot": 
        "Treatment: Copper hydroxide spray. Cultural: Avoid working in wet fields, disinfect tools, and rotate crops yearly.",

    "Tomato_Two_spotted_Spider_mites": 
        "Treatment: Use Abamectin or neem oil spray. Cultural: Increase humidity slightly and remove heavily infested leaves.",

    "Tomato_Early_blight": 
        "Treatment: Chlorothalonil or Mancozeb every 7 days. Cultural: Remove old leaves and mulch to prevent soil splash.",

    "Tomato_healthy": 
        "Cultural: Use disease-free seedlings, balanced nutrients, and apply neem oil fortnightly as preventive care.",
}

# ------------------------------------------------------------------------
# Helper Function – Retrieve Context Based on Severity
# ------------------------------------------------------------------------
def get_treatment_context(disease_name: str, severity: int) -> str:
    base_treatment = TREATMENT_DOCUMENTS.get(
        disease_name,
        "No verified treatment data available. Please consult a local agricultural officer."
    )

    if severity in [1, 2]:
        severity_note = "The infection is mild. Focus on sanitation and organic treatments."
    elif severity in [3, 4]:
        severity_note = "The infection is moderate. Begin recommended fungicide or insecticide treatments immediately."
    elif severity == 5:
        severity_note = "The infection is severe. Immediate professional help and lab diagnosis are required."
    else:
        severity_note = "Invalid severity level (should be 1–5)."

    return f"Disease: {disease_name}. Severity: {severity}/5. Details: {base_treatment} Additional Instructions: {severity_note}"

# ------------------------------------------------------------------------
# Main Function – Generate Recommendation via LLM
# ------------------------------------------------------------------------
def generate_recommendation(disease_name: str, severity: int, language_code: str = "en") -> str:
    """Generate localized, farmer-friendly recommendation using Groq/OpenAI."""
    if not API_KEY:
        return f"⚠️ Missing API key for {LLM_PROVIDER_NAME}. Please set `{LLM_PROVIDER_NAME.upper()}_API_KEY` in .env."

    try:
        client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
        rag_context = get_treatment_context(disease_name, severity)

        system_prompt = f"""
        You are SmartCropDoc-AI, a professional agricultural assistant for farmers.
        Your job: generate easy-to-understand, localized (language = {language_code}) disease management advice.

        RULES:
        1. Base the answer strictly on the CONTEXT provided below.
        2. If severity = 5, return ONLY:
           🚨 "This is a severe infection. Immediate professional lab diagnosis is required. Please check the Nearest Labs section for contact information."
        3. Divide the output into:
           - **Sanitation / Cultural Practices**
           - **Treatment / Pesticide Recommendation**
           - **Safety Note**
        4. Keep the tone simple and instructive for farmers.

        CONTEXT:
        ---
        {rag_context}
        ---
        """

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Give treatment plan for {disease_name} (Severity {severity}) translated to {language_code}."}
            ],
            temperature=0.3,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"❌ Error: {str(e)}. Please verify your internet connection or API configuration."

# ------------------------------------------------------------------------
# Example Debug Run (Uncomment to test)
# ------------------------------------------------------------------------
# if __name__ == "__main__":
#     print(generate_recommendation("Tomato_Early_blight", 3, "en"))
