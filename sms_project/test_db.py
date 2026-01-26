from db import cursor

cursor.execute("SHOW TABLES")
tables = cursor.fetchall()

print("Tables in database:")
for t in tables:
    print(t)



    
