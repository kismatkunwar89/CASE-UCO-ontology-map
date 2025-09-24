# Tests Directory

This directory contains the essential test files for the ontology research agent.

## Files

- **`clean_prompt_simulation.py`** - Main simulation script that tests the agent with the updated prompt
- **`test_prompt.py`** - Updated prompt with property extraction instructions
- **`clean_agent_report.md`** - Generated report from the simulation
- **`offline_graph_generator_test.py`** - Graph generator tests (production code)

## Usage

To run the main simulation:

```bash
cd tests
python3 clean_prompt_simulation.py
```

This will:
1. Load `test.json` from the parent directory
2. Simulate the agent's workflow using the updated prompt
3. Generate a markdown report in `clean_agent_report.md`

## Test Data

The test data is in `../test.json` and contains MFT Records with the following structure:
- `artifact_type`: "MFT Records"
- `description`: Master File Table records description
- `source`: "NTFS filesystem analysis"
- `records`: Array of MFT record data

