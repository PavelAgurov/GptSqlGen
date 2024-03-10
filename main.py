"""
    Main APP and UI
"""
# pylint: disable=C0301,C0103,C0303,C0411,W1203

import streamlit as st
import logging

from utils_streamlit import streamlit_hack_remove_top_space
from utils.app_logger import init_streamlit_logger

from backend.core import Core
from backend import prompts
import strings

init_streamlit_logger()

# ------------------------------- Logger
logger : logging.Logger = logging.getLogger()

# ------------------------------- Session
if 'core' not in st.session_state:
    st.session_state.core = Core()
if 'tokens' not in st.session_state:
    st.session_state.tokens = 0
if 'generated_schema' not in st.session_state:
    st.session_state.generated_schema = ''
if 'generated_sql' not in st.session_state:
    st.session_state.generated_sql = ''
if 'operation_done' not in st.session_state:
    st.session_state.operation_done = None
if 'operation_errors' not in st.session_state:
    st.session_state.operation_errors = None
if 'tokens_currently_used' not in st.session_state:
    st.session_state.tokens_currently_used = 0
if 'tokens_total_used' not in st.session_state:
    st.session_state.tokens_total_used = 0
if 'table_rules' not in st.session_state or st.session_state.table_rules is None or st.session_state.table_rules.strip() == '':
    st.session_state.table_rules = prompts.GENERATE_SCHEMA_DEFAULT_RULES.strip()
if 'table_script_definition' not in st.session_state or st.session_state.table_script_definition is None or st.session_state.table_script_definition.strip() == '':
    st.session_state.table_script_definition = prompts.GENERATE_SQL_DEFAULT_CRUD.strip()

# ------------------------------- UI
st.set_page_config(page_title= "Sql Generator", layout="wide")
streamlit_hack_remove_top_space()

st.markdown("## Sql Generator") 
st.info(strings.APP_INFO, icon="ℹ️")
st.info(f'Used {st.session_state.tokens_currently_used} tokens. Total used {st.session_state.tokens_total_used} tokens.')

if st.session_state.operation_done:
    st.success(st.session_state.operation_done)
    st.session_state.operation_done = None

if st.session_state.operation_errors:
    st.error(st.session_state.operation_errors)
    st.session_state.operation_errors = None

db_name = st.text_input("Database Name:", value="Postgres")

tab_tables, tab_procedures = st.tabs(["Generate Tables", "Generate Procedures"])

with tab_tables:
    table_description_example_str = strings.TABLE_DESCRIPTION_EXAMPLE.strip()
    table_description_example = st.expander("Examples", expanded=False).markdown(table_description_example_str)

    table_generate_columns = st.columns(2)
    table_description = table_generate_columns[0].text_area("Table Description:", height=200, placeholder= "See Examples above")
    table_rules = table_generate_columns[1].text_area("Table Rules for schema generation:", st.session_state.table_rules, height=200, placeholder= "See Examples above")
    button_generate_columns = st.columns(8)
    button_generate_schema = button_generate_columns[0].button("Generate XML schema")
    button_generate_prisma = button_generate_columns[1].button("Generate Prisma schema")

    table_sql_columns = st.columns(2)
    table_schema = table_sql_columns[0].text_area("Table Schema:", st.session_state.generated_schema, height=200, placeholder= "See Examples above")
    table_schema_script_definition = table_sql_columns[1].text_area("Script Definition for SQL generation:", st.session_state.table_script_definition, height=200, placeholder= "See Examples above")
    button_generate_sql = st.button("Generate SQL")
    table_sql = st.text_area("Sql:", st.session_state.generated_sql, height=200)

with tab_procedures:
    st.info("TBD")

def update_used_tokens(currently_used = 0):
    """Update token counters"""
    st.session_state.tokens_currently_used = currently_used
    st.session_state.tokens_total_used += currently_used

update_used_tokens()

if button_generate_schema:
    if not db_name or not table_description or not table_rules:
        st.session_state.operation_errors = "Please enter database name, table description and rules"
    else:
        existed_tables_str = ""
        st.session_state.generated_schema, tokens_used = st.session_state.core.generate_sql_schema(db_name, table_description, table_rules, existed_tables_str)
        update_used_tokens(tokens_used)
        st.session_state.operation_done = "Schema generated"
    st.rerun()

if button_generate_prisma:
    if not db_name or not table_description or not table_rules:
        st.session_state.operation_errors = "Please enter database name, table description and rules"
    else:
        existed_tables_str = ""
        st.session_state.generated_schema, tokens_used = st.session_state.core.generate_prisma_schema(db_name, table_description, table_rules, existed_tables_str)
        update_used_tokens(tokens_used)
        st.session_state.operation_done = "Prisma schema generated"
    st.rerun()

if button_generate_sql:
    if not db_name or not table_schema or not st.session_state.table_script_definition:
        st.session_state.operation_errors = "Please enter database name, table schema and script definition"
    else:
        existed_tables_str = ""
        st.session_state.generated_sql, tokens_used = st.session_state.core.generate_sql(db_name, table_schema, st.session_state.table_script_definition, existed_tables_str)
        update_used_tokens(tokens_used)
        st.session_state.operation_done = "SQL generated"
    st.rerun()
