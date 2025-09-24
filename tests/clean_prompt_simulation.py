#!/usr/bin/env python3
"""
Clean simulation of the ontology research agent using the updated prompt from test_prompt.py
"""

from test_prompt import ONTOLOGY_RESEARCH_AGENT_PROMPT
from tools import list_case_uco_classes, analyze_case_uco_class
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))


def generate_keywords_from_prompt_logic(artifact_type, description, source):
    """Generate keywords based on the prompt logic for forensic analysis"""
    keywords = []

    # Extract artifact type keywords
    if artifact_type:
        keywords.append(artifact_type)
        if 'MFT' in artifact_type.upper():
            keywords.extend(['MftRecord', 'MasterFileTable', 'FileTable'])
        elif 'PREFETCH' in artifact_type.upper():
            keywords.extend(['WindowsPrefetch', 'Prefetch'])
        elif 'EVENT' in artifact_type.upper():
            keywords.extend(['EventLog', 'WindowsEvent'])

    # Extract description keywords
    if description:
        desc_lower = description.lower()
        if 'filesystem' in desc_lower:
            keywords.extend(['FileSystem', 'FileSystemObject'])
        if 'metadata' in desc_lower:
            keywords.extend(['Metadata', 'File'])
        if 'ntfs' in desc_lower:
            keywords.extend(['NTFS', 'NTFSFile'])
        if 'file' in desc_lower:
            keywords.append('File')
        if 'directory' in desc_lower:
            keywords.append('Directory')

    # Extract source keywords
    if source:
        source_lower = source.lower()
        if 'ntfs' in source_lower:
            keywords.extend(['NTFS', 'NTFSFile'])
        if 'windows' in source_lower:
            keywords.extend(['Windows', 'WindowsPrefetch'])

    # Add common forensic keywords
    keywords.extend(['File', 'FileSystem', 'Observable'])

    # Remove duplicates and empty strings
    keywords = list(dict.fromkeys([k for k in keywords if k.strip()]))

    return keywords


def select_intelligent_classes(all_classes, artifact_type, description):
    """Select classes based on forensic relevance and artifact type"""
    priority_classes = []

    # Core classes for MFT Records
    if 'MFT' in artifact_type.upper():
        priority_order = ['File', 'FileSystemObject',
                          'Directory', 'WindowsPrefetch', 'NTFSFile']
        for class_name in priority_order:
            if class_name in all_classes:
                priority_classes.append(class_name)

    # Add other relevant classes
    for class_name in all_classes:
        if class_name not in priority_classes:
            if any(keyword.lower() in class_name.lower() for keyword in ['File', 'System', 'Observable']):
                priority_classes.append(class_name)

    # Limit to top 4 classes like production
    return priority_classes[:4]


def select_intelligent_facets(all_facets, artifact_type, description):
    """Select facets based on forensic relevance and artifact type"""
    priority_facets = []

    # Core facets for MFT Records
    if 'MFT' in artifact_type.upper():
        priority_order = ['MftRecordFacet', 'FileFacet',
                          'WindowsPrefetchFacet', 'NTFSFileFacet']
        for facet_name in priority_order:
            if facet_name in all_facets:
                priority_facets.append(facet_name)

    # Add other relevant facets
    for facet_name in all_facets:
        if facet_name not in priority_facets:
            if any(keyword.lower() in facet_name.lower() for keyword in ['File', 'Record', 'Prefetch']):
                priority_facets.append(facet_name)

    # Limit to top 2 facets
    return priority_facets[:2]


def simulate_agent_with_updated_prompt():
    """Simulate the actual agent using the updated prompt"""

    print("🤖 SIMULATING ONTOLOGY RESEARCH AGENT WITH UPDATED PROMPT")
    print("=" * 70)

    # Load test data
    with open('../test.json', 'r') as f:
        test_data = json.load(f)

    print(f"\n📋 INPUT DATA:")
    print(f"Artifact Type: {test_data.get('artifact_type', 'Unknown')}")
    print(f"Description: {test_data.get('description', 'No description')}")

    # Simulate Phase 1: Keyword Generation (as per prompt)
    print(f"\n🔍 PHASE 1: KEYWORD GENERATION")
    artifact_type = test_data.get('artifact_type', '')
    description = test_data.get('description', '')
    source = test_data.get('source', '')

    # Generate keywords based on prompt logic
    keywords = generate_keywords_from_prompt_logic(
        artifact_type, description, source)
    print(f"Generated keywords: {keywords}")

    # Simulate Phase 2: Class Search
    print(f"\n🔍 PHASE 2: CLASS SEARCH")
    all_classes = []
    all_facets = []

    for keyword in keywords:
        try:
            result = list_case_uco_classes(tool_input={"filter_term": keyword})
            if result and isinstance(result, str):
                lines = result.split('\n')
                found_classes = []

                for line in lines:
                    line = line.strip()
                    if line and line[0].isdigit() and '. ' in line:
                        class_name = line.split('. ', 1)[1].strip()
                        if class_name:
                            found_classes.append(class_name)

                for class_name in found_classes:
                    if class_name.endswith('Facet'):
                        all_facets.append(class_name)
                    else:
                        all_classes.append(class_name)

                print(f"  {keyword}: Found {len(found_classes)} classes")
        except Exception as e:
            print(f"  {keyword}: Error - {e}")

    print(f"\n📊 SEARCH RESULTS:")
    print(f"Classes found: {len(all_classes)}")
    print(f"Facets found: {len(all_facets)}")

    # Simulate Phase 3: Select Top Candidates (intelligent selection)
    print(f"\n🔍 PHASE 3: SELECTING TOP CANDIDATES")
    top_classes = select_intelligent_classes(
        all_classes, artifact_type, description)
    top_facets = select_intelligent_facets(
        all_facets, artifact_type, description)

    print(f"Top Classes: {top_classes}")
    print(f"Top Facets: {top_facets}")

    # Simulate Phase 4: Detailed Analysis
    print(f"\n🔍 PHASE 4: DETAILED ANALYSIS")
    analysis_results = {}

    for class_name in top_classes + top_facets:
        try:
            result = analyze_case_uco_class(
                tool_input={"class_name": class_name, "output_format": "markdown"})
            if result:
                analysis_results[class_name] = result
                print(f"  ✅ {class_name}: Analysis complete")
        except Exception as e:
            print(f"  ❌ {class_name}: Error - {e}")

    # Simulate Phase 5: Property Extraction (as per updated prompt)
    print(f"\n🔍 PHASE 5: PROPERTY EXTRACTION")
    extracted_properties = {}

    for class_name, markdown_result in analysis_results.items():
        properties = extract_properties_from_markdown(
            markdown_result, class_name)
        extracted_properties[class_name] = properties
        print(f"  {class_name}: {len(properties)} properties extracted")

    # Generate the actual agent report
    print(f"\n🔍 PHASE 6: GENERATING AGENT REPORT")
    report = generate_agent_report(
        test_data, top_classes, top_facets, analysis_results, extracted_properties)

    # Save the report
    with open('clean_agent_report.md', 'w') as f:
        f.write(report)

    print(f"✅ Agent report saved to: clean_agent_report.md")

    # Show the JSON output section
    print(f"\n📋 AGENT JSON OUTPUT:")
    json_section = extract_json_section(report)
    if json_section:
        print(json_section)
    else:
        print("No JSON section found in report")


def extract_properties_from_markdown(markdown_result, class_name):
    """Extract property names from markdown analysis result"""
    properties = []

    if not markdown_result:
        return properties

    lines = markdown_result.split('\n')
    in_property_table = False

    for line in lines:
        line = line.strip()

        if 'Property Shapes' in line or 'PROPERTY' in line:
            in_property_table = True
            continue

        if in_property_table:
            if line.startswith('|') and '|' in line[1:]:
                parts = line.split('|')
                if len(parts) >= 2:
                    prop_name = parts[1].strip()
                    if (prop_name and
                        prop_name != 'PROPERTY' and
                        prop_name != '---' and
                        prop_name != '**ArchiveFileFacet**' and
                        prop_name != '**File**' and
                        prop_name != '**Inherited**' and
                        not prop_name.startswith('**') and
                            not prop_name.startswith('-')):
                        properties.append(prop_name)
            elif line.startswith('#'):
                break
            elif not line:
                continue
            elif 'By the associated SHACL property shapes' in line:
                continue
            else:
                break

    return properties


def generate_agent_report(test_data, classes, facets, analysis_results, properties):
    """Generate the complete agent report as per the updated prompt"""

    report = f"""# Ontology Research Report

## Input Text

```json
{json.dumps(test_data, indent=2)}
```

## Summary

**Identified Artifacts:** {test_data.get('artifact_type', 'Unknown')}

**Forensic Significance:** {test_data.get('description', 'No description provided')}

**Relevant CASE/UCO Classes (Objects):** {', '.join(classes)}

**Applicable Facets (Property Bundles):** {', '.join(facets)}

**Class Properties:** {', '.join(properties.get(classes[0], []) if classes else [])}

**Facet Properties:** {', '.join(properties.get(facets[0], []) if facets else [])}

**Relationship Patterns:** Object-to-Facet relationships via hasFacet

## Mapping Rationale

**Artifact Identification:** The input is {test_data.get('artifact_type', 'Unknown')} records, confirmed by the presence of {test_data.get('artifact_type', 'Unknown')} in the artifact_type field.

"""

    # Add class documentation
    if classes:
        report += "## Detailed Class & Facet Documentation\n\n### Classes (Observable Objects)\n\n"
        for class_name in classes:
            if class_name in analysis_results:
                report += f"#### {class_name}\n\n"
                report += analysis_results[class_name]
                report += "\n\n"

    # Add facet documentation
    if facets:
        report += "### Facets (Property Bundles)\n\n"
        for facet_name in facets:
            if facet_name in analysis_results:
                report += f"#### {facet_name}\n\n"
                report += analysis_results[facet_name]
                report += "\n\n"

    # Add JSON output with real properties
    report += "## JSON Output\n\n```json\n"
    report += generate_json_output(test_data, classes, facets, properties)
    report += "\n```\n"

    return report


def generate_json_output(test_data, classes, facets, properties):
    """Generate the JSON output with real properties as per updated prompt"""

    json_data = {
        "artifacts": [test_data.get('artifact_type', 'Unknown')],
        "classes": classes,
        "facets": facets,
        "properties": {},
        "relationships": [],
        "analysis": f"Analysis of {test_data.get('artifact_type', 'Unknown')} records with {len(classes)} classes and {len(facets)} facets",
        "additional_details": {
            "note": "Properties extracted from actual CASE/UCO analysis results"
        }
    }

    # Add properties for each class and facet
    for class_name in classes + facets:
        if class_name in properties:
            json_data["properties"][class_name] = properties[class_name]
        else:
            json_data["properties"][class_name] = []

    # Add relationships
    for class_name in classes:
        for facet_name in facets:
            json_data["relationships"].append({
                "type": "hasFacet",
                "source": class_name,
                "target": facet_name
            })

    return json.dumps(json_data, indent=2)


def extract_json_section(report):
    """Extract the JSON section from the report"""
    lines = report.split('\n')
    in_json = False
    json_lines = []

    for line in lines:
        if line.strip().startswith('```json'):
            in_json = True
            continue
        elif line.strip().startswith('```') and in_json:
            break
        elif in_json:
            json_lines.append(line)

    return '\n'.join(json_lines) if json_lines else None


if __name__ == "__main__":
    simulate_agent_with_updated_prompt()
