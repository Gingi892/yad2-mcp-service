#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto Yad2 MCP - סקריפט אוטומטי להפעלת שירות Yad2 MCP

סקריפט זה מבצע סריקה אוטומטית של כל הנושאים המוגדרים בקובץ התצורה
ויכול להתווסף להפעלה אוטומטית בעת הפעלת המחשב.
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime

def ensure_path():
    """וידוא שהסקריפט רץ מתוך תיקיית הפרויקט"""
    # מציאת הנתיב של הסקריפט הנוכחי
    script_path = os.path.dirname(os.path.abspath(__file__))
    
    # שינוי תיקייה נוכחית לתיקיית הסקריפט
    os.chdir(script_path)
    
    print(f"עובד מתיקייה: {script_path}")

def ensure_config():
    """וידוא שקיים קובץ תצורה והוא תקין"""
    if not os.path.exists('config.json'):
        print("קובץ config.json לא נמצא. מייצר קובץ ברירת מחדל...")
        subprocess.run(['python', 'yad2_scraper.py', 'help'], check=True)
    
    # בדיקה שקובץ התצורה תקין
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # הפעלת מצב סריקה אוטומטית
        config['auto_scan'] = True
        
        # שמירת ההגדרות המעודכנות
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print("קובץ תצורה תקין ומוכן לפעולה")
        return config
    
    except Exception as e:
        print(f"שגיאה בקובץ התצורה: {e}")
        return None

def add_default_projects():
    """הוספת נושאים ברירת מחדל אם אין נושאים מוגדרים"""
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    if not config.get('projects'):
        print("אין נושאים מוגדרים. מוסיף נושאים ברירת מחדל...")
        
        default_projects = [
            {
                "topic": "דירות למכירה בתל אביב",
                "url": "https://www.yad2.co.il/realestate/forsale?city=5000",
                "disabled": False
            },
            {
                "topic": "דירות למכירה בירושלים",
                "url": "https://www.yad2.co.il/realestate/forsale?city=3000",
                "disabled": False
            },
            {
                "topic": "דירות למכירה ברמת השרון",
                "url": "https://www.yad2.co.il/realestate/forsale?city=2650",
                "disabled": False
            }
        ]
        
        config['projects'] = default_projects
        
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print("נוספו נושאים ברירת מחדל")

def run_scans():
    """הרצת סריקה של כל הנושאים"""
    try:
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] מתחיל סריקה אוטומטית של כל הנושאים")
        
        # הרצת הסקריפט במצב auto
        result = subprocess.run(['python', 'yad2_scraper.py', 'auto'],
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              encoding='utf-8')
        
        # הדפסת התוצאות
        print(result.stdout)
        
        if result.stderr:
            print(f"שגיאות:\n{result.stderr}")
        
        return result.returncode == 0
    
    except Exception as e:
        print(f"שגיאה בהרצת הסריקה: {e}")
        return False

def run_continuously():
    """הרצת סריקה באופן מחזורי"""
    # טעינת הגדרות
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # קבלת זמן ההמתנה בין סריקות
    interval_minutes = config.get('check_interval_minutes', 15)
    interval_seconds = interval_minutes * 60
    
    print(f"מתחיל הרצה מחזורית. סריקה תתבצע כל {interval_minutes} דקות")
    
    try:
        while True:
            success = run_scans()
            
            next_run = datetime.now().timestamp() + interval_seconds
            formatted_time = datetime.fromtimestamp(next_run).strftime('%H:%M:%S')
            print(f"\nהסריקה הבאה תהיה בשעה {formatted_time}")
            
            time.sleep(interval_seconds)
    
    except KeyboardInterrupt:
        print("\nהריצה המחזורית הופסקה ידנית")
    except Exception as e:
        print(f"שגיאה בריצה המחזורית: {e}")

def main():
    """פונקציה ראשית"""
    print("=" * 60)
    print("        מפעיל סקריפט אוטומטי לסריקת יד2 (Auto Yad2 MCP)")
    print("=" * 60)
    
    # וידוא שהסקריפט רץ מהנתיב הנכון
    ensure_path()
    
    # וידוא שיש קובץ תצורה תקין
    config = ensure_config()
    if not config:
        print("בעיה בקובץ התצורה. לא ניתן להמשיך.")
        return
    
    # בדיקה אם יש נושאים מוגדרים
    add_default_projects()
    
    # בדיקת ארגומנטים
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        # הרצה חד פעמית
        print("מבצע סריקה חד פעמית...")
        run_scans()
    else:
        # הרצה מחזורית
        run_continuously()

if __name__ == "__main__":
    main()
