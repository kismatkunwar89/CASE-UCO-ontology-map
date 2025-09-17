import streamlit as st
import json
import time
from main import execute_forensic_analysis_session_stream, generate_session_id

# Page configuration
st.set_page_config(
    page_title="CASE/UCO Ontology Mapping Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Page title
st.title("🔍 CASE/UCO Ontology Mapping Agent")
st.markdown("Transform unstructured digital forensics reports into structured JSON-LD graphs using our multi-agent system.")

# Create two-column layout
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📝 Input Configuration")

    # User identifier input
    user_identifier = st.text_input(
        "User Identifier",
        value="forensic_analyst",
        help="Enter a unique identifier for this analysis session"
    )

    # Forensic artifacts input
    st.subheader("Forensic Artifacts")
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

    # Run analysis button
    run_analysis = st.button(
        "🚀 Run Analysis", type="primary", use_container_width=True)

with col2:
    st.header("📊 Analysis Results")

    # Create placeholder containers for real-time updates
    log_container = st.empty()
    json_container = st.empty()
    download_container = st.empty()
    phoenix_container = st.empty()

# Initialize session state
if 'analysis_running' not in st.session_state:
    st.session_state.analysis_running = False

# Handle button click
if run_analysis and input_artifacts.strip():
    if not st.session_state.analysis_running:
        st.session_state.analysis_running = True

        # Generate session ID
        session_id = generate_session_id(user_identifier)

        # Clear previous results
        log_container.empty()
        json_container.empty()
        download_container.empty()
        phoenix_container.empty()

        # Display initial message
        with log_container.container():
            st.info(f"🚀 Starting analysis session: {session_id}")
            st.info("Initializing multi-agent system...")

        try:
            # Create a progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Execute the analysis session with real-time streaming
            final_result = None
            step_count = 0

            # Initialize log display
            log_display = log_container.container()

            for stream_event in execute_forensic_analysis_session_stream(session_id, input_artifacts):
                if stream_event["type"] == "step":
                    step_count = stream_event["step_number"]
                    event = stream_event["event"]

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

                    # Small delay to make the UI more readable
                    time.sleep(0.5)

                elif stream_event["type"] == "completion":
                    # Update progress to 100%
                    progress_bar.progress(1.0)
                    status_text.text("✅ Analysis completed!")

                    # Display completion message
                    with log_display:
                        st.success("✅ Analysis completed successfully!")
                        st.info(
                            f"Session completed in {stream_event['total_steps']} steps")

                    final_result = stream_event
                    break

                elif stream_event["type"] == "error":
                    # Handle error
                    progress_bar.progress(0)
                    status_text.text("❌ Analysis failed")

                    with log_display:
                        st.error(f"❌ Analysis failed: {stream_event['error']}")
                    break

            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()

            # Display results if successful
            if final_result:
                # Extract and display the final JSON-LD graph
                final_graph = final_result.get(
                    "final_event", {}).get("jsonldGraph", {})

                if final_graph:
                    with json_container.container():
                        st.subheader("📋 Generated JSON-LD Graph")
                        st.json(final_graph)

                    # Create download button
                    json_str = json.dumps(final_graph, indent=2)
                    with download_container.container():
                        st.download_button(
                            label="💾 Download JSON-LD",
                            data=json_str,
                            file_name=f"forensic_analysis_{session_id}.json",
                            mime="application/json",
                            use_container_width=True
                        )

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

        except Exception as e:
            with log_container.container():
                st.error(f"❌ Analysis failed: {str(e)}")
            st.exception(e)

        finally:
            st.session_state.analysis_running = False

elif run_analysis and not input_artifacts.strip():
    st.error("⚠️ Please enter forensic artifact description before running analysis")

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
    1. Enter your user identifier
    2. Paste forensic artifact text
    3. Click "Run Analysis"
    4. View real-time progress
    5. Download JSON-LD output
    6. Check Phoenix trace
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
