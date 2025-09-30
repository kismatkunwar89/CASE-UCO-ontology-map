import streamlit as st
import json
import time
import requests
from sseclient import SSEClient
import logging

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('streamlit_debug.log')
    ]
)
logger = logging.getLogger(__name__)

# Log import timing
print("🚀 [APP START] Starting Streamlit app imports...")
logger.info("🚀 [APP START] Starting Streamlit app imports...")
import_start = time.time()

# Log page config timing
print("⚙️ [CONFIG] Setting up page configuration...")
logger.info("⚙️ [CONFIG] Setting up page configuration...")
config_start = time.time()

# Page configuration - optimized for faster rendering
st.set_page_config(
    page_title="CASE/UCO Ontology Mapping Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
    # Optimize for faster initial load
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "CASE/UCO Ontology Mapping Agent v1.0"
    }
)

config_end = time.time()
print(f"✅ [CONFIG] Page config completed in {config_end - config_start:.3f}s")
logger.info(
    f"✅ [CONFIG] Page config completed in {config_end - config_start:.3f}s")

# Log UI rendering timing
print("🎨 [UI] Starting UI rendering...")
logger.info("🎨 [UI] Starting UI rendering...")
ui_start = time.time()

# Page title
st.title("🔍 CASE/UCO Ontology Mapping Agent")
st.markdown("Transform unstructured digital forensics reports into structured JSON-LD graphs using our multi-agent system.")

# Remove blocking import - let UI render immediately
# Ontology loading will happen when user clicks "Run Analysis"
logger.info("✅ [UI] Basic UI elements rendered")

# Log layout creation timing
logger.info("📐 [LAYOUT] Creating two-column layout...")
layout_start = time.time()

# Create two-column layout
col1, col2 = st.columns([1, 1])

with col1:
    logger.info("📝 [INPUT] Rendering input configuration...")
    st.header("📝 Input Configuration")

    # User identifier input
    user_identifier = st.text_input(
        "User Identifier",
        value="forensic_analyst",
        help="Enter a unique identifier for this analysis session"
    )

    # Forensic artifacts input
    st.subheader("Forensic Artifacts")

    # Input method selection
    input_method = st.radio(
        "Select input method:",
        options=["Text Input", "CSV File Upload"],
        horizontal=True,
        help="Choose whether to paste text directly or upload a CSV file"
    )

    # Text input or CSV file upload based on selection
    input_artifacts = None
    uploaded_file = None

    if input_method == "Text Input":
        input_artifacts = st.text_area(
            "Paste your forensic artifact description here:",
            height=300,
            placeholder="""Example:
Artifact: Windows Prefetch File
- Path: C:\\Windows\\Prefetch\\MALICIOUS.EXE-12345678.pf
- Created: 2025-09-17T10:30:00Z
- Process ID: 4567
- Executable: MALICIOUS.EXE
- Last Run: 2025-09-17T10:35:15Z""",
            help="Enter unstructured text describing the digital forensic artifact"
        )
    else:  # CSV File Upload
        # Metadata fields for CSV context
        st.markdown("**Provide Context for Your CSV Data:**")
        artifact_type = st.text_input(
            "Artifact Type",
            placeholder="e.g., MFT Record, Browser History, Registry Key",
            help="Specify the type of forensic artifact in your CSV"
        )
        description = st.text_input(
            "Description",
            placeholder="e.g., File system metadata from forensic image",
            help="Describe what this data represents"
        )
        source = st.text_input(
            "Source",
            placeholder="e.g., suspect_laptop_image.E01",
            help="Specify the source of this data"
        )

        st.markdown("**Upload CSV File:**")
        uploaded_file = st.file_uploader(
            "Choose a CSV file:",
            type=["csv"],
            help="Upload a CSV file containing forensic artifact data. Each row represents one artifact."
        )

        if uploaded_file is not None:
            st.success(f"✅ File uploaded: {uploaded_file.name}")
            if artifact_type or description or source:
                st.info("✓ Context metadata provided")
            st.info("Click 'Run Analysis' to process the CSV file")

    # Run analysis button
    run_analysis = st.button(
        "🚀 Run Analysis", type="primary", use_container_width=True)

    logger.info("✅ [INPUT] Input configuration rendered")

with col2:
    logger.info("📊 [OUTPUT] Rendering output area...")
    st.header("📊 Analysis Results")

    # Create placeholder containers for real-time updates
    log_container = st.empty()
    json_container = st.empty()
    download_container = st.empty()
    phoenix_container = st.empty()

    logger.info("✅ [OUTPUT] Output area rendered")

# Log layout completion
layout_end = time.time()
logger.info(f"✅ [LAYOUT] Layout completed in {layout_end - layout_start:.3f}s")

# Log session state initialization
logger.info("🔧 [SESSION] Initializing session state...")
session_start = time.time()

# Initialize session state
if 'analysis_running' not in st.session_state:
    st.session_state.analysis_running = False

# API Configuration
API_BASE_URL = "http://localhost:9000/api/v1"

session_end = time.time()
logger.info(
    f"✅ [SESSION] Session state initialized in {session_end - session_start:.3f}s")

# Log total UI render time
ui_end = time.time()
total_ui_time = ui_end - ui_start
print(f"🎉 [UI COMPLETE] Total UI rendering completed in {total_ui_time:.3f}s")
logger.info(
    f"🎉 [UI COMPLETE] Total UI rendering completed in {total_ui_time:.3f}s")

# Log total app startup time
import_end = time.time()
total_startup_time = import_end - import_start
print(
    f"🚀 [APP COMPLETE] Total app startup completed in {total_startup_time:.3f}s")
logger.info(
    f"🚀 [APP COMPLETE] Total app startup completed in {total_startup_time:.3f}s")

# Handle button click
# Check if we have either text input or uploaded file
has_input = (input_artifacts and input_artifacts.strip()) or (uploaded_file is not None)

if run_analysis and has_input:
    if not st.session_state.analysis_running:
        st.session_state.analysis_running = True

        # Clear previous results
        log_container.empty()
        json_container.empty()
        download_container.empty()
        phoenix_container.empty()

        # Display initial message
        with log_container.container():
            st.info("🚀 Starting analysis session...")
            st.info("Connecting to API server...")

        try:
            # Show initialization status
            with log_container.container():
                st.info("🚀 Starting analysis session...")
                st.info("🔧 Initializing ontology analyzer...")

            # Create a progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Handle CSV file upload or text input
            if uploaded_file is not None:
                # Read CSV file content as string
                csv_content = uploaded_file.read().decode("utf-8")

                # Prepare API request data with CSV content and metadata
                api_data = {
                    "user_identifier": user_identifier,
                    "input_artifacts": csv_content
                }

                # Add metadata if provided
                if artifact_type:
                    api_data["artifact_type"] = artifact_type
                if description:
                    api_data["description"] = description
                if source:
                    api_data["source"] = source
            else:
                # Try to parse as JSON; if it fails, send as text
                parsed = None
                try:
                    parsed = json.loads(input_artifacts)
                except Exception:
                    pass

                # Prepare API request data
                api_data = {
                    "user_identifier": user_identifier,
                    "input_artifacts": parsed if parsed is not None else input_artifacts
                }

            # Make streaming request to FastAPI server
            response = requests.post(
                f"{API_BASE_URL}/invoke-streaming",
                json=api_data,
                stream=True,
                headers={"Accept": "text/plain"}
            )

            if response.status_code != 200:
                raise Exception(
                    f"API request failed with status {response.status_code}: {response.text}")

            # Initialize variables for processing
            final_result = None
            step_count = 0
            session_id = None

            # Initialize log display
            log_display = log_container.container()

            # Process streaming response
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith("data: "):
                    try:
                        # Parse the JSON data from the SSE stream
                        data = json.loads(line[6:])  # Remove "data: " prefix

                        if data["type"] == "step":
                            step_count = data["data"]["step_number"]
                            event = data["data"]["event"]
                            session_id = data["session_id"]

                            # Update progress
                            # Cap at 90% until completion
                            progress_bar.progress(min(step_count / 10, 0.9))
                            status_text.text(
                                f"Step {step_count}: Processing agent workflow...")

                            # Display step information in log
                            with log_display:
                                st.info(
                                    f"🔄 Step {step_count}: Agent workflow in progress")
                                if "messages" in event and event["messages"]:
                                    last_message = event["messages"][-1]
                                    if hasattr(last_message, 'content'):
                                        st.text(
                                            f"Agent: {last_message.content[:200]}...")

                        elif data["type"] == "completion":
                            # Update progress to 100%
                            progress_bar.progress(1.0)
                            status_text.text("✅ Analysis completed!")

                            # Display completion message
                            with log_display:
                                st.success(
                                    "✅ Analysis completed successfully!")
                                st.info(
                                    f"Session completed in {data['data']['total_steps']} steps")

                            final_result = data["data"]
                            session_id = data["session_id"]
                            break

                        elif data["type"] == "error":
                            # Handle error
                            progress_bar.progress(0)
                            status_text.text("❌ Analysis failed")

                            error_message = data['data']['error']
                            with log_display:
                                st.error(f"❌ Analysis failed: {error_message}")

                                # Display helpful message for CSV-specific errors
                                if "csv" in error_message.lower() or "invalid format" in error_message.lower():
                                    st.info("💡 **CSV Tips:**\n"
                                           "- Ensure your CSV has headers\n"
                                           "- Check for proper column formatting\n"
                                           "- Verify the file is not corrupted")
                            break

                        elif data["type"] == "stream_error":
                            # Handle stream error
                            progress_bar.progress(0)
                            status_text.text("❌ Stream error")

                            with log_display:
                                st.error(f"❌ Stream error: {data['error']}")
                            break

                    except json.JSONDecodeError as e:
                        # Skip malformed JSON lines
                        continue

            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()

            # Display results if successful
            if final_result:
                # Extract and display the final JSON-LD graph
                final_graph = final_result.get(
                    "final_event", {}).get("jsonldGraph", {})

                if final_graph:
                    # Pre-serialize JSON for download (optimized)
                    json_str = json.dumps(final_graph, separators=(
                        ',', ':'))  # Compact format for speed

                    # Batch all UI updates together for better performance
                    with json_container.container():
                        st.subheader("📋 Generated JSON-LD Graph")

                        # Show summary first for immediate feedback
                        graph_summary = {
                            "entities_count": len(final_graph.get("@graph", [])),
                            "context_namespaces": len(final_graph.get("@context", {})),
                            "graph_size": f"{len(json_str)} characters"
                        }
                        st.info(
                            f"📊 Graph Summary: {graph_summary['entities_count']} entities, {graph_summary['context_namespaces']} namespaces")

                        # Use expander for better performance with large JSON
                        with st.expander("🔍 View Full JSON-LD Graph", expanded=True):
                            st.json(final_graph)

                    # Create download button with pre-serialized data
                    with download_container.container():
                        st.download_button(
                            label="💾 Download JSON-LD",
                            # Pretty format for download
                            data=json.dumps(final_graph, indent=2),
                            file_name=f"forensic_analysis_{session_id}.json",
                            mime="application/json",
                            use_container_width=True
                        )

                    # Display suggestions from both validation layers if present
                    validation_suggestions = final_result.get("validation_suggestions", None)
                    hallucination_suggestions = final_result.get("hallucination_suggestions", None)

                    # Show suggestions if either layer has them
                    if (validation_suggestions and len(validation_suggestions) > 0) or \
                       (hallucination_suggestions and len(hallucination_suggestions) > 0):
                        with json_container.container():
                            st.subheader("💡 Suggestions for Improvement")

                            total_suggestions = (len(validation_suggestions) if validation_suggestions else 0) + \
                                              (len(hallucination_suggestions) if hallucination_suggestions else 0)

                            st.info(f"Found {total_suggestions} suggestion(s) to enhance your data quality and graph structure.")

                            with st.expander("📝 View All Suggestions", expanded=False):
                                # Layer 1 (Structural/Syntax) suggestions
                                if validation_suggestions and len(validation_suggestions) > 0:
                                    st.markdown("### 📐 Structural & Syntax Suggestions (Layer 1)")
                                    st.caption("Recommendations for improving CASE/UCO compliance and graph structure")
                                    for idx, suggestion in enumerate(validation_suggestions, 1):
                                        st.markdown(f"**{idx}.** {suggestion}")
                                    st.markdown("---")

                                # Layer 2 (Data Fidelity) observations
                                if hallucination_suggestions and len(hallucination_suggestions) > 0:
                                    st.markdown("### 🔍 Data Fidelity Observations (Layer 2)")
                                    st.caption("Informational observations about data accuracy and completeness")
                                    for idx, suggestion in enumerate(hallucination_suggestions, 1):
                                        st.markdown(f"**{idx}.** {suggestion}")

                                st.markdown("---")
                                st.caption("ℹ️ These are informational suggestions and do not prevent successful validation.")

                    # Display Phoenix traceability link
                    phoenix_endpoint = "https://app.phoenix.arize.com/s/ktamsik101/v1/traces"
                    phoenix_url = f"{phoenix_endpoint}?session_id={session_id}"

                    with phoenix_container.container():
                        st.subheader("🔗 Phoenix Traceability")
                        st.markdown(
                            f"[View detailed trace in Phoenix →]({phoenix_url})")
                        st.caption(
                            "Click to view the complete agent execution trace and performance metrics")

                else:
                    with json_container.container():
                        st.error("❌ No JSON-LD graph was generated")
                        st.info("Check the logs for more information")

        except requests.exceptions.ConnectionError:
            with log_container.container():
                st.error("❌ Cannot connect to API server")
                st.info(
                    "Please make sure the FastAPI server is running on http://localhost:9000")
                st.info("Start the server with: python main.py")
        except Exception as e:
            with log_container.container():
                st.error(f"❌ Analysis failed: {str(e)}")
            st.exception(e)

        finally:
            st.session_state.analysis_running = False

elif run_analysis and not has_input:
    st.error("⚠️ Please enter forensic artifact description or upload a CSV file before running analysis")

# Sidebar with additional information
with st.sidebar:
    st.header("ℹ️ About This System")
    st.markdown("""
    This application demonstrates our **CASE/UCO Ontology Mapping Agent** - a sophisticated multi-agent system that:
    
    - 🔍 **Analyzes** unstructured forensic reports
    - 🧠 **Maps** data to CASE/UCO standards
    - ✅ **Validates** output for accuracy
    - 📊 **Generates** structured JSON-LD graphs
    
    ### Key Features:
    - Multi-agent architecture
    - Two-layer validation
    - Self-correction loops
    - Phoenix observability
    - Session management
    """)

    st.header("🚀 Quick Start")
    st.markdown("""
    1. **Start the API server**: `python main.py`
    2. **Start this UI**: `streamlit run app.py`
    3. Enter your user identifier
    4. Paste forensic artifact text
    5. Click "Run Analysis"
    6. View real-time progress
    7. Download JSON-LD output
    8. Check Phoenix trace
    """)

    st.header("📚 Resources")
    st.markdown("""
    - [CASE/UCO Documentation](https://caseontology.org/)
    - [Phoenix Observability](https://app.phoenix.arize.com)
    - [Project Repository](https://github.com/your-repo)
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "CASE/UCO Ontology Mapping Agent | Built with Streamlit & LangGraph"
    "</div>",
    unsafe_allow_html=True
)
