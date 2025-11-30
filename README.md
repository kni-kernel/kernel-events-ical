# Kernel Events iCal

Automated event management system that generates iCalendar files from YAML definitions with template inheritance.

## Architecture

### Event Definitions (`./resources/**/*.yaml`)

Events are defined in YAML files. All YAML files are concatenated - order and file names don't matter.

**Template inheritance via `templates`:**

```yaml
# Template definition
lecture_hall_A:
  template: true
  location: Lecture Hall A
  x: 321
  y: 321

# Event using template
lecture_1:
  templates: [lecture_hall_A]
  summary: Introduction to Programming
  dtstart: 2024-01-15T10:00:00
```

**Result after parsing:**
```python
{
  "lecture_1": {
    "name": "lecture_1",
    "location": "Lecture Hall A",
    "x": 321,
    "y": 321,
    "summary": "Introduction to Programming",
    "dtstart": "2024-01-15T10:00:00"
  }
}
```

### Conventions for where events should go
* normal events - `YYYY-MM.yaml` - ordered from earliest to latest
* event types (lecture, kernel starter, etc.) - `event_types/*.yaml`
* locations - `locations/*.yaml`

Templates (`template: true`) are excluded from final output but provide scaffolding for inheritance.

### Workflow

1. **Define** events in `./resources/*.yaml`
2. **Parse** YAML files → consolidated dictionary
3. **Export** dictionary → `./artifacts/events.ical`
4. **Auto-commit** via GitHub Action on every main branch commit
5. **Subscribe** in Google Calendar using raw GitHub URL:
   ```
   https://raw.githubusercontent.com/kni-kernel/kernel-events-ical/refs/heads/main/artifacts/events.ical
   ```

### GitHub Action

Triggers on push to `main` (excluding bot commits), regenerates `events.ical`, and commits changes.

## Usage

### Setup

```bash
pip install -r requirements.txt
```

### Manual Generation

```bash
python src/post_merge_hook.py
```

Output: `./artifacts/events.ical`

### Event definitions

**Event Properties that should be in every non-template event after template resolution:**
- `name` - should be unique, taken from events' top-level keys
- `title` - Event title, if not specified, name is used
- `dtstart` - Start datetime (ISO 8601: `2024-01-15T10:00:00`)
- `dtend` - End datetime (or use `duration`)
- `duration` - Duration string (`2h`, `30m`, `1h30m`)
- `location` - Event location
- `description` - Event description
- `url` - Related URL
- `status` - should be one of `CONFIRMED`, `TENTATIVE`, `CANCELLED` (case-insensitive)

Events should have either `dtstart` or `dtend`, not neither, not both. All fields are optional except for these and `dtend`.

### Subscribing to Calendar

Add this URL to your calendar app:
```
https://raw.githubusercontent.com/kni-kernel/kernel-events-ical/refs/heads/main/artifacts/events.ical
```

## Roadmap

- GitHub Pages for embedded-calendar view, events list view (or on official kernel site)
- Auto-publish to Facebook events
- Discord/Instagram/E-mail announcements
- Messenger bot notifications
- Unit tests, for now it is fine without them, but will come in handy once things go more complex

## Implementation

### Core Components

- **`src/parser.py`** - YAML resource loader with templates resolution
- **`src/ical_gen.py`** - RFC 5545 iCalendar generator
- **`src/post_merge_hook.py`** - Orchestration script (parse → generate → write iCal artifacts)
- **`.github/workflows/generate-ical.yml`** - GitHub Action for automatic regeneration

### Testing

```bash
# Test full pipeline locally
python src/post_merge_hook.py
```

It is recommended that you do not regenerate events and `git add artifacts/events.ical` yourself, but rely on the gh action post-commit hook.
