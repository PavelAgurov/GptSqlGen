"""
    LLM Core
"""
# pylint: disable=C0301,C0103,C0303,C0411,W1203

import logging
import os
from typing import Any

from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain.globals import set_llm_cache
from langchain_community.cache import SQLiteCache
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.callbacks.manager import get_openai_callback

from backend import prompts
from backend import xml_utils

logger : logging.Logger = logging.getLogger()

class LLMCore:
    """
        LLM Core
    """
    _BASE_MODEL_NAME = "gpt-3.5-turbo-0125"
    _MAX_TOKENS = 2000

    chain_generate_sql_schema = None
    chain_generate_prisma_schema = None
    chain_generate_sql = None

    def __init__(self, all_secrets : dict[str, Any]):

        # Init cache
        set_llm_cache(SQLiteCache(database_path=".langchain.db"))

        # init env
        self.init_llm_environment(all_secrets)

        # Init LLM
        llm = self.create_llm(self._MAX_TOKENS, self._BASE_MODEL_NAME)

        # Init chains
        generate_sql_schema_prompt = ChatPromptTemplate.from_template(prompts.GENERATE_SQL_SCHEMA_PROMPT)
        self.chain_generate_sql_schema  = generate_sql_schema_prompt | llm | StrOutputParser()

        generate_prisma_schema_prompt = ChatPromptTemplate.from_template(prompts.GENERATE_PRISMA_SCHEMA_PROMPT)
        self.chain_generate_prisma_schema  = generate_prisma_schema_prompt | llm | StrOutputParser()

        generate_sql_prompt = ChatPromptTemplate.from_template(prompts.GENERATE_SQL_PROMPT)
        self.chain_generate_sql  = generate_sql_prompt | llm | StrOutputParser()

    def init_llm_environment(self, all_secrets : dict[str, any]):
        """Inint OpenAI or Azure environment"""

        self.openai_api_type = 'openai'
        self.openai_api_deployment = None
        if not all_secrets:
            return
 
        # read from secrets
        self.openai_api_type = all_secrets.get('OPENAI_API_TYPE')

        if self.openai_api_type == 'openai':
            openai_secrets = all_secrets.get('open_api_openai')
            if openai_secrets:
                os.environ["OPENAI_API_KEY"] = openai_secrets.get('OPENAI_API_KEY')
                base_model_name = openai_secrets.get('OPENAI_BASE_MODEL_NAME')
                if base_model_name:
                    self._BASE_MODEL_NAME = base_model_name
                max_tokens = openai_secrets.get('MAX_TOKENS')
                if max_tokens:
                    self._MAX_TOKENS = int(max_tokens)
                logger.info(f'Run with OpenAI from config file [{len(os.environ["OPENAI_API_KEY"])}]')
                logger.info(f'Base model {self._BASE_MODEL_NAME}')
            else:
                logger.error('open_api_openai section is required')
            return

        if self.openai_api_type == 'azure':
            azure_secrets = all_secrets.get('open_api_azure')
            if azure_secrets:
                os.environ["AZURE_OPENAI_API_KEY"] = azure_secrets.get('AZURE_OPENAI_API_KEY')
                os.environ["OPENAI_API_TYPE"] = "azure"
                os.environ["OPENAI_API_VERSION"] = azure_secrets.get('OPENAI_API_VERSION')
                os.environ["AZURE_OPENAI_ENDPOINT"] = azure_secrets.get('AZURE_OPENAI_ENDPOINT')
                self.openai_api_deployment = azure_secrets.get('OPENAI_API_DEPLOYMENT')
                base_model_name = azure_secrets.get('OPENAI_BASE_MODEL_NAME')
                if base_model_name:
                    self._BASE_MODEL_NAME = base_model_name
                max_tokens = azure_secrets.get('MAX_TOKENS')
                if max_tokens:
                    self._MAX_TOKENS = int(max_tokens)
                logger.info('Run with Azure OpenAI config file')
                logger.info(f'Base model {self._BASE_MODEL_NAME}')
            else:
                logger.error('open_api_azure section is required')
            return
        
        logger.error(f'init_llm_environment: unsupported OPENAI_API_TYPE: {self.openai_api_type}')

    def create_llm(self, max_tokens : int, model_name : str) -> ChatOpenAI:
        """Create LLM"""

        if self.openai_api_type == 'openai':
            return ChatOpenAI(
                model_name     = model_name,
                max_tokens     = max_tokens,
                temperature    = 0,
                verbose        = False
            )
        
        if self.openai_api_type == 'azure':
            return AzureChatOpenAI(
                azure_deployment   = self.openai_api_deployment,
                model_name     = model_name,
                max_tokens     = max_tokens,
                temperature    = 0,
                verbose        = False
            )
        
        logger.error(f'create_llm: unsupported OPENAI_API_TYPE: {self.openai_api_type}')
        return None


    def generate_sql_schema(self, db_name : str, table_description : str, rules : str = None, existed_tables : list[str] = None) -> str :
        """
            Generate SQL schema based on table description and list of existed tables
        """
        if existed_tables is None:
            existed_tables = []
        existed_tables_str = "\n".join([f"- {t} - table for {t.replace('tb_', '')}" for t in existed_tables])

        if rules is None:
            rules = prompts.GENERATE_SCHEMA_DEFAULT_RULES

        with get_openai_callback() as cb:
            sql_xml = self.chain_generate_sql_schema.invoke({
                "dbname" : db_name,
                "rules" : rules,
                "existed_tables": existed_tables_str, 
                "table_description": table_description
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
    

    def generate_prisma_schema(self, db_name : str, table_description : str, rules : str = None, existed_tables : list[str] = None) -> str :
        """
            Generate Prisma schema based on table description and list of existed tables
        """
        if existed_tables is None:
            existed_tables = []
        existed_tables_str = "\n".join([f"- {t} - table for {t.replace('tb_', '')}" for t in existed_tables])

        if rules is None:
            rules = prompts.GENERATE_SCHEMA_DEFAULT_RULES

        with get_openai_callback() as cb:
            sql_xml = self.chain_generate_prisma_schema.invoke({
                "dbname" : db_name,
                "rules" : rules,
                "existed_tables": existed_tables_str, 
                "table_description": table_description
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
    
        prisma_element = x.find('.//prisma')
        prisma_string = prisma_element.text.strip()
        return prisma_string, table_name, tokens_used


    def generate_sql(self, db_name : str, table_schema : str, script_definition : str = None, existed_tables : list[str] = None) -> str:
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
                "dbname" : db_name,
                "existed_tables": existed_tables_str, 
                "script": script_definition, 
                "table_schema": table_schema
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