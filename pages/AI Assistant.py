import streamlit as st
from utils import get_gemini_response  # Import the function from your utils file

# --- Custom CSS for "Flashy" Look ---
st.markdown("""
<style>
    /* Main app background */
    .stApp {
        background: #0e1117; /* Dark background */
    }

    /* Increase caption font size */
    [data-testid="stCaptionContainer"] {
        font-size: 1.1em !important;
    }

    /* Chat message containers */
    [data-testid="stChatMessage"] {
        border-radius: 0px; /* Sharp corners for messages */
        margin-bottom: 10px;
        padding: 16px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        animation: fadeIn 0.5s ease-in-out;
    }

    /* User message styling for dark theme */
    .st-emotion-cache-1c7y2kd {
        background-color: #262730; /* Slightly lighter background for user message */
    }

    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p {
        color: #FFFFFF; /* White text for user */
    }

    /* Assistant message */
    [data-testid="stChatMessage"]:has([data-testid="stMarkdownContainer"] p) {
        background: linear-gradient(135deg, #6e45e2 0%, #88d3ce 100%);
        color: white; /* White text for assistant */
    }
    
    [data-testid="stChatMessage"]:has([data-testid="stMarkdownContainer"] p) p {
        color: white; /* Ensure assistant text is white */
    }

    /* Chat input box */
    [data-testid="stChatInput"] {
        border: 0px solid #6e45e2;
        background-color: #0e1117;
        border-radius: 2px;
    }

    /* Fade-in animation for new messages */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
</style>
""", unsafe_allow_html=True)


# --- Page Configuration ---
st.set_page_config(
    page_title="NYC City 360",
    page_icon="✨",
    layout="centered"
)

# --- App Title & Caption ---
st.title("NYC City 360 Assistant")
st.caption("Welcome to your NYC City 360 Assistant, the all-in-one interactive chatbot for navigating the five boroughs. Powered by the speed of Google's Gemini, this tool provides a comprehensive, 360-degree view of the city in real time. Get instant, streaming answers on weather, air quality, traffic conditions, public safety, and more. Our assistant is strictly focused only on New York City, guaranteeing you receive the most relevant, local information. If it's not about NYC, we won't answer it. Ask anything about life in the city and get an immediate, focused response.")


# --- Initialize Session State & Add Default Greeting ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Add a default greeting if the chat is empty
if not st.session_state.messages:
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "Hello! I'm your dedicated NYC assistant. Ask me anything about traffic, weather, or life in the five boroughs."
    })

# --- Display Chat History ---
for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "✨"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# --- Chat Input and Response Logic ---
if prompt := st.chat_input("Ask about NYC..."):
    
    # 1. Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 2. Display user message
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    
    # 3. Get and display bot response (streaming)
    with st.chat_message("assistant", avatar="✨"):
        
        # Prepare the history for the API call
        history_for_api = [msg for msg in st.session_state.messages]
        
        # Call the streaming function and display the response
        response_stream = get_gemini_response(prompt, history=history_for_api)
        
        # st.write_stream is the key to the "live" typing effect
        full_response = st.write_stream(response_stream)
    
    # 4. Add the full bot response to history
    st.session_state.messages.append({"role": "assistant", "content": full_response})