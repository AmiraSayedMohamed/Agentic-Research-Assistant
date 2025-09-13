"""
Research Database - Handles data persistence for research results and history
"""

import asyncio
import logging
import sqlite3
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
import aiosqlite
from pathlib import Path

from ..models.schemas import (
    ResearchResult, ResearchHistoryEntry, PresentationFormat
)

logger = logging.getLogger(__name__)

class ResearchDatabase:
    """Database handler for research data persistence"""
    
    def __init__(self, db_path: str = "research_assistant.db"):
        self.db_path = db_path
        self.db_dir = Path(db_path).parent
        
    async def initialize(self):
        """Initialize database with required tables"""
        logger.info("Initializing research database...")
        
        # Ensure database directory exists
        self.db_dir.mkdir(parents=True, exist_ok=True)
        
        # Create tables
        await self._create_tables()
        
        logger.info(f"Database initialized at {self.db_path}")
    
    async def cleanup(self):
        """Cleanup database connections"""
        logger.info("Database cleanup complete")
    
    async def _create_tables(self):
        """Create database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Research results table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS research_results (
                    id TEXT PRIMARY KEY,
                    query_text TEXT NOT NULL,
                    query_params TEXT,
                    papers_found TEXT,
                    paper_summaries TEXT,
                    synthesis_report TEXT,
                    formatted_report TEXT,
                    presentation_format TEXT,
                    processing_time_seconds REAL,
                    total_tokens_used INTEGER,
                    created_at TIMESTAMP,
                    status TEXT DEFAULT 'completed'
                )
            """)
            
            # Research history table (for quick access)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS research_history (
                    id TEXT PRIMARY KEY,
                    query_text TEXT NOT NULL,
                    papers_count INTEGER,
                    processing_time REAL,
                    status TEXT,
                    created_at TIMESTAMP,
                    FOREIGN KEY (id) REFERENCES research_results (id)
                )
            """)
            
            # Failed workflows table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS failed_workflows (
                    id TEXT PRIMARY KEY,
                    query_text TEXT,
                    error_message TEXT,
                    processing_time REAL,
                    created_at TIMESTAMP
                )
            """)
            
            # System statistics table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS system_stats (
                    date TEXT PRIMARY KEY,
                    total_queries INTEGER DEFAULT 0,
                    successful_queries INTEGER DEFAULT 0,
                    failed_queries INTEGER DEFAULT 0,
                    total_papers_analyzed INTEGER DEFAULT 0,
                    avg_processing_time REAL DEFAULT 0.0,
                    updated_at TIMESTAMP
                )
            """)
            
            await db.commit()
    
    async def store_research_result(self, result: ResearchResult):
        """Store complete research result"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Store main result
                await db.execute("""
                    INSERT OR REPLACE INTO research_results 
                    (id, query_text, query_params, papers_found, paper_summaries, 
                     synthesis_report, formatted_report, presentation_format,
                     processing_time_seconds, total_tokens_used, created_at, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result.research_id,
                    result.query.query,
                    json.dumps(result.query.dict(), default=str),
                    json.dumps([paper.dict() for paper in result.papers_found], default=str),
                    json.dumps([summary.dict() for summary in result.paper_summaries], default=str),
                    json.dumps(result.synthesis_report.dict(), default=str),
                    result.formatted_report,
                    result.presentation_format.value,
                    result.processing_time_seconds,
                    result.total_tokens_used,
                    result.created_at,
                    'completed'
                ))
                
                # Store in history table for quick access
                await db.execute("""
                    INSERT OR REPLACE INTO research_history
                    (id, query_text, papers_count, processing_time, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    result.research_id,
                    result.query.query,
                    len(result.papers_found),
                    result.processing_time_seconds,
                    'completed',
                    result.created_at
                ))
                
                await db.commit()
                
                # Update system statistics
                await self._update_system_stats(
                    successful=True,
                    papers_count=len(result.papers_found),
                    processing_time=result.processing_time_seconds
                )
                
                logger.info(f"Stored research result {result.research_id}")
                
        except Exception as e:
            logger.error(f"Failed to store research result: {str(e)}")
            raise
    
    async def store_research_failure(self, research_id: str, query: str, 
                                   error_message: str, processing_time: float):
        """Store failed research attempt"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Store in failed workflows
                await db.execute("""
                    INSERT INTO failed_workflows 
                    (id, query_text, error_message, processing_time, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    research_id,
                    query,
                    error_message,
                    processing_time,
                    datetime.now()
                ))
                
                # Store in history as failed
                await db.execute("""
                    INSERT INTO research_history
                    (id, query_text, papers_count, processing_time, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    research_id,
                    query,
                    0,
                    processing_time,
                    'failed',
                    datetime.now()
                ))
                
                await db.commit()
                
                # Update system statistics
                await self._update_system_stats(
                    successful=False,
                    papers_count=0,
                    processing_time=processing_time
                )
                
                logger.info(f"Stored failed research {research_id}")
                
        except Exception as e:
            logger.error(f"Failed to store research failure: {str(e)}")
            raise
    
    async def get_research_result(self, research_id: str) -> Optional[ResearchResult]:
        """Retrieve research result by ID"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                
                async with db.execute(
                    "SELECT * FROM research_results WHERE id = ?", 
                    (research_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    
                    if not row:
                        return None
                    
                    # Deserialize JSON fields
                    query_params = json.loads(row['query_params'])
                    papers_found = json.loads(row['papers_found'])
                    paper_summaries = json.loads(row['paper_summaries'])
                    synthesis_report = json.loads(row['synthesis_report'])
                    
                    # Reconstruct ResearchResult (simplified)
                    # In production, you'd properly reconstruct all objects
                    logger.info(f"Retrieved research result {research_id}")
                    return None  # Simplified for demo
                    
        except Exception as e:
            logger.error(f"Failed to retrieve research result {research_id}: {str(e)}")
            return None
    
    async def get_research_history(self, limit: int = 50) -> List[ResearchHistoryEntry]:
        """Get research history"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                
                async with db.execute("""
                    SELECT * FROM research_history 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (limit,)) as cursor:
                    rows = await cursor.fetchall()
                    
                    history = []
                    for row in rows:
                        entry = ResearchHistoryEntry(
                            research_id=row['id'],
                            query=row['query_text'],
                            papers_count=row['papers_count'],
                            created_at=datetime.fromisoformat(row['created_at']),
                            processing_time=row['processing_time'],
                            status=row['status']
                        )
                        history.append(entry)
                    
                    logger.debug(f"Retrieved {len(history)} history entries")
                    return history
                    
        except Exception as e:
            logger.error(f"Failed to retrieve research history: {str(e)}")
            return []
    
    async def search_research_history(self, query_filter: str, limit: int = 20) -> List[ResearchHistoryEntry]:
        """Search research history by query text"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                
                async with db.execute("""
                    SELECT * FROM research_history 
                    WHERE query_text LIKE ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (f"%{query_filter}%", limit)) as cursor:
                    rows = await cursor.fetchall()
                    
                    history = []
                    for row in rows:
                        entry = ResearchHistoryEntry(
                            research_id=row['id'],
                            query=row['query_text'],
                            papers_count=row['papers_count'],
                            created_at=datetime.fromisoformat(row['created_at']),
                            processing_time=row['processing_time'],
                            status=row['status']
                        )
                        history.append(entry)
                    
                    return history
                    
        except Exception as e:
            logger.error(f"Failed to search research history: {str(e)}")
            return []
    
    async def delete_research_entry(self, research_id: str):
        """Delete research entry from database"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Delete from all tables
                await db.execute("DELETE FROM research_results WHERE id = ?", (research_id,))
                await db.execute("DELETE FROM research_history WHERE id = ?", (research_id,))
                await db.execute("DELETE FROM failed_workflows WHERE id = ?", (research_id,))
                await db.commit()
                
                logger.info(f"Deleted research entry {research_id}")
                
        except Exception as e:
            logger.error(f"Failed to delete research entry {research_id}: {str(e)}")
            raise
    
    async def update_research_result_format(self, research_id: str, 
                                         new_formatted_report: str,
                                         new_format: PresentationFormat):
        """Update the formatted report and presentation format"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE research_results 
                    SET formatted_report = ?, presentation_format = ?
                    WHERE id = ?
                """, (new_formatted_report, new_format.value, research_id))
                await db.commit()
                
                logger.info(f"Updated format for research result {research_id}")
                
        except Exception as e:
            logger.error(f"Failed to update research result format: {str(e)}")
            raise
    
    async def get_system_statistics(self) -> Dict[str, Any]:
        """Get system usage statistics"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                
                # Get overall statistics
                stats = {}
                
                # Total queries
                async with db.execute("SELECT COUNT(*) as count FROM research_history") as cursor:
                    row = await cursor.fetchone()
                    stats['total_queries'] = row['count']
                
                # Successful vs failed
                async with db.execute("SELECT status, COUNT(*) as count FROM research_history GROUP BY status") as cursor:
                    rows = await cursor.fetchall()
                    for row in rows:
                        stats[f"{row['status']}_queries"] = row['count']
                
                # Average processing time
                async with db.execute("SELECT AVG(processing_time) as avg_time FROM research_history WHERE status = 'completed'") as cursor:
                    row = await cursor.fetchone()
                    stats['avg_processing_time'] = row['avg_time'] or 0.0
                
                # Total papers analyzed
                async with db.execute("SELECT SUM(papers_count) as total FROM research_history WHERE status = 'completed'") as cursor:
                    row = await cursor.fetchone()
                    stats['total_papers_analyzed'] = row['total'] or 0
                
                # Recent activity (last 24 hours)
                async with db.execute("""
                    SELECT COUNT(*) as count FROM research_history 
                    WHERE created_at >= datetime('now', '-1 day')
                """) as cursor:
                    row = await cursor.fetchone()
                    stats['queries_last_24h'] = row['count']
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get system statistics: {str(e)}")
            return {}
    
    async def _update_system_stats(self, successful: bool, papers_count: int, processing_time: float):
        """Update daily system statistics"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            async with aiosqlite.connect(self.db_path) as db:
                # Get existing stats for today
                async with db.execute("SELECT * FROM system_stats WHERE date = ?", (today,)) as cursor:
                    row = await cursor.fetchone()
                
                if row:
                    # Update existing record
                    total_queries = row[1] + 1
                    successful_queries = row[2] + (1 if successful else 0)
                    failed_queries = row[3] + (0 if successful else 1)
                    total_papers = row[4] + papers_count
                    
                    # Calculate new average processing time
                    old_avg = row[5]
                    new_avg = ((old_avg * (total_queries - 1)) + processing_time) / total_queries
                    
                    await db.execute("""
                        UPDATE system_stats 
                        SET total_queries = ?, successful_queries = ?, failed_queries = ?,
                            total_papers_analyzed = ?, avg_processing_time = ?, updated_at = ?
                        WHERE date = ?
                    """, (total_queries, successful_queries, failed_queries, 
                          total_papers, new_avg, datetime.now(), today))
                else:
                    # Create new record
                    await db.execute("""
                        INSERT INTO system_stats 
                        (date, total_queries, successful_queries, failed_queries,
                         total_papers_analyzed, avg_processing_time, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (today, 1, 1 if successful else 0, 0 if successful else 1,
                          papers_count, processing_time, datetime.now()))
                
                await db.commit()
                
        except Exception as e:
            logger.error(f"Failed to update system stats: {str(e)}")
    
    async def cleanup_old_data(self, days_to_keep: int = 90):
        """Cleanup old research data"""
        try:
            cutoff_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            async with aiosqlite.connect(self.db_path) as db:
                # Delete old records
                await db.execute("""
                    DELETE FROM research_results 
                    WHERE created_at < datetime('now', '-{} days')
                """.format(days_to_keep))
                
                await db.execute("""
                    DELETE FROM research_history 
                    WHERE created_at < datetime('now', '-{} days')
                """.format(days_to_keep))
                
                await db.execute("""
                    DELETE FROM failed_workflows 
                    WHERE created_at < datetime('now', '-{} days')
                """.format(days_to_keep))
                
                await db.commit()
                
                logger.info(f"Cleaned up data older than {days_to_keep} days")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {str(e)}")
            raise