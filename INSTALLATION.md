# Installation Guide

This guide will help you set up the Forensic Agent System on any system.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- OpenAI API key

## Quick Installation

1. **Clone or download the project**
   ```bash
   git clone <repository-url>
   cd Case-base-map/my-agent
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Create a .env file or set environment variables
   export OPENAI_API_KEY="your-openai-api-key-here"
   ```

5. **Run the system**
   ```bash
   python main.py
   ```

## Detailed Dependencies

### Core Dependencies

- **langchain** (>=0.1.0): Core LangChain framework for LLM applications
- **langchain-core** (>=0.1.0): Core LangChain components
- **langchain-openai** (>=0.1.0): OpenAI integration for LangChain
- **langgraph** (>=0.1.0): LangGraph for building stateful agent workflows
- **openai** (>=1.0.0): OpenAI API client

### Observability and Tracing

- **phoenix-otel** (>=0.1.0): Phoenix tracing for observability (hardcoded in main.py)

### Web and Data Processing

- **requests** (>=2.31.0): HTTP library for web requests
- **beautifulsoup4** (>=4.12.0): HTML/XML parsing for web scraping
- **rdflib** (>=7.0.0): RDF processing for ontology analysis

### Data Validation and Processing

- **pydantic** (>=2.0.0): Data validation and settings management
- **pydantic-v1** (>=1.10.0): Legacy Pydantic v1 compatibility
- **typing-extensions** (>=4.7.0): Extended typing support

### User Interface

- **tqdm** (>=4.65.0): Progress bars for long-running operations

### Optional Dependencies

For graph visualization (uncomment in requirements.txt if needed):
- **pillow** (>=10.0.0): Image processing for graph visualization
- **matplotlib** (>=3.7.0): Plotting library

For development and testing:
- **pytest** (>=7.4.0): Testing framework
- **pytest-asyncio** (>=0.21.0): Async testing support

## System Requirements

### Minimum System Requirements
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space
- **Network**: Internet connection for OpenAI API calls

### Supported Operating Systems
- Windows 10/11
- macOS 10.15+
- Linux (Ubuntu 18.04+, CentOS 7+, etc.)

## Environment Setup

### Required Environment Variables

```bash
# OpenAI API Key (required)
export OPENAI_API_KEY="sk-your-openai-api-key-here"

# Optional: Custom OpenAI base URL (if using proxy)
# export OPENAI_BASE_URL="https://your-proxy-url.com/v1"
```

### Optional Environment Variables

```bash
# Phoenix tracing (already hardcoded in main.py)
export PHOENIX_API_KEY="your-phoenix-key"  # Optional override
export PHOENIX_ENDPOINT="your-phoenix-endpoint"  # Optional override
```

## Troubleshooting

### Common Issues

1. **ImportError: No module named 'rdflib'**
   ```bash
   pip install rdflib
   ```

2. **OpenAI API Key not found**
   ```bash
   export OPENAI_API_KEY="your-key-here"
   ```

3. **Permission denied on Windows**
   ```bash
   # Run as administrator or use --user flag
   pip install --user -r requirements.txt
   ```

4. **Virtual environment not activating**
   ```bash
   # On Windows PowerShell, you might need:
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

### Platform-Specific Notes

#### Windows
- Use PowerShell or Command Prompt
- Ensure Python is added to PATH
- Consider using Windows Subsystem for Linux (WSL) for better compatibility

#### macOS
- Use Terminal or iTerm2
- You might need to install Xcode command line tools:
  ```bash
  xcode-select --install
  ```

#### Linux
- Ensure pip is up to date:
  ```bash
  python -m pip install --upgrade pip
  ```

## Verification

After installation, verify everything works:

```bash
# Test basic imports
python -c "import langchain, langgraph, openai; print('All imports successful')"

# Run the test suite
python test.py

# Run domain-agnostic test
python test_any_case.py
```

## Getting Help

If you encounter issues:

1. Check the troubleshooting section above
2. Verify all dependencies are installed: `pip list`
3. Check Python version: `python --version`
4. Ensure virtual environment is activated
5. Verify OpenAI API key is set correctly

## Next Steps

After successful installation:

1. **Configure your OpenAI API key**
2. **Run the basic test**: `python test.py`
3. **Run the comprehensive test**: `python test_any_case.py`
4. **Start using the system**: `python main.py`

The system is now ready to handle any forensic artifact type dynamically!
