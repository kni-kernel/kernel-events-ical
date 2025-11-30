"""
iCalendar (RFC 5545) generator from parsed event dictionary.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any

from icalendar import Calendar, Event


def parse_duration(duration: str) -> timedelta:
    """
    Parse duration string like '2h', '30m', '1h30m'.
    
    Args:
        duration: Duration string
        
    Returns:
        timedelta object
    """
    total_minutes = 0
    
    if 'h' in duration:
        parts = duration.split('h')
        total_minutes += int(parts[0]) * 60
        duration = parts[1] if len(parts) > 1 else ''
    
    if 'm' in duration:
        parts = duration.split('m')
        if parts[0]:
            total_minutes += int(parts[0])
    
    return timedelta(minutes=total_minutes)


def generate_uid(event_name: str) -> str:
    return f"{event_name}@kernel-events"


def parse_schema_to_description(schema, event_dict):
    """
    Parse multi-line schema string to description

    Example:
    schema = "A lecture on {title} will take place on {dtstart} in {location}"
    event_dict = {
        'title': 'Introduction to Programming',
        'dtstart': '2024-01-15T10:00:00',
        'location': 'Lecture Hall A',
    }
    parse_schema_to_description(schema, event_dict) -> "A lecture on Introduction to Programming will take place on 2024-01-15T10:00:00 in Lecture Hall A"
    One can use variables from the event_dict dictionary.
    :param schema: schema string with variable expansion
    :return: the resolved description
    """
    return schema.format(**event_dict)


def event_to_vevent(name: str, event_dict: Dict[str, Any]) -> Event:
    """
    Convert event dictionary to icalendar Event component.
    
    Args:
        name: Event identifier
        event_dict: Event properties dictionary
        
    Returns:
        icalendar Event object
    """
    event = Event()

    event.add('uid', event_dict.get('uid', generate_uid(name)))
    event.add('dtstamp', datetime.now(timezone.utc))
    
    dtstart = event_dict['dtstart']
    event.add('dtstart', dtstart)

    if not (('dtend' in event_dict) ^ ('duration' in event_dict)):
        raise ValueError(f"Event must have either dtend or duration, not neither or both. Event: {event_dict}")
    if 'dtend' in event_dict:
        event.add('dtend', event_dict['dtend'])
    else:
        duration_delta = parse_duration(event_dict['duration'])
        event.add('dtend', dtstart + duration_delta)
    
    if 'title' in event_dict:
        event.add('summary', event_dict['title'])
    else:
        # make name be the summary if title does not exist
        event.add('summary', event_dict['name'])
    
    if 'description' in event_dict and 'schema' not in event_dict:
        event.add('description', event_dict['description'])
    elif 'schema' in event_dict:
        event.add('description', parse_schema_to_description(event_dict['schema'], event_dict))

    if 'location' in event_dict:
        event.add('location', event_dict['location'])
    
    if 'status' in event_dict:
        event.add('status', event_dict['status'].upper())
    
    if 'url' in event_dict:
        event.add('url', event_dict['url'])
    
    return event


def generate_ical(events: Dict[str, Dict[str, Any]], 
                  calendar_name: str = "Wydarzenia KNI KERNEL@AGH",
                  timezone: str = "Europe/Warsaw") -> str:
    """
    Generate complete iCalendar file from events dictionary.
    
    Args:
        events: Dictionary of event definitions
        calendar_name: Calendar display name
        timezone: Timezone identifier
        
    Returns:
        Complete iCal file content as string
    """
    cal = Calendar()
    
    cal.add('prodid', '-//KNI Kernel//EventsAutoPublisher//PL')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', calendar_name)
    cal.add('x-wr-timezone', timezone)
    cal.add('calscale', 'GREGORIAN')
    cal.add('method', 'PUBLISH')
    
    for name, event_dict in events.items():
        event = event_to_vevent(name, event_dict)
        cal.add_component(event)
    
    return cal.to_ical().decode('utf-8')
