"""
    LLM Core
"""
# pylint: disable=C0301,C0103,C0303,C0411,W1203

import logging

from langchain_openai import ChatOpenAI
from langchain.globals import set_llm_cache
from langchain.cache import SQLiteCache
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain.callbacks import get_openai_callback

from backend import prompts
from backend import xml_utils

logger : logging.Logger = logging.getLogger()

class LLMCore:
    """
        LLM Core
    """

    def __init__(self):

        # Init cache
        set_llm_cache(SQLiteCache(database_path=".langchain.db"))

        # Init LLM
        self.llm = ChatOpenAI(
            model_name="gpt-3.5-turbo-0125", 
            #model_name = "gpt-4-0125-preview",
            temperature=0,
            max_tokens = 2000
        )

        # Init chains
        generate_schema_prompt = ChatPromptTemplate.from_template(prompts.GENERATE_SCHEMA_PROMPT)
        self.chain_generate_schema  = generate_schema_prompt | self.llm | StrOutputParser()

        generate_sql_prompt = ChatPromptTemplate.from_template(prompts.GENERATE_SQL_PROMPT)
        self.chain_generate_sql  = generate_sql_prompt | self.llm | StrOutputParser()


    def generate_schema(self, table_description : str, rules : str = None, existed_tables : list[str] = None) -> str :
        """
            Generate schema based on table description and list of existed tables
        """
        if existed_tables is None:
            existed_tables = []
        existed_tables_str = "\n".join([f"- {t} - table for {t.replace('tb_', '')}" for t in existed_tables])

        if rules is None:
            rules = prompts.GENERATE_SCHEMA_DEFAULT_RULES

        with get_openai_callback() as cb:
            sql_xml = self.chain_generate_schema.invoke({
                "rules" : rules,
                "existed_tables": existed_tables_str, 
                "table_fields": table_description
            })
        tokens_used = cb.total_tokens
       
        sql_xml = self.extract_llm_xml_string(sql_xml)
        logger.debug(f"LLM generated schema: {sql_xml}")
        logger.debug(f"LLM used tokens: {tokens_used}")
        
        x = xml_utils.get_as_xml(sql_xml)
        table_element = x.find('.//table')
        if table_element is None:
            logger.error("Could not find table element in LLM generated XML")
            return None, None, tokens_used
    
        table_name = table_element.attrib['name']
        if table_name is None:
            logger.error("Could not find table name in LLM generated XML")
            return table_element, None, tokens_used
    
        table_string = xml_utils.xml_to_string(table_element)
        return table_string, table_name, tokens_used
    
    def generate_sql(self, table_schema : str, script_definition : str = None, existed_tables : list[str] = None) -> str:
        """
            Generate sql for a table
        """
        if not script_definition:
            script_definition = prompts.GENERATE_SQL_DEFAULT_CRUD
        
        if existed_tables is None:
            existed_tables = []
        existed_tables_str = "\n".join([f"- {t} - table for {t.replace('tb_', '')}" for t in existed_tables])

        with get_openai_callback() as cb:
            sql_xml = self.chain_generate_sql.invoke({
                "existed_tables": existed_tables_str, 
                "script": script_definition, 
                "table_fields": table_schema
            })
        tokens_used = cb.total_tokens
       
        sql_xml = self.extract_llm_xml_string(sql_xml)
        logger.debug(f"LLM generated sql: {sql_xml}")
        logger.debug(f"LLM used tokens: {tokens_used}")
        
        x = xml_utils.get_as_xml(sql_xml)

        new_tables    = xml_utils.get_array_by_xpath(x , './/created_tables//table')
        foregn_tables = xml_utils.get_array_by_xpath(x , './/foregn_key_tables//table')
        sql_script    = xml_utils.get_text_by_xpath(x , './/sql_script_text').strip('\n ')
    
        local_errors = []
    
        new_tables    = [i for i in new_tables if i and i.lower() != 'none'] # remove empty
        foregn_tables = [i for i in foregn_tables if i and i.lower() != 'none']
    
        for t in foregn_tables:
            if t not in new_tables and t not in existed_tables:
                local_errors.append(f"Table {t} doesn't exist")
    
        return new_tables, sql_script, local_errors, tokens_used

    def extract_llm_xml_string(self, sql_xml : str) -> str:
        """
        Extract LLM generated XML string
        """
        sql_xml = sql_xml.strip()
            
        xml_begin = "```xml"
        if sql_xml.startswith(xml_begin):
            sql_xml = sql_xml[len(xml_begin):]

        xml_end = "```"
        if sql_xml.endswith(xml_end):
            sql_xml = sql_xml[:-len(xml_end)]
            
        sql_xml = sql_xml.strip()

        return sql_xml