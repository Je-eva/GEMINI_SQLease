import sqlite3

## Connect to Sqlite
connection=sqlite3.connect("student.db")

# Create a cursor object to insert record,create table

cursor=connection.cursor()


## create the table
table_info="""
Create table STUDENT(NAME VARCHAR(25),CLASS VARCHAR(25),
SECTION VARCHAR(25),MARKS INT);

"""
#cursor.execute(table_info)

## Insert Some  records

#cursor.execute('''Insert Into STUDENT values('Krish','Data Science','A',90)''')
#cursor.execute('''Insert Into STUDENT values('Sudhanshu','Data Science','B',100)''')
#cursor.execute('''Insert Into STUDENT values('Darius','Data Science','A',86)''')
#cursor.execute('''Insert Into STUDENT values('Vikash','DEVOPS','A',50)''')
#cursor.execute('''Insert Into STUDENT values('Dipesh','DEVOPS','A',35)''')

records_to_insert = [
    ('John', 'Data Science', 'B', 95),
    ('Alice', 'DEVOPS', 'B', 75),
    ('Emily', 'Data Science', 'A', 88),
    ('Michael', 'DEVOPS', 'B', 60),
    ('Sophia', 'Data Science', 'B', 92),
    ('David', 'DEVOPS', 'A', 65),
    ('Emma', 'Data Science', 'A', 85),
    ('James', 'DEVOPS', 'B', 70),
    ('Olivia', 'Data Science', 'A', 93),
    ('Alexander', 'DEVOPS', 'A', 55)
]

# Execute the insertion for each record
for record in records_to_insert:
    cursor.execute("INSERT INTO STUDENT (NAME, CLASS, SECTION, MARKS) VALUES (?, ?, ?, ?)", record)

## Disply record

print("The inserted records are")
data=cursor.execute('''Select * from STUDENT''')
for row in data:
    print(row)

## Commit your changes into databse
connection.commit()
connection.close()