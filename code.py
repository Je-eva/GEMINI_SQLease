from dotenv import load_dotenv
import streamlit as st
import os
import sqlite3
import spacy
import random
import google.generativeai as genai
from spacy.training.example import Example

# Load the English NLP model
nlp = spacy.load("en_core_web_sm")

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to parse user input and extract operation details
def parse_input(input_text):
    doc = nlp(input_text)
    operation = None
    details = {}

    # Extract operation type
    for token in doc:
        if token.pos_ == "VERB":
            operation = token.text
            break

    # Extract details
    for ent in doc.ents:
        if ent.label_ == "COLUMN":
            details["column_name"] = ent.text
        elif ent.label_ == "DATATYPE":
            details["data_type"] = ent.text
        elif ent.label_ == "CONSTRAINT":
            details["constraint"] = ent.text

    return operation, details

# Function to load gemini model and provide SQL query as response
def get_gemini_response(question, prompt):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content([prompt[0], question])
    return response.text

# Function to retrieve query from SQL database
def read_sql_query(sql, db):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    conn.commit()
    conn.close()
    return rows

# Function to perform SQL operations based on user input
def perform_sql_operations(operation, details):
    if operation == "delete":
        if "column_name" in details:
            sql_query = f"ALTER TABLE STUDENT DROP COLUMN {details['column_name']}"
        elif "row_condition" in details:
            sql_query = f"DELETE FROM STUDENT WHERE {details['row_condition']}"
        else:
            return "Delete operation requires either column name or row condition"
    elif operation == "insert":
        if "values" in details:
            values = ', '.join([f"'{value}'" for value in details['values']])
            sql_query = f"INSERT INTO STUDENT VALUES ({values})"
        else:
            return "Insert operation requires values to be inserted"
    elif operation == "alter":
        if "column_name" in details and "new_data_type" in details:
            sql_query = f"ALTER TABLE STUDENT ALTER COLUMN {details['column_name']} SET DATA TYPE {details['new_data_type']}"
        elif "column_name" in details and "constraint" in details:
            sql_query = f"ALTER TABLE STUDENT ADD CONSTRAINT {details['constraint']} ON {details['column_name']}"
        else:
            return "Alter operation requires either column name with new data type or column name with constraint"
    else:
        return "Operation not supported"


    # Execute SQL query
    conn = sqlite3.connect("student.db")
    cur = conn.cursor()
    cur.execute(sql_query)
    conn.commit()
    conn.close()

    return "Operation completed successfully"

# Function to view the contents of the database
def view_database(db):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT * FROM STUDENT")
    rows = cur.fetchall()
    conn.close()

    st.subheader("Database Contents:")
    for row in rows:
        st.write(row)

## Streamlit App

st.set_page_config(page_title="Gemini SQL App")

# Main Streamlit app
st.header("Gemini SQL App")
prompt = [
        """
        You are an expert in converting English questions to SQL query!
        The SQL database has the name STUDENT and has the following columns - NAME, CLASS, 
        SECTION, and MARKS \n\nFor example,\nExample 1 - How many entries of records are present?, 
        the SQL command will be something like this SELECT COUNT(*) FROM STUDENT ;
        \nExample 2 - Tell me all the students studying in Data Science class?, 
        the SQL command will be something like this SELECT * FROM STUDENT 
        where CLASS="Data Science"; 
        also the SQL code should not have ``` in the beginning or end and the SQL word in the output
        """
        ]

# Define examples list
examples = [
    ("Delete the records with ID greater than 100", {"entities": [(12, 19, "COLUMN"), (35, 37, "CONSTRAINT")]}),
    ("Insert a new student into the database", {"entities": [(7, 13, "VERB"), (17, 24, "COLUMN")]}),
    ("Alter the table to add a new column", {"entities": [(0, 5, "VERB"), (16, 21, "VERB"), (28, 34, "COLUMN")]}),
    ("Delete all students with a score less than 60", {"entities": [(0, 6, "VERB"), (16, 23, "COLUMN"), (35, 37, "CONSTRAINT")]}),
    ("Insert a new row with student name and marks", {"entities": [(0, 6, "VERB"), (12, 15, "COLUMN"), (30, 35, "COLUMN")]}),
    ("Delete all students with MARKS less than 60", {"entities": [(0, 6, "VERB"), (16, 23, "COLUMN"), (35, 37, "CONSTRAINT")]}),
    ("Insert a new student with NAME and CLASS", {"entities": [(0, 6, "VERB"), (17, 21, "COLUMN"), (26, 31, "COLUMN")]}),
    ("Alter the table to add SECTION column", {"entities": [(0, 5, "VERB"), (16, 21, "VERB"), (27, 34, "COLUMN")]}),
    ("Delete all students with SECTION A", {"entities": [(0, 6, "VERB"), (16, 23, "COLUMN"), (35, 36, "CONSTRAINT")]}),
    ("Insert a new row with CLASS and MARKS", {"entities": [(0, 6, "VERB"), (12, 17, "COLUMN"), (28, 33, "COLUMN")]}),
    # Add more examples as needed
]

# Your annotated training examples
formatted_examples = []
for text, annotations in examples:
    doc = nlp.make_doc(text)
    entities = annotations["entities"]
    example = Example.from_dict(nlp.make_doc(text), {"entities": entities})
    formatted_examples.append(example)

# Shuffle examples for better training
random.shuffle(formatted_examples)

# Update the model with the formatted examples
nlp.begin_training()
for example in formatted_examples:
    nlp.update([example], losses={})

# Check alignment using offsets_to_biluo_tags
for text, annotations in examples:
    doc = nlp.make_doc(text)
    entities = annotations["entities"]
    biluo_tags = spacy.training.offsets_to_biluo_tags(doc, entities)
    print(f"Text: {text}")
    print(f"BILOU tags: {biluo_tags}")

option = st.radio("Select Option", ["Fetch SQL Query", "Edit the database"])

# Fetch SQL Query operation
if option == "Fetch SQL Query":
    question = st.text_input("Input: ")
    if st.button("Fetch SQL Query"):
        response = get_gemini_response(question, prompt)
        st.write("Response from Gemini:", response)

        if response.strip().lower().startswith("select"):
            data = read_sql_query(response, "student.db")
            st.subheader("The Response is")
            for row in data:
                st.write(row)

# Edit the database operation
else:
    question = st.text_input("Input: ")

    if st.button("Edit the database"):
        operation, details = parse_input(question)
        if operation:
            response = perform_sql_operations(operation, details)
            st.write("Response:", response)
        else:
            response = get_gemini_response(question, prompt)
            st.write("Response from Gemini:", response)
            
    # Display the database contents
    data = read_sql_query("SELECT * FROM STUDENT", "student.db")
    st.subheader("Database Contents:")
    for row in data:
        st.write(row)
