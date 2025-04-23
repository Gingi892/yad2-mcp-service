#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yad2 MCP Service - שירות MCP לסריקת מודעות חדשות ביד2

סורק שמאפשר לקבל עדכונים על מודעות חדשות מיד2 דרך שיחה עם Claude
"""

import os
import json
import time
import smtplib
import argparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import random
import traceback

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0'
]

def load_config():
    """טעינת הגדרות מקובץ התצורה"""
    
    # אם אין קובץ הגדרות, נייצר אחד עם הגדרות ברירת מחדל
    if not os.path.exists('config.json'):
        default_config = {
            "email": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "sender_email": "your-email@gmail.com",
                "sender_password": "your-app-password",
                "recipient_email": "your-email@gmail.com"
            },
            "projects": [
                {
                    "topic": "דירות למכירה בת\"א",
                    "url": "https://www.yad2.co.il/realestate/forsale?city=5000",
                    "disabled": False
                }
            ],
            "data_dir": "data",
            "check_interval_minutes": 15
        }
        
        os.makedirs('data', exist_ok=True)
        
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        
        print("נוצר קובץ הגדרות חדש (config.json). אנא ערוך אותו לפני הרצה.")
        return default_config
    
    # טעינת הגדרות מהקובץ
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def get_yad2_response(url):
    """קבלת תוכן העמוד מיד2"""
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept-Language': 'he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept': 'text/html,application/xhtml+xml,application/xml',
        'Referer': 'https://www.yad2.co.il/',
        'sec-ch-ua': '"Chromium";v="110", "Not A(Brand";v="24", "Google Chrome";v="110"'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"שגיאה בקבלת תוכן מיד2: {e}")
        return None

def extract_items(html_content):
    """חילוץ פרטי המודעות מתוך תוכן ה-HTML"""
    if not html_content:
        return []
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # בדיקה אם יש דף CAPTCHA
    if soup.title and "ShieldSquare Captcha" in soup.title.text:
        print("זוהה דף CAPTCHA - יד2 חוסם את הגישה. נסה שוב מאוחר יותר.")
        return []
    
    items = []
    feed_items = soup.select('div.feeditem')
    
    for item in feed_items:
        try:
            # מזהה מודעה
            item_id = item.get('item-id') or item.get('data-item-id')
            
            # כותרת המודעה
            title_elem = item.select_one('.title')
            title = title_elem.text.strip() if title_elem else "אין כותרת"
            
            # מחיר
            price_elem = item.select_one('.price')
            price = price_elem.text.strip() if price_elem else "מחיר לא צוין"
            
            # תמונה
            img_elem = item.select_one('.image img')
            img_url = img_elem.get('src') if img_elem else None
            
            # קישור למודעה
            link = f"https://www.yad2.co.il/item/{item_id}" if item_id else None
            
            # כתובת
            address_elem = item.select_one('.subtitle')
            address = address_elem.text.strip() if address_elem else "כתובת לא צוינה"
            
            # תאריך פרסום
            date_elem = item.select_one('.date')
            date = date_elem.text.strip() if date_elem else "תאריך לא צוין"
            
            items.append({
                'id': item_id,
                'title': title,
                'price': price,
                'address': address,
                'date': date,
                'image': img_url,
                'link': link
            })
        except Exception as e:
            print(f"שגיאה בחילוץ פרטי מודעה: {e}")
    
    print(f"נמצאו {len(items)} מודעות בעמוד.")
    return items

def check_for_new_items(items, topic, config):
    """בדיקה אם יש מודעות חדשות"""
    data_dir = config.get('data_dir', 'data')
    os.makedirs(data_dir, exist_ok=True)
    file_path = os.path.join(data_dir, f"{topic.replace(' ', '_')}.json")
    
    saved_items = []
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                saved_items = json.load(f)
        except Exception as e:
            print(f"שגיאה בקריאת קובץ {file_path}: {e}")
    
    # זיהוי מודעות חדשות לפי מזהה
    saved_ids = [item.get('id') for item in saved_items]
    new_items = [item for item in items if item.get('id') not in saved_ids]
    
    # עדכון הקובץ אם יש מודעות חדשות
    if new_items:
        updated_items = saved_items + new_items
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(updated_items, f, ensure_ascii=False, indent=2)
        
        print(f"נמצאו {len(new_items)} מודעות חדשות בנושא '{topic}'.")
    else:
        print(f"לא נמצאו מודעות חדשות בנושא '{topic}'.")
    
    return new_items

def send_email_notification(new_items, topic, config):
    """שליחת התראה בדוא"ל על מודעות חדשות"""
    if not config.get('email', {}).get('enabled', False):
        return False
    
    email_config = config.get('email', {})
    smtp_server = email_config.get('smtp_server')
    smtp_port = email_config.get('smtp_port')
    sender_email = email_config.get('sender_email')
    sender_password = email_config.get('sender_password')
    recipient_email = email_config.get('recipient_email')
    
    if not all([smtp_server, smtp_port, sender_email, sender_password, recipient_email]):
        print("חסרים פרטי דוא\"ל בהגדרות. לא נשלחה התראה.")
        return False
    
    try:
        # יצירת הודעה
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"🔍 נמצאו {len(new_items)} מודעות חדשות ב{topic}"
        msg['From'] = sender_email
        msg['To'] = recipient_email
        
        # יצירת תוכן HTML
        html = f"""
        <html dir="rtl">
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; direction: rtl; }}
                .item {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
                .title {{ font-size: 18px; font-weight: bold; color: #3366cc; }}
                .price {{ font-size: 16px; color: #e63946; font-weight: bold; }}
                .link {{ color: #3366cc; }}
                .address {{ color: #666; }}
                .date {{ color: #888; font-size: 14px; }}
            </style>
        </head>
        <body>
            <h2>נמצאו {len(new_items)} מודעות חדשות ב{topic}</h2>
            <p>הסריקה בוצעה בתאריך: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        """
        
        for item in new_items:
            html += f"""
            <div class="item">
                <div class="title">{item.get('title', 'אין כותרת')}</div>
                <div class="price">{item.get('price', 'מחיר לא צוין')}</div>
                <div class="address">{item.get('address', 'כתובת לא צוינה')}</div>
                <div class="date">{item.get('date', 'תאריך לא צוין')}</div>
                <p><a class="link" href="{item.get('link', '#')}">צפייה במודעה</a></p>
            </div>
            """
        
        html += """
            <p>סורק יד2 הפשוט</p>
        </body>
        </html>
        """
        
        # הוספת תוכן HTML להודעה
        msg.attach(MIMEText(html, 'html', 'utf-8'))
        
        # שליחת הדוא"ל
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        print(f"נשלחה התראה לכתובת {recipient_email}")
        return True
    
    except Exception as e:
        print(f"שגיאה בשליחת דוא\"ל: {e}")
        return False

def format_items_for_response(new_items, topic):
    """פרמוט המודעות החדשות לתצוגה"""
    if not new_items:
        return f"לא נמצאו מודעות חדשות בנושא '{topic}'."
    
    response = f"נמצאו {len(new_items)} מודעות חדשות בנושא '{topic}':\n\n"
    
    for i, item in enumerate(new_items, 1):
        response += f"{i}. {item.get('title', 'אין כותרת')}\n"
        response += f"   מחיר: {item.get('price', 'מחיר לא צוין')}\n"
        response += f"   כתובת: {item.get('address', 'כתובת לא צוינה')}\n"
        response += f"   תאריך: {item.get('date', 'תאריך לא צוין')}\n"
        response += f"   קישור: {item.get('link', '#')}\n\n"
    
    return response

def scrape_project(project, config):
    """סריקת פרויקט יחיד"""
    topic = project.get('topic')
    url = project.get('url')
    
    if not topic or not url:
        return "חסרים פרטי נושא או URL. מדלג."
    
    try:
        result = f"סריקת נושא: {topic}\nURL: {url}\n\n"
        
        # קבלת תוכן העמוד
        html_content = get_yad2_response(url)
        if not html_content:
            return result + f"לא הצלחנו לקבל תוכן מהURL: {url}"
        
        # חילוץ פרטי המודעות
        items = extract_items(html_content)
        if not items:
            return result + "לא נמצאו מודעות בעמוד."
        
        # בדיקה אם יש מודעות חדשות
        new_items = check_for_new_items(items, topic, config)
        
        # הוספת פרטי המודעות החדשות לתוצאה
        result += format_items_for_response(new_items, topic)
        
        # שליחת התראה בדוא"ל אם יש מודעות חדשות ואם מופעל
        if new_items and config.get('email', {}).get('enabled', False):
            send_email_notification(new_items, topic, config)
            result += "\nנשלחה התראה בדוא\"ל על המודעות החדשות."
        
        return result
    
    except Exception as e:
        error_traceback = traceback.format_exc()
        return f"שגיאה בסריקת הנושא '{topic}':\n{str(e)}\n\n{error_traceback}"

def add_project(topic, url, config_path="config.json"):
    """הוספת פרויקט חדש לקובץ ההגדרות"""
    try:
        config = load_config()
        
        # בדיקה אם הפרויקט כבר קיים
        for project in config.get('projects', []):
            if project.get('topic') == topic:
                project['url'] = url
                project['disabled'] = False
                break
        else:
            # הוספת פרויקט חדש
            config.setdefault('projects', []).append({
                'topic': topic,
                'url': url,
                'disabled': False
            })
        
        # שמירת ההגדרות המעודכנות
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        return f"הפרויקט '{topic}' נוסף בהצלחה לקובץ ההגדרות."
    
    except Exception as e:
        return f"שגיאה בהוספת הפרויקט: {str(e)}"

def run_mcp_command(command, args=None):
    """הרצת פקודה עבור MCP"""
    config = load_config()
    
    if command == "help":
        return """פקודות זמינות ב-MCP:
1. scan - סריקת כל הפרויקטים או פרויקט ספציפי
   דוגמה: scan [שם נושא]
2. add - הוספת פרויקט חדש
   דוגמה: add [שם נושא] [URL]
3. list - הצגת רשימת הפרויקטים
4. help - הצגת עזרה זו
"""
    
    elif command == "scan":
        if args and len(args) > 0:
            # סריקת נושא ספציפי
            topic = args[0]
            for project in config.get('projects', []):
                if project.get('topic') == topic and not project.get('disabled', False):
                    return scrape_project(project, config)
            return f"לא נמצא פרויקט בשם '{topic}' או שהוא מושבת."
        else:
            # סריקת כל הנושאים
            results = []
            for project in config.get('projects', []):
                if not project.get('disabled', False):
                    results.append(scrape_project(project, config))
            
            if not results:
                return "אין פרויקטים זמינים לסריקה. הוספת פרויקט חדש באמצעות פקודת 'add'."
            
            return "\n" + "="*50 + "\n".join(results)
    
    elif command == "add":
        if args and len(args) >= 2:
            topic = args[0]
            url = args[1]
            return add_project(topic, url)
        else:
            return "שימוש שגוי בפקודת add. הפורמט הנכון: add [שם נושא] [URL]"
    
    elif command == "list":
        projects = config.get('projects', [])
        if not projects:
            return "אין פרויקטים מוגדרים. הוספת פרויקט חדש באמצעות פקודת 'add'."
        
        result = "רשימת הפרויקטים:\n"
        for i, project in enumerate(projects, 1):
            status = "פעיל" if not project.get('disabled', False) else "מושבת"
            result += f"{i}. {project.get('topic')} [{status}]\n"
            result += f"   URL: {project.get('url')}\n"
        
        return result
    
    else:
        return f"פקודה לא מוכרת: '{command}'. הקלד 'help' לקבלת רשימת הפקודות."

def main():
    """נקודת הכניסה הראשית"""
    parser = argparse.ArgumentParser(description='שירות MCP לסריקת מודעות חדשות ביד2')
    parser.add_argument('command', nargs='?', default='help', help='הפקודה להרצה (scan, add, list, help)')
    parser.add_argument('args', nargs='*', help='פרמטרים נוספים לפקודה')
    
    args = parser.parse_args()
    result = run_mcp_command(args.command, args.args)
    print(result)

if __name__ == "__main__":
    main()
