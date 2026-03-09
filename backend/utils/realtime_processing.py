#!/usr/bin/env python3
"""
Real-time Processing Service for Enhanced OCR Certificate Processing
Provides WebSocket connections for live processing updates and statistics tracking
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
import uuid
from dataclasses import dataclass, asdict

@dataclass
class ProcessingStats:
    """Real-time processing statistics"""
    total_processed: int = 0
    successful: int = 0
    failed: int = 0
    enhanced_processed: int = 0
    fallback_processed: int = 0
    duplicates_found: int = 0
    average_confidence: float = 0.0
    processing_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ProcessingUpdate:
    """Individual processing update message"""
    id: str
    filename: str
    status: str  # 'processing', 'completed', 'failed', 'duplicate'
    confidence: Optional[float] = None
    processing_method: Optional[str] = None  # 'enhanced_ocr', 'fallback_ocr'
    error_message: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat() if self.timestamp else None
        return data

class RealtimeProcessingService:
    """Service for managing real-time certificate processing updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.processing_sessions: Dict[str, Dict[str, Any]] = {}
        self.global_stats = ProcessingStats()
    
    async def connect(self, websocket: WebSocket, session_id: str = None) -> str:
        """Connect a WebSocket client for real-time updates"""
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        await websocket.accept()
        self.active_connections[session_id] = websocket
        
        # Initialize session stats
        self.processing_sessions[session_id] = {
            "stats": ProcessingStats(),
            "current_batch": [],
            "start_time": datetime.utcnow()
        }
        
        # Send initial connection message
        await self.send_message(session_id, {
            "type": "connection_established",
            "session_id": session_id,
            "global_stats": self.global_stats.to_dict()
        })
        
        return session_id
    
    def disconnect(self, session_id: str):
        """Disconnect a WebSocket client"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.processing_sessions:
            del self.processing_sessions[session_id]
    
    async def send_message(self, session_id: str, message: Dict[str, Any]) -> bool:
        """Send a message to a specific client"""
        if session_id in self.active_connections:
            try:
                websocket = self.active_connections[session_id]
                await websocket.send_text(json.dumps(message))
                return True
            except Exception as e:
                print(f"Error sending message to {session_id}: {e}")
                # Clean up broken connection
                self.disconnect(session_id)
                return False
        return False
    
    async def broadcast_message(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients"""
        disconnected_sessions = []
        
        for session_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                print(f"Error broadcasting to {session_id}: {e}")
                disconnected_sessions.append(session_id)
        
        # Clean up broken connections
        for session_id in disconnected_sessions:
            self.disconnect(session_id)
    
    async def start_batch_processing(self, session_id: str, file_count: int) -> bool:
        """Initialize a new batch processing session"""
        if session_id not in self.processing_sessions:
            return False
        
        session = self.processing_sessions[session_id]
        session["current_batch"] = []
        session["batch_size"] = file_count
        session["processed_count"] = 0
        
        await self.send_message(session_id, {
            "type": "batch_started",
            "file_count": file_count,
            "session_stats": session["stats"].to_dict()
        })
        
        return True
    
    async def update_processing_status(
        self, 
        session_id: str, 
        filename: str, 
        status: str,
        confidence: Optional[float] = None,
        processing_method: Optional[str] = None,
        error_message: Optional[str] = None,
        extracted_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update the processing status of a file"""
        if session_id not in self.processing_sessions:
            return False
        
        session = self.processing_sessions[session_id]
        session_stats = session["stats"]
        
        # Create processing update
        update = ProcessingUpdate(
            id=str(uuid.uuid4()),
            filename=filename,
            status=status,
            confidence=confidence,
            processing_method=processing_method,
            error_message=error_message,
            extracted_data=extracted_data
        )
        
        # Update session statistics
        session_stats.total_processed += 1
        
        if status == "completed":
            session_stats.successful += 1
            if processing_method == "enhanced_ocr":
                session_stats.enhanced_processed += 1
            elif processing_method == "fallback_ocr":
                session_stats.fallback_processed += 1
            
            # Update average confidence
            if confidence is not None:
                current_avg = session_stats.average_confidence
                total_success = session_stats.successful
                session_stats.average_confidence = ((current_avg * (total_success - 1)) + confidence) / total_success
                
        elif status == "failed":
            session_stats.failed += 1
        elif status == "duplicate":
            session_stats.duplicates_found += 1
        
        # Add to current batch
        session["current_batch"].append(update)
        session["processed_count"] = session["processed_count"] + 1 if "processed_count" in session else 1
        
        # Send update to client
        await self.send_message(session_id, {
            "type": "processing_update",
            "update": update.to_dict(),
            "session_stats": session_stats.to_dict(),
            "progress": {
                "processed": session.get("processed_count", 0),
                "total": session.get("batch_size", 0)
            }
        })
        
        # Update global stats
        self._update_global_stats(update)
        
        return True
    
    def _update_global_stats(self, update: ProcessingUpdate):
        """Update global processing statistics"""
        self.global_stats.total_processed += 1
        
        if update.status == "completed":
            self.global_stats.successful += 1
            if update.processing_method == "enhanced_ocr":
                self.global_stats.enhanced_processed += 1
            elif update.processing_method == "fallback_ocr":
                self.global_stats.fallback_processed += 1
                
            # Update global average confidence
            if update.confidence is not None:
                current_avg = self.global_stats.average_confidence
                total_success = self.global_stats.successful
                self.global_stats.average_confidence = ((current_avg * (total_success - 1)) + update.confidence) / total_success
                
        elif update.status == "failed":
            self.global_stats.failed += 1
        elif update.status == "duplicate":
            self.global_stats.duplicates_found += 1
    
    async def complete_batch_processing(self, session_id: str, final_results: Dict[str, Any]) -> bool:
        """Complete a batch processing session"""
        if session_id not in self.processing_sessions:
            return False
        
        session = self.processing_sessions[session_id]
        session_stats = session["stats"]
        
        # Calculate processing time
        start_time = session["start_time"]
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        session_stats.processing_time_ms = processing_time
        
        # Send completion message
        await self.send_message(session_id, {
            "type": "batch_completed",
            "final_results": final_results,
            "session_stats": session_stats.to_dict(),
            "processing_time_ms": processing_time
        })
        
        return True
    
    async def get_real_time_stats(self, session_id: str = None) -> Dict[str, Any]:
        """Get current processing statistics"""
        if session_id and session_id in self.processing_sessions:
            return {
                "session_stats": self.processing_sessions[session_id]["stats"].to_dict(),
                "global_stats": self.global_stats.to_dict()
            }
        else:
            return {
                "global_stats": self.global_stats.to_dict(),
                "active_sessions": len(self.active_connections)
            }
    
    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of a processing session"""
        if session_id not in self.processing_sessions:
            return None
        
        session = self.processing_sessions[session_id]
        stats = session["stats"]
        
        return {
            "session_id": session_id,
            "start_time": session["start_time"].isoformat(),
            "stats": stats.to_dict(),
            "files_processed": len(session["current_batch"]),
            "recent_updates": [update.to_dict() for update in session["current_batch"][-10:]]  # Last 10 updates
        }

# Global instance for the service
realtime_service = RealtimeProcessingService()

# WebSocket endpoint handler
async def websocket_endpoint(websocket: WebSocket, session_id: str = None):
    """WebSocket endpoint for real-time processing updates"""
    session_id = await realtime_service.connect(websocket, session_id)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types from client
            if message.get("type") == "get_stats":
                stats = await realtime_service.get_real_time_stats(session_id)
                await realtime_service.send_message(session_id, {
                    "type": "stats_response",
                    "stats": stats
                })
            elif message.get("type") == "ping":
                await realtime_service.send_message(session_id, {
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
    except WebSocketDisconnect:
        realtime_service.disconnect(session_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        realtime_service.disconnect(session_id)
