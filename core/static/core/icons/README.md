# Icons Directory

This directory contains custom icons for the Undiscovered Destinations application.

## Usage

To use icons in your Django templates:

```html
{% load static %}
<img src="{% static 'core/icons/icon-name.svg' %}" alt="Icon description">
```

## File Formats

- **SVG**: Preferred format for scalable vector icons
- **PNG**: For raster icons with transparency
- **ICO**: For favicons

## Naming Convention

Use descriptive names with hyphens:
- `dashboard-icon.svg`
- `user-profile.svg`
- `financial-analysis.svg`
- `tour-departure.svg`

## Organization

Consider creating subdirectories for different categories:
- `navigation/` - Menu and navigation icons
- `actions/` - Button and action icons
- `status/` - Status indicators and badges
- `financial/` - Financial and analytics icons
