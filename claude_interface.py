#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ממשק לשימוש ב-Yad2 MCP דרך Claude

קובץ זה מאפשר לנו להגדיר פונקציות עזר לחיבור בין Claude לבין שירות ה-MCP של יד2
"""

import sys
import os
import subprocess
import shlex

def parse_mcp_command(message):
    """ניתוח פקודת MCP מתוך הודעה של המשתמש"""
    # בודק אם ההודעה מתחילה ב-Yad2 MCP
    if not message.startswith("Yad2 MCP"):
        return None, None
    
    # חלוקת ההודעה לחלקים
    parts = message.strip().split(" ", 2)
    
    if len(parts) < 3:
        # אם אין מספיק חלקים, מניחים שזו פקודת help
        return "help", []
    
    command = parts[2].strip()
    
    # מחלקים את החלק השלישי לפקודה וארגומנטים
    command_parts = command.split(" ", 1)
    
    if len(command_parts) == 1:
        # אם יש רק פקודה ללא ארגומנטים
        return command_parts[0], []
    
    # ניתוח הארגומנטים בהתאם לפקודה
    cmd = command_parts[0]
    args_str = command_parts[1].strip()
    
    # טיפול מיוחד בפקודת add שמקבלת נושא ו-URL
    if cmd == "add":
        # חיפוש מרכאות לנושא
        if args_str.startswith('"'):
            # מחפשים את סוף המרכאות של הנושא
            topic_end = args_str.find('"', 1)
            if topic_end > 0:
                topic = args_str[1:topic_end]
                url_part = args_str[topic_end+1:].strip()
                
                # מחפשים מרכאות ל-URL
                if url_part.startswith('"'):
                    url_end = url_part.find('"', 1)
                    if url_end > 0:
                        url = url_part[1:url_end]
                        return "add", [topic, url]
        
        # אם לא מצאנו מרכאות או הפורמט לא נכון, ננסה לפצל על רווח
        args = args_str.split()
        if len(args) >= 2:
            return "add", [args[0], args[1]]
        else:
            return "add", [args_str]  # לא מספיק ארגומנטים, אבל נשלח מה שיש
    
    # טיפול בפקודת scan עם נושא אופציונלי
    elif cmd == "scan":
        # אם יש מרכאות, נחלץ את הנושא מתוכן
        if args_str.startswith('"'):
            topic_end = args_str.find('"', 1)
            if topic_end > 0:
                topic = args_str[1:topic_end]
                return "scan", [topic]
        
        # אחרת נשתמש בארגומנט כמות שהוא
        return "scan", [args_str]
    
    # פקודות אחרות
    else:
        return cmd, [args_str]

def execute_mcp_command(command, args=None):
    """הרצת פקודת MCP באמצעות הסקריפט"""
    try:
        # בניית פקודה להרצה
        cmd = ["python", "yad2_scraper.py", command]
        
        # הוספת ארגומנטים אם יש
        if args:
            cmd.extend(args)
        
        # הרצת הפקודה
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        # בדיקה אם הפקודה הצליחה
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"שגיאה בהרצת הפקודה: {result.stderr.strip()}"
    
    except Exception as e:
        return f"שגיאה בהרצת פקודת MCP: {str(e)}"

def handle_claude_request(message):
    """טיפול בבקשת MCP שהגיעה דרך Claude"""
    # ניתוח הפקודה מתוך ההודעה
    command, args = parse_mcp_command(message)
    
    if not command:
        return None  # זו לא פקודת MCP
    
    # הרצת הפקודה
    result = execute_mcp_command(command, args)
    
    # החזרת התוצאה לתצוגה ב-Claude
    return f"""
## תוצאות סריקת יד2 MCP

פקודה: `{command} {' '.join(args) if args else ''}`

```
{result}
```

לסריקה נוספת או לרשימת פקודות, השתמש ב-`Yad2 MCP help`
"""

# לשימוש ישיר בשורת הפקודה לצורכי בדיקה
if __name__ == "__main__":
    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
        result = handle_claude_request(message)
        if result:
            print(result)
        else:
            print("זו לא פקודת MCP")
    else:
        print("Usage: python claude_interface.py \"Yad2 MCP command [args]\"")
