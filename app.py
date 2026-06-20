import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS
import os
import json
from dotenv import load_dotenv
from datetime import datetime

# Load local environment variables if available
load_dotenv()

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    # Using the fast, highly capable Flash model for general orchestration
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    st.error("Missing GEMINI_API_KEY environment variable.")

# --- AGENT CORE FUNCTIONS ---

def run_planner_agent(user_query: str) -> list:
    """Agent 1: Dynamically analyzes the query's domain and creates targeted search vectors."""
    current_date = datetime.now().strftime("%B %Y")
    
    prompt = f"""
    You are an Expert Research Strategist across all industries (Tech, Finance, Science, Geopolitics).
    The current date is {current_date}. 
    
    Your job is to analyze the user's query, determine its domain, and break it down into exactly 3 distinct, highly targeted search queries optimized for a search engine.
    
    CRITICAL INSTRUCTIONS:
    1. Focus heavily on retrieving deep situational analysis, recent developments, metrics, data points, and operational outcomes.
    2. NEVER generate queries that result in basic dictionary definitions (e.g., do not search for the meaning of a word).
    3. Append the relevant year or timeframe to the queries to ensure up-to-date data ingestion.
    
    User Topic: {user_query}
    
    Respond strictly with a JSON list of strings. Do not include markdown formatting or backticks outside the valid JSON.
    Example output format: ["query 1", "query 2", "query 3"]
    """
    response = model.generate_content(prompt)
    try:
        # Fixed syntax error: keeps the string replacement strictly on one line
        clean_text = response.text.strip().replace("```json", "").replace("```", "")
        queries = json.loads(clean_text)
        return queries if isinstance(queries, list) else [user_query]
    except Exception:
        return [user_query]


def run_researcher_agent(search_queries: list) -> list:
    """Agent 2: Executes web searches safely and gathers textual fragments."""
    compiled_results = []
    with DDGS() as ddgs:
        for query in search_queries:
            try:
                # Limit to top 3 results per query to conserve context space
                results = ddgs.text(query, max_results=3)
                for r in results:
                    compiled_results.append({
                        "title": r.get("title"),
                        "body": r.get("body"),
                        "href": r.get("href")
                    })
            except Exception as e:
                print(f"Search error for '{query}': {e}")
    return compiled_results


def run_synthesizer_agent(user_query: str, raw_data: list) -> str:
    """Agent 3: Universally evaluates data chunks and writes a structural professional report."""
    current_date = datetime.now().strftime("%B %d, %Y")
    
    data_context = ""
    for idx, item in enumerate(raw_data):
        data_context += f"\n[Source #{idx+1}]: {item['title']}\nURL: {item['href']}\nContent: {item['body']}\n---"
        
    prompt = f"""
    You are a Lead Intelligence Synthesizer. The current date is {current_date}.
    Your task is to draft a comprehensive, executive-level research report on the user's topic based strictly on the gathered data provided below.
    
    User Topic: {user_query}
    
    Gathered Research Data:
    {data_context}
    
    Report Requirements:
    1. Title: Create a professional title tailored to the query's domain and include today's date.
    2. Executive Summary: High-level overview of findings.
    3. Core Analysis / Key Findings: Break this section down into thematic subsections based on what the data actually reveals (e.g., if it's tech, talk about technical benchmarks; if it's finance, talk about market impacts).
    4. Future Implications: What do these findings mean moving forward?
    5. Use inline citations like [Source #1] matching the numbers from the Gathered Research Data.
    6. References: Provide a mapped list of sources with their actual URLs.
    7. Filter out and ignore any data fragments that are just generic dictionary definitions.
    """
    response = model.generate_content(prompt)
    return response.text

# --- STREAMLIT FULL-STACK INTERFACE ---

st.set_page_config(page_title="Autonomous Agent Researcher", page_icon="🤖", layout="wide")

st.title("🤖 Autonomous Multi-Agent Researcher")
st.caption("An enterprise-grade orchestration pipeline executing complex multi-step research entirely in parallel via specialized LLM agents.")

# Sidebar configuration for user input
with st.sidebar:
    st.header("Research Configuration")
    user_query = st.text_area(
        "Enter complex research query:",
        placeholder="e.g., Analyze the financial impact of the 2024 EU AI Act on open-source startups"
    )
    start_research = st.button("Launch Autonomous Agents", type="primary")

# Main Application Board UI Splits
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("🕵️ Agent Control Center & Logs")
    planner_status = st.empty()
    researcher_status = st.empty()
    synthesizer_status = st.empty()

with col2:
    st.subheader("📑 Final Intelligence Report")
    report_area = st.empty()
    report_area.info("Awaiting execution instructions from the Agent Control Center.")

# --- ORCHESTRATION EXECUTION LOOP ---
if start_research and user_query.strip():
    
    # --- PHASE 1: PLANNER AGENT ---
    planner_status.status("🧠 **Agent 1 (Planner):** Analyzing query and generating target search vectors...")
    search_queries = run_planner_agent(user_query)
    
    with planner_status.expander("Planner Output Vectors Found", expanded=True):
        for q in search_queries:
            st.write(f"🔍 `{q}`")
            
    # --- PHASE 2: RESEARCHER AGENT ---
    researcher_status.status("🌐 **Agent 2 (Researcher):** Executing search vectors across index networks...")
    raw_research_data = run_researcher_agent(search_queries)
    
    # CRITICAL FIX: Halt execution if no data is found
    if not raw_research_data:
        researcher_status.error("🚨 Agent 2 Failed: DuckDuckGo returned 0 results. This is usually due to temporary rate-limiting on Hugging Face's shared IPs. Please wait a minute and try again.")
        st.stop() # Stops the rest of the script from running
        
    with researcher_status.expander("Gathered Context Fragments", expanded=False):
        st.write(f"Total reference nodes ingested: {len(raw_research_data)}")
        st.json(raw_research_data)
        
    # --- PHASE 3: SYNTHESIZER AGENT ---
    synthesizer_status.status("✍️ **Agent 3 (Synthesizer):** Contextualizing fragments and compiling final report...")
    final_report = run_synthesizer_agent(user_query, raw_research_data)
    
    # Complete execution pipeline state
    planner_status.markdown("✅ **Agent 1 (Planner):** Success")
    researcher_status.markdown("✅ **Agent 2 (Researcher):** Data Ingested")
    synthesizer_status.markdown("✅ **Agent 3 (Synthesizer):** Compilation Finished")
    
    # Render final report natively as markdown inside the second UI block
    report_area.markdown(final_report)