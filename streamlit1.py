import streamlit as st
st.title("Codex")

input = st.text_input('Enter the Text')
from google.cloud import bigquery

import os 
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'bigquery-project-372513-08ef878a3a5f.json'

client = bigquery.Client()

sql = """
SELECT table_catalog,
table_schema,
table_name,
 ddl 
 FROM bigquery-project-372513.dbt_wowskincare_presentation.INFORMATION_SCHEMA.TABLES
 where table_name = 'order_headers';

"""
table_metadata = client.query(sql).to_dataframe()
table_metadata.head()

def table_info(table_metadata):

    schema_summary = f"""DDL for table {table_metadata.table_name[0]}: {table_metadata.ddl[0]}
    \t
    """
    #print(schema_summary," shdfa print schema")
    table_name = table_metadata.table_catalog[0]+"."+table_metadata.table_schema[0]+"."+table_metadata.table_name[0]
    #print("table name",table_name)
    #sql = f"select * from {table_name} limit 10"
    #print("sql",sql)
    sample_table = client.query(sql).to_dataframe()

    s = f"""{schema_summary}
    Sample data for table: {table_metadata.table_name}:
    {sample_table}
    """
    #print(s,"s")
    return s
table_info=table_info(table_metadata)
class Query():

    def __init__(self, sql, result, error):
        self.sql = sql
        self.result = result
        self.error = error
        
def get_sql_result(q):
    try:
        sql = q.sql
        result = client.query(sql).to_dataframe()   
        q.result = result
        q.error = None
        return q
    except Exception as e:
        import traceback
        try:
            error = str(e.__dict__['orig'])
        except KeyError:
            error = str(e)
        q.error = error
        q.result = None
        return q
import openai

# Set up OpenAI API key
api_key = "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"
openai.api_key = api_key

# Function to send a message to the OpenAI chatbot model and return its response
def send_message(message_log):
    # Use OpenAI's ChatCompletion API to get the chatbot's response
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # The name of the OpenAI chatbot model to use
        messages=message_log,   # The conversation history up to this point, as a list of dictionaries
        max_tokens=300,        # The maximum number of tokens (words or subwords) in the generated response
        stop=None,              # The stopping sequence for the generated response, if any (not used here)
        temperature=0,        # The "creativity" of the generated response (higher temperature = more creative)
    )

    # Find the first response from the chatbot that has text in it (some responses may not have text)
    for choice in response.choices:
        if "text" in choice:
            return choice.text

    # If no response with text is found, return the first response's content (which may be empty)
    return response.choices[0].message.content
def build_prompt(table_info):
    tables_summary = table_info
    prompt = f"""{tables_summary}
    As a senior analyst, given above is DDL query and sample data, help user write a detailed and correct syntax for SQL queries using standard SQL for BigQuery to answer the analytical questions.
    please write the query in code block of markdown and explain the query
     """
    #print("table_summary",tables_summary)
    #print(prompt)
    return prompt

def fix_bug(query: Query):

    error_prompt = f"""{query.sql}
The query above produced the following error:
{query.error}
Rewrite the query with the error fixed: 
enter the query in markdown sql block and also explain the query"""

    no_result_prompt = f"""{query.sql}
The query above produced no result. Try rewriting the query so it will return results:
enter the query in markdown sql block and also explain the query
try using different columns in filters if there is no data"""

    print("ERROR")
    
    if query.error:
        prompt = error_prompt
        print("fixing bug")
    else:
        prompt = no_result_prompt
        print("fixing empty data")
    
    messages.append({"role": "user", "content": prompt})
    
    response = send_message(messages)
    print("response")
    print(response)
    string = response
    match = re.search(r'```(.+?)```', string, re.DOTALL)
    code_block = match.group(1).replace("sql","")
    messages.append({"role": "system", "content": response})
    query.sql=code_block
    query = get_sql_result(query)
    
    # create a completion
    return query


messages = []
messages=[
        {"role": "system", "content": build_prompt(table_info)},
        {"role": "user", "content": input},
    ]

response = send_message(messages)
import re

string = response
print("string",string)
match = re.search(r'```(.+?)```', string, re.DOTALL)
#print(match,"match")
st.write(string)
#st.write(match)


try:
    code_block = match.group(1).replace("sql","")
    flag=True
except AttributeError:
    flag=False
#st.write(code_block)
if flag==True:
    p=Query(sql=code_block, result=None , error=None)
    p = get_sql_result(p)

    print("sql code = ",p.sql)
    if p.result is not None :
        print(p.result)
        st.write(p.result)
    if p.error is not None :
        print("error",p.error)

    while p.error is not None  or  p.result is None:
                # Try to fix error
        p = fix_bug(p)
        print("sql code = ",p.sql)
        if p.result is not None :
            print("result",p.result)
            st.write(p.result)
        if p.error is not None :
            print("error",p.error)

            