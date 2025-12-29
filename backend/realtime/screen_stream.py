# backend/realtime/screen_stream.py
import asyncio
import logging
from typing import Callable, Optional
from collections import deque
from datetime import datetime
from services.vision import VisionService

logger = logging.getLogger(__name__)

class ScreenStreamHandler:
    """
    Handles real-time screen capture analysis with change detection
    """
    
    def __init__(
        self,
        vision_service: VisionService,
        analysis_interval: float = 5.0,  # seconds between analyses
        change_threshold: float = 0.3    # 30% change triggers alert
    ):
        self.vision_service = vision_service
        self.analysis_interval = analysis_interval
        self.change_threshold = change_threshold
        
        # Frame buffer
        self.frame_buffer = deque(maxlen=100)  # Keep last 100 frames
        self.last_analysis_time: Optional[datetime] = None
        self.last_analysis_result: Optional[str] = None
        
        # Callbacks
        self.on_analysis: Optional[Callable] = None
        self.on_change_detected: Optional[Callable] = None
        
        logger.info(f"Screen stream handler initialized (interval: {analysis_interval}s)")
    
    async def process_frame(
        self,
        frame_base64: str,
        frame_timestamp: float
    ) -> Optional[dict]:
        """
        Process incoming screen frame
        
        Args:
            frame_base64: Base64 encoded screenshot
            frame_timestamp: Client timestamp
            
        Returns:
            Analysis result if threshold met, None otherwise
        """
        try:
            # Store frame
            self.frame_buffer.append({
                'data': frame_base64,
                'timestamp': datetime.fromtimestamp(frame_timestamp / 1000),
                'analyzed': False
            })
            
            # Check if we should analyze
            now = datetime.now()
            should_analyze = (
                self.last_analysis_time is None or
                (now - self.last_analysis_time).total_seconds() >= self.analysis_interval
            )
            
            if should_analyze:
                result = await self._analyze_current_frame(frame_base64)
                self.last_analysis_time = now
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            return None
    
    async def _analyze_current_frame(self, frame_base64: str) -> dict:
        """Analyze current screen frame"""
        
        try:
            logger.info("Analyzing screen frame...")
            
            # General analysis
            analysis = await self.vision_service.analyze_image(
                frame_base64,
                prompt="""Analyze this screen capture and provide:
1. Main content/application visible
2. Any important data, metrics, or alerts
3. Notable changes or issues (errors, warnings)
4. Overall status (normal/warning/critical)

Be concise and focus on actionable insights."""
            )
            
            # Check for changes if we have previous analysis
            has_significant_change = False
            if self.last_analysis_result:
                has_significant_change = await self._detect_changes(
                    frame_base64,
                    self.last_analysis_result,
                    analysis
                )
            
            result = {
                'timestamp': datetime.now().isoformat(),
                'analysis': analysis,
                'has_significant_change': has_significant_change,
                'frame_number': len(self.frame_buffer)
            }
            
            self.last_analysis_result = analysis
            
            logger.info(f"Screen analysis complete (change detected: {has_significant_change})")
            
            return result
            
        except Exception as e:
            logger.error(f"Screen analysis error: {e}")
            raise
    
    async def _detect_changes(
        self,
        current_frame: str,
        previous_analysis: str,
        current_analysis: str
    ) -> bool:
        """
        Detect if significant changes occurred
        
        Simple heuristic: compare text similarity
        Advanced: could use image diff or semantic comparison
        """
        # Simple text-based change detection
        prev_words = set(previous_analysis.lower().split())
        curr_words = set(current_analysis.lower().split())
        
        # Calculate Jaccard similarity
        intersection = len(prev_words & curr_words)
        union = len(prev_words | curr_words)
        
        similarity = intersection / union if union > 0 else 1.0
        change_ratio = 1.0 - similarity
        
        logger.debug(f"Change detection: {change_ratio:.2%} different")
        
        return change_ratio > self.change_threshold
    
    async def analyze_with_comparison(
        self,
        frame1_base64: str,
        frame2_base64: str
    ) -> str:
        """Compare two specific frames"""
        
        try:
            comparison = await self.vision_service.compare_images(
                frame1_base64,
                frame2_base64
            )
            return comparison
            
        except Exception as e:
            logger.error(f"Frame comparison error: {e}")
            raise
    
    async def detect_anomalies(self, frame_base64: str) -> dict:
        """
        Detect anomalies in screen (errors, warnings, unusual patterns)
        """
        try:
            analysis = await self.vision_service.analyze_image(
                frame_base64,
                prompt="""Analyze this screen for issues:
- Error messages or warnings
- Unusual metrics or patterns
- System alerts
- Performance issues

Return JSON: {"has_issues": bool, "severity": "low/medium/high", "details": "..."}"""
            )
            
            # Try to parse as JSON (Claude might return it)
            import json
            try:
                return json.loads(analysis)
            except:
                # Fallback if not JSON
                return {
                    "has_issues": any(word in analysis.lower() for word in ['error', 'warning', 'failed', 'critical']),
                    "severity": "medium",
                    "details": analysis
                }
                
        except Exception as e:
            logger.error(f"Anomaly detection error: {e}")
            raise
    
    def get_frame_history(self, count: int = 10) -> list:
        """Get recent frames"""
        return list(self.frame_buffer)[-count:]
    
    def clear_buffer(self):
        """Clear frame buffer"""
        self.frame_buffer.clear()
        logger.debug("Frame buffer cleared")