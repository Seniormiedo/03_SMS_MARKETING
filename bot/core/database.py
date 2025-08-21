"""
Database connection and query manager for Contact Extractor Bot
Handles PostgreSQL connections and optimized queries
"""

import asyncio
from contextlib import asynccontextmanager
from typing import List, Optional, Tuple, Dict, Any
import asyncpg
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool

from config import get_config
from models.contact import Contact, ContactFilter, ContactStatus
from utils.logger import get_logger


class DatabaseManager:
    """
    Professional database manager for PostgreSQL operations
    Supports both sync and async operations with connection pooling
    """
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger()
        self._sync_pool: Optional[psycopg2.pool.ThreadedConnectionPool] = None
        self._async_pool: Optional[asyncpg.Pool] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize database connections and pools"""
        if self._initialized:
            return
        
        try:
            # Initialize sync connection pool with optimized settings
            self._sync_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=2,
                maxconn=self.config.db_pool_size,
                host=self.config.db_host,
                port=self.config.db_port,
                database=self.config.db_name,
                user=self.config.db_user,
                password=self.config.db_password,
                # Optimized connection parameters for large datasets
                options="-c default_statistics_target=100 -c work_mem=256MB -c maintenance_work_mem=512MB"
            )
            
            # Initialize async connection pool
            self._async_pool = await asyncpg.create_pool(
                host=self.config.db_host,
                port=self.config.db_port,
                database=self.config.db_name,
                user=self.config.db_user,
                password=self.config.db_password,
                min_size=1,
                max_size=self.config.db_pool_size,
                command_timeout=self.config.query_timeout
            )
            
            self._initialized = True
            self.logger.info("Database connections initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database connections: {e}")
            raise
    
    async def close(self):
        """Close all database connections"""
        if self._async_pool:
            await self._async_pool.close()
        
        if self._sync_pool:
            self._sync_pool.closeall()
        
        self._initialized = False
        self.logger.info("Database connections closed")
    
    @asynccontextmanager
    async def get_async_connection(self):
        """Get async database connection from pool"""
        if not self._initialized:
            await self.initialize()
        
        connection = await self._async_pool.acquire()
        try:
            yield connection
        finally:
            await self._async_pool.release(connection)
    
    def get_sync_connection(self):
        """Get sync database connection from pool"""
        if not self._initialized:
            # For sync operations, we need to initialize sync pool only
            self._sync_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=self.config.db_pool_size,
                host=self.config.db_host,
                port=self.config.db_port,
                database=self.config.db_name,
                user=self.config.db_user,
                password=self.config.db_password
            )
        
        return self._sync_pool.getconn()
    
    def return_sync_connection(self, connection):
        """Return sync connection to pool"""
        if self._sync_pool:
            self._sync_pool.putconn(connection)
    
    def test_connection(self) -> bool:
        """
        Test database connection
        
        Returns:
            bool: True if connection successful
        """
        try:
            conn = self.get_sync_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            self.return_sync_connection(conn)
            
            self.logger.info("Database connection test successful")
            return result[0] == 1
            
        except Exception as e:
            self.logger.error(f"Database connection test failed: {e}")
            return False
    
    def get_premium_contacts(self, limit: int) -> List[Contact]:
        """
        Get contacts from premium LADAs (mejores_ladas) - PRODUCTION OPTIMIZED
        Mapea LADAs de 2 dígitos (55->551,552,553 y 81->811) a LADAs reales de 3 dígitos
        
        Args:
            limit: Maximum number of contacts to return
            
        Returns:
            List[Contact]: Premium contacts available for extraction
        """
        query = """
        -- Extraer contactos de LADAs premium reales (551,552,553,811, etc.)
        WITH premium_ladas_real AS (
            -- Las LADAs premium que realmente existen en contacts
            SELECT DISTINCT c.lada, COUNT(*) as contact_count
            FROM contacts c
            WHERE c.lada IN ('551', '552', '553', '811', '818', '656', '614', '667', '668', '669')
              AND c.status = 'VERIFIED' 
              AND c.opt_out_at IS NULL
            GROUP BY c.lada
            HAVING COUNT(*) > 1000
            ORDER BY COUNT(*) DESC
            LIMIT 10
        ),
        balanced_selection AS (
            SELECT c.id, c.phone_national, c.phone_e164, c.city, c.state_name, 
                   c.lada, c.operator, c.is_mobile, c.status, c.created_at,
                   ROW_NUMBER() OVER (
                       PARTITION BY c.lada 
                       ORDER BY RANDOM()
                   ) as rn
            FROM contacts c
            JOIN premium_ladas_real plr ON c.lada = plr.lada
            WHERE c.status = 'VERIFIED' 
              AND c.opt_out_at IS NULL
        )
        SELECT id, phone_national, phone_e164, city, state_name, lada, 
               operator, is_mobile, status, created_at,
               NULL as full_name, NULL as address, NULL as neighborhood,
               NULL as state_code, NULL as municipality,
               NULL as status_updated_at, NULL as status_source,
               0 as send_count, NULL as last_sent_at,
               NULL as opt_out_at, NULL as opt_out_method,
               NULL as last_validated_at, 0 as validation_attempts,
               'TELCEL2022' as source, NULL as import_batch_id, NULL as updated_at
        FROM balanced_selection
        WHERE rn <= CEIL(%s / 10.0)  -- Distribuir entre las 10 mejores LADAs
        ORDER BY RANDOM()
        LIMIT %s;
        """
        
        return self._execute_contact_query(query, (limit, limit))
    
    def get_contacts_by_state(self, state: str, limit: int) -> List[Contact]:
        """
        Get contacts by state name with EXACT matching
        
        Args:
            state: State name to filter by
            limit: Maximum number of contacts to return
            
        Returns:
            List[Contact]: Contacts from specified state
        """
        query = """
        SELECT id, phone_national, phone_e164, city, state_name, lada, 
               operator, is_mobile, status, created_at,
               full_name, address, neighborhood, state_code, municipality,
               status_updated_at, status_source, send_count, last_sent_at,
               opt_out_at, opt_out_method, last_validated_at, validation_attempts,
               source, import_batch_id, updated_at
        FROM contacts 
        WHERE UPPER(TRIM(state_name)) = UPPER(TRIM(%s))
          AND status = 'VERIFIED'
          AND opt_out_at IS NULL
        ORDER BY RANDOM()
        LIMIT %s;
        """
        
        return self._execute_contact_query(query, (state, limit))
    
    def get_contacts_by_city(self, city: str, limit: int) -> List[Contact]:
        """
        Get contacts by city name with fuzzy matching
        Searches in both city and municipality fields for better coverage
        
        Args:
            city: City name to filter by
            limit: Maximum number of contacts to return
            
        Returns:
            List[Contact]: Contacts from specified city
        """
        # Enhanced query that searches in both city and municipality
        # This handles cases where city data might be in either field
        query = """
        SELECT id, phone_national, phone_e164, city, state_name, lada, 
               operator, is_mobile, status, created_at,
               full_name, address, neighborhood, state_code, municipality,
               status_updated_at, status_source, send_count, last_sent_at,
               opt_out_at, opt_out_method, last_validated_at, validation_attempts,
               source, import_batch_id, updated_at
        FROM contacts 
        WHERE (city ILIKE %s OR municipality ILIKE %s)
          AND status = 'VERIFIED'
          AND opt_out_at IS NULL
        ORDER BY 
            -- Prioritize exact city matches, then municipality matches
            CASE 
                WHEN city ILIKE %s THEN 1 
                WHEN municipality ILIKE %s THEN 2 
                ELSE 3 
            END,
            RANDOM()
        LIMIT %s;
        """
        
        city_pattern = f"%{city}%"
        return self._execute_contact_query(query, (
            city_pattern, city_pattern, city_pattern, city_pattern, limit
        ))
    
    def get_contacts_by_municipality(self, municipality: str, limit: int) -> List[Contact]:
        """
        Get contacts by municipality name
        
        Args:
            municipality: Municipality name to filter by
            limit: Maximum number of contacts to return
            
        Returns:
            List[Contact]: Contacts from specified municipality
        """
        query = """
        SELECT *
        FROM contacts 
        WHERE municipality ILIKE %s 
          AND status = 'VERIFIED'
          AND opt_out_at IS NULL
        ORDER BY RANDOM()
        LIMIT %s;
        """
        
        return self._execute_contact_query(query, (f"%{municipality}%", limit))
    
    def get_contacts_by_lada(self, lada: str, limit: int) -> List[Contact]:
        """
        Get contacts by LADA
        
        Args:
            lada: LADA to filter by
            limit: Maximum number of contacts to return
            
        Returns:
            List[Contact]: Contacts from specified LADA
        """
        query = """
        SELECT *
        FROM contacts 
        WHERE lada = %s 
          AND status = 'VERIFIED'
          AND opt_out_at IS NULL
        ORDER BY RANDOM()
        LIMIT %s;
        """
        
        return self._execute_contact_query(query, (lada, limit))
    
    def mark_contacts_as_opted_out(self, contact_ids: List[int]) -> bool:
        """
        Mark contacts as OPTED_OUT to prevent reuse
        
        Args:
            contact_ids: List of contact IDs to mark
            
        Returns:
            bool: True if successful
        """
        if not contact_ids:
            return True
        
        query = """
        UPDATE contacts 
        SET status = %s,
            opt_out_at = NOW(),
            opt_out_method = %s,
            updated_at = NOW()
        WHERE id = ANY(%s);
        """
        
        try:
            conn = self.get_sync_connection()
            cursor = conn.cursor()
            
            cursor.execute(query, (
                ContactStatus.OPTED_OUT.value,
                'BOT_EXTRACTION',
                contact_ids
            ))
            
            rows_affected = cursor.rowcount
            conn.commit()
            cursor.close()
            self.return_sync_connection(conn)
            
            self.logger.info(f"Marked {rows_affected} contacts as OPTED_OUT")
            return rows_affected > 0
            
        except Exception as e:
            self.logger.error(f"Failed to mark contacts as opted out: {e}")
            if conn:
                conn.rollback()
                cursor.close()
                self.return_sync_connection(conn)
            return False
    
    def get_available_states(self) -> List[str]:
        """
        Get list of available states with contacts
        
        Returns:
            List[str]: Available state names
        """
        query = """
        SELECT DISTINCT state_name
        FROM contacts 
        WHERE state_name IS NOT NULL 
          AND status = 'VERIFIED'
          AND opt_out_at IS NULL
        ORDER BY state_name;
        """
        
        return self._execute_simple_query(query)
    
    def get_available_cities(self, state: Optional[str] = None) -> List[str]:
        """
        Get list of available cities with contacts
        
        Args:
            state: Optional state filter
            
        Returns:
            List[str]: Available city names
        """
        if state:
            query = """
            SELECT DISTINCT city
            FROM contacts 
            WHERE city IS NOT NULL 
              AND state_name ILIKE %s
              AND status = 'VERIFIED'
              AND opt_out_at IS NULL
            ORDER BY city;
            """
            params = (f"%{state}%",)
        else:
            query = """
            SELECT DISTINCT city
            FROM contacts 
            WHERE city IS NOT NULL 
              AND status = 'VERIFIED'
              AND opt_out_at IS NULL
            ORDER BY city;
            """
            params = ()
        
        return self._execute_simple_query(query, params)
    
    def get_premium_states(self) -> List[str]:
        """
        Get premium states from mejores_ladas table
        
        Returns:
            List[str]: Premium state names ordered by ICPTH
        """
        query = """
        SELECT DISTINCT estado
        FROM mejores_ladas 
        ORDER BY MAX(icpth_2022) DESC
        LIMIT 10;
        """
        
        return self._execute_simple_query(query)
    
    def validate_premium_availability(self, limit: int) -> bool:
        """
        Check if enough premium contacts are available
        
        Args:
            limit: Required number of contacts
            
        Returns:
            bool: True if enough contacts available
        """
        query = """
        WITH premium_states AS (
            SELECT DISTINCT estado 
            FROM mejores_ladas 
            ORDER BY icpth_2022 DESC 
            LIMIT 10
        )
        SELECT COUNT(c.id) as available_count
        FROM contacts c
        JOIN premium_states ps ON c.state_name = ps.estado
        WHERE c.status = 'VERIFIED' 
          AND c.opt_out_at IS NULL;
        """
        
        try:
            conn = self.get_sync_connection()
            cursor = conn.cursor()
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()
            self.return_sync_connection(conn)
            
            available = result[0] if result else 0
            return available >= limit
            
        except Exception as e:
            self.logger.error(f"Failed to validate premium availability: {e}")
            return False
    
    def validate_location_availability(self, location: str, location_type: str, limit: int) -> bool:
        """
        Check if enough contacts are available for a location
        
        Args:
            location: Location name
            location_type: Type of location (state, city, municipality, lada)
            limit: Required number of contacts
            
        Returns:
            bool: True if enough contacts available
        """
        column_map = {
            "state": "state_name",
            "city": "city", 
            "municipality": "municipality",
            "lada": "lada"
        }
        
        column = column_map.get(location_type, "city")  # Default to city for better matching
        
        # For cities, also check municipality as fallback
        if location_type == "city":
            query = f"""
            SELECT COUNT(id) as available_count
            FROM contacts 
            WHERE (city ILIKE %s OR municipality ILIKE %s)
              AND status = 'VERIFIED'
              AND opt_out_at IS NULL;
            """
            params = (f"%{location}%", f"%{location}%")
        else:
            query = f"""
            SELECT COUNT(id) as available_count
            FROM contacts 
            WHERE {column} ILIKE %s 
              AND status = 'VERIFIED'
              AND opt_out_at IS NULL;
            """
            params = (f"%{location}%",)
        
        try:
            conn = self.get_sync_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchone()
            cursor.close()
            self.return_sync_connection(conn)
            
            available = result[0] if result else 0
            self.logger.info(f"Location availability check: {location} ({location_type}) = {available:,} contacts (need {limit})")
            return available >= limit
            
        except Exception as e:
            self.logger.error(f"Failed to validate location availability: {e}")
            return False
    
    def _execute_contact_query(self, query: str, params: tuple = ()) -> List[Contact]:
        """
        Execute query and return Contact objects
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            List[Contact]: List of contact objects
        """
        try:
            conn = self.get_sync_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            self.return_sync_connection(conn)
            
            contacts = []
            for row in rows:
                try:
                    # Convert database row to Contact object
                    contact_data = dict(row)
                    contact = Contact(**contact_data)
                    contacts.append(contact)
                except Exception as e:
                    self.logger.warning(f"Failed to parse contact {row.get('id', 'unknown')}: {e}")
                    continue
            
            self.logger.info(f"Retrieved {len(contacts)} contacts from database")
            return contacts
            
        except Exception as e:
            self.logger.error(f"Failed to execute contact query: {e}")
            return []
    
    def _execute_simple_query(self, query: str, params: tuple = ()) -> List[str]:
        """
        Execute simple query and return list of strings
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            List[str]: Query results
        """
        try:
            conn = self.get_sync_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            self.return_sync_connection(conn)
            
            results = [row[0] for row in rows if row[0] is not None]
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to execute simple query: {e}")
            return []
    
    def get_validation_numbers(self) -> List[Dict[str, Any]]:
        """
        Get all active validation numbers
        Returns list of validation numbers with metadata
        """
        connection = None
        try:
            connection = self.get_sync_connection()
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT 
                    id,
                    phone_number,
                    lada,
                    state_validation as state_name,
                    municipality_validation as municipality,
                    usage_count,
                    last_used,
                    created_at
                FROM validation_numbers 
                WHERE is_active = TRUE
                ORDER BY usage_count ASC, RANDOM()
            """)
            
            results = cursor.fetchall()
            self.logger.debug(f"Retrieved {len(results)} active validation numbers")
            
            return [dict(row) for row in results]
            
        except Exception as e:
            self.logger.error(f"Failed to get validation numbers: {e}")
            return []
        finally:
            if connection:
                self.return_sync_connection(connection)
    
    def get_random_validation_number(self) -> Optional[Dict[str, Any]]:
        """
        Get a random validation number with lowest usage count
        Returns validation number data or None if none available
        """
        connection = None
        try:
            connection = self.get_sync_connection()
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            
            # Get validation number with lowest usage count (random among ties)
            cursor.execute("""
                SELECT 
                    id,
                    phone_number,
                    lada,
                    state_validation as state_name,
                    municipality_validation as municipality,
                    usage_count,
                    last_used
                FROM validation_numbers 
                WHERE is_active = TRUE
                ORDER BY usage_count ASC, RANDOM()
                LIMIT 1
            """)
            
            result = cursor.fetchone()
            
            if result:
                self.logger.debug(f"Selected validation number: {result['phone_number']} (usage: {result['usage_count']})")
                return dict(result)
            else:
                self.logger.warning("No active validation numbers available")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get random validation number: {e}")
            return None
        finally:
            if connection:
                self.return_sync_connection(connection)
    
    def update_validation_usage(self, phone_number: str) -> bool:
        """
        Update usage statistics for a validation number
        Increments usage_count and updates last_used timestamp
        """
        connection = None
        try:
            connection = self.get_sync_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                UPDATE validation_numbers 
                SET 
                    usage_count = usage_count + 1,
                    last_used = CURRENT_TIMESTAMP
                WHERE phone_number = %s AND is_active = TRUE
            """, (phone_number,))
            
            updated_rows = cursor.rowcount
            connection.commit()
            
            if updated_rows > 0:
                self.logger.debug(f"Updated usage for validation number: {phone_number}")
                return True
            else:
                self.logger.warning(f"Validation number not found or inactive: {phone_number}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to update validation usage for {phone_number}: {e}")
            if connection:
                connection.rollback()
            return False
        finally:
            if connection:
                self.return_sync_connection(connection)
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """
        Get validation numbers statistics
        Returns usage statistics and distribution
        """
        connection = None
        try:
            connection = self.get_sync_connection()
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            
            # Get overall stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_numbers,
                    COUNT(CASE WHEN is_active THEN 1 END) as active_numbers,
                    SUM(usage_count) as total_usage,
                    AVG(usage_count) as avg_usage,
                    MIN(usage_count) as min_usage,
                    MAX(usage_count) as max_usage,
                    COUNT(CASE WHEN last_used IS NOT NULL THEN 1 END) as used_numbers
                FROM validation_numbers
            """)
            
            stats = dict(cursor.fetchone())
            
            # Get top used numbers
            cursor.execute("""
                SELECT phone_number, usage_count, last_used
                FROM validation_numbers 
                WHERE is_active = TRUE
                ORDER BY usage_count DESC, last_used DESC
                LIMIT 5
            """)
            
            top_used = [dict(row) for row in cursor.fetchall()]
            
            # Get least used numbers
            cursor.execute("""
                SELECT phone_number, usage_count, last_used
                FROM validation_numbers 
                WHERE is_active = TRUE
                ORDER BY usage_count ASC, last_used ASC NULLS FIRST
                LIMIT 5
            """)
            
            least_used = [dict(row) for row in cursor.fetchall()]
            
            return {
                'stats': stats,
                'top_used': top_used,
                'least_used': least_used
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get validation stats: {e}")
            return {}
        finally:
            if connection:
                self.return_sync_connection(connection)


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """
    Get global database manager instance (singleton)
    
    Returns:
        DatabaseManager: Database manager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


async def initialize_database():
    """Initialize database connections"""
    db = get_database_manager()
    await db.initialize()
    return db


async def close_database():
    """Close database connections"""
    db = get_database_manager()
    await db.close()


# Export main classes and functions
__all__ = [
    "DatabaseManager",
    "get_database_manager", 
    "initialize_database",
    "close_database"
]