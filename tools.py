# tools.py
import json
import uuid
import tempfile
import os
from typing import Literal, Any, Dict, Optional

from langchain_core.tools import tool
from pydantic.v1 import BaseModel, Field

# Import CASE validation utility, which is used by a tool
try:
    from case_utils.case_validate import validate
    CASE_VALIDATION_AVAILABLE = True
except ImportError:
    CASE_VALIDATION_AVAILABLE = False
    print("[WARNING] [tools.py] 'case-utils' package not found. The 'validate_case_jsonld' tool will be disabled.")

# =============================================================================
# Agentic Tools
# =============================================================================

# Note: The 'case_uco' library is imported dynamically inside the tools
# to avoid a hard dependency at the top level if it's not installed.

# --- CASE/UCO Ontology Tools ---


class AnalyzeCaseUcoInput(BaseModel):
    """Input schema for the analyze_case_uco_class tool."""
    class_name: str = Field(...,
                            description="CASE/UCO class (e.g., 'WindowsPrefetch')")
    output_format: Literal["markdown", "summary", "properties"] = "markdown"


@tool("analyze_case_uco_class", args_schema=AnalyzeCaseUcoInput)
def analyze_case_uco_class(class_name: str, output_format: str = "markdown") -> str:
    """
    Analyze a CASE/UCO ontology class and return detailed information.
    Supported formats: 'markdown', 'summary', 'properties'.
    """
    try:
        fmt = (output_format or "markdown").strip().lower()
        cls = (class_name or "").strip()
        if not cls:
            return "Error: class_name is required."

        # Cached analyzer instance with lazy loading
        analyzer = globals().get("_case_uco_analyzer")
        if analyzer is None:
            print("[INFO] [Tools] Initializing CASE/UCO analyzer (first time only)...")
            # Use fast analyzer for quick startup
            from case_uco_fast import get_fast_analyzer
            analyzer = get_fast_analyzer()
            globals()["_case_uco_analyzer"] = analyzer
            print("[SUCCESS] [Tools] CASE/UCO analyzer ready")

        # Early guard for unknown class
        probe = analyzer.get_class_summary(cls)
        if isinstance(probe, dict) and probe.get("error"):
            return f"Error: {probe['error']}"

        if fmt == "markdown":
            return analyzer.export_to_markdown(cls)
        elif fmt == "summary":
            s = probe
            usage = ("Use 'hasFacet' property to link to {0}Facet".format(cls)
                     if s.get('has_facet_pattern') else "Direct property usage")
            superclasses = ", ".join(s.get('superclasses', [])) or "None"
            pc = s.get('property_counts', {})
            return (
                "CASE/UCO Class Analysis Summary for {cls}:\n\n"
                "Class: {name}\n"
                "URI: {uri}\n"
                "Description: {desc}\n\n"
                "Hierarchy Information:\n"
                "- Superclasses: {scount} ({sclasses})\n\n"
                "Property Summary:\n"
                "- Total Properties: {pt}\n"
                "- Facet Properties: {pf}\n"
                "- Inherited Properties: {pi}\n"
                "- Semantic Properties: {ps}\n\n"
                "Usage Pattern: {usage}"
            ).format(
                cls=cls, name=s.get('name', cls), uri=s.get('uri', ''),
                desc=(s.get('description') or '').strip(),
                scount=s.get('superclass_count', 0), sclasses=superclasses,
                pt=pc.get('total', 0), pf=pc.get('facet', 0),
                pi=pc.get('inherited', 0), ps=pc.get('semantic', 0),
                usage=usage
            )
        elif fmt == "properties":
            props = analyzer.get_shacl_property_shapes(cls) or {}
            if not props:
                return (f"SHACL Property Shapes Analysis for {cls}:\n"
                        f"Total Properties: 0\n\n"
                        f"(No SHACL shapes found in the loaded graphs for this class.)")
            by_class = {}
            for pname, pdata in props.items():
                by_class.setdefault(
                    pdata.get('sourceClass', 'Unknown'), []).append((pname, pdata))
            lines = [
                f"SHACL Property Shapes Analysis for {cls}:", f"Total Properties: {len(props)}", ""]
            for source_class, pairs in sorted(by_class.items()):
                lines.append(
                    f"\n{source_class} Properties ({len(pairs)} total):")
                lines.append("-" * 50)
                for pname, pdata in sorted(pairs):
                    ptype = pdata.get('propertyType') or 'owl:Property'
                    row = f"• {pname}: {ptype}"
                    if pdata.get('minCount') or pdata.get('maxCount'):
                        row += f" [{pdata.get('minCount') or '0'}..{pdata.get('maxCount') or '*'}]"
                    if pdata.get('localRange'):
                        row += f" → {pdata['localRange']}"
                    elif pdata.get('globalRange'):
                        row += f" → {pdata['globalRange']}"
                    lines.append(row)
                    desc = (pdata.get('description') or '').strip()
                    if desc:
                        lines.append(
                            f"     Description: {desc[:80] + '...' if len(desc) > 80 else desc}")
            return "\n".join(lines)
        else:
            return "Invalid output_format: 'markdown', 'summary', or 'properties' are supported."
    except Exception as e:
        return f"Error analyzing CASE/UCO class '{class_name}': {e}"


@tool
def list_case_uco_classes(filter_term: str = "") -> str:
    """List available CASE/UCO classes with optional filtering."""
    try:
        analyzer = globals().get("_case_uco_analyzer")
        if analyzer is None:
            from case_uco_fast import get_fast_analyzer
            analyzer = get_fast_analyzer()
            globals()["_case_uco_analyzer"] = analyzer
        classes = analyzer.list_all_classes()
        if filter_term:
            filtered_classes = [
                cls for cls in classes if filter_term.lower() in cls['name'].lower()]
            if not filtered_classes:
                return f"No CASE/UCO classes found containing '{filter_term}'. Try a different search term."
            result = f"CASE/UCO Classes containing '{filter_term}' ({len(filtered_classes)} found):\n\n"
            for i, cls in enumerate(filtered_classes, 1):
                result += f"{i:3d}. {cls['name']}\n"
        else:
            result = f"Available CASE/UCO Classes ({len(classes)} total):\n\n"
            for i, cls in enumerate(classes, 1):
                result += f"{i:3d}. {cls['name']}\n"
            result += "\nTip: Use filter_term parameter to search for specific types or keywords"
        return result
    except Exception as e:
        return f"Error listing CASE/UCO classes: {str(e)}"


@tool
def analyze_case_uco_facets() -> str:
    """Analyze all available Facet classes in the CASE/UCO ontology."""
    try:
        analyzer = globals().get("_case_uco_analyzer")
        if analyzer is None:
            from case_uco_fast import get_fast_analyzer
            analyzer = get_fast_analyzer()
            globals()["_case_uco_analyzer"] = analyzer
        facet_analysis = analyzer.analyze_facets()
        result = f"CASE/UCO Facet Analysis:\n"
        result += f"=" * 50 + "\n\n"
        result += f"Total Available Facets: {facet_analysis['total_facets']}\n\n"
        result += "Complete Facet List:\n"
        result += "-" * 30 + "\n"
        for i, facet in enumerate(facet_analysis['facet_list'], 1):
            result += f"{i:3d}. {facet}\n"
        result += "\n" + "=" * 50 + "\n"
        result += "Duck Typing Principle (from CASE FAQ):\n"
        result += "Any rational combination of facets can be applied to Observable objects.\n"
        result += "This allows flexible representation of forensic artifacts with unexpected\n"
        result += "combinations of properties without rigid class structures.\n\n"
        result += "Usage: Use 'hasFacet' property to attach any of these facets to Observable objects.\n"
        result += "Custom Facets: If needed data is not represented, create custom facets following CASE patterns.\n"
        return result
    except Exception as e:
        return f"Error analyzing CASE/UCO facets: {str(e)}"


@tool
def analyze_case_uco_relationships() -> str:
    """Analyze relationship patterns and connection types in CASE/UCO ontology."""
    try:
        analyzer = globals().get("_case_uco_analyzer")
        if analyzer is None:
            from case_uco_fast import get_fast_analyzer
            analyzer = get_fast_analyzer()
            globals()["_case_uco_analyzer"] = analyzer
        relationship_analysis = analyzer.analyze_relationships()
        result = f"CASE/UCO Relationship Analysis:\n"
        result += f"=" * 50 + "\n\n"
        result += f"Total Relationship Types: {relationship_analysis['total_relationship_types']}\n\n"
        if relationship_analysis['observable_relationships']:
            result += f"Observable Relationship Types ({len(relationship_analysis['observable_relationships'])}):\n"
            result += "-" * 40 + "\n"
            for i, rel in enumerate(relationship_analysis['observable_relationships'], 1):
                result += f"{i:2d}. {rel}\n"
            result += "\n"
        if relationship_analysis['general_relationships']:
            result += f"General Relationship Types ({len(relationship_analysis['general_relationships'])}):\n"
            result += "-" * 40 + "\n"
            for i, rel in enumerate(relationship_analysis['general_relationships'], 1):
                result += f"{i:2d}. {rel}\n"
            result += "\n"
        if relationship_analysis['common_patterns']:
            result += f"Common Relationship Patterns ({len(relationship_analysis['common_patterns'])}):\n"
            result += "-" * 40 + "\n"
            for i, pattern in enumerate(relationship_analysis['common_patterns'], 1):
                result += f"{i:2d}. {pattern}\n"
            result += "\n"
        result += "CASE FAQ Relationship Guidance:\n"
        result += "=" * 40 + "\n"
        result += "- Use ObservableRelationship to link any objects\n"
        result += "- Specify 'kindOfRelationship' property for relationship type\n"
        result += "- Examples: 'Referenced_Within', 'Contained_Within', 'Connected_To'\n"
        result += "- Set 'isDirectional' property for directional relationships\n"
        result += "- Links can represent device connections, file relationships, etc.\n\n"
        result += "Usage Example (from FAQ):\n"
        result += "- source: device1, target: device2\n"
        result += "- kindOfRelationship: 'Referenced_Within'\n"
        result += "- isDirectional: true\n"
        return result
    except Exception as e:
        return f"Error analyzing CASE/UCO relationships: {str(e)}"


# --- Graph Generation Tools ---

class GenerateJsonldGraphInput(BaseModel):
    """Input schema for the generate_jsonld_graph tool."""
    ontology_map: Dict[str, Any] = Field(
        ..., description="Dictionary containing parsed ontology information")


@tool("generate_jsonld_graph", args_schema=GenerateJsonldGraphInput)
def generate_jsonld_graph(ontology_map: Dict[str, Any]) -> str:
    """(DEPRECATED) Generate a complete CASE/UCO JSON-LD graph from the ontology map."""
    return "Tool deprecated - use base JSON-LD structure from prompt and populate @graph array"


@tool
def generate_uuid(entity_type: str) -> str:
    """Generate RFC 4122 v4 compliant UUID for CASE/UCO entities.

    CRITICAL: Each call generates a UNIQUE UUID, even for the same entity_type.
    Use this tool for EVERY @id field in your JSON-LD output.

    Args:
        entity_type: The type of entity (e.g., 'file', 'relationship', 'filefacet')

    Returns:
        A unique identifier string in format 'kb:<entity-type>-<UUIDv4>'

    Examples:
        - generate_uuid("file") → "kb:file-a1b2c3d4-e5f6-4567-8901-ef1234567890"
        - generate_uuid("relationship") → "kb:relationship-b2c3d4e5-f6g7-5678-9012-fg2345678901"
        - generate_uuid("filefacet") → "kb:filefacet-c3d4e5f6-g7h8-6789-0123-gh3456789012"

    IMPORTANT: 
    - Call this tool for EACH @id field, even if multiple entities have the same type
    - Never reuse UUIDs - each entity must have a unique identifier
    - The LLM will track which UUIDs to use for which entities
    """
    try:
        uuid_v4 = str(uuid.uuid4())
        result = f"kb:{entity_type}-{uuid_v4}"
        print(f"[UUID TOOL] Generated unique UUID: {result}")
        return result
    except Exception as e:
        error_msg = f"Error generating UUID: {str(e)}"
        print(f"[UUID TOOL ERROR] {error_msg}")
        return error_msg


@tool
def validate_case_jsonld(input_data: str, case_version: Optional[str] = "case-1.4.0") -> str:
    """Validate CASE/UCO JSON-LD data and return validation results"""
    if not CASE_VALIDATION_AVAILABLE:
        return "Error: case-utils package not available for validation"
    
    temp_files = []
    try:
        # Handle input
        if input_data.strip().startswith(("{", "[")):
            with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonld", delete=False) as f:
                f.write(input_data)
                temp_files.append(f.name)
                file_paths = [f.name]
        else:
            file_paths = [input_data]

        # Validate using case-utils
        result = validate(
            input_file=file_paths,
            case_version=case_version,
            review_tbox=False,
            supplemental_graphs=None,
        )

        conforms = getattr(result, "conforms", False)
        results_text = getattr(result, "text", None)
        
        # Return validation report
        if isinstance(results_text, str) and results_text.strip():
            return results_text
        else:
            return f"Validation {'PASSED' if conforms else 'FAILED'}: Unable to parse detailed results"
    except Exception as e:
        return f"Error during validation: {str(e)}"
