"""
    Core module
"""
# pylint: disable=C0301,C0103,C0303,C0411,W1203

import logging
from backend.llm_core import LLMCore 

logger : logging.Logger = logging.getLogger()

class Core:
    """
        Core class for back-end
    """

    llm_backend = None

    def __init__(self):
        logger.info("Core init")
        self.llm_backend = LLMCore()


    def generate_sql_schema(self, db_name : str, table_description : str, table_rules : str, existed_tables_str : str) -> str :
        """
            Generate SQL schema for a table
        """
        logger.info("Generate SQL schema...")
        existed_tables = existed_tables_str.split()
        table_schema, table_name, tokens_used = self.llm_backend.generate_sql_schema(db_name, table_description, table_rules, existed_tables)
        logger.debug(f"table_schema: {table_schema}")
        logger.debug(f"table_name: {table_name}")
        logger.debug(f"LLM used tokens: {tokens_used}")

        return table_schema, tokens_used
    
    def generate_prisma_schema(self, db_name : str, table_description : str, table_rules : str, existed_tables_str : str) -> str :
        """
            Generate Prisma schema for a table
        """
        logger.info("Generate Prisma schema...")
        existed_tables = existed_tables_str.split()
        table_schema, table_name, tokens_used = self.llm_backend.generate_prisma_schema(db_name, table_description, table_rules, existed_tables)
        logger.debug(f"table_schema: {table_schema}")
        logger.debug(f"table_name: {table_name}")
        logger.debug(f"LLM used tokens: {tokens_used}")

        return table_schema, tokens_used

    def generate_sql(self, db_name : str, table_schema : str, script_definition : str, existed_tables_str : str) -> str:
        """
            Generate sql for a table
        """
        logger.info("Generate_sql...")
        existed_tables = existed_tables_str.split()
        new_tables, table_sql, local_errors, tokens_used = self.llm_backend.generate_sql(db_name, table_schema, script_definition, existed_tables)
        logger.debug(f"Table sql: {table_sql}")
        logger.debug(f"New tables: {new_tables}")
        logger.debug(f"Local errors: {local_errors}")
        logger.debug(f"LLM used tokens: {tokens_used}")

        return table_sql, tokens_used
