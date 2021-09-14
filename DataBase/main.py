import sqlite3
import datetime

# Создаем соединение с нашей базой данных
# В нашем примере у нас это просто файл базы
conn = sqlite3.connect('NewDataBase.sqlite3')
cursor = conn.cursor()

try:
    cursor.execute("CREATE TABLE IF NOT EXISTS Logs (DateTime TEXT PRIMARY KEY,Log TEXT NOT NULL);")
    conn.commit()
except sqlite3.DatabaseError as err:       
    print("Error: ", err)


try:
    currentTime = datetime.datetime.now()
    cursor.execute("insert into Logs values ('" + currentTime.date().strftime("%d.%m.%Y") + " "+ currentTime.time().strftime("%H:%M:%S") + "', 'Log') ")
    # Если мы не просто читаем, но и вносим изменения в базу данных - необходимо сохранить транзакцию
    conn.commit()
except sqlite3.DatabaseError as err:       
    print("Error: ", err)


# Делаем SELECT запрос к базе данных, используя обычный SQL-синтаксис
try:
    cursor.execute("""
SELECT * FROM Logs
ORDER BY DateTime
""")# LIMIT 3
except sqlite3.DatabaseError as err:       
    print("Error: ", err)

results = cursor.fetchall()
print(results) 

if results.__len__() > 5:
    try:
        cursor.execute("delete from Logs")
        conn.commit()
    except sqlite3.DatabaseError as err:       
        print("Error: ", err)

# Не забываем закрыть соединение с базой данных
conn.close()
#git checking


