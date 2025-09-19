"""
CASE/UCO Ontology Analyzer
A comprehensive Python class for analyzing CASE/UCO ontology classes and properties.

Author: Generated from Jupyter Notebook Research
Date: August 27, 2025
"""

import sys
import requests
from typing import Dict, List, Any, Optional
from collections import defaultdict
import concurrent.futures
import threading

try:
    import rdflib
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'rdflib'])
    import rdflib

from rdflib import Graph, RDF, RDFS, OWL, Namespace


class CaseUcoAnalyzer:
    """
    Comprehensive analyzer for CASE/UCO ontology classes and properties.
    Provides methods to explore, analyze, and document CASE/UCO ontological structures.
    """

    def __init__(self):
        """Initialize the analyzer and load ontologies."""
        self.graph = Graph()
        self.loaded = False
        self._class_cache = {}
        self._property_cache = {}

        # SHACL namespace for shape analysis
        self.SHACL = Namespace("http://www.w3.org/ns/shacl#")

        # Ontology URLs
        self.uco_urls = {
            'uco-core': 'https://raw.githubusercontent.com/ucoProject/UCO/master/ontology/uco/core/core.ttl',
            'uco-observable': 'https://raw.githubusercontent.com/ucoProject/UCO/master/ontology/uco/observable/observable.ttl',
            'uco-action': 'https://raw.githubusercontent.com/ucoProject/UCO/master/ontology/uco/action/action.ttl',
            'uco-identity': 'https://raw.githubusercontent.com/ucoProject/UCO/master/ontology/uco/identity/identity.ttl',
            'uco-location': 'https://raw.githubusercontent.com/ucoProject/UCO/master/ontology/uco/location/location.ttl',
            'uco-marking': 'https://raw.githubusercontent.com/ucoProject/UCO/master/ontology/uco/marking/marking.ttl',
            'uco-pattern': 'https://raw.githubusercontent.com/ucoProject/UCO/master/ontology/uco/pattern/pattern.ttl',
            'uco-role': 'https://raw.githubusercontent.com/ucoProject/UCO/master/ontology/uco/role/role.ttl',
            'uco-tool': 'https://raw.githubusercontent.com/ucoProject/UCO/master/ontology/uco/tool/tool.ttl',
            'uco-types': 'https://raw.githubusercontent.com/ucoProject/UCO/master/ontology/uco/types/types.ttl',
            'uco-vocabulary': 'https://raw.githubusercontent.com/ucoProject/UCO/master/ontology/uco/vocabulary/vocabulary.ttl',
            'uco-analysis': 'https://raw.githubusercontent.com/ucoProject/UCO/master/ontology/uco/analysis/analysis.ttl',
            'uco-configuration': 'https://raw.githubusercontent.com/ucoProject/UCO/master/ontology/uco/configuration/configuration.ttl',
            'uco-time': 'https://raw.githubusercontent.com/ucoProject/UCO/master/ontology/uco/time/time.ttl',
            'uco-victim': 'https://raw.githubusercontent.com/ucoProject/UCO/master/ontology/uco/victim/victim.ttl',
            'case-complete': 'https://raw.githubusercontent.com/casework/CASE-Utilities-Python/main/case_utils/ontology/case-1.4.0.ttl'
        }

        # Load ontologies on initialization
        self._load_ontologies()

    def _load_single_ontology(self, name: str, url: str) -> tuple:
        """Load a single ontology and return (success, name, data, error)."""
        try:
            print(f"  Loading {name}...")
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            print(f"  ✅ {name} loaded successfully")
            return (True, name, response.text, None)
        except Exception as e:
            print(f"  ❌ Failed to load {name}: {e}")
            return (False, name, None, str(e))

    def _load_ontologies(self):
        """Load all CASE/UCO ontologies from official sources in parallel."""
        if self.loaded:
            return

        print("Loading CASE/UCO ontologies in parallel...")
        total_ontologies = len(self.uco_urls)
        
        # Use ThreadPoolExecutor for parallel loading with optimized workers
        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
            # Submit all download tasks
            future_to_name = {
                executor.submit(self._load_single_ontology, name, url): name 
                for name, url in self.uco_urls.items()
            }
            
            # Collect results as they complete
            loaded_count = 0
            failed_urls = []
            
            for future in concurrent.futures.as_completed(future_to_name):
                success, name, data, error = future.result()
                
                if success:
                    # Parse the ontology data
                    try:
                        self.graph.parse(data=data, format='turtle')
                        loaded_count += 1
                    except Exception as parse_error:
                        print(f"  ❌ Failed to parse {name}: {parse_error}")
                        failed_urls.append((name, future_to_name[future], str(parse_error)))
                else:
                    failed_urls.append((name, future_to_name[future], error))

        print(f"\nLoaded {loaded_count}/{len(self.uco_urls)} ontologies")
        
        # If some ontologies failed, show details but continue
        if failed_urls:
            print(f"\n⚠️ {len(failed_urls)} ontologies failed to load:")
            for name, url, error in failed_urls:
                print(f"  - {name}: {error}")
            print("Continuing with successfully loaded ontologies...")
        
        # Only proceed if we loaded at least some ontologies
        if loaded_count == 0:
            raise Exception("Failed to load any CASE/UCO ontologies. Check network connectivity.")
        
        self.loaded = True
        self._build_caches()


    def _build_caches(self):
        """Build internal caches for classes and properties."""
        # Cache all classes
        for cls in self.graph.subjects(RDF.type, OWL.Class):
            class_name = self._extract_local_name(str(cls))
            if class_name and len(class_name) > 1:
                self._class_cache[class_name] = {
                    'uri': str(cls),
                    'name': class_name
                }

        # Cache all properties
        for prop_type in [OWL.ObjectProperty, OWL.DatatypeProperty]:
            for prop in self.graph.subjects(RDF.type, prop_type):
                prop_name = self._extract_local_name(str(prop))
                if prop_name:
                    self._property_cache[prop_name] = {
                        'uri': str(prop),
                        'name': prop_name,
                        'type': 'ObjectProperty' if prop_type == OWL.ObjectProperty else 'DatatypeProperty'
                    }

    def _extract_local_name(self, uri: str) -> str:
        """Extract local name from URI."""
        if '#' in uri:
            return uri.split('#')[-1]
        elif '/' in uri:
            return uri.split('/')[-1]
        return uri

    def _get_superclass_hierarchy(self, class_name: str) -> List[str]:
        """Get complete superclass hierarchy using rdflib traversal."""
        if class_name not in self._class_cache:
            return []

        class_uri = self._class_cache[class_name]['uri']
        cls_ref = rdflib.URIRef(class_uri)

        hierarchy = []
        visited = set()

        # Use rdflib's traversal instead of SPARQL
        def traverse_superclasses(current_ref):
            if current_ref in visited:
                return
            visited.add(current_ref)

            for superclass_ref in self.graph.objects(current_ref, RDFS.subClassOf):
                if isinstance(superclass_ref, rdflib.URIRef):
                    local_name = self._extract_local_name(str(superclass_ref))
                    if local_name and local_name != class_name and local_name not in ['Thing', 'Resource']:
                        hierarchy.append(local_name)
                    traverse_superclasses(superclass_ref)

        traverse_superclasses(cls_ref)

        # Sort hierarchy with most general first (reverse order)
        return list(reversed(list(set(hierarchy))))  # Remove duplicates

    def _get_superclass_hierarchy_fallback(self, class_name: str) -> List[str]:
        """Fallback method for getting superclass hierarchy."""
        if class_name not in self._class_cache:
            return []

        hierarchy = []
        visited = set()
        current_class = class_name

        while current_class and current_class not in visited:
            visited.add(current_class)

            if current_class not in self._class_cache:
                break

            class_uri = self._class_cache[current_class]['uri']
            cls_ref = rdflib.URIRef(class_uri)

            parent_found = False
            for parent in self.graph.objects(cls_ref, RDFS.subClassOf):
                if isinstance(parent, rdflib.URIRef):
                    parent_name = self._extract_local_name(str(parent))
                    if parent_name and parent_name != current_class and parent_name not in visited:
                        hierarchy.append(parent_name)
                        current_class = parent_name
                        parent_found = True
                        break

            if not parent_found:
                break

        return hierarchy

    def _get_property_constraints(self, prop_uri: str) -> Dict[str, Any]:
        """Get property constraints from SHACL shapes."""
        prop_ref = rdflib.URIRef(prop_uri)
        constraints = {
            'datatype': None,
            'class': None,
            'min_count': None,
            'max_count': None,
            'node_kind': None,
            'rdfs_range': [],
            'rdfs_domain': []
        }

        # RDFS range/domain
        for range_val in self.graph.objects(prop_ref, RDFS.range):
            if isinstance(range_val, rdflib.URIRef):
                constraints['rdfs_range'].append(
                    self._extract_local_name(str(range_val)))

        for domain_val in self.graph.objects(prop_ref, RDFS.domain):
            if isinstance(domain_val, rdflib.URIRef):
                constraints['rdfs_domain'].append(
                    self._extract_local_name(str(domain_val)))

        # SHACL constraints
        for shape in self.graph.subjects(self.SHACL.targetClass, None):
            for prop_constraint in self.graph.objects(shape, self.SHACL.property):
                for path in self.graph.objects(prop_constraint, self.SHACL.path):
                    if str(path) == prop_uri:
                        for datatype in self.graph.objects(prop_constraint, self.SHACL.datatype):
                            constraints['datatype'] = self._extract_local_name(
                                str(datatype))

                        for cls in self.graph.objects(prop_constraint, self.SHACL['class']):
                            constraints['class'] = self._extract_local_name(
                                str(cls))

                        for min_count in self.graph.objects(prop_constraint, self.SHACL.minCount):
                            constraints['min_count'] = int(str(min_count))

                        for max_count in self.graph.objects(prop_constraint, self.SHACL.maxCount):
                            constraints['max_count'] = int(str(max_count))

                        for node_kind in self.graph.objects(prop_constraint, self.SHACL.nodeKind):
                            constraints['node_kind'] = self._extract_local_name(
                                str(node_kind))

        return constraints

    def get_shacl_property_shapes(self, class_name: str) -> Dict[str, Any]:
        """
        Extract SHACL property shapes for a class in CASE documentation format.
        Returns all properties available to instances of the class through SHACL shapes.

        Returns a dictionary with property names as keys and property details as values.
        Each property detail includes: sourceClass, propertyType, description, minCount, maxCount, localRange, globalRange
        """
        if not self.loaded:
            self.load_ontologies()

        if class_name not in self._class_cache:
            return {}

        # Get all properties for this class
        properties = self._analyze_class_properties(class_name)

        # Convert to SHACL format expected by export_to_markdown
        shacl_properties = {}

        # Process facet properties
        for prop in properties['facet']:
            constraints = prop['constraints']
            shacl_properties[prop['name']] = {
                'sourceClass': f"{class_name}Facet",
                'propertyType': prop['type'],
                'description': prop['description'],
                'minCount': constraints.get('min_count', 0),
                'maxCount': constraints.get('max_count', 1),
                'localRange': ', '.join(constraints.get('rdfs_range', [])),
                'globalRange': constraints.get('class', 'N/A')
            }

        # Process inherited properties
        for prop in properties['inherited']:
            constraints = prop['constraints']
            source_class = prop['source'].replace('inherited_from_', '') if 'inherited_from_' in prop['source'] else 'Inherited'
            shacl_properties[prop['name']] = {
                'sourceClass': source_class,
                'propertyType': prop['type'],
                'description': prop['description'],
                'minCount': constraints.get('min_count', 0),
                'maxCount': constraints.get('max_count', 1),
                'localRange': ', '.join(constraints.get('rdfs_range', [])),
                'globalRange': constraints.get('class', 'N/A')
            }

        # Process semantic properties
        for prop in properties['semantic']:
            constraints = prop['constraints']
            shacl_properties[prop['name']] = {
                'sourceClass': 'Semantic',
                'propertyType': prop['type'],
                'description': prop['description'],
                'minCount': constraints.get('min_count', 0),
                'maxCount': constraints.get('max_count', 1),
                'localRange': ', '.join(constraints.get('rdfs_range', [])),
                'globalRange': constraints.get('class', 'N/A')
            }

        return shacl_properties

    def _analyze_class_properties(self, class_name: str) -> Dict[str, List[Dict]]:
        """Analyze properties for a class by source type."""
        facet_props = []
        inherited_props = []
        semantic_props = []

        # Facet properties
        facet_name = f"{class_name}Facet"
        facet_prop_names = set()  # Track names to avoid duplicates

        if facet_name in self._class_cache:
            facet_uri = self._class_cache[facet_name]['uri']
            facet_ref = rdflib.URIRef(facet_uri)

            for shape in self.graph.subjects(self.SHACL.targetClass, facet_ref):
                for prop_path in self.graph.objects(shape, self.SHACL.property):
                    for path in self.graph.objects(prop_path, self.SHACL.path):
                        prop_name = self._extract_local_name(str(path))

                        # Avoid duplicates
                        if (prop_name in self._property_cache and
                                prop_name not in facet_prop_names):

                            prop_info = self._property_cache[prop_name]
                            prop_ref = rdflib.URIRef(prop_info['uri'])
                            comments = list(self.graph.objects(
                                prop_ref, RDFS.comment))

                            facet_props.append({
                                'name': prop_name,
                                'uri': prop_info['uri'],
                                'type': prop_info['type'],
                                'description': str(comments[0]) if comments else f"{prop_name} property",
                                'constraints': self._get_property_constraints(prop_info['uri']),
                                'source': 'facet'
                            })
                            facet_prop_names.add(prop_name)

        # Inherited properties - Get properties from ALL superclasses
        superclasses = self._get_superclass_hierarchy(class_name)
        inherited_prop_names = set()  # Track names to avoid duplicates

        for superclass in superclasses:
            # Skip if superclass not in cache
            if superclass not in self._class_cache:
                continue

            # Get facet properties from superclass
            superclass_facet = f"{superclass}Facet"
            if superclass_facet in self._class_cache:
                facet_uri = self._class_cache[superclass_facet]['uri']
                facet_ref = rdflib.URIRef(facet_uri)

                for shape in self.graph.subjects(self.SHACL.targetClass, facet_ref):
                    for prop_path in self.graph.objects(shape, self.SHACL.property):
                        for path in self.graph.objects(prop_path, self.SHACL.path):
                            prop_name = self._extract_local_name(str(path))

                            # Avoid duplicates and don't inherit properties that are already facet properties
                            if (prop_name in self._property_cache and
                                prop_name not in inherited_prop_names and
                                    prop_name not in [p['name'] for p in facet_props]):

                                prop_info = self._property_cache[prop_name]
                                prop_ref = rdflib.URIRef(prop_info['uri'])
                                comments = list(self.graph.objects(
                                    prop_ref, RDFS.comment))

                                inherited_props.append({
                                    'name': prop_name,
                                    'uri': prop_info['uri'],
                                    'type': prop_info['type'],
                                    'description': str(comments[0]) if comments else f"{prop_name} property",
                                    'constraints': self._get_property_constraints(prop_info['uri']),
                                    'source': f'inherited_from_{superclass}'
                                })
                                inherited_prop_names.add(prop_name)

        # Also add common UCO properties if not already included
        common_props = ['createdBy', 'description',
                        'hasFacet', 'name', 'tag', 'externalReference']
        for prop_name in common_props:
            if (prop_name in self._property_cache and
                prop_name not in inherited_prop_names and
                    prop_name not in [p['name'] for p in facet_props]):

                prop_info = self._property_cache[prop_name]
                prop_ref = rdflib.URIRef(prop_info['uri'])
                comments = list(self.graph.objects(prop_ref, RDFS.comment))

                inherited_props.append({
                    'name': prop_name,
                    'uri': prop_info['uri'],
                    'type': prop_info['type'],
                    'description': str(comments[0]) if comments else f"{prop_name} property",
                    'constraints': self._get_property_constraints(prop_info['uri']),
                    'source': 'inherited_common'
                })
                inherited_prop_names.add(prop_name)

        # Semantic properties (properties mentioning class in description)
        class_lower = class_name.lower()
        for prop_name, prop_info in self._property_cache.items():
            prop_ref = rdflib.URIRef(prop_info['uri'])
            comments = list(self.graph.objects(prop_ref, RDFS.comment))

            if comments:
                desc = str(comments[0]).lower()
                if class_lower in desc and prop_name not in [p['name'] for p in facet_props + inherited_props]:
                    semantic_props.append({
                        'name': prop_name,
                        'uri': prop_info['uri'],
                        'type': prop_info['type'],
                        'description': str(comments[0]),
                        'constraints': self._get_property_constraints(prop_info['uri']),
                        'source': 'semantic'
                    })

        return {
            'facet': facet_props,
            'inherited': inherited_props,
            'semantic': semantic_props
        }

    # PUBLIC METHODS

    def list_all_classes(self) -> List[Dict[str, str]]:
        """
        Get list of all available CASE/UCO classes.

        Returns:
            List of dictionaries with class name and URI
        """
        classes = []
        for class_name, class_info in self._class_cache.items():
            classes.append({
                'name': class_name,
                'uri': class_info['uri']
            })

        return sorted(classes, key=lambda x: x['name'])

    def get_class_summary(self, class_name: str) -> Dict[str, Any]:
        """
        Get basic summary information for a class.

        Args:
            class_name: Name of the CASE/UCO class

        Returns:
            Dictionary with basic class information
        """
        if class_name not in self._class_cache:
            return {'error': f"Class '{class_name}' not found in CASE/UCO ontologies"}

        class_uri = self._class_cache[class_name]['uri']
        cls_ref = rdflib.URIRef(class_uri)

        # Get description
        comments = list(self.graph.objects(cls_ref, RDFS.comment))
        description = str(
            comments[0]) if comments else f"CASE/UCO {class_name} class"

        # Get hierarchy
        hierarchy = self._get_superclass_hierarchy(class_name)

        # Get property counts
        properties = self._analyze_class_properties(class_name)

        return {
            'name': class_name,
            'uri': class_uri,
            'description': description,
            'superclasses': hierarchy,
            'superclass_count': len(hierarchy),
            'property_counts': {
                'facet': len(properties['facet']),
                'inherited': len(properties['inherited']),
                'semantic': len(properties['semantic']),
                'total': len(properties['facet']) + len(properties['inherited']) + len(properties['semantic'])
            },
            'has_facet_pattern': len(properties['facet']) > 0
        }

    def get_class_details(self, class_name: str) -> Dict[str, Any]:
        """
        Get complete detailed information for a class.

        Args:
            class_name: Name of the CASE/UCO class

        Returns:
            Dictionary with complete class analysis
        """
        if class_name not in self._class_cache:
            return {'error': f"Class '{class_name}' not found in CASE/UCO ontologies"}

        # Get basic info
        summary = self.get_class_summary(class_name)
        if 'error' in summary:
            return summary

        # Get detailed properties
        properties = self._analyze_class_properties(class_name)

        # Combine all properties
        all_properties = properties['facet'] + \
            properties['inherited'] + properties['semantic']

        return {
            'class_information': {
                'name': summary['name'],
                'uri': summary['uri'],
                'description': summary['description']
            },
            'superclasses': {
                'count': summary['superclass_count'],
                'list': summary['superclasses']
            },
            'properties': {
                'facet_properties': properties['facet'],
                'inherited_properties': properties['inherited'],
                'semantic_properties': properties['semantic'],
                'all_properties': all_properties
            },
            'summary': {
                'total_properties': len(all_properties),
                'facet_properties': len(properties['facet']),
                'inherited_properties': len(properties['inherited']),
                'semantic_properties': len(properties['semantic'])
            },
            'usage_pattern': f"Use 'hasFacet' property to link to {class_name}Facet" if properties['facet'] else "Direct property usage"
        }

    def compare_classes(self, *class_names) -> Dict[str, Any]:
        """
        Compare multiple CASE/UCO classes.

        Args:
            *class_names: Variable number of class names to compare

        Returns:
            Dictionary with comparison results
        """
        comparison = {
            'classes': {},
            'summary_table': []
        }

        for class_name in class_names:
            summary = self.get_class_summary(class_name)
            if 'error' not in summary:
                comparison['classes'][class_name] = summary
                comparison['summary_table'].append({
                    'class': class_name,
                    'facet_props': summary['property_counts']['facet'],
                    'inherited_props': summary['property_counts']['inherited'],
                    'semantic_props': summary['property_counts']['semantic'],
                    'total_props': summary['property_counts']['total'],
                    'superclasses': summary['superclass_count'],
                    'has_facet': summary['has_facet_pattern']
                })

        return comparison

    def search_classes(self, keyword: str) -> List[Dict[str, str]]:
        """
        Search for classes by keyword in name or description.

        Args:
            keyword: Search term

        Returns:
            List of matching classes
        """
        keyword_lower = keyword.lower()
        matches = []

        for class_name in self._class_cache:
            # Check name
            if keyword_lower in class_name.lower():
                summary = self.get_class_summary(class_name)
                matches.append({
                    'name': class_name,
                    'uri': summary['uri'],
                    'description': summary['description'],
                    'match_type': 'name'
                })
            else:
                # Check description
                summary = self.get_class_summary(class_name)
                if keyword_lower in summary['description'].lower():
                    matches.append({
                        'name': class_name,
                        'uri': summary['uri'],
                        'description': summary['description'],
                        'match_type': 'description'
                    })

        return sorted(matches, key=lambda x: x['name'])

    def get_property_details(self, property_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific property.

        Args:
            property_name: Name of the property

        Returns:
            Dictionary with property details
        """
        if property_name not in self._property_cache:
            return {'error': f"Property '{property_name}' not found in CASE/UCO ontologies"}

        prop_info = self._property_cache[property_name]
        prop_ref = rdflib.URIRef(prop_info['uri'])

        # Get description
        comments = list(self.graph.objects(prop_ref, RDFS.comment))
        description = str(
            comments[0]) if comments else f"{property_name} property"

        # Get constraints
        constraints = self._get_property_constraints(prop_info['uri'])

        return {
            'name': property_name,
            'uri': prop_info['uri'],
            'type': prop_info['type'],
            'description': description,
            'constraints': constraints
        }

    def export_to_markdown(self, class_name: str) -> str:
        """
        Generate markdown documentation for a class using SHACL property shapes.

        Args:
            class_name: Name of the CASE/UCO class

        Returns:
            Markdown formatted string
        """
        # Get basic details and SHACL property shapes
        details = self.get_class_details(class_name)
        if 'error' in details:
            return f"Error: {details['error']}"

        shacl_properties = self.get_shacl_property_shapes(class_name)

        md_lines = []

        # Header
        md_lines.append(f"# {details['class_information']['name']}")
        md_lines.append("")
        md_lines.append(f"**URI:** `{details['class_information']['uri']}`")
        md_lines.append("")
        md_lines.append(
            f"**Description:** {details['class_information']['description']}")
        md_lines.append("")

        # Superclasses
        if details['superclasses']['count'] > 0:
            md_lines.append(
                f"## Superclasses ({details['superclasses']['count']})")
            md_lines.append("")
            for i, superclass in enumerate(details['superclasses']['list'], 1):
                md_lines.append(f"{i}. {superclass}")
            md_lines.append("")

        # SHACL Property Shapes (CASE Documentation Format)
        if shacl_properties:
            md_lines.append("## Property Shapes")
            md_lines.append("")
            md_lines.append("By the associated SHACL property shapes, instances of " +
                            f"{class_name} can have the following properties:")
            md_lines.append("")
            md_lines.append(
                "| PROPERTY | PROPERTY TYPE | DESCRIPTION | MIN COUNT | MAX COUNT | LOCAL RANGE | GLOBAL RANGE |")
            md_lines.append(
                "|----------|---------------|-------------|-----------|-----------|-------------|--------------|")

            # Group properties by source class
            by_class = {}
            for prop_name, prop_data in shacl_properties.items():
                source_class = prop_data['sourceClass']
                if source_class not in by_class:
                    by_class[source_class] = []
                by_class[source_class].append((prop_name, prop_data))

            # Sort classes by hierarchy importance
            class_order = ['UcoObject', 'ObservableObject',
                           'Observable', 'UcoThing', 'Item']
            facet_classes = [
                cls for cls in by_class.keys() if cls not in class_order]

            for source_class in class_order + facet_classes:
                if source_class in by_class:
                    # Add class header row
                    md_lines.append(f"| **{source_class}** | | | | | | |")

                    # Add properties for this class
                    for prop_name, prop_data in sorted(by_class[source_class]):
                        desc = prop_data['description'][:50] + '...' if len(
                            prop_data['description']) > 50 else prop_data['description']
                        md_lines.append(f"| {prop_name} | {prop_data['propertyType']} | {desc} | " +
                                        f"{prop_data['minCount']} | {prop_data['maxCount']} | " +
                                        f"{prop_data['localRange']} | {prop_data['globalRange']} |")
            md_lines.append("")

        # Count properties by type for summary
        facet_count = sum(1 for prop in shacl_properties.values()
                          if 'Facet' in prop['sourceClass'])
        inherited_count = len(shacl_properties) - facet_count

        # Summary
        md_lines.append("## Summary")
        md_lines.append("")
        md_lines.append(f"- **Total Properties:** {len(shacl_properties)}")
        md_lines.append(f"- **Facet Properties:** {facet_count}")
        md_lines.append(f"- **Inherited Properties:** {inherited_count}")
        md_lines.append(f"- **Semantic Properties:** 0")
        md_lines.append(
            f"- **Usage Pattern:** Use 'hasFacet' property to link to {class_name}Facet" if facet_count > 0 else "Direct property usage")

        return "\n".join(md_lines)

    def print_class_summary(self, class_name: str):
        """Print a formatted summary of a class."""
        summary = self.get_class_summary(class_name)
        if 'error' in summary:
            print(f"Error: {summary['error']}")
            return

        print(f"Class: {summary['name']}")
        print(f"URI: {summary['uri']}")
        print(f"Description: {summary['description']}")
        print(f"Superclasses: {summary['superclass_count']}")
        print(f"Properties: {summary['property_counts']['total']} total")
        print(f"  - Facet: {summary['property_counts']['facet']}")
        print(f"  - Inherited: {summary['property_counts']['inherited']}")
        print(f"  - Semantic: {summary['property_counts']['semantic']}")
        print(f"Has Facet Pattern: {summary['has_facet_pattern']}")

    def print_all_classes(self):
        """Print list of all available classes."""
        classes = self.list_all_classes()
        print(f"Available CASE/UCO Classes ({len(classes)} total):")
        print("=" * 50)

        for i, cls in enumerate(classes, 1):
            print(f"{i:3d}. {cls['name']}")

        print("=" * 50)
        print("Use get_class_details(class_name) for detailed analysis")

    # ==== NEW HIGH-PRIORITY METHODS FROM FAQ ANALYSIS ====

    def analyze_facets(self) -> Dict[str, Any]:
        """
        HIGH PRIORITY: Analyze all Facet classes in the CASE/UCO ontology

        Returns:
            Dict containing facet analysis results with categorization
        """
        # Use rdflib traversal instead of SPARQL to avoid parsing issues
        facet_uri = "https://ontology.unifiedcyberontology.org/uco/core/Facet"
        facet_ref = rdflib.URIRef(facet_uri)

        facets = []
        visited = set()

        def traverse_subclasses(current_ref):
            if current_ref in visited:
                return
            visited.add(current_ref)

            for subclass_ref in self.graph.subjects(RDFS.subClassOf, current_ref):
                if isinstance(subclass_ref, rdflib.URIRef):
                    facet_name = self._extract_local_name(str(subclass_ref))
                    if facet_name and facet_name != 'Facet':
                        facets.append(facet_name)
                    traverse_subclasses(subclass_ref)

        traverse_subclasses(facet_ref)

        return {
            'total_facets': len(facets),
            'facet_list': sorted(facets),
            'categories': self._categorize_facets(facets)
        }

    def get_compatible_facets(self, class_name: str) -> Dict[str, Any]:
        """
        HIGH PRIORITY: Get facets compatible with a given class (duck typing support)

        Args:
            class_name: Name of the CASE/UCO class

        Returns:
            Dict containing compatible facets and duck typing information
        """
        if class_name not in self._class_cache:
            return {'error': f"Class '{class_name}' not found"}

        # Get all facets
        all_facets = self.analyze_facets()['facet_list']

        # For duck typing, any facet can theoretically be applied to any object
        # But we can suggest relevant ones based on naming patterns
        relevant_facets = self._find_relevant_facets(class_name, all_facets)

        return {
            'class_name': class_name,
            'total_available_facets': len(all_facets),
            'relevant_facets': relevant_facets,
            'duck_typing_principle': 'Any rational combination of facets can be applied',
            'usage_example': f"{class_name} + {relevant_facets[0] if relevant_facets else 'AnyFacet'}"
        }

    def analyze_relationships(self) -> Dict[str, Any]:
        """
        HIGH PRIORITY: Analyze ObservableRelationship patterns and connection types

        Returns:
            Dict containing relationship analysis results
        """
        # Use rdflib traversal instead of SPARQL to avoid parsing issues
        relationship_uri = "https://ontology.unifiedcyberontology.org/uco/observable/ObservableRelationship"
        relationship_ref = rdflib.URIRef(relationship_uri)

        relationships = []
        visited = set()

        def traverse_relationship_subclasses(current_ref):
            if current_ref in visited:
                return
            visited.add(current_ref)

            for subclass_ref in self.graph.subjects(RDFS.subClassOf, current_ref):
                if isinstance(subclass_ref, rdflib.URIRef):
                    rel_name = self._extract_local_name(str(subclass_ref))
                    if rel_name and rel_name != 'ObservableRelationship':
                        relationships.append(rel_name)
                    traverse_relationship_subclasses(subclass_ref)

        traverse_relationship_subclasses(relationship_ref)

        # Also search for any class with "relationship" in the name using rdflib
        general_relationships = []
        for cls in self.graph.subjects(RDF.type, OWL.Class):
            cls_name = self._extract_local_name(str(cls))
            if cls_name and "relationship" in cls_name.lower() and len(cls_name) > 2 and cls_name not in relationships:
                general_relationships.append(cls_name)

        return {
            'observable_relationships': relationships,
            'general_relationships': general_relationships,
            'total_relationship_types': len(relationships) + len(general_relationships),
            'common_patterns': self._get_common_relationship_patterns()
        }

    # ==== HELPER METHODS FOR NEW FUNCTIONALITY ====

    def _categorize_facets(self, facets: List[str]) -> Dict[str, List[str]]:
        """Dynamically categorize facets by discovering patterns in their names"""
        # Let the LLM handle categorization based on facet names
        # This method just returns the raw list for dynamic processing
        return {
            'all_facets': sorted(facets),
            'total_count': len(facets)
        }

    def _find_relevant_facets(self, class_name: str, all_facets: List[str]) -> List[str]:
        """Find facets most relevant to a given class using simple name matching"""
        relevant = []
        class_lower = class_name.lower()

        # Direct name matching - let LLM handle semantic relationships
        for facet in all_facets:
            if class_lower in facet.lower() or facet.lower() in class_lower:
                relevant.append(facet)

        return list(set(relevant))[:10]  # Return unique, limit to 10

    def _get_common_relationship_patterns(self) -> List[str]:
        """Dynamically discover relationship patterns from the ontology data"""
        # Use rdflib traversal instead of SPARQL to avoid parsing issues
        patterns = []
        for prop in self.graph.subjects(RDF.type, OWL.ObjectProperty):
            prop_name = self._extract_local_name(str(prop))
            if prop_name and len(prop_name) > 2:
                prop_lower = prop_name.lower()
                if ("relation" in prop_lower or
                    "connect" in prop_lower or
                        "link" in prop_lower):
                    patterns.append(prop_name)

        return patterns[:10]  # Return first 10 discovered patterns


# Example usage and testing
if __name__ == "__main__":
    # Create analyzer instance
    analyzer = CaseUcoAnalyzer()

    # Example usage
    print("CASE/UCO Analyzer - Example Usage")
    print("=" * 40)

    # List some classes
    classes = analyzer.list_all_classes()
    print(f"Total classes available: {len(classes)}")

    # Analyze a specific class
    print("\nAnalyzing WindowsPrefetch class:")
    analyzer.print_class_summary('WindowsPrefetch')

    # Compare classes
    print("\nComparing Event vs File:")
    comparison = analyzer.compare_classes('Event', 'File')
    for row in comparison['summary_table']:
        print(
            f"{row['class']}: {row['total_props']} total props, {row['facet_props']} facet")
