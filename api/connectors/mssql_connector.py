# filepath: c:\git\FitnessFunctions\api\connectors\mssql_connector.py
from api.connectors.base_connector import BaseConnector
from typing import Dict, Any, Optional, List
import pyodbc
import logging

logger = logging.getLogger(__name__)

class MsSqlConnector(BaseConnector):
    """Connects to Microsoft SQL Server and executes a configured query."""

    def fetch_data(self, app_config: Optional[Dict[str, Any]] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Connects to MS SQL Server, executes the configured query, potentially
        parameterized by app_config, and returns the results as a list of dictionaries.

        Required params:
            - connection_string: The pyodbc connection string.
              OR
            - server: Server name or IP.
            - database: Database name.
            - driver: ODBC Driver name (e.g., '{ODBC Driver 17 for SQL Server}').
            Optional params for connection:
            - uid: User ID (if using SQL authentication).
            - pwd: Password (if using SQL authentication).
            - trusted_connection: 'yes' (if using Windows authentication).
            Required params for query:
            - query: The SQL query to execute.

        Optional app_config usage:
            - If the query contains placeholders like '?' and app_config contains
              relevant keys (e.g., 'app_id'), they can be passed as parameters.
              For simplicity, this initial version assumes the query might use
              one parameter derived from app_config['app_id']' if present.
        """
        query = self.params.get('query')
        if not query:
            logger.error("MS SQL Connector: Missing 'query' parameter.")
            return None

        conn_string = self.params.get('connection_string')
        if not conn_string:
            server = self.params.get('server')
            database = self.params.get('database')
            driver = self.params.get('driver')
            uid = self.params.get('uid')
            pwd = self.params.get('pwd')
            trusted = self.params.get('trusted_connection', 'no') # Default to no

            if not all([server, database, driver]):
                 logger.error("MS SQL Connector: Missing required connection parameters (server, database, driver) or connection_string.")
                 return None

            conn_parts = [
                f"DRIVER={driver}",
                f"SERVER={server}",
                f"DATABASE={database}",
            ]
            if trusted.lower() == 'yes':
                 conn_parts.append("Trusted_Connection=yes")
            elif uid and pwd:
                 conn_parts.append(f"UID={uid}")
                 conn_parts.append(f"PWD={pwd}")
            else:
                 logger.error("MS SQL Connector: Missing credentials (uid/pwd) or trusted_connection=yes.")
                 return None
            conn_string = ";".join(conn_parts)

        conn = None
        cursor = None
        results = []
        params_list = []

        # Basic parameterization: Use app_id if query has '?' and app_config has 'app_id'
        if '?' in query and app_config and 'app_id' in app_config:
            params_list.append(app_config['app_id'])
            logger.info(f"MS SQL Connector: Using app_id '{app_config['app_id']}' as query parameter.")

        try:
            logger.info(f"MS SQL Connector: Connecting to {self.params.get('server')}/{self.params.get('database')}")
            conn = pyodbc.connect(conn_string, autocommit=True) # Autocommit often simpler for read-only
            cursor = conn.cursor()

            logger.info(f"MS SQL Connector: Executing query: {query} with params: {params_list}")
            if params_list:
                cursor.execute(query, params_list)
            else:
                cursor.execute(query)

            columns = [column[0] for column in cursor.description]
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

            logger.info(f"MS SQL Connector: Fetched {len(results)} rows.")
            return results # Return list of dicts

        except pyodbc.Error as ex:
            sqlstate = ex.args[0]
            logger.error(f"MS SQL Connector: Database error (SQLSTATE: {sqlstate}): {ex}")
            return None
        except Exception as e:
            logger.error(f"MS SQL Connector: Unexpected error: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
                logger.debug("MS SQL Connector: Cursor closed.")
            if conn:
                conn.close()
                logger.debug("MS SQL Connector: Connection closed.")

