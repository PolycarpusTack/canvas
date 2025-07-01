"""
Export Transaction System

CLAUDE.md Implementation:
- #2.1.4: Atomic file operations with rollback
- #7.1: Path validation for security
- #12.1: Transaction logging
"""

import asyncio
import aiofiles
import shutil
import logging
from pathlib import Path
from typing import List, Optional, Union, Dict, Any
import tempfile
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class ExportTransaction:
    """
    Manages atomic file operations during export
    
    CLAUDE.md #2.1.4: Resource management with proper cleanup
    """
    
    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.temp_dir = None
        self.backup_dir = None
        self.written_files: List[Path] = []
        self.transaction_id = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self._lock = asyncio.Lock()
        self._committed = False
        self._rolled_back = False
        
        # Create paths
        self._setup_directories()
    
    def _setup_directories(self) -> None:
        """Setup temporary and backup directories"""
        # Create temp directory in system temp
        self.temp_dir = Path(tempfile.mkdtemp(prefix=f"canvas_export_{self.transaction_id}_"))
        
        # Backup path (if output exists)
        if self.output_path.exists():
            parent = self.output_path.parent
            self.backup_dir = parent / f".{self.output_path.name}_backup_{self.transaction_id}"
        
        logger.debug(
            f"Transaction initialized",
            extra={
                "transaction_id": self.transaction_id,
                "temp_dir": str(self.temp_dir),
                "output_path": str(self.output_path)
            }
        )
    
    async def write_file(
        self,
        relative_path: str,
        content: Union[str, bytes],
        encoding: str = "utf-8"
    ) -> None:
        """
        Write file to temporary location
        
        CLAUDE.md #7.1: Validate paths for security
        """
        async with self._lock:
            if self._committed or self._rolled_back:
                raise RuntimeError(f"Transaction already {'committed' if self._committed else 'rolled back'}")
            
            # Validate relative path
            if ".." in relative_path or relative_path.startswith("/"):
                raise ValueError(f"Invalid relative path: {relative_path}")
            
            # Create full path
            file_path = self.temp_dir / relative_path
            
            # Create parent directories
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            try:
                if isinstance(content, str):
                    async with aiofiles.open(file_path, 'w', encoding=encoding) as f:
                        await f.write(content)
                else:
                    async with aiofiles.open(file_path, 'wb') as f:
                        await f.write(content)
                
                self.written_files.append(file_path)
                
                logger.debug(
                    f"File written to transaction",
                    extra={
                        "transaction_id": self.transaction_id,
                        "file": relative_path,
                        "size": len(content) if isinstance(content, (str, bytes)) else 0
                    }
                )
                
            except Exception as e:
                logger.error(
                    f"Failed to write file in transaction",
                    extra={
                        "transaction_id": self.transaction_id,
                        "file": relative_path,
                        "error": str(e)
                    }
                )
                raise
    
    async def write_json(
        self,
        relative_path: str,
        data: Dict[str, Any],
        indent: int = 2
    ) -> None:
        """Write JSON file"""
        content = json.dumps(data, indent=indent, ensure_ascii=False)
        await self.write_file(relative_path, content)
    
    async def copy_file(
        self,
        source_path: Path,
        relative_dest: str
    ) -> None:
        """Copy existing file into transaction"""
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        dest_path = self.temp_dir / relative_dest
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file
        shutil.copy2(source_path, dest_path)
        self.written_files.append(dest_path)
    
    async def commit(self) -> None:
        """
        Atomically move temp files to final location
        
        CLAUDE.md #2.1.4: Atomic operations with rollback capability
        """
        async with self._lock:
            if self._committed:
                raise RuntimeError("Transaction already committed")
            if self._rolled_back:
                raise RuntimeError("Cannot commit rolled back transaction")
            
            try:
                # Backup existing directory if present
                if self.output_path.exists():
                    logger.info(f"Backing up existing export to {self.backup_dir}")
                    shutil.move(str(self.output_path), str(self.backup_dir))
                
                # Create output directory
                self.output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Move temp to final location
                shutil.move(str(self.temp_dir), str(self.output_path))
                
                # Remove backup on success
                if self.backup_dir and self.backup_dir.exists():
                    shutil.rmtree(self.backup_dir)
                    self.backup_dir = None
                
                self._committed = True
                
                logger.info(
                    f"Transaction committed successfully",
                    extra={
                        "transaction_id": self.transaction_id,
                        "files_written": len(self.written_files),
                        "output_path": str(self.output_path)
                    }
                )
                
            except Exception as e:
                # Restore backup on failure
                logger.error(
                    f"Transaction commit failed, restoring backup",
                    extra={
                        "transaction_id": self.transaction_id,
                        "error": str(e)
                    }
                )
                
                await self._restore_backup()
                raise
    
    async def rollback(self) -> None:
        """Rollback transaction and restore original state"""
        async with self._lock:
            if self._committed:
                raise RuntimeError("Cannot rollback committed transaction")
            if self._rolled_back:
                return  # Already rolled back
            
            try:
                # Clean up temp directory
                if self.temp_dir and self.temp_dir.exists():
                    shutil.rmtree(self.temp_dir)
                
                # Restore backup if exists
                await self._restore_backup()
                
                self._rolled_back = True
                
                logger.info(
                    f"Transaction rolled back",
                    extra={
                        "transaction_id": self.transaction_id,
                        "files_cleaned": len(self.written_files)
                    }
                )
                
            except Exception as e:
                logger.error(
                    f"Error during rollback",
                    extra={
                        "transaction_id": self.transaction_id,
                        "error": str(e)
                    }
                )
                # Continue with cleanup
    
    async def _restore_backup(self) -> None:
        """Restore backup directory"""
        if self.backup_dir and self.backup_dir.exists():
            # Remove any partial output
            if self.output_path.exists():
                shutil.rmtree(self.output_path)
            
            # Restore backup
            shutil.move(str(self.backup_dir), str(self.output_path))
            self.backup_dir = None
            
            logger.info(f"Backup restored to {self.output_path}")
    
    async def cleanup(self) -> None:
        """
        Clean up temporary resources
        
        CLAUDE.md #2.1.4: Ensure cleanup in all cases
        """
        try:
            # Clean up temp directory if not committed
            if not self._committed and self.temp_dir and self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
            
            # Clean up any remaining backup
            if self.backup_dir and self.backup_dir.exists():
                shutil.rmtree(self.backup_dir)
            
            logger.debug(
                f"Transaction cleanup completed",
                extra={
                    "transaction_id": self.transaction_id,
                    "committed": self._committed,
                    "rolled_back": self._rolled_back
                }
            )
            
        except Exception as e:
            logger.error(
                f"Error during cleanup",
                extra={
                    "transaction_id": self.transaction_id,
                    "error": str(e)
                }
            )
    
    async def create_directory(self, relative_path: str) -> None:
        """Create directory in transaction"""
        if ".." in relative_path or relative_path.startswith("/"):
            raise ValueError(f"Invalid relative path: {relative_path}")
        
        dir_path = self.temp_dir / relative_path
        dir_path.mkdir(parents=True, exist_ok=True)
    
    def get_temp_path(self, relative_path: str) -> Path:
        """Get full temporary path for a relative path"""
        return self.temp_dir / relative_path
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if exc_type is not None:
            # Rollback on exception
            await self.rollback()
        
        # Always cleanup
        await self.cleanup()


class TransactionManager:
    """
    Manages multiple concurrent transactions
    
    CLAUDE.md #6.1: Clear transaction ownership
    """
    
    def __init__(self):
        self.active_transactions: Dict[str, ExportTransaction] = {}
        self._lock = asyncio.Lock()
    
    async def create_transaction(self, output_path: Path) -> ExportTransaction:
        """Create and track new transaction"""
        transaction = ExportTransaction(output_path)
        
        async with self._lock:
            self.active_transactions[transaction.transaction_id] = transaction
        
        return transaction
    
    async def cleanup_transaction(self, transaction_id: str) -> None:
        """Remove transaction from tracking"""
        async with self._lock:
            if transaction_id in self.active_transactions:
                transaction = self.active_transactions[transaction_id]
                await transaction.cleanup()
                del self.active_transactions[transaction_id]
    
    async def cleanup_all(self) -> None:
        """Cleanup all active transactions"""
        async with self._lock:
            for transaction in self.active_transactions.values():
                try:
                    await transaction.cleanup()
                except Exception as e:
                    logger.error(f"Failed to cleanup transaction: {e}")
            
            self.active_transactions.clear()