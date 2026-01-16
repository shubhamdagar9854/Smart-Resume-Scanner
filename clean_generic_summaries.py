#!/usr/bin/env python3
"""
Database Cleanup Script - Remove Generic Summaries
"""

import sqlite3
import sys

def clean_generic_summaries():
    """Remove all generic summaries from database"""
    try:
        conn = sqlite3.connect('resumes.db')
        cursor = conn.cursor()
        
        # Delete generic summaries
        generic_patterns = [
            '%Experienced professional with relevant skills%',
            '%skilled professional with relevant experience%',
            '%motivated professional%',
            '%experienced software engineer with relevant skills%'
        ]
        
        deleted_count = 0
        for pattern in generic_patterns:
            cursor.execute("DELETE FROM resumes WHERE summary LIKE ?", (pattern,))
            deleted_count += cursor.rowcount
        
        conn.commit()
        conn.close()
        
        print(f"✅ Cleaned up {deleted_count} generic summaries from database")
        
    except Exception as e:
        print(f"❌ Error cleaning database: {e}")

if __name__ == "__main__":
    clean_generic_summaries()
