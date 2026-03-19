import streamlit as st
import requests
import os
import json

# Configuration
st.set_page_config(
    page_title="AKA-ONE",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="expanded"
)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Custom CSS for "AKA-ONE" Premium Interface
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Inter:wght@300;400;600&display=swap');

    /* --- ANIMATED BACKGROUND --- */
    .stApp {
        background: linear-gradient(-45deg, #0f0c29, #302b63, #24243e, #000000);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
        color: #e0e6ed;
        font-family: 'Inter', sans-serif;
    }

    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* --- SIDEBAR GLASSMORPHISM --- */
    section[data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
    }
    
    /* Titles & Headers (Orbitron) */
    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif !important;
        background: -webkit-linear-gradient(45deg, #00f260, #0575E6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0px 0px 10px rgba(0, 242, 96, 0.3);
    }

    /* --- CHAT BUBBLES --- */
    .user-msg {
        background: linear-gradient(135deg, #00b09b, #96c93d);
        color: white;
        padding: 1.2rem;
        border-radius: 15px 15px 0 15px;
        box-shadow: 0 5px 15px rgba(0, 176, 155, 0.3);
        margin-bottom: 1rem;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        animation: slideInRight 0.3s ease-out;
    }

    .bot-msg {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #d1d5db;
        padding: 1.2rem;
        border-radius: 15px 15px 15px 0;
        margin-bottom: 1rem;
        border-left: 4px solid #0575E6;
        animation: slideInLeft 0.3s ease-out;
    }
    
    @keyframes slideInRight {
        from { opacity: 0; transform: translateX(20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    @keyframes slideInLeft {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }

    /* --- INPUT FIELDS & BUTTONS --- */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        background-color: rgba(0, 0, 0, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border-radius: 10px;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus {
        border-color: #00f260 !important;
        box-shadow: 0 0 10px rgba(0, 242, 96, 0.2);
    }

    .stButton > button {
        background: linear-gradient(45deg, #11998e, #38ef7d);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        font-family: 'Orbitron', sans-serif;
        border-radius: 25px;
        transition: transform 0.2s, box-shadow 0.2s;
        box-shadow: 0 4px 15px rgba(56, 239, 125, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(56, 239, 125, 0.5);
    }
    
    /* --- STATUS BADGE --- */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        background: rgba(0, 255, 0, 0.1);
        color: #00ff00;
        border: 1px solid #00ff00;
        font-family: 'Orbitron', monospace;
        font-size: 0.8rem;
        box-shadow: 0 0 10px rgba(0, 255, 0, 0.2);
    }

    /* Fixed Input Position */
    .stChatInput {
        position: fixed;
        bottom: 2rem;
        z-index: 100;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("💻 AKA-ONE")
    st.markdown("---")
    st.write("**SYSTEM MODULES**")
    mode = st.radio("Select Module", ["Terminal Chat 💬", "Memory Visualizer 🧠", "Data Ingestion 📥", "Autonomous Agent 🤖"])
    st.markdown("---")
    # Custom HTML Badge
    st.markdown('<div class="status-badge">● SYSTEM ONLINE</div>', unsafe_allow_html=True)
    st.markdown("")
    st.caption("v2.0 • Premium Build")

# State Management
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "System Ready. AKA-ONE initialized. How can I assist you with Computer Science?"}
    ]

# --- MODE: CHAT ---
if mode == "Terminal Chat 💬":
    st.header("Terminal Link 📟")
    
    # Display Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Input
    if prompt := st.chat_input("Enter command or query..."):
        # User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Assistant Response (Streamed placeholder)
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("⏳ Processing...")
            
            try:
                # API Call to Backend
                response = requests.post(
                    f"{BACKEND_URL}/api/chat",
                    json={"query": prompt},
                    timeout=120
                )
                
                if response.status_code == 200:
                    answer = response.json().get("answer", "No data returned.")
                    message_placeholder.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    err_msg = f"Error: {response.text}"
                    message_placeholder.error(err_msg)
            except Exception as e:
                message_placeholder.error(f"Connection Lost: {e}")

# --- MODE: C-VISUALIZER ---
elif mode == "Memory Visualizer 🧠":
    st.header("Memory Map (Stack/Heap) 🗺️")
    st.info("Input C code to visualize memory allocation dynamically.")
    
    code = st.text_area("Source Code:", height=200, value="""void main() {
  int x = 10;
  int *p = &x;
  int *h = (int*)malloc(sizeof(int));
  *h = 20;
}""")
    
    if st.button("Execute Visualization 🔮"):
        with st.spinner("Compiling memory view..."):
            try:
                # 1. Get JSON from Backend
                response = requests.post(f"{BACKEND_URL}/api/visualize", json={"code": code}, timeout=30)
                if response.status_code != 200:
                    st.error(f"Error: {response.text}")
                else:
                    data = response.json()
                    
                    if "error" in data:
                        st.error(f"Analysis failed: {data['error']}")
                        st.write(data.get("raw"))
                    else:
                        # 2. Render with Graphviz
                        import graphviz
                        
                        dot = graphviz.Digraph(comment='Memory Layout')
                        dot.attr(rankdir='LR')
                        dot.attr(bgcolor='#0d1117') # Dark BG for graph
                        
                        # Stack Subgraph
                        with dot.subgraph(name='cluster_stack') as s:
                            s.attr(label='Stack Frame', color='#58a6ff', fontcolor='#58a6ff', style='dashed')
                            s.attr(sortv='1')
                            
                            for var in data.get("stack", []):
                                label = f"<{var['type']}> {var['name']} = {var['value']}\n[{var.get('address', '')}]"
                                s.node(var['name'], label=label, shape='box', style='filled', fillcolor='#1f2428', fontcolor='#c9d1d9', color='#30363d')
                                
                                # Handle pointer logic in next pass or here if simple
                                if "target" in var and var["target"]:
                                    # We defer edges to ensure nodes exist
                                    pass

                        # Heap Subgraph
                        with dot.subgraph(name='cluster_heap') as h:
                            h.attr(label='Heap Memory', color='#ff7b72', fontcolor='#ff7b72', style='dashed')
                            
                            for var in data.get("heap", []):
                                label = f"<{var['type']}> = {var['value']}\n[{var.get('address', '')}]"
                                node_id = var.get("id", f"heap_{var['address']}")
                                h.node(node_id, label=label, shape='ellipse', style='filled', fillcolor='#1f2428', fontcolor='#c9d1d9', color='#30363d')

                        # Edges (Pointers)
                        for var in data.get("stack", []):
                            if "target" in var and var["target"]:
                                dot.edge(var['name'], var['target'], label="ptr", color='#7ee787')
                                
                        for var in data.get("heap", []):
                            if "target" in var and var["target"]:
                                node_id = var.get("id", f"heap_{var['address']}")
                                dot.edge(node_id, var['target'], color='#7ee787')

                        st.graphviz_chart(dot)
                        st.success("Memory Map Generated Successfully.")
                        
                        with st.expander("Raw Data Stream"):
                            st.json(data)
                            
            except Exception as e:
                st.error(f"Visualization Error: {e}")

# --- MODE: INGEST ---
elif mode == "Data Ingestion 📥":
    st.header("Classroom Ingestion 🍎")
    
    # 1. Auth Status Check
    is_authenticated = False
    try:
        auth_res = requests.get(f"{BACKEND_URL}/api/auth/status", timeout=5)
        if auth_res.status_code == 200 and auth_res.json().get("authenticated"):
            is_authenticated = True
            st.sidebar.success("✅ Google Connected")
        else:
            st.sidebar.warning("⚠️ Disconnected")
            if st.sidebar.button("Log in with Google"):
                login_res = requests.get(f"{BACKEND_URL}/api/auth/login")
                if login_res.status_code == 200:
                    auth_url = login_res.json().get("url")
                    st.sidebar.markdown(f"[👉 Click to Login]({auth_url})")
                else:
                    st.sidebar.error("Failed to generate login link")
    except Exception as e:
        st.sidebar.error(f"Auth Check Failed: {e}")

    # 2. Course Selection (If Authenticated, show list. Else show placeholder)
    if is_authenticated:
        st.subheader("Select a Course")
        
        # Search Box (just filters the dropdown really, or re-fetches)
        # For simplicity, we fetch all courses
        courses = []
        try:
            c_res = requests.get(f"{BACKEND_URL}/api/courses", timeout=10)
            if c_res.status_code == 200:
                courses = c_res.json().get("courses", [])
        except:
            st.error("Failed to load courses.")
            
        course_options = {f"{c['name']} ({c['id']})": c['id'] for c in courses}
        
        selected_course_label = st.selectbox("Available Courses", list(course_options.keys()))
        
        if st.button("Ingest Selected Course 🚀"):
            if selected_course_label:
                course_id = course_options[selected_course_label]
                st.info(f"Triggering ingestion for ID: {course_id}...")
                
                try:
                    res = requests.post(f"{BACKEND_URL}/api/ingest", json={"course_id": course_id, "drive_folder_id": ""})
                    if res.status_code == 200:
                        st.success(f"Task Queued! ID: {res.json()['task_id']}")
                        st.balloons()
                    else:
                        st.error("Error launching task.")
                except Exception as e:
                    st.error(f"Connection Error: {e}")
    else:
        st.info("🔒 Please log in via the Sidebar to access your Google Classroom courses.")
        st.text_input("Manual Course ID (Fallback)", "CS101")

    st.markdown("---")
    st.subheader("Or Upload Document 📄")
    uploaded_file = st.file_uploader("Upload PDF or Text file", type=['pdf', 'txt', 'md'])
    
    if uploaded_file is not None:
        if st.button("Ingest File 📤"):
            with st.spinner("Uploading & Processing..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                    # hardcoded user_id for now until Auth is full
                    res = requests.post(f"{BACKEND_URL}/api/ingest/upload", files=files, params={"user_id": "default_user"})
                    
                    if res.status_code == 200:
                        st.success(f"File Queued! Task ID: {res.json()['task_id']}")
                        st.balloons()
                    else:
                        st.error(f"Upload failed: {res.text}")
                except Exception as e:
                    st.error(f"Connection Error: {e}")

# --- MODE: AGENT AUTONOME ---
elif mode == "Autonomous Agent 🤖":
    st.header("Global Orchestrator & Multi-PC Agent 🌍")
    st.info("Ask the agent to install apps, edit code, or manage the network.")
    
    # Node Status Panel
    with st.expander("📡 Network Nodes Status"):
        if st.button("Refresh Nodes"):
            try:
                nodes_res = requests.get(f"{BACKEND_URL}/api/nodes/nodes", timeout=5)
                if nodes_res.status_code == 200:
                    nodes = nodes_res.json().get("nodes", {})
                    if not nodes:
                        st.warning("No nodes currently connected.")
                    for nid, nurl in nodes.items():
                        st.write(f"**{nid}** : {nurl}")
                else:
                    st.error("Failed to fetch nodes.")
            except Exception as e:
                st.error(f"Cannot connect to Brain: {e}")
                
    st.markdown("---")
    
    agent_prompt = st.chat_input("Ex: Install Chrome on PC-1 and add a new button to streamli...")
    
    if "agent_history" not in st.session_state:
        st.session_state.agent_history = []
        
    for msg in st.session_state.agent_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if agent_prompt:
        st.session_state.agent_history.append({"role": "user", "content": agent_prompt})
        with st.chat_message("user"):
            st.markdown(agent_prompt)
            
        with st.chat_message("assistant"):
            agent_placeholder = st.empty()
            with st.spinner("Agent is thinking, researching, and executing..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/api/agent/task",
                        json={"query": agent_prompt},
                        timeout=300 # Agent tasks might take a long time
                    )
                    
                    if response.status_code == 200:
                        ans = response.json().get("result", "Done.")
                        agent_placeholder.markdown(ans)
                        st.session_state.agent_history.append({"role": "assistant", "content": ans})
                    else:
                        agent_placeholder.error(f"Brain Error: {response.text}")
                except Exception as e:
                    agent_placeholder.error(f"Network error with Agent Brain: {e}")
