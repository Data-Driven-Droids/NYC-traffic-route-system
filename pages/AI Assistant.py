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
        background: linear-gradient(135deg, #0e1117 0%, #1a1d29 100%);
    }

    /* Chat message containers */
    [data-testid="stChatMessage"] {
        border-radius: 16px;
        margin-bottom: 1rem;
        padding: 1.2rem;
        box-shadow: 0 8px 24px rgba(0,0,0,0.3);
        animation: fadeIn 0.5s ease-in-out;
        width: 90%;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }

    /* User message styling */
    [data-testid="stChatMessage"]:has(.st-chat-message-container.user) {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%);
        margin-left: auto;
        margin-right: 0;
        border-left: 4px solid #6366f1;
    }

    /* Assistant message styling */
    [data-testid="stChatMessage"]:has(.st-chat-message-container.assistant) {
        background: linear-gradient(135deg, rgba(110, 69, 226, 0.3) 0%, rgba(136, 211, 206, 0.3) 100%);
        margin-left: 0;
        margin-right: auto;
        border-left: 4px solid #88d3ce;
    }

    /* Ensure text inside all markdown containers is white and readable */
    [data-testid="stMarkdownContainer"] p {
        color: #FFFFFF !important;
    }

    /* Caption styling */
    [data-testid="stCaptionContainer"] p {
        font-size: 1.1em !important;
        color: rgba(255, 255, 255, 0.75) !important;
        line-height: 1.6 !important;
    }
    
    /* Chat input box */
    [data-testid="stChatInput"] {
        border-top: 2px solid rgba(136, 211, 206, 0.3);
        background-color: #1a1d29;
        border-radius: 12px;
    }

    /* Header decoration */
    .ai-header {
        background: linear-gradient(135deg, #6e45e2 0%, #88d3ce 100%);
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 40px rgba(110, 69, 226, 0.3);
        border: 2px solid rgba(136, 211, 206, 0.4);
    }
    
    .ai-header h1 {
        color: white;
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    .ai-header p {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.1rem;
        margin-top: 0.5rem;
        line-height: 1.6;
    }
    
    .feature-icons {
        display: flex;
        justify-content: center;
        gap: 2rem;
        margin-top: 1.5rem;
        flex-wrap: wrap;
    }
    
    .feature-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.5rem;
        padding: 1rem;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        min-width: 100px;
        backdrop-filter: blur(10px);
        transition: transform 0.3s ease;
    }
    
    .feature-item:hover {
        transform: translateY(-5px);
        background: rgba(255, 255, 255, 0.15);
    }
    
    .feature-icon {
        font-size: 2rem;
    }
    
    .feature-label {
        color: white;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    /* Pulse animation for AI icon */
    @keyframes pulse {
        0%, 100% {
            transform: scale(1);
            opacity: 1;
        }
        50% {
            transform: scale(1.05);
            opacity: 0.8;
        }
    }
    
    .ai-icon-pulse {
        animation: pulse 2s infinite;
        display: inline-block;
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
    
    /* Typing indicator */
    .typing-indicator {
        display: inline-flex;
        gap: 4px;
    }
    
    .typing-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #88d3ce;
        animation: typing 1.4s infinite;
    }
    
    .typing-dot:nth-child(2) {
        animation-delay: 0.2s;
    }
    
    .typing-dot:nth-child(3) {
        animation-delay: 0.4s;
    }
    
    @keyframes typing {
        0%, 60%, 100% {
            transform: translateY(0);
        }
        30% {
            transform: translateY(-10px);
        }
    }
</style>
""", unsafe_allow_html=True)


# --- Decorative Header with Icons ---
st.markdown("""<div class="ai-header"><h1><span class="ai-icon-pulse">🤖</span> NYC City 360 AI Assistant <span class="ai-icon-pulse">✨</span></h1><p>Your intelligent companion for navigating the five boroughs. Powered by Google Gemini for instant, real-time insights about New York City.</p><div class="feature-icons"><div class="feature-item"><div class="feature-icon">🌤️</div><div class="feature-label">Weather</div></div><div class="feature-item"><div class="feature-icon">🚦</div><div class="feature-label">Traffic</div></div><div class="feature-item"><div class="feature-icon">🏙️</div><div class="feature-label">City Info</div></div><div class="feature-item"><div class="feature-icon">🚨</div><div class="feature-label">Safety</div></div><div class="feature-item"><div class="feature-icon">🗺️</div><div class="feature-label">Navigation</div></div></div></div>""", unsafe_allow_html=True)

st.sidebar.markdown("""### 🗽 NYC 360 AI Assistant

**What I can help with:**
- 🌤️ **Weather** - Current conditions & forecasts
- 🚦 **Traffic** - Real-time congestion updates
- 🏙️ **City Info** - Neighborhoods & attractions
- 🚨 **Safety** - Alerts & emergency info
- 🗺️ **Navigation** - Routes & directions

**Powered by:**
- ⚡ Google Gemini AI
- 🔄 Real-time data streams
- 🎯 NYC-focused responses only
""")

# --- Initialize session state ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "👋 **Hello! I'm your NYC City 360 AI Assistant.**\n\nI'm here to help you navigate the five boroughs with real-time information. You can ask me about:\n\n🌤️ **Weather** - Current conditions, forecasts, and alerts\n🚦 **Traffic** - Live congestion, incidents, and route planning\n🏙️ **City Information** - Neighborhoods, attractions, and local insights\n🚨 **Safety** - Emergency alerts and public safety updates\n🗺️ **Navigation** - Directions and transportation options\n\nWhat would you like to know about NYC today?"
        }
    ]

# --- Display chat history ---
for message in st.session_state.messages:
    # Use role to determine the avatar and styling
    avatar = "👨‍💼" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# --- Chat Input and Response Streaming ---
if prompt := st.chat_input("💬 Ask me anything about NYC - traffic, weather, safety, or city info..."):
    # 1. Add and display the user's message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👨‍💼"):
        st.markdown(prompt)

    # 2. Stream and display the assistant's response
    with st.chat_message("assistant", avatar="🤖"):
        # Use st.write_stream for a cleaner, more robust implementation
        # This works with both sync and async generators
        full_response = st.write_stream(stream_gemini_response(prompt, st.session_state.messages))

    # 3. Add the complete assistant response to the session state
    st.session_state.messages.append({"role": "assistant", "content": full_response})