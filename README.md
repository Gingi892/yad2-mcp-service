# שירות MCP לסריקת מודעות חדשות ביד2

שירות MCP (Model Context Protocol) שמאפשר סריקה של מודעות חדשות באתר יד2 דרך שיחה עם Claude.

## יתרונות המערכת

- **גישה דרך Claude**: אפשרות לסרוק ולקבל עדכונים דרך שיחה עם Claude
- **פשטות**: התקנה מהירה וקלה
- **התאמה אישית**: אפשרות להגדיר מספר נושאים לסריקה
- **התראות במייל**: אופציה לקבלת התראות מיידיות בדוא"ל
- **תמיכה מלאה בעברית**: ממשק והתראות בעברית

## התקנה

### 1. שבט (Clone) של המאגר
```bash
git clone https://github.com/Gingi892/yad2-mcp-service.git
cd yad2-mcp-service
```

### 2. התקנת החבילות הדרושות
```bash
pip install requests beautifulsoup4
```

### 3. הרצה ראשונית להגדרות
```bash
python yad2_scraper.py
```
בהרצה הראשונית, ייווצר קובץ `config.json` וספריית `data`.

### 4. עדכון קובץ ההגדרות
ערוך את קובץ `config.json` והגדר את הנושאים לסריקה והגדרות המייל אם נדרש.

## שימוש באמצעות שיחה עם Claude

אחרי שהתקנת את השירות, תוכל להשתמש בו דרך שיחה עם Claude.

### פקודות זמינות

1. **סריקת מודעות**:
   ```
   Yad2 MCP scan
   ```
   או סריקת נושא ספציפי:
   ```
   Yad2 MCP scan "דירות למכירה בת"א"
   ```

2. **הוספת נושא חדש**:
   ```
   Yad2 MCP add "דירות בחיפה" "https://www.yad2.co.il/realestate/forsale?city=4000"
   ```

3. **הצגת רשימת הנושאים**:
   ```
   Yad2 MCP list
   ```

4. **עזרה**:
   ```
   Yad2 MCP help
   ```

## שימוש ישיר דרך שורת הפקודה

ניתן להשתמש בשירות גם באופן ישיר דרך שורת הפקודה:

```bash
python yad2_scraper.py scan
python yad2_scraper.py add "דירות בירושלים" "https://www.yad2.co.il/realestate/forsale?city=3000"
python yad2_scraper.py list
```

## הגדרת התראות דוא"ל

לקבלת התראות בדוא"ל, עדכן את חלק `email` בקובץ `config.json`:

```json
"email": {
  "enabled": true,
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "sender_email": "your-email@gmail.com",
  "sender_password": "your-app-password",
  "recipient_email": "your-email@gmail.com"
}
```

**שים לב**: עבור Gmail, יש להשתמש ב"סיסמה לאפליקציה" ולא בסיסמה הרגילה.

## טיפים

1. **סינון יעיל**: השתמש בפילטרים של יד2 כדי לקבל תוצאות ממוקדות יותר.
2. **הרצה מחזורית**: תוכל להגדיר הרצה מחזורית באמצעות cron או כלי תזמון אחר.
3. **התאמה אישית**: המערכת מאפשרת התאמות שונות בקוד המקור.

## מבנה הפרויקט

- `yad2_scraper.py` - סקריפט ראשי
- `config.json` - קובץ הגדרות
- `data/` - תיקייה לשמירת נתונים על המודעות

## רישיון

פרויקט זה מופץ תחת רישיון MIT.

---

נוצר עבור Claude כשירות MCP (Model Context Protocol) לסריקת אתר יד2.
