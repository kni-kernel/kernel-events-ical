"""
Post-merge hook: generate iCal from YAML resources.
"""

from pathlib import Path
import sys

from parser import parse_events
from ical_gen import generate_ical


def main():
    """
    Main entry point for generating iCal artifacts. Used by the gh action.
    """
    project_root = Path(__file__).parent.parent
    resources_dir = project_root / "resources"
    ical_file = project_root / "artifacts" / "events.ical"
    
    print(f"Parsing events from {resources_dir}...")
    try:
        events = parse_events(resources_dir)
        print(f"Parsed {len(events)} events")
    except Exception as e:
        print(f"Error parsing events: {e}", file=sys.stderr)
        sys.exit(1)
    
    print("Generating iCal...")
    try:
        ical_content = generate_ical(events)
    except Exception as e:
        print(f"Error generating iCal: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Writing to {ical_file}...")
    with open(ical_file, 'w') as f:
        f.write(ical_content)
    
    print(f"Generated {ical_file}")
    print(f"Total events: {len(events)}")


if __name__ == "__main__":
    main()
