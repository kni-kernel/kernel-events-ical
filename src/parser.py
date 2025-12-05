"""
YAML event parser with template inheritance.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict


class CircularDependencyError(Exception):
    """Raised when circular template dependencies are detected."""
    pass


def load_yaml_resources(resources_dir: Path) -> Dict[str, Any]:
    """
    Load and concatenate all YAML files from resources directory.
    
    Args:
        resources_dir: Path to directory containing YAML files
        
    Returns:
        Dictionary of all event definitions
    """
    if not resources_dir.exists():
        return {}
    resources = {}

    for file in resources_dir.rglob("*"):
        if file.is_dir():
            continue
        with open(file, 'r') as f:
            for name, event in yaml.safe_load(f).items():
                if "name" in event:
                    raise ValueError(f"Event must not have an explicit name (it should be deduced from event key): {event}")
                event["name"] = name
                if event["name"] in resources:
                    raise ValueError(f"Duplicate event name: {event['name']}")
                resources[event["name"]] = event

    return resources


def topological_sort(resources: Dict[str, Any]) -> List[str]:
    """
    Top sort templates prior to template resolution
    """
    graph = defaultdict(list)
    in_degree = defaultdict(int)
    all_nodes = set(resources.keys())
    
    for name, config in resources.items():
        templates = config.get('templates', [])
        templates = [templates] if isinstance(templates, str) else templates

        for template in templates:
            if template not in resources:
                raise ValueError(f"Template {template} not found (used by {name})")
            graph[template].append(name)
            in_degree[name] += 1

    queue = [node for node in all_nodes if not in_degree[node]]
    result = []
    
    while queue:
        node = queue.pop(0)
        result.append(node)
        
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    if len(result) != len(all_nodes):
        raise CircularDependencyError("Circular template dependencies detected. Did not manage to perform top-sort.")
    
    return result


def resolve_templates(resources: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Resolve template inheritance
    """
    resolved = {}
    
    for name in topological_sort(resources):
        object = resources[name]

        curr_resolved = {}
        
        templates = object.get('templates', [])
        templates = [templates] if isinstance(templates, str) else templates

        for template_name in templates:
            curr_resolved |= resolved[template_name]
        curr_resolved |= object
        if 'template' not in object:
            curr_resolved.pop('template', False)
        else:
            curr_resolved['template'] = object['template']

        resolved[name] = curr_resolved
    
    return {name: config for name, config in resolved.items() if not config.get('template', False)}


def parse_events(resources_dir: Path = Path("./resources")) -> Dict[str, Dict[str, Any]]:
    """
    Parse events from YAML files with template inheritance.
    E.g. (below would be ):

    ```
    lecture_hall_A:
      template: true
      location: Lecture Hall A

    lecture_1:
      templates: [lecture_hall_A]
      summary: Introduction to Programming
      dtstart: 2024-01-15T10:00:00
    ```

    should resolve to:

    ```
    {
        "lecture_1": {
            "name": "lecture_1",
            "location": "Lecture Hall A",
            "summary": "Introduction to Programming",
            "dtstart": "2024-01-15T10:00:00"
        }
    }
    ```
    """
    raw_resources = load_yaml_resources(resources_dir)
    return resolve_templates(raw_resources)
