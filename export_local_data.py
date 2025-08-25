#!/usr/bin/env python
"""
Script to export local data for migration to production
Run this locally to create a data dump for your production database
"""

import os
import django
from django.core.management import execute_from_command_line

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'undiscovered_destinations.settings')
django.setup()

if __name__ == '__main__':
    print("Exporting local data...")
    
    # Export all data to JSON files
    execute_from_command_line(['manage.py', 'dumpdata', 'core', '--indent', '2', '-o', 'local_data_backup.json'])
    
    print("✅ Data exported to local_data_backup.json")
    print("📝 To import this data in production:")
    print("   1. Upload local_data_backup.json to your production server")
    print("   2. Run: python manage.py loaddata local_data_backup.json")
