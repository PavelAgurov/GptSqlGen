"""
    LLM Prompts
"""

GENERATE_SQL_SCHEMA_PROMPT = """
You are {dbname} DB engineer with 10 years of experience.
Your task is to generate table fields based on provided table description and list of already existed tables.
Check each field and build foregn key where field is a reference to the existed table.
Use the best db practices:
- find the best name for each field
- all names are in lower case
- boolean fields should have "is" prefix
- tables have prefix "tb_"
###
Output has to be in XML format as table name and set of fields.
{rules}
Do not add field if it has default value.
###
Table definition:
{table_description}
###
Existed tables (used for references in foregn key):
{existed_tables}
###
<output>
    <table name="">
       <field name="" />
    </table>
</output>
"""

GENERATE_PRISMA_SCHEMA_PROMPT = """
You are {dbname} DB engineer with 10 years of experience.
Your task is to generate Prisma table definision.
Check each field and build foregn key where field is a reference to the existed table.
Use the best db practices:
- find the best name for each field
- all names are in lower case
- boolean fields should have "is" prefix
- tables have prefix "tb_"
###
Output has to be in XML format as table name and prisma schema.
###
Table definition:
{table_description}
###
Existed tables (used for references in foregn key):
{existed_tables}
###
<output>
 <table name="">
  <prisma>
  Prisma schema here
  </prisma>
 </table>
</output>
"""

GENERATE_SCHEMA_DEFAULT_RULES = """
Field contains:
- correct database field name based on SQL notation
- field type based on SQL types
- primary_key (if true, default value is false)
- not_null (if true, default value is false)
- unique (if true, default value is false)
- foreign_key (if field is id for another table)
"""

GENERATE_SQL_PROMPT = """
You are {dbname} DB engineer with 10 years of experience. 
Your task is to generate {dbname} scripts based on provided table desciption.
Use the best db practices:
- for get operation you should generate VIEW and do NOT use "select *"
- all foregn key constrains must have name

When table has "is_deleted" field then delete procedure should set this flag and do not delete item from the table.
But if table has no "is_deleted" field - do NOT add it.

###
Output has to be in XML format.
###
Scripts to generate:
{script}
###
Table schema:
{table_schema}
###
Existed tables (used for references in foregn key):
{existed_tables}
###
You MUST generate ALL requested scripts! It's very important task.
###
<output>
 <created_tables>
     <table>table</table>
 </created_tables>
 <foregn_key_tables>
     <table>foregn key table</table>
 </foregn_key_tables>
 <sql_script_text>
   put result here as SQL-text with comments, do not add additional xml tags
 </sql_script_text>
</output>
"""

GENERATE_SQL_DEFAULT_CRUD = """
1. CREATE TABLE script
2. Stored procedures to create (return new id) 
3. Stored procedures to update by id (return True if success)
4. Stored procedures to delete by id (return True if success)
5. Stored procedures to get by id
6. View and stored procedures to get all items
"""
