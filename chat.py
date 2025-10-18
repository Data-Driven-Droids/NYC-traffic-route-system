import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Dict, Optional

def get_nyc_demographics() -> Optional[Dict[str, str]]:
    """
    Calls the Gemini 1.5 Flash model to get the latest population and birth rate for NYC.

    This function securely retrieves a Google API key from environment variables,
    sends a structured prompt to the Gemini API, and parses the JSON response.

    Returns:
        Optional[Dict[str, str]]: A dictionary with 'population' and 'birth_rate'
        if successful, otherwise None.
    """
    # Load environment variables from a .env file
    load_dotenv()
    
    # 1. Configure the Gemini API
    try:
        api_key = os.environ["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
    except KeyError:
        print("🚨 ERROR: GOOGLE_API_KEY not found. Please set it in your .env file.")
        return None

    # 2. Craft a clear, structured prompt
    prompt = """
    What is the latest estimated population and the latest reported birth rate for New York City?
    Provide the answer in a strict JSON format with two keys: "population" and "birth_rate".
    
    For example:
    {
      "population": "8.5 million (as of 2023)",
      "birth_rate": "11.2 births per 1,000 people (as of 2022)"
    }
    """
    
    # 3. Call the Gemini 1.5 Flash model
    try:
        print("Calling Gemini 1.5 Flash to fetch NYC demographics...")
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        
        # Clean up the response to extract only the JSON part
        response_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        
        # 4. Parse the JSON response
        data = json.loads(response_text)
        
        # Validate that the expected keys are in the response
        if "population" in data and "birth_rate" in data:
            print("✅ Successfully fetched and parsed data.")
            return data
        else:
            print("⚠️ ERROR: The model response was missing the required 'population' or 'birth_rate' keys.")
            return None

    except json.JSONDecodeError:
        print(f"❌ ERROR: Failed to decode JSON from the model's response. Response was:\n{response_text}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

# --- Example of how to use the function ---
if __name__ == "__main__":
    nyc_data = get_nyc_demographics()
    
    if nyc_data:
        print("\n--- New York City Demographics ---")
        print(f"🏙️ Population: {nyc_data['population']}")
        print(f"👶 Birth Rate: {nyc_data['birth_rate']}")
        print("---------------------------------")
    else:
        print("\nCould not retrieve NYC demographic data.")