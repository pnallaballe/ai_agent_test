"""
Audit Manager - Tracks all activities and detects fraud
Maintains complete audit trail for compliance and quality control
"""

import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import uuid

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuditManager:
    """
    Manages audit trails and fraud detection.
    
    Responsibilities:
    - Log every upload and grading activity
    - Detect suspicious patterns
    - Track farmer/batch history
    - Generate audit reports
    """
    
    def __init__(self, audit_log_path: str):
        """
        Initialize Audit Manager
        
        Args:
            audit_log_path: Path to store audit logs
        """
        self.audit_log_path = Path(audit_log_path)
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        self.fraud_flags = []
        
    def log_upload(self, 
                   farmer_id: str,
                   batch_number: str,
                   file_name: str,
                   file_hash: str,
                   file_size: int,
                   upload_timestamp: datetime,
                   location: Optional[Dict] = None,
                   device_info: Optional[Dict] = None) -> str:
        """
        Log a file upload event
        
        Args:
            farmer_id: Unique farmer identifier
            batch_number: Batch identifier
            file_name: Name of uploaded file
            file_hash: Hash of file (SHA256) for duplicate detection
            file_size: Size in bytes
            upload_timestamp: When file was uploaded
            location: GPS location if available
            device_info: Device/browser information
            
        Returns:
            upload_id: Unique identifier for this upload
        """
        upload_id = str(uuid.uuid4())
        
        audit_entry = {
            'timestamp': upload_timestamp.isoformat(),
            'event_type': 'UPLOAD',
            'upload_id': upload_id,
            'farmer_id': farmer_id,
            'batch_number': batch_number,
            'file_name': file_name,
            'file_hash': file_hash,
            'file_size': file_size,
            'location': location,
            'device_info': device_info,
            'status': 'SUCCESS'
        }
        
        self._write_audit_log(audit_entry)
        logger.info(f"Upload logged - Farmer: {farmer_id}, Batch: {batch_number}")
        
        return upload_id
    
    def log_grading(self,
                    upload_id: str,
                    farmer_id: str,
                    batch_number: str,
                    grade: str,
                    confidence: float,
                    detected_issues: List[str],
                    grading_timestamp: datetime) -> None:
        """
        Log a grading result
        
        Args:
            upload_id: References the upload
            farmer_id: Farmer ID
            batch_number: Batch identifier
            grade: Grade assigned (A/B/C/Reject)
            confidence: Confidence score (0-1)
            detected_issues: List of detected problems
            grading_timestamp: When grading was done
        """
        audit_entry = {
            'timestamp': grading_timestamp.isoformat(),
            'event_type': 'GRADING',
            'upload_id': upload_id,
            'farmer_id': farmer_id,
            'batch_number': batch_number,
            'grade': grade,
            'confidence': confidence,
            'detected_issues': detected_issues,
            'status': 'SUCCESS'
        }
        
        self._write_audit_log(audit_entry)
        logger.info(f"Grade logged - Farmer: {farmer_id}, Grade: {grade}, "
                   f"Confidence: {confidence:.2f}")
    
    def detect_duplicate_images(self,
                               farmer_id: str,
                               file_hash: str,
                               threshold: float = 0.95) -> Tuple[bool, Optional[str]]:
        """
        Detect if image might be duplicate/reused
        
        Args:
            farmer_id: Farmer uploading the image
            file_hash: SHA256 hash of image
            threshold: Similarity threshold (0-1)
            
        Returns:
            Tuple of (is_duplicate, previous_upload_id)
        """
        logs = self._read_recent_logs(farmer_id, days=30)
        
        for log in logs:
            if log.get('event_type') == 'UPLOAD':
                # Simple hash matching - exact duplicate
                if log.get('file_hash') == file_hash:
                    logger.warning(f"FRAUD ALERT: Duplicate image detected for {farmer_id}")
                    self.fraud_flags.append({
                        'type': 'DUPLICATE_IMAGE',
                        'farmer_id': farmer_id,
                        'severity': 'HIGH',
                        'timestamp': datetime.now().isoformat()
                    })
                    return True, log.get('upload_id')
        
        return False, None
    
    def detect_statistical_anomalies(self,
                                     farmer_id: str,
                                     recent_grades: List[Dict]) -> List[Dict]:
        """
        Detect suspicious grading patterns
        
        Args:
            farmer_id: Farmer to analyze
            recent_grades: List of recent grading results
            
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        if not recent_grades:
            return anomalies
        
        # Check 1: Too many perfect grades
        grade_a_count = sum(1 for g in recent_grades if g['grade'] == 'Grade A')
        grade_a_percentage = (grade_a_count / len(recent_grades)) * 100
        
        if grade_a_percentage > 85:  # More than 85% Grade A = suspicious
            anomalies.append({
                'type': 'SUSPICIOUS_PERFECT_GRADES',
                'severity': 'MEDIUM',
                'details': f"{grade_a_percentage:.1f}% Grade A (expected ~60%)",
                'farmer_id': farmer_id,
                'timestamp': datetime.now().isoformat()
            })
            logger.warning(f"FRAUD ALERT: {farmer_id} has {grade_a_percentage:.1f}% Grade A")
        
        # Check 2: Low variance in quality scores
        confidence_scores = [g['confidence'] for g in recent_grades]
        variance = max(confidence_scores) - min(confidence_scores)
        
        if variance < 0.05:  # Very little variation = suspicious
            anomalies.append({
                'type': 'LOW_QUALITY_VARIANCE',
                'severity': 'MEDIUM',
                'details': f"Confidence variance only {variance:.3f} (suspicious consistency)",
                'farmer_id': farmer_id,
                'timestamp': datetime.now().isoformat()
            })
            logger.warning(f"FRAUD ALERT: {farmer_id} has suspiciously consistent scores")
        
        # Check 3: Consecutive perfect batches
        consecutive_a = 0
        for grade in recent_grades:
            if grade['grade'] == 'Grade A':
                consecutive_a += 1
            else:
                consecutive_a = 0
            
            if consecutive_a >= 10:
                anomalies.append({
                    'type': 'CONSECUTIVE_PERFECT_BATCHES',
                    'severity': 'HIGH',
                    'details': f"{consecutive_a} consecutive Grade A batches",
                    'farmer_id': farmer_id,
                    'timestamp': datetime.now().isoformat()
                })
                logger.error(f"FRAUD ALERT: {farmer_id} has {consecutive_a} perfect batches")
                break
        
        return anomalies
    
    def detect_upload_speed_anomaly(self,
                                    farmer_id: str,
                                    batch_number: str,
                                    num_images: int,
                                    total_upload_time_seconds: int,
                                    min_time_per_image: int = 10) -> Optional[Dict]:
        """
        Detect if farmer uploaded too many images too quickly
        Suggests they might be duplicate/copy-paste
        
        Args:
            farmer_id: Farmer ID
            batch_number: Batch number
            num_images: Number of images uploaded
            total_upload_time_seconds: Total time taken (seconds)
            min_time_per_image: Minimum expected seconds per image
            
        Returns:
            Anomaly object if detected, None otherwise
        """
        time_per_image = total_upload_time_seconds / num_images
        
        if time_per_image < min_time_per_image:
            anomaly = {
                'type': 'SUSPICIOUSLY_FAST_UPLOAD',
                'severity': 'MEDIUM',
                'details': f"Only {time_per_image:.1f}s per image (expected min {min_time_per_image}s)",
                'farmer_id': farmer_id,
                'batch_number': batch_number,
                'timestamp': datetime.now().isoformat()
            }
            self.fraud_flags.append(anomaly)
            logger.warning(f"FRAUD ALERT: {farmer_id} uploaded {num_images} images in "
                          f"{total_upload_time_seconds}s")
            return anomaly
        
        return None
    
    def detect_location_anomaly(self,
                               farmer_id: str,
                               current_location: Dict,
                               registered_location: Dict,
                               max_distance_km: float = 50) -> Optional[Dict]:
        """
        Detect if upload location is too far from registered farm
        
        Args:
            farmer_id: Farmer ID
            current_location: Current GPS coordinates {'lat': float, 'lon': float}
            registered_location: Registered farm location
            max_distance_km: Maximum allowed distance
            
        Returns:
            Anomaly if detected, None otherwise
        """
        if not current_location or not registered_location:
            return None
        
        distance = self._calculate_distance(
            current_location['lat'], current_location['lon'],
            registered_location['lat'], registered_location['lon']
        )
        
        if distance > max_distance_km:
            anomaly = {
                'type': 'LOCATION_ANOMALY',
                'severity': 'HIGH',
                'details': f"Upload from {distance:.1f}km away (max {max_distance_km}km)",
                'farmer_id': farmer_id,
                'timestamp': datetime.now().isoformat()
            }
            self.fraud_flags.append(anomaly)
            logger.error(f"FRAUD ALERT: {farmer_id} uploaded from {distance:.1f}km away")
            return anomaly
        
        return None
    
    def check_batch_minimum_requirements(self,
                                         farmer_id: str,
                                         batch_number: str,
                                         num_images: int,
                                         num_angles: int,
                                         min_images: int = 20,
                                         min_angles: int = 3) -> List[str]:
        """
        Verify batch meets minimum requirements
        
        Args:
            farmer_id: Farmer ID
            batch_number: Batch number
            num_images: Total images uploaded
            num_angles: Number of different angles
            min_images: Minimum required images
            min_angles: Minimum required angles
            
        Returns:
            List of violations (empty if all good)
        """
        violations = []
        
        if num_images < min_images:
            violations.append(
                f"Only {num_images} images uploaded (minimum {min_images} required)"
            )
            logger.warning(f"Batch {batch_number} (Farmer {farmer_id}) "
                          f"has insufficient images: {num_images}")
        
        if num_angles < min_angles:
            violations.append(
                f"Only {num_angles} angles (minimum {min_angles} required)"
            )
            logger.warning(f"Batch {batch_number} (Farmer {farmer_id}) "
                          f"has insufficient angles: {num_angles}")
        
        return violations
    
    def get_farmer_fraud_score(self, farmer_id: str, days: int = 30) -> float:
        """
        Calculate fraud risk score for a farmer (0-1)
        Higher = more suspicious
        
        Args:
            farmer_id: Farmer ID
            days: Period to analyze
            
        Returns:
            Fraud score (0-1)
        """
        logs = self._read_recent_logs(farmer_id, days=days)
        
        if not logs:
            return 0.0
        
        score = 0.0
        anomaly_count = sum(1 for flag in self.fraud_flags 
                           if flag.get('farmer_id') == farmer_id)
        
        # Each anomaly adds to score
        score += min(anomaly_count * 0.1, 0.5)  # Max 0.5 from anomalies
        
        # Grading logs
        grading_logs = [l for l in logs if l.get('event_type') == 'GRADING']
        if grading_logs:
            grade_a_count = sum(1 for l in grading_logs if l.get('grade') == 'Grade A')
            if len(grading_logs) > 0:
                grade_a_pct = grade_a_count / len(grading_logs)
                if grade_a_pct > 0.85:
                    score += 0.3
        
        return min(score, 1.0)
    
    def generate_audit_report(self, farmer_id: str, days: int = 30) -> Dict:
        """
        Generate audit report for a farmer
        
        Args:
            farmer_id: Farmer ID
            days: Period to analyze
            
        Returns:
            Audit report dictionary
        """
        logs = self._read_recent_logs(farmer_id, days=days)
        
        upload_logs = [l for l in logs if l.get('event_type') == 'UPLOAD']
        grading_logs = [l for l in logs if l.get('event_type') == 'GRADING']
        
        fraud_score = self.get_farmer_fraud_score(farmer_id, days=days)
        
        report = {
            'farmer_id': farmer_id,
            'period_days': days,
            'total_uploads': len(upload_logs),
            'total_grades': len(grading_logs),
            'fraud_score': fraud_score,
            'fraud_level': self._get_fraud_level(fraud_score),
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'grade_a': sum(1 for l in grading_logs if l.get('grade') == 'Grade A'),
                'grade_b': sum(1 for l in grading_logs if l.get('grade') == 'Grade B'),
                'grade_c': sum(1 for l in grading_logs if l.get('grade') == 'Grade C'),
                'rejected': sum(1 for l in grading_logs if l.get('grade') == 'Reject'),
            },
            'anomalies': [f for f in self.fraud_flags 
                         if f.get('farmer_id') == farmer_id]
        }
        
        return report
    
    # ========================================================================
    # Private Helper Methods
    # ========================================================================
    
    def _write_audit_log(self, entry: Dict) -> None:
        """Write audit entry to log file"""
        try:
            with open(self.audit_log_path, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
    
    def _read_recent_logs(self, farmer_id: str, days: int = 30) -> List[Dict]:
        """Read recent logs for a farmer"""
        logs = []
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            if self.audit_log_path.exists():
                with open(self.audit_log_path, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            if entry.get('farmer_id') == farmer_id:
                                entry_date = datetime.fromisoformat(entry['timestamp'])
                                if entry_date > cutoff_date:
                                    logs.append(entry)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"Failed to read audit logs: {e}")
        
        return logs
    
    @staticmethod
    def _calculate_distance(lat1: float, lon1: float, 
                           lat2: float, lon2: float) -> float:
        """
        Calculate distance between two GPS coordinates (Haversine formula)
        Returns distance in kilometers
        """
        from math import radians, cos, sin, asin, sqrt
        
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        km = 6371 * c
        return km
    
    @staticmethod
    def _get_fraud_level(score: float) -> str:
        """Convert fraud score to risk level"""
        if score < 0.2:
            return 'LOW'
        elif score < 0.5:
            return 'MEDIUM'
        elif score < 0.8:
            return 'HIGH'
        else:
            return 'CRITICAL'


def calculate_file_hash(file_path: str) -> str:
    """
    Calculate SHA256 hash of a file
    
    Args:
        file_path: Path to file
        
    Returns:
        Hex hash string
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
