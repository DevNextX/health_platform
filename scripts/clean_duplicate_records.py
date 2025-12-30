"""
Clean duplicate health records.
Keep the earliest record (by created_at) for each member+timestamp(minute) combination.

Usage:
    python scripts/clean_duplicate_records.py --dry-run    # Preview what would be deleted
    python scripts/clean_duplicate_records.py              # Actually delete duplicates
"""
import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.extensions import db
from src.models import HealthRecord, RecordSubject
from src.app import create_app
from sqlalchemy import and_


def truncate_to_minute(dt):
    """Truncate datetime to minute precision"""
    return dt.replace(second=0, microsecond=0)


def find_duplicates():
    """Find all duplicate records grouped by member+timestamp(minute)"""
    # Get all records with their associated member
    records_with_member = db.session.query(
        HealthRecord.id,
        HealthRecord.timestamp,
        HealthRecord.created_at,
        RecordSubject.member_id
    ).join(
        RecordSubject, HealthRecord.id == RecordSubject.record_id
    ).order_by(
        RecordSubject.member_id,
        HealthRecord.timestamp,
        HealthRecord.created_at
    ).all()
    
    # Group by member_id + truncated timestamp
    groups = {}
    for rec in records_with_member:
        truncated_ts = truncate_to_minute(rec.timestamp)
        key = (rec.member_id, truncated_ts)
        if key not in groups:
            groups[key] = []
        groups[key].append({
            'id': rec.id,
            'timestamp': rec.timestamp,
            'created_at': rec.created_at,
            'member_id': rec.member_id
        })
    
    # Find groups with duplicates (more than 1 record)
    duplicates = {}
    for key, recs in groups.items():
        if len(recs) > 1:
            # Sort by created_at to keep the earliest
            recs.sort(key=lambda r: r['created_at'])
            duplicates[key] = recs
    
    return duplicates


def clean_duplicates(dry_run=True):
    """Clean duplicate records, keeping the earliest one"""
    app = create_app()
    
    with app.app_context():
        duplicates = find_duplicates()
        
        if not duplicates:
            print("✅ No duplicate records found!")
            return
        
        print(f"Found {len(duplicates)} duplicate groups:")
        print()
        
        total_to_delete = 0
        records_to_delete = []
        
        for (member_id, truncated_ts), recs in duplicates.items():
            keep = recs[0]  # Keep the earliest (first after sorting)
            to_delete = recs[1:]  # Delete the rest
            
            print(f"Member ID: {member_id}, Time: {truncated_ts.strftime('%Y-%m-%d %H:%M')}")
            print(f"  - Keep:   Record ID {keep['id']} (created at {keep['created_at']})")
            for rec in to_delete:
                print(f"  - Delete: Record ID {rec['id']} (created at {rec['created_at']})")
                records_to_delete.append(rec['id'])
            print()
            total_to_delete += len(to_delete)
        
        print(f"Total records to delete: {total_to_delete}")
        print()
        
        if dry_run:
            print("🔍 DRY RUN MODE - No changes made")
            print("To actually delete these records, run without --dry-run flag")
        else:
            confirm = input("⚠️  Are you sure you want to delete these records? (yes/no): ")
            if confirm.lower() != 'yes':
                print("❌ Aborted")
                return
            
            # Delete RecordSubject mappings first (foreign key constraint)
            deleted_subjects = RecordSubject.query.filter(
                RecordSubject.record_id.in_(records_to_delete)
            ).delete(synchronize_session=False)
            
            # Delete HealthRecords
            deleted_records = HealthRecord.query.filter(
                HealthRecord.id.in_(records_to_delete)
            ).delete(synchronize_session=False)
            
            db.session.commit()
            
            print(f"✅ Deleted {deleted_records} health records and {deleted_subjects} record subjects")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean duplicate health records')
    parser.add_argument('--dry-run', action='store_true', 
                      help='Preview what would be deleted without actually deleting')
    
    args = parser.parse_args()
    
    clean_duplicates(dry_run=args.dry_run)
