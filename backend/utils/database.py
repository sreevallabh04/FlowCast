from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
import logging
from typing import Optional, Generator, Any, Dict, List
import time
from functools import wraps
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime

class DatabaseManager:
    """Database connection and session manager."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize database manager.
        
        Args:
            config: Database configuration dictionary
        """
        self.config = config
        self.engine = None
        self.session_factory = None
        self._setup_engine()
        self._setup_session()
        
    def _setup_engine(self) -> None:
        """Set up SQLAlchemy engine with connection pooling."""
        try:
            # Construct database URL
            db_url = f"postgresql://{self.config['user']}:{self.config['password']}@{self.config['host']}:{self.config['port']}/{self.config['database']}"
            
            # Create engine with connection pooling
            self.engine = create_engine(
                db_url,
                poolclass=QueuePool,
                pool_size=self.config.get('pool_size', 5),
                max_overflow=self.config.get('max_overflow', 10),
                pool_timeout=self.config.get('pool_timeout', 30),
                pool_recycle=self.config.get('pool_recycle', 1800),
                echo=self.config.get('echo', False)
            )
            
            # Add event listeners for connection management
            @event.listens_for(self.engine, 'connect')
            def connect(dbapi_connection, connection_record):
                logging.debug("New database connection established")
                
            @event.listens_for(self.engine, 'checkout')
            def checkout(dbapi_connection, connection_record, connection_proxy):
                logging.debug("Database connection checked out from pool")
                
            @event.listens_for(self.engine, 'checkin')
            def checkin(dbapi_connection, connection_record):
                logging.debug("Database connection returned to pool")
                
        except Exception as e:
            logging.error(f"Error setting up database engine: {str(e)}")
            raise
            
    def _setup_session(self) -> None:
        """Set up SQLAlchemy session factory."""
        try:
            self.session_factory = scoped_session(
                sessionmaker(
                    bind=self.engine,
                    autocommit=False,
                    autoflush=False,
                    expire_on_commit=False
                )
            )
        except Exception as e:
            logging.error(f"Error setting up session factory: {str(e)}")
            raise
            
    @contextmanager
    def get_session(self) -> Generator[Any, None, None]:
        """Get database session context manager.
        
        Yields:
            Database session
        """
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
            
    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Execute raw SQL query.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of result dictionaries
        """
        try:
            with self.engine.connect() as connection:
                result = connection.execute(query, params or {})
                return [dict(row) for row in result]
        except SQLAlchemyError as e:
            logging.error(f"Error executing query: {str(e)}")
            raise
            
    def execute_transaction(self, queries: List[Dict[str, Any]]) -> None:
        """Execute multiple queries in a transaction.
        
        Args:
            queries: List of query dictionaries with 'query' and 'params' keys
        """
        with self.get_session() as session:
            try:
                for query_dict in queries:
                    session.execute(query_dict['query'], query_dict.get('params', {}))
                session.commit()
            except SQLAlchemyError as e:
                session.rollback()
                logging.error(f"Error executing transaction: {str(e)}")
                raise
                
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get database connection pool statistics.
        
        Returns:
            Dictionary containing pool statistics
        """
        return {
            'pool_size': self.engine.pool.size(),
            'checked_in': self.engine.pool.checkedin(),
            'checked_out': self.engine.pool.checkedout(),
            'overflow': self.engine.pool.overflow(),
            'checkedin_connections': len(self.engine.pool._pool),
            'max_overflow': self.engine.pool._max_overflow
        }
        
    def optimize_connection_pool(self) -> None:
        """Optimize connection pool settings based on usage patterns."""
        stats = self.get_connection_stats()
        
        # Adjust pool size if needed
        if stats['checked_out'] > stats['pool_size'] * 0.8:
            new_size = min(stats['pool_size'] * 1.5, self.config.get('max_pool_size', 20))
            self.engine.pool._pool.resize(new_size)
            logging.info(f"Connection pool size adjusted to {new_size}")
            
        # Adjust max overflow if needed
        if stats['overflow'] > self.config.get('max_overflow', 10) * 0.8:
            new_overflow = min(self.config.get('max_overflow', 10) * 1.5, 30)
            self.engine.pool._max_overflow = new_overflow
            logging.info(f"Max overflow adjusted to {new_overflow}")
            
    def health_check(self) -> bool:
        """Check database connection health.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            with self.engine.connect() as connection:
                connection.execute("SELECT 1")
            return True
        except Exception as e:
            logging.error(f"Database health check failed: {str(e)}")
            return False
            
    def close(self) -> None:
        """Close all database connections."""
        if self.engine:
            self.engine.dispose()
            logging.info("Database connections closed")

def query_logger(func):
    """Decorator for logging database queries."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Log query details
            logging.info({
                'query': func.__name__,
                'execution_time': execution_time,
                'status': 'success'
            })
            
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Log error details
            logging.error({
                'query': func.__name__,
                'execution_time': execution_time,
                'status': 'error',
                'error': str(e)
            })
            
            raise
    return wrapper

class QueryOptimizer:
    """Query optimization and monitoring."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize query optimizer.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.query_stats = {}
        
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze query performance.
        
        Args:
            query: SQL query to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            with self.db_manager.engine.connect() as connection:
                result = connection.execute(f"EXPLAIN ANALYZE {query}")
                return {
                    'query': query,
                    'analysis': [dict(row) for row in result],
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            logging.error(f"Error analyzing query: {str(e)}")
            raise
            
    def track_query(self, query: str, execution_time: float) -> None:
        """Track query execution time.
        
        Args:
            query: SQL query
            execution_time: Query execution time in seconds
        """
        if query not in self.query_stats:
            self.query_stats[query] = []
            
        self.query_stats[query].append({
            'execution_time': execution_time,
            'timestamp': datetime.now().isoformat()
        })
        
    def get_slow_queries(self, threshold: float = 1.0) -> List[Dict[str, Any]]:
        """Get queries that exceed execution time threshold.
        
        Args:
            threshold: Execution time threshold in seconds
            
        Returns:
            List of slow queries with statistics
        """
        slow_queries = []
        for query, stats in self.query_stats.items():
            avg_time = sum(s['execution_time'] for s in stats) / len(stats)
            if avg_time > threshold:
                slow_queries.append({
                    'query': query,
                    'avg_execution_time': avg_time,
                    'execution_count': len(stats)
                })
        return slow_queries

# Example usage
if __name__ == "__main__":
    # Database configuration
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'flowcast',
        'user': 'postgres',
        'password': 'postgres',
        'pool_size': 5,
        'max_overflow': 10
    }
    
    # Initialize database manager
    db_manager = DatabaseManager(db_config)
    
    # Example query execution
    @query_logger
    def get_users():
        with db_manager.get_session() as session:
            return session.execute("SELECT * FROM users").fetchall()
            
    # Execute query
    try:
        users = get_users()
        print(f"Found {len(users)} users")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        db_manager.close() 