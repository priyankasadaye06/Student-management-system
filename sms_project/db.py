import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="btsarmy062013",
        database="student_management_db"
    )

