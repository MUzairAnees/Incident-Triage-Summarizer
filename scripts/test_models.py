# This is to test if the database models are running correctly

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from datetime import datetime, timedelta, timezone
from src.database.config import SessionLocal, init_database
from src.models.database_models import LogBatch, Incident, AnalysisMetric
import hashlib

def test_models():

    print("Testing Models")
    print("="*50)

    #initialize the database models -> create the tables
    print("1. Creating tables...")
    init_database()

    #create a session to work with the tables
    session = SessionLocal()

    try:
        #testing the logbatch model with fields
        print("\n2. Testing LogBatch model...")

        #creating the file hash
        file_content = "test content"
        file_hash = hashlib.sha256(file_content.encode()).hexdigest()

        batch = LogBatch(
            file_name="test_logbatch.log",
            file_size_in_bytes=1024576,
            file_hash=file_hash,

            processing_started_at=datetime.now(timezone.utc),

            log_count=1000,
            log_type="nginx",
            time_range_start=datetime.now(timezone.utc) - timedelta(hours=1),
            time_range_end=datetime.now(timezone.utc),
            status="processing"
        )
        session.add(batch)
        session.commit()
        print(f"Created LogBatch: {batch}")

        #testing property
        batch.processing_finished_at = datetime.now(timezone.utc)
        session.commit()
        print(f"Total Processing Time: {batch.processing_time_ms}ms")

        #testing the incident model with fields
        print("\n3. Testing Incident model...")
        incident = Incident(
            log_batch_id=batch.id,

            incident_type="http_error_spike",
            severity="high",

            title="500 error spikes detected",
            description="Massive spike in errors",
            occurrence_count=150,

            first_occurrence=datetime.now(timezone.utc) - timedelta(minutes=30),
            last_occurrence=datetime.now(timezone.utc),
            duration_in_min=30.0,

            ai_explanation="Server overload detected",
            ai_recommendations=["Scale up","Check logs","Review deployments"]
        )
        session.add(incident)
        session.commit()
        print(f"Created Incident: {incident}")

        #testing to_dict method
        incident_dict = incident.info_dict_format_to_json()
        print(f"Incident Info as keys: {incident_dict}")

        print("\n4. Testing AnalysisMetric model...")
        metrics = AnalysisMetric(
            log_batch_id=batch.id,

            total_requests=10000,
            successful_2xx=9500,
            redirects_3xx=200,
            client_errors_4xx=200,
            server_errors_5xx=100,

            avg_response_time_ms=145.5,

            peak_hour=14,
            peak_requests_per_minute=500
        )
        metrics.calculate_rates()
        session.add(metrics)
        session.commit()
        print(f"Created AnalysisMetric: {metrics}")
        print(f"Error rate: {metrics.error_rate:.2%}")
        print(f"Success rate: {metrics.success_rate:.2%}")

        #Test relationships
        print("\n5. Testing relationships...")
        print(f"Batch has {len(batch.incidents)} incident(s)")
        print(f"Batch has metric: {batch.metric is not None}")
        print(f"Incident belongs to batch: {incident.log_batch.id}")

        #testing validation
        print("\n6. Testing validation...")
        try:
            batch.status = "invalid_status"
        except ValueError as e:
            print(f"Status validation works: {e}")

        print("All model tests passed!")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()

    finally:
        #cleaning up
        session.query(AnalysisMetric).delete()
        session.query(LogBatch).delete()
        session.query(Incident).delete()
        session.commit()
        session.close()
        print("Test data cleaned up")

if __name__ == "__main__":
    test_models()