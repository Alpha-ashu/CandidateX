"""
Anti-cheat system utilities for monitoring interview integrity.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import asyncio
from enum import Enum
from bson import ObjectId

from app.config import settings
from app.models import get_database, get_redis

logger = logging.getLogger(__name__)

class ViolationType(str, Enum):
    """Types of anti-cheat violations."""
    TAB_SWITCH = "tab_switch"
    WINDOW_FOCUS_LOST = "window_focus_lost"
    FULLSCREEN_EXIT = "fullscreen_exit"
    MULTIPLE_FACES = "multiple_faces"
    FACE_NOT_DETECTED = "face_not_detected"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    BROWSER_DEV_TOOLS = "browser_dev_tools"
    SCREENSHOT_ATTEMPT = "screenshot_attempt"
    EXTERNAL_DEVICE = "external_device"

class ViolationSeverity(str, Enum):
    """Severity levels for violations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AntiCheatMonitor:
    """Monitor for anti-cheat violations during interviews."""

    def __init__(self):
        self.violation_thresholds = {
            ViolationType.TAB_SWITCH: {"count": 3, "severity": ViolationSeverity.MEDIUM},
            ViolationType.WINDOW_FOCUS_LOST: {"count": 5, "severity": ViolationSeverity.MEDIUM},
            ViolationType.FULLSCREEN_EXIT: {"count": 2, "severity": ViolationSeverity.HIGH},
            ViolationType.MULTIPLE_FACES: {"count": 1, "severity": ViolationSeverity.CRITICAL},
            ViolationType.FACE_NOT_DETECTED: {"count": 10, "severity": ViolationSeverity.HIGH},
            ViolationType.BROWSER_DEV_TOOLS: {"count": 1, "severity": ViolationSeverity.CRITICAL},
            ViolationType.SCREENSHOT_ATTEMPT: {"count": 1, "severity": ViolationSeverity.HIGH},
        }

    async def log_violation(
        self,
        interview_id: str,
        user_id: str,
        violation_type: ViolationType,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
        severity: Optional[ViolationSeverity] = None
    ) -> Dict[str, Any]:
        """
        Log an anti-cheat violation.
        """
        db = await get_database()
        redis_client = await get_redis()

        # Determine severity if not provided
        if not severity:
            severity = self.violation_thresholds.get(violation_type, {}).get("severity", ViolationSeverity.LOW)

        violation = {
            "id": str(ObjectId()),
            "session_id": interview_id,
            "user_id": user_id,
            "event_type": violation_type.value,
            "severity": severity.value,
            "description": description,
            "timestamp": datetime.utcnow(),
            "metadata": metadata or {}
        }

        # Store in database
        await db.anti_cheat_events.insert_one(violation)

        # Update interview with violation
        await db.interviews.update_one(
            {"_id": interview_id},
            {
                "$push": {"anti_cheat_events": violation},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

        # Check if violation threshold exceeded
        threshold_exceeded = await self._check_violation_threshold(
            interview_id, violation_type, redis_client
        )

        if threshold_exceeded:
            await self._handle_threshold_exceeded(interview_id, user_id, violation_type, db)

        # Store violation count in Redis for quick access
        violation_key = f"interview_violations:{interview_id}:{violation_type.value}"
        await redis_client.incr(violation_key)
        await redis_client.expire(violation_key, 3600)  # 1 hour

        logger.warning(f"Anti-cheat violation logged: {violation_type.value} for user {user_id} in interview {interview_id}")

        return violation

    async def _check_violation_threshold(
        self,
        interview_id: str,
        violation_type: ViolationType,
        redis_client
    ) -> bool:
        """Check if violation threshold has been exceeded."""
        threshold = self.violation_thresholds.get(violation_type, {}).get("count", float('inf'))
        violation_key = f"interview_violations:{interview_id}:{violation_type.value}"

        current_count = int(await redis_client.get(violation_key) or 0)
        return current_count >= threshold

    async def _handle_threshold_exceeded(
        self,
        interview_id: str,
        user_id: str,
        violation_type: ViolationType,
        db
    ):
        """Handle when violation threshold is exceeded."""
        severity = self.violation_thresholds.get(violation_type, {}).get("severity", ViolationSeverity.LOW)

        actions = {
            ViolationSeverity.LOW: self._handle_low_severity,
            ViolationSeverity.MEDIUM: self._handle_medium_severity,
            ViolationSeverity.HIGH: self._handle_high_severity,
            ViolationSeverity.CRITICAL: self._handle_critical_severity
        }

        action_func = actions.get(severity, self._handle_low_severity)
        await action_func(interview_id, user_id, violation_type, db)

    async def _handle_low_severity(self, interview_id: str, user_id: str, violation_type: ViolationType, db):
        """Handle low severity violations - just log and flag for review."""
        await db.interviews.update_one(
            {"_id": interview_id},
            {"$set": {"flagged_for_review": True, "updated_at": datetime.utcnow()}}
        )

    async def _handle_medium_severity(self, interview_id: str, user_id: str, violation_type: ViolationType, db):
        """Handle medium severity violations - warn user and flag."""
        await db.interviews.update_one(
            {"_id": interview_id},
            {
                "$set": {
                    "flagged_for_review": True,
                    "status": "flagged",
                    "updated_at": datetime.utcnow()
                }
            }
        )

        # In a real implementation, send warning via WebSocket
        # await notify_user_warning(user_id, interview_id, violation_type)

    async def _handle_high_severity(self, interview_id: str, user_id: str, violation_type: ViolationType, db):
        """Handle high severity violations - pause interview."""
        await db.interviews.update_one(
            {"_id": interview_id},
            {
                "$set": {
                    "flagged_for_review": True,
                    "status": "suspended",
                    "suspended_reason": f"High severity violation: {violation_type.value}",
                    "updated_at": datetime.utcnow()
                }
            }
        )

        # Notify user and potentially terminate session
        # await notify_interview_suspended(user_id, interview_id, violation_type)

    async def _handle_critical_severity(self, interview_id: str, user_id: str, violation_type: ViolationType, db):
        """Handle critical severity violations - terminate interview."""
        await db.interviews.update_one(
            {"_id": interview_id},
            {
                "$set": {
                    "flagged_for_review": True,
                    "status": "terminated",
                    "terminated_reason": f"Critical violation: {violation_type.value}",
                    "completed_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )

        # Terminate session and notify user
        # await terminate_interview_session(user_id, interview_id, violation_type)

    async def get_violation_summary(self, interview_id: str) -> Dict[str, Any]:
        """Get violation summary for an interview."""
        db = await get_database()
        redis_client = await get_redis()

        # Get violations from database
        violations = await db.anti_cheat_events.find({"session_id": interview_id}).to_list(length=None)

        # Count by type and severity
        summary = {
            "total_violations": len(violations),
            "by_type": {},
            "by_severity": {},
            "critical_events": [],
            "flagged_for_review": False
        }

        for violation in violations:
            v_type = violation.get("event_type", "unknown")
            severity = violation.get("severity", "low")

            summary["by_type"][v_type] = summary["by_type"].get(v_type, 0) + 1
            summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1

            if severity == "critical":
                summary["critical_events"].append({
                    "type": v_type,
                    "description": violation.get("description", ""),
                    "timestamp": violation.get("timestamp")
                })

        # Check if interview is flagged
        interview = await db.interviews.find_one({"_id": interview_id})
        if interview:
            summary["flagged_for_review"] = interview.get("flagged_for_review", False)

        return summary

    async def validate_environment(self, environment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate candidate's environment before interview starts."""
        validation_result = {
            "valid": True,
            "checks": {},
            "warnings": [],
            "blockers": []
        }

        # Check camera permissions
        camera_access = environment_data.get("camera_access", False)
        validation_result["checks"]["camera_access"] = camera_access
        if not camera_access:
            validation_result["blockers"].append("Camera access is required for interview verification")

        # Check microphone permissions
        mic_access = environment_data.get("microphone_access", False)
        validation_result["checks"]["microphone_access"] = mic_access
        if not mic_access:
            validation_result["blockers"].append("Microphone access is required for audio responses")

        # Check single screen
        multiple_screens = environment_data.get("multiple_screens", False)
        validation_result["checks"]["single_screen"] = not multiple_screens
        if multiple_screens:
            validation_result["warnings"].append("Multiple screens detected - ensure only one screen is used")

        # Check fullscreen capability
        fullscreen_supported = environment_data.get("fullscreen_supported", True)
        validation_result["checks"]["fullscreen_supported"] = fullscreen_supported
        if not fullscreen_supported:
            validation_result["warnings"].append("Fullscreen mode not supported - interview integrity may be compromised")

        # Check browser compatibility
        browser_compatible = environment_data.get("browser_compatible", True)
        validation_result["checks"]["browser_compatible"] = browser_compatible
        if not browser_compatible:
            validation_result["blockers"].append("Browser not compatible with interview system")

        # Check network speed (mock check)
        network_speed = environment_data.get("network_speed", 10)  # Mbps
        validation_result["checks"]["network_speed"] = network_speed >= 1
        if network_speed < 1:
            validation_result["blockers"].append("Network connection too slow for real-time interview")

        # Overall validation
        validation_result["valid"] = len(validation_result["blockers"]) == 0

        return validation_result

    async def monitor_session_activity(
        self,
        interview_id: str,
        user_id: str,
        activity_data: Dict[str, Any]
    ):
        """Monitor ongoing session activity for suspicious behavior."""
        db = await get_database()

        # Check for suspicious patterns
        mouse_movements = activity_data.get("mouse_movements", [])
        if self._detect_suspicious_mouse_movement(mouse_movements):
            await self.log_violation(
                interview_id,
                user_id,
                ViolationType.SUSPICIOUS_ACTIVITY,
                "Suspicious mouse movement patterns detected",
                {"mouse_data": mouse_movements[:10]}  # Store first 10 points
            )

        # Check for face detection issues
        face_detected = activity_data.get("face_detected", True)
        if not face_detected:
            await self.log_violation(
                interview_id,
                user_id,
                ViolationType.FACE_NOT_DETECTED,
                "Face not detected in camera feed",
                {"timestamp": activity_data.get("timestamp")}
            )

        # Check for multiple faces
        face_count = activity_data.get("face_count", 1)
        if face_count > 1:
            await self.log_violation(
                interview_id,
                user_id,
                ViolationType.MULTIPLE_FACES,
                f"Multiple faces detected: {face_count}",
                {"face_count": face_count}
            )

    def _detect_suspicious_mouse_movement(self, movements: List[Dict[str, Any]]) -> bool:
        """Detect suspicious mouse movement patterns."""
        if len(movements) < 10:
            return False

        # Check for robotic/automated movement patterns
        # This is a simplified check - real implementation would use ML
        velocities = []
        for i in range(1, len(movements)):
            prev = movements[i-1]
            curr = movements[i]
            time_diff = curr.get("timestamp", 0) - prev.get("timestamp", 0)
            if time_diff > 0:
                distance = ((curr.get("x", 0) - prev.get("x", 0)) ** 2 +
                           (curr.get("y", 0) - prev.get("y", 0)) ** 2) ** 0.5
                velocity = distance / time_diff
                velocities.append(velocity)

        if velocities:
            avg_velocity = sum(velocities) / len(velocities)
            # Flag if movement is too consistent (potentially automated)
            velocity_variance = sum((v - avg_velocity) ** 2 for v in velocities) / len(velocities)
            return velocity_variance < 100  # Low variance indicates robotic movement

        return False

# Global anti-cheat monitor instance
anti_cheat_monitor = AntiCheatMonitor()
