# CASE/UCO Ontology Mapping Agent

This project implements a sophisticated multi-agent system using LangGraph to automate the process of mapping unstructured digital forensics reports into the formal CASE/UCO (Cyber-investigation Analysis Standard Expression / Unified Cyber Ontology) format. The system ingests text-based artifact descriptions and produces a structured, valid JSON-LD graph.

## 🚀 Key Features

### Multi-Agent Architecture
Utilizes a supervisor-worker pattern where a central supervisor orchestrates a team of specialized agents:
- **Ontology Researcher**: Researches relevant CASE/UCO ontology classes and properties
- **Custom Facet Generator**: Creates custom facets for domain-specific artifacts
- **Graph Generator**: Constructs the JSON-LD graph structure
- **Validator**: Performs structural validation of the generated graph
- **Hallucination Checker**: Ensures data fidelity against source text

### Two-Layer Validation System
Implements a robust, two-stage validation process:

1. **Layer 1 (Structural)**: Validates the generated JSON-LD for structural integrity and basic ontology compliance
2. **Layer 2 (Fidelity)**: A dedicated agent checks the structurally valid graph for data hallucinations (i.e., information not present in the original source text)

### Self-Correction Loops
The system is designed to be resilient. If the validator or hallucination checker finds an error, the graph and feedback are routed back to the graph generator for autonomous correction attempts.

### Persistent Sessions
Each analysis run is managed in a unique session with its state checkpointed to a local SQLite database, allowing for resilience and a complete audit trail.

### Structured Tool-Based Output
Employs LangChain's tool-calling capabilities with Pydantic models to enforce a valid JSON structure for the final graph output, dramatically increasing reliability over raw JSON generation.

### Observability
Integrated with Arize Phoenix for tracing, allowing for the visualization and debugging of the agent's execution flow.

### Modular Design
The code is organized into a clean, modular structure that separates concerns (configuration, state, tools, agent logic, etc.), making it easy to maintain and extend.

## 📁 Project Structure

The project is organized into a modular structure for clarity and maintainability:

```
my-agent/
├── agents/                          # Agent implementations
│   ├── __init__.py
│   ├── custom_facet.py             # Custom facet generation agent
│   ├── graph_generator.py          # JSON-LD graph construction agent
│   ├── hallucination_checker.py    # Data fidelity validation agent
│   ├── ontology_researcher.py      # CASE/UCO ontology research agent
│   ├── supervisor.py               # Central orchestration agent
│   └── validator.py                # Structural validation agent
├── sessions/                        # Session databases (created at runtime)
├── test/                           # Test files
├── .env                            # Environment variables
├── case_uco.py                     # CASE/UCO ontology definitions
├── config.py                       # Configuration management
├── graph.py                        # LangGraph workflow definition
├── main.py                         # Main execution entry point
├── memory.py                       # Memory and state management
├── schemas.py                      # Pydantic data models
├── state.py                        # Agent state definitions
├── tools.py                        # LangChain tools and functions
├── utils.py                        # Utility functions
├── visualize.py                    # Graph visualization utilities
├── visualize_graph.py              # Alternative visualization
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- OpenAI API key (for LLM access)

### Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd my-agent
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## 🚀 Usage

### Basic Usage

Run the system with a sample forensic artifact:

```bash
python main.py
```

This will execute the default example with a Windows Prefetch file artifact.

### Programmatic Usage

```python
from main import call_forensic_analysis_with_session

# Create a new analysis session
result = call_forensic_analysis_with_session(
    user_identifier="analyst_001",
    input_artifacts="Your forensic artifact description here...",
    show_all_steps=True  # Set to False for summary only
)

# Access the generated JSON-LD graph
jsonld_graph = result["final_state"]["jsonldGraph"]
print(jsonld_graph)
```

### Session Management

Each analysis run creates a unique session with persistent state:

```python
from main import generate_session_id, execute_forensic_analysis_session

# Generate a unique session ID
session_id = generate_session_id("user_123")

# Execute analysis with session isolation
result = execute_forensic_analysis_session(
    session_id=session_id,
    input_artifacts="Artifact description...",
    show_all_steps=False
)
```

## 🔧 Configuration

The system can be configured through `config.py`. Key configuration options include:

- **Model Settings**: OpenAI model selection and parameters
- **Agent Behavior**: Timeout settings, retry limits, and validation thresholds
- **Phoenix Tracing**: Observability and debugging configuration
- **Session Management**: Database and checkpointing settings

## 📊 Observability

The system integrates with Arize Phoenix for comprehensive tracing and observability:

- **Execution Flow**: Visualize the complete agent workflow
- **Performance Metrics**: Track execution times and resource usage
- **Error Debugging**: Detailed error traces and debugging information
- **Agent Interactions**: Monitor inter-agent communication and decision-making

Access the Phoenix dashboard at: `https://app.phoenix.arize.com`

## 🧪 Testing

Run the test suite:

```bash
python -m pytest test/
```

## 📈 Example Output

The system generates structured JSON-LD graphs conforming to CASE/UCO standards:

```json
{
  "@context": {
    "uco-core": "https://ontology.unifiedcyberontology.org/uco/core/",
    "uco-observable": "https://ontology.unifiedcyberontology.org/uco/observable/"
  },
  "@graph": [
    {
      "@id": "kb:prefetch-file-001",
      "@type": "uco-observable:File",
      "uco-core:hasFacet": [
        {
          "@type": "uco-observable:PrefetchFacet",
          "uco-observable:applicationFileName": "MALICIOUS.EXE",
          "uco-observable:prefetchHash": "12345678",
          "uco-observable:runCount": 1
        }
      ]
    }
  ]
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **CASE/UCO Community**: For the comprehensive ontology standards
- **LangChain/LangGraph**: For the multi-agent framework
- **Arize Phoenix**: For observability and tracing capabilities
- **OpenAI**: For the language model capabilities

## 📞 Support

For questions, issues, or contributions, please:

1. Check the existing issues in the repository
2. Create a new issue with detailed information
3. Contact the development team

---

**Note**: This system is designed for digital forensics professionals and researchers working with CASE/UCO standards. Ensure you have appropriate permissions and follow ethical guidelines when processing forensic data.
