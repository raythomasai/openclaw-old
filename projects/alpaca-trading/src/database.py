"""Database module for trade history."""
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import Trade


class TradeDatabase:
    """SQLite database for trade history."""
    
    def __init__(self, db_path: str | Path | None = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent / "data" / "trades.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    qty REAL NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    pnl REAL,
                    strategy TEXT NOT NULL,
                    status TEXT NOT NULL,
                    order_id TEXT
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_trades_strategy ON trades(strategy)
            """)
    
    def insert_trade(self, trade: Trade) -> int:
        """Insert a trade and return its ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO trades 
                (timestamp, symbol, side, qty, entry_price, exit_price, pnl, strategy, status, order_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade.timestamp.isoformat(),
                trade.symbol,
                trade.side,
                trade.qty,
                trade.entry_price,
                trade.exit_price,
                trade.pnl,
                trade.strategy,
                trade.status,
                trade.order_id
            ))
            return cursor.lastrowid
    
    def update_trade(self, trade_id: int, exit_price: float, pnl: float, status: str) -> None:
        """Update a trade with exit info."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE trades 
                SET exit_price = ?, pnl = ?, status = ?
                WHERE id = ?
            """, (exit_price, pnl, status, trade_id))
    
    def get_trades_today(self) -> list[dict]:
        """Get all trades from today."""
        today = datetime.now().strftime("%Y-%m-%d")
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM trades 
                WHERE timestamp LIKE ?
                ORDER BY timestamp DESC
            """, (f"{today}%",))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_daily_pnl(self, date: str | None = None) -> float:
        """Get total P&L for a date (defaults to today)."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT COALESCE(SUM(pnl), 0) as total_pnl
                FROM trades 
                WHERE timestamp LIKE ? AND pnl IS NOT NULL
            """, (f"{date}%",))
            row = cursor.fetchone()
            return row[0] if row else 0.0
    
    def get_strategy_stats(self, strategy: str, days: int = 30) -> dict:
        """Get performance stats for a strategy."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                    COALESCE(SUM(pnl), 0) as total_pnl,
                    COALESCE(AVG(pnl), 0) as avg_pnl
                FROM trades 
                WHERE strategy = ? 
                AND timestamp >= date('now', ?)
                AND pnl IS NOT NULL
            """, (strategy, f"-{days} days"))
            row = cursor.fetchone()
            return {
                "total_trades": row[0],
                "winning_trades": row[1] or 0,
                "losing_trades": row[2] or 0,
                "total_pnl": row[3],
                "avg_pnl": row[4],
                "win_rate": (row[1] / row[0] * 100) if row[0] > 0 else 0
            }
    
    def get_all_trades(self, limit: int = 100) -> list[dict]:
        """Get recent trades."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM trades 
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]


if __name__ == "__main__":
    # Quick test
    db = TradeDatabase()
    print(f"Database: {db.db_path}")
    print(f"Today's trades: {len(db.get_trades_today())}")
    print(f"Today's P&L: ${db.get_daily_pnl():.2f}")
