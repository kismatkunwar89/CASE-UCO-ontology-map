## Relevant Files

-   `utils.py` - **File to be modified.** The `parse_ontology_response` function will be refactored to simplify its output.
-   `agents/ontology_researcher.py` - **File to be modified.** The `ontology_research_node` will be updated to use the newly refactored parser.
-   `tests/test_parser.py` - **File to be created.** It is recommended to create a unit test to verify the new behavior of the parser function.

### Notes

-   This refactor is a small but important optimization that will make the application's state management more efficient and the code easier to understand.

## Tasks

-   [ ] 1.0 **Refactor the Ontology Response Parser**
    -   [ ] 1.1 Open the `utils.py` file.
    -   [ ] 1.2 Locate the `parse_ontology_response` function.
    -   [ ] 1.3 Modify the function to remove the logic that adds the `additional_details` key. The function should only find the fenced JSON block, parse it, and return the resulting dictionary.
    -   [ ] 1.4 Update the function's return logic to provide a simple error dictionary (e.g., `{"error": "No JSON found"}`) if parsing fails or no JSON block is found.
    -   [ ] 1.5 Update the function signature to accept only one argument: `content: str`.

-   [ ] 2.0 **Update the Ontology Research Node**
    -   [ ] 2.1 Open the `agents/ontology_researcher.py` file.
    -   [ ] 2.2 Locate the `ontology_research_node` function.
    -   [ ] 2.3 Update the line where the parser is called to pass only one argument: `ontology_map = parse_ontology_response(agent_output_markdown)`.
    -   [ ] 2.4 Verify that the `return Command(...)` block updates the state with two distinct keys: `ontologyMarkdown` (containing the full raw text) and `ontologyMap` (containing the clean dictionary from the updated parser).