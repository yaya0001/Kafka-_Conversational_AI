import streamlit as st
from testing import kafka_rag_answer

st.set_page_config(
    page_title="Kafka Conversational AI",
    page_icon="🖋️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    /* Main title styling */
    .main-title {
        font-size: 2.5rem;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 0.5rem;
        border-bottom: 3px solid #3498db;
        padding-bottom: 0.5rem;
    }
    
    /* Chat message styling */
    .stChatMessage {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    /* User message specific */
    .stChatMessage[data-testid="user-message"] {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    
    /* Assistant message specific */
    .stChatMessage[data-testid="assistant-message"] {
        background-color: #f5f5f5;
        border-left: 4px solid #757575;
    }
    
    /* Source card styling */
    .source-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Metadata badge */
    .metadata-badge {
        display: inline-block;
        background-color: #e8f5e9;
        color: #2e7d32;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
        margin: 0.25rem;
    }
    
    /* Stats display */
    .stat-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    /* Clear chat button */
    .stButton button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "message_sources" not in st.session_state:
    st.session_state.message_sources = {}  # Dictionary: message_index -> sources

if "message_count" not in st.session_state:
    st.session_state.message_count = 0

# Sidebar
with st.sidebar:
    st.markdown("### 🎭 About Kafka AI")
    st.markdown("""
    This AI simulates Franz Kafka's voice, personality, and worldview based on his:
    - Literary works (stories, novels)
    - Personal letters
    - Diaries and biographical material
    """)
    
    st.markdown("---")
    
    # Stats
    st.markdown("### 📊 Session Stats")
    st.metric("Messages", st.session_state.message_count)
    st.metric("Exchanges", len(st.session_state.chat_history) // 2)
    
    st.markdown("---")
    
    # Clear chat button
    if st.button("🗑️ Clear Conversation", type="secondary"):
        st.session_state.chat_history = []
        st.session_state.message_sources = {}
        st.session_state.message_count = 0
        st.rerun()
    
    st.markdown("---")
    
    # Example prompts
    st.markdown("### 💡 Try asking:")
    example_prompts = [
        "I feel trapped in my routine",
        "What happens to Gregor in Metamorphosis?",
        "Tell me about your relationship with your father",
        "What is the meaning of suffering?",
        "How do you deal with loneliness?"
    ]
    
    for prompt in example_prompts:
        if st.button(f"💬 {prompt}", key=f"example_{prompt[:20]}"):
            st.session_state.pending_input = prompt
            st.rerun()

# Main content
st.markdown('<h1 class="main-title">🖋️ Kafka Conversational AI</h1>', unsafe_allow_html=True)

# Create two columns
col1, col2 = st.columns([2.5, 1.5])

# ---------------- LEFT COLUMN (CHAT) ----------------
with col1:
    st.markdown("### 💭 Conversation")
    
    # Display chat history
    if not st.session_state.chat_history:
        st.info("👋 Start a conversation with Kafka. Ask about his works, his life, or share your thoughts...")
    
    for i, message in enumerate(st.session_state.chat_history):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Handle pending input from sidebar examples
    if hasattr(st.session_state, 'pending_input'):
        user_input = st.session_state.pending_input
        delattr(st.session_state, 'pending_input')
    else:
        user_input = st.chat_input("Ask Kafka something...", key="main_input")
    
    # Process user input
    if user_input:
        # Add user message to history
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Convert chat history to memory format (exclude current message)
        memory = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in st.session_state.chat_history[:-1]
        ]
        
        # Get response with spinner
        with st.spinner("🤔 Kafka is contemplating..."):
            try:
                answer, sources = kafka_rag_answer(user_input, memory)
                
                # Add assistant response to history
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": answer
                })
                
                # Store sources for THIS SPECIFIC message
                message_index = len(st.session_state.chat_history) - 1
                st.session_state.message_sources[message_index] = sources
                
                # Update message count
                st.session_state.message_count += 2
                
                # Rerun to display new messages
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.error("Please check that Ollama is running and models are loaded.")

# ---------------- RIGHT COLUMN (SOURCES) ----------------
with col2:
    st.markdown("### 📚 Source Context")
    
    # Find the most recent assistant message index
    assistant_indices = [
        i for i, msg in enumerate(st.session_state.chat_history) 
        if msg["role"] == "assistant"
    ]
    
    # Display sources for the MOST RECENT assistant message
    if assistant_indices:
        latest_assistant_idx = assistant_indices[-1]
        
        if latest_assistant_idx in st.session_state.message_sources:
            current_sources = st.session_state.message_sources[latest_assistant_idx]
            st.success(f"✓ {len(current_sources)} sources retrieved")
            
            for i, src in enumerate(current_sources):
                with st.expander(f"📄 Source {i+1}: {src['metadata'].get('work', 'Unknown')}", expanded=False):
                    # Display metadata as badges
                    st.markdown("**Metadata:**")
                    metadata = src['metadata']
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown(f"**Author:** {metadata.get('author', 'N/A')}")
                        st.markdown(f"**Type:** {metadata.get('type', 'N/A')}")
                    with col_b:
                        st.markdown(f"**Work:** {metadata.get('work', 'N/A')}")
                        st.markdown(f"**Chunk:** {metadata.get('chunk_id', 'N/A')}")
                    
                    st.markdown("---")
                    
                    # Display full content
                    st.markdown("**Content:**")
                    content = src['content']
                    st.text_area(
                        "Retrieved text",
                        value=content,
                        height=250,
                        key=f"source_msg{latest_assistant_idx}_chunk{i}",  # Unique key per message
                        disabled=True,
                        label_visibility="collapsed"
                    )
        else:
            st.warning("⚠️ No sources found for the last message")
    else:
        st.info("📭 Sources will appear here after asking a question.")
        st.markdown("""
        Sources show which parts of Kafka's works, letters, or biographical material 
        were used to generate each response.
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #7f8c8d; font-size: 0.9rem;'>
    <p>🖋️ Built with Langchain + Ollama + Chroma | Simulating Franz Kafka's voice and perspective</p>
    <p><em>"I write differently from what I speak, I speak differently from what I think..."</em></p>
</div>
""", unsafe_allow_html=True)