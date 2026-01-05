# 🔄 Database Sync Tool
import sqlite3
import os
import shutil

def sync_database():
    """Sync database across devices"""
    
    # Check if database exists
    if os.path.exists('resumes.db'):
        print("✅ Database found")
        
        # Show current data
        conn = sqlite3.connect('resumes.db')
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM resumes")
        count = cur.fetchone()[0]
        print(f"📊 Current resumes: {count}")
        
        cur.execute("SELECT id, name, email FROM resumes ORDER BY id DESC")
        resumes = cur.fetchall()
        
        print("\n📋 Recent Resumes:")
        for resume in resumes[-5:]:  # Show last 5
            print(f"  ID: {resume[0]}, Name: {resume[1]}, Email: {resume[2]}")
        
        conn.close()
        
        print("\n🔄 To sync from another device:")
        print("1. Copy 'resumes.db' from other device")
        print("2. Paste it in this project folder")
        print("3. Refresh admin dashboard")
        
    else:
        print("❌ Database not found!")
        print("🔧 Run: python app.py to create database")

if __name__ == "__main__":
    sync_database()
