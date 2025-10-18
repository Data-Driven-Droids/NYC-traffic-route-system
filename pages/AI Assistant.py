import streamlit as st
from utils import stream_gemini_response  # Async Gemini utility

# --- Page Configuration ---
# This must be the first Streamlit command in your script
st.set_page_config(
    page_title="NYC City 360",
    page_icon="✨",
    layout="centered"
)

# --- Custom CSS for a Polished Look ---
st.markdown("""
<style>
    /* Main app background */
    .stApp {
        background-color: #0e1117;
    }

    /* Chat message containers */
    [data-testid="stChatMessage"] {
        border-radius: 12px; /* Softer corners */
        margin-bottom: 1rem;
        padding: 1rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        animation: fadeIn 0.5s ease-in-out;
        width: 90%; /* Prevent messages from spanning the full width */
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* --- STABLE SELECTORS FOR USER AND ASSISTANT MESSAGES --- */
    /* We use :has() to select the parent container based on a stable child element */

    /* User message styling */
    [data-testid="stChatMessage"]:has(.st-chat-message-container.user) {
        background-color: #262730;
        margin-left: auto; /* Align to the right */
        margin-right: 0;
    }

    /* Assistant message styling */
    [data-testid="stChatMessage"]:has(.st-chat-message-container.assistant) {
        background: linear-gradient(135deg, #6e45e2 0%, #88d3ce 100%);
        margin-left: 0; /* Align to the left */
        margin-right: auto;
    }

    /* Ensure text inside all markdown containers is white and readable */
    [data-testid="stMarkdownContainer"] p {
        color: #FFFFFF !important;
    }

    /* --- MODIFICATION: Increase caption font size --- */
    [data-testid="stCaptionContainer"] p {
        font-size: 1.3em !important; /* Or any size you prefer, e.g., 16px */
        color: rgba(255, 255, 255, 0.75) !important; /* Adjust color for readability */
    }
    
    /* Chat input box */
    [data-testid="stChatInput"] {
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        background-color: #0e1117;
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


# --- App Title & Caption ---
st.title("NYC City 360 Assistant ✨")
st.caption("Welcome to your NYC City 360 Assistant, the all-in-one interactive chatbot for navigating the five boroughs. Powered by the speed of Google's Gemini, this tool provides a comprehensive, 360-degree view of the city in real time. Get instant, streaming answers on weather, air quality, traffic conditions, public safety, and more. Our assistant is strictly focused only on New York City, guaranteeing you receive the most relevant, local information. If it's not about NYC, we won't answer it. Ask anything about life in the city and get an immediate, focused response.")

st.sidebar.title("NYC 360 AI Assistant")

# --- Initialize session state ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hello! How can I help you navigate NYC today? Ask me anything about traffic, weather, or local information."
        }
    ]

# --- Display chat history ---
for message in st.session_state.messages:
    # Use role to determine the avatar and styling
    avatar = "👤" if message["role"] == "user" else "✨"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# --- Chat Input and Response Streaming ---
if prompt := st.chat_input("Ask about traffic, weather, or safety in NYC..."):
    # 1. Add and display the user's message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # 2. Stream and display the assistant's response
    with st.chat_message("assistant", avatar="✨"):
        # Use st.write_stream for a cleaner, more robust implementation
        # This works with both sync and async generators
        full_response = st.write_stream(stream_gemini_response(prompt, st.session_state.messages))

    # 3. Add the complete assistant response to the session state
    st.session_state.messages.append({"role": "assistant", "content": full_response})