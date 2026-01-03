"""
Database Models are the DB table models that we're going to build for our service.
We build them as classes using Base() that we initialized in our database config file.
A reminder as to how these classes would work:
- Each Class = A table in the database
- Each Class Attribute = A column(field) in that table
- Each Instance of a Class = One row in that table

Example:
    if LogBatch is a class (table)
    Then LogBatch.file_name is an attribute (column)
    And LogBatch (file_name="access.log") creates an instance (row)

Our models for the app:
1) LogBatch - Records each batch of logs uploaded
2) Incident - Problems found in the logs
3) AnalysisMetric - Statistics from the analysis
"""

from datetime import datetime, timezone                 # datetime to keep track of date of logs/metrics
from typing import Optional, List, Dict, Any    # allows for your ORM objects to show what type of input/output for each field and whatnot (NOT ENFORCED)

from sqlalchemy import (
    Column,                     # defines the columns of a table
    Integer,
    String,                     # for text but with limits
    DateTime,                   # for timestamps
    Text,                       # for text but without limits
    JSON,                       # JSON data has a flexible structure -- helpful in logs
    Float,
    Boolean,
    ForeignKey,                 # links to another table as a relationship
    Index,                      # makes queries faster on specific columns
    text
)
from sqlalchemy.orm import relationship, validates

from src.database.config import Base        # remember Base is used to help SQLAlchemy make your ORM python model
                                            # classes(written below) come to life as tables. When inherited from
                                            # Base, SQLAlchemy treats your classes as database tables. Base also
                                            # gives the classes ORM abilities(insert, update, delete, query)
                                            # without Base, the classes stay classes and do not get treated as
                                            # database tables


'''
LOG BATCH TABLE
Represents a group of logs that were uploaded for analysis
- Keeps a record of each log FILE (the file could contain 1 log or multiple logs)
- It keeps track of multiple aspects of the file: when it was uploaded("uploaded_at"),
the file size, when the processing of the file started("processing_started_at"), etc.
- So one file is one LogBatch record
'''

class LogBatch(Base):
    __tablename__ = 'log_batches'

    # primary key(ssn for each log file; helps establish a relationship other tables),
    # autoincrement=true starts counting from 1->n automatically
    id = Column(Integer, primary_key=True, autoincrement=True)


    # ============================================
    # ==============FILE INFORMATION==============
    # Log name/size/hash_id

    file_name = Column(String(255), nullable=False)                 # name limit is 255 char and THERE HAS TO BE A NAME

    file_size_in_bytes = Column(Integer, nullable=False)            # example: 1029343

    file_hash = Column(String(64), nullable=False, unique=True)     # hash number so we can check if the file was detected before


    # ============================================
    # ============TIMING INFORMATION==============
    # When logs were uploaded/processed

    uploaded_at = Column(DateTime(timezone=True),
                         default=lambda: datetime.now(timezone.utc),    # lambda because now the function is stored and called everytime a row is inputted
                         server_default=text("CURRENT_TIMESTAMP"),      # safety net if server-side misses adding the datetime for any reason
                         nullable=False)

    processing_started_at = Column(DateTime(timezone=True), nullable=True)     # when the service starts to analyze logs (time is set when we calculate that in the logic)

    processing_finished_at = Column(DateTime(timezone=True), nullable=True)    # when the service finishes analyzing logs (time is set when we calculate that in the logic)

    #processing_time_ms = Column(Float, nullable=True)           # difference in the start and time in milliseconds but commented since it can be derived anyway(info already stored in other 2 columns just need to do math instead)


    # ============================================
    # ================LOG DETAILS=================
    # specifics about the uploaded log file

    log_count = Column(Integer, default=0)              # checking how many individual log lines are in the log file, if none->default to 0 for no issues

    log_type = Column(String(50), nullable=False)       # logs can be of different types (our own application logs, could AWS cloudwatch logs, etc.)

    time_range_start = Column(DateTime, nullable=True)  # helps with filtering through logs- no need to rescan potentially massive logs

    time_range_end = Column(DateTime, nullable=True)    # helps with filtering through logs- no need to rescan potentially massive logs


    # ============================================
    # =======PROCESSING STATUS/STATUS INFO========
    # Basically meant to give insight as to how the log processing is going

    status = Column(String(50),                     # status between "pending", "processing", "completed", "failed", " cancelled"
                    nullable=False,
                    default='pending'
                    )

    error_message = Column(Text, nullable=True)     # example: "Failed to parse log format: unrecognized timestamp"


    # ============================================
    # ==============STORAGE LOCATION==============
    # Where we keep the actual log data (For GCP it was GoogleCloudStorage(GCS Bucket), for AWS it's going to be S3)

    raw_logs_sample = Column(Text, nullable=True)   # for preview purposes: "2024-01-15 10:00:00 GET /api/users 200 45ms\n2024-01-15 10:00:01..."

    s3_bucket = Column(String(100), nullable=True)  # when we start using the AWS S3 bucket, which bucket: "my-company-logs-bucket"

    s3_key = Column(String(500), nullable=True)     # the path to the file in s3: "uploads/2024/01/15/batch_123_access.log"


    # ============================================
    # ============AI ANALYSIS DETAILS=============
    # Tracking AI usage for cost management

    ai_model_used = Column(String(50), nullable=True)   # OpenAI offers many different models for different costs

    ai_tokens_used = Column(Integer, nullable=True)     # ex: 1token is 4characters, cost differs based on tokens offered-> 0.002$/1k tokens

    ai_cost_usd = Column(Float, nullable=True)         # Essentially displays the cost of AI analysis for each log batch record (meaning a single log file)


    # ============================================
    # ================PROPERTIES==================
    '''
    We are currently making processing_time_ms as a property since this can be easily derived
    We can call this whenever we want from other files
    REFER TO TIME_PROCESSING CODE BLOCK ABOVE
    '''
    @property
    def processing_time_ms(self):
        if self.processing_started_at and self.processing_finished_at:
            delta = self.processing_finished_at - self.processing_started_at
            return int(delta.total_seconds() * 1000)
        return None


    # ============================================
    # ==============RELATIONSHIPS=================
    '''
    Essentially we are coding a Pythonic relationship attribute
    that ties to another relationship attribute from another table.
    When we mention Table1/Table2, we are referring to their Class names
    - relationship_attribute_name_of_Table1_relating_to_table2 = relationship("Table2,      # = relationship("Table2" means that we're forming a relationship with Table2
            back_populates = relationship_attribute_name_of_Table2_relating_to_Table1,      # back_populates lets SQLAlchemy know that it has to sync the 2 tables with any changes
            cascade = "all, delete-orphan                                                   # if a record is deleted in the parent table/class(Table1), delete all related records in orphan table/class(Table2)
            uselist = True/False)                                                           # uselist = False for 1-to-1 relationship(one record of table1->one record of table2), True for 1-to-many relationship(one record of table1->many records of table2)
    This is a general format for relationships
    '''
    incidents = relationship("Incident",
                             back_populates="log_batch",
                             cascade="all, delete-orphan")

    metric = relationship("AnalysisMetric",
                           back_populates="log_batch",
                           cascade="all, delete-orphan",
                           uselist=False)


    # ============================================
    # ==========INDEXES FOR PERFORMANCE===========
    '''
    Indexing is a way for the database to return specific information without scanning the entire table.
    Without indexes, the database needs to look through every record for whatever you query for.
    When you add a index, the database builds a "sorted look up structure" that stores the POINTERS to the specific rows
    for quick results.
    
    You will see in the syntax that there is a name before the field name you want to idx. That name is 
    for the database and for devs to debug and whatnot. You don't use that explicitly to query results.
    - __table_args__ = (
        Index('idx_<table_name>_<column_name1>', '<column_name1>',),
        Index('idx_<table_name>_<column_name2>', '<column_name2>',),
    '''
    __table_args__ = (
        Index('idx_log_batches_uploaded_at', 'uploaded_at',),      # important as to when the errors occurred so quick search is important
        Index('idx_log_batches_status', 'status',),                # obviously you want to search quickly based on what status the file is in
    )


    # ============================================
    # ===========REPRESENTATION METHOD============
    '''
    So "repr" means representation. In this case, we are making a representation of how a Log_Batch object will be shown
    __repr__ is a special python method that allows the above. Be mindful that this applies universally with python.
    You NEED to define a way to display objects in Python.
    If we didn't use this and we printed/displayed a LogBatch object it would look like: <LogBatch object at 0x7ff9c3a1b5e0>
    With this it would look like how we represent it below: <LogBatch(id=3, status=completed)>
    '''
    def __repr__(self):
        return f"<LogBatch(id={self.id}, file={self.file_name}, status={self.status})>"


    # ============================================
    # ==========VALIDATE STATUS METHOD============
    '''
    A special decorater created by the SQLAlchemy author that "listens" to an attribute assignment on ORM models
    So here we have @validates('status') listening to whenever 'status'(the column/field) is set and when the status column is set
    internally SQLAlchemy is thinking:
    "Ok so for the current object(self), AND for the 'status'(key) column, some value(the actual status aka 'status_val') is being set..
    so lets call the validates_status function which takes the self arg, the key(column) arg, and the status_val(actual value) arg
    and check if its a valid status"
    '''
    @validates('status')
    def validate_status(self, key, status_val):
        allowed = ["pending", "processing", "completed", "failed", "cancelled"]
        if status_val not in allowed:
            raise ValueError(f"Invalid status: {status_val}, Must be one of: {allowed}")
        return status_val


'''
INCIDENT TABLE
This is a table that has information on all the incidents filed in the logs
A real world example:
- Database Response time exceeding 5 seconds
- 500 errors increase by 500% in the last 5 minutes
However each incident belongs to one Log_Batch
'''
class Incident(Base):
    __tablename__ = 'incidents'

    # ============================================
    # ====================KEYS====================
    id = Column(Integer, primary_key=True, autoincrement=True)  # this class/tables identification number for each row/record

    log_batch_id = Column(Integer,
                          ForeignKey('log_batches.id',      # points to the Log_Batch class ex. id-1 -> log_batch_id-1, id-2 -> log_batch_id-1, id-3 -> log_batch_id-2
                                     ondelete="CASCADE"),           # if the log_batch_id is deleted, delete all related id records/rows as well
                          nullable=False)


    # ============================================
    # ==========INCIDENT CLASSIFICATION===========
    incident_type = Column(String(50), nullable=False)          # ex. memory_leak, slow_database, http_error_spike, security_threat

    severity = Column(String(20), nullable=False)

    confidence_score = Column(Float, nullable=True)             # we will keep this between 0.0 to 1.0 (0%-100%)


    # ============================================
    # =============INCIDENT DETAILS===============
    title = Column(String(200), nullable=False)                 # human-understandable title

    description = Column(Text, nullable=True)                   # more detailed description

    pattern_details = Column(Text, nullable=True)               # ex. 503 errors, 15/min to 150/min (900% increase)

    occurrence_count = Column(Integer, default=1)               # wouldn't be 0 since any incident means 1 or more


    # ============================================
    # ===================TIMING===================
    first_occurrence = Column(DateTime, nullable=True)          # when problem first started or first occurrence in the logs

    last_occurrence = Column(DateTime, nullable=True)

    duration_in_min = Column(Float, nullable=True)              # ex. 20.5 -> 20 and half minutes -> 20 minutes and 30 sec

    detected_at = Column(DateTime(timezone=True),                       # reason for including is that there could've been another log that allowed  us to detect/solidify the issue rather the first occurrence
                         default=lambda: datetime.now(timezone.utc),    # also we are making it so that it catches at UTC timing as a general wya
                         server_default=text("CURRENT_TIMESTAMP"),
                         nullable=False)


    # ============================================
    # ===========AI GENERATED CONTENT=============
    ai_explanation = Column(Text, nullable=True)

    ai_recommendations = Column(JSON,                        # JSON used because it is a flexible structure that can store lists, dicts, etc.
                               nullable=True)               # Example: ["Check server health", "Scale up instances", "Review recent deployments"]

    ai_root_cause = Column(Text, nullable=True)             # Human understandable root cause


    # ============================================
    # ============AFFECTED COMPONENTS=============
    affected_endpoints = Column(JSON, nullable=True)        # Example: ["/api/users", "/api/orders", "/api/payments"]

    number_of_affected_users = Column(Integer, nullable=True)

    error_codes = Column(JSON, nullable=True)               # Example: [500, 502, 503, 504]

    sample_log_lines = Column(JSON, nullable=True)          # Example: ["2024-01-15 14:25:01 ERROR 500...", "2024-01-15 14:25:02 ERROR 500..."]


    # ============================================
    # ==============RELATIONSHIPS=================

    log_batch = relationship("LogBatch",
                             back_populates="incidents")


    # ============================================
    # ==================INDEXES===================

    __table_args__ = (
        Index('idx_incidents_severity', 'severity'),
        Index('idx_incidents_incident_type', 'incident_type'),
        Index('idx_incidents_log_batch_id', 'log_batch_id'),
    )


    # ============================================
    # ==============REPRESENTATION================
    def __repr__(self):
        return f"<Incident(id={self.id}, type={self.incident_type}, severity={self.severity})>"

    def info_dict_format_to_json(self) -> Dict[str, Any]:       # purpose is to put the information in dict format since this is how JSON data is represented
        return {
            'id': self.id,
            'log_batch_id': self.log_batch_id,
            'incident_type': self.incident_type,
            'severity': self.severity,
            'description': self.description,
            'occurrence_count': self.occurrence_count,
            'ai_explanation': self.ai_explanation,
            'ai_recommendations': self.ai_recommendations,
        }


    # ============================================
    # ================VALIDATION==================
    @validates('severity')
    def validate_severity(self, key, severity):
        allowed = ["low", "medium", "high", "critical"]
        if severity not in allowed:
            raise ValueError(f"Invalid severity: {severity}, Must be one of: {allowed}")
        return severity

    #@validates('incident_type') if ever needed to validate this in the future


'''
ANALYSIS METRIC TABLE
This table is supposed to store the aggregated(sum/diff) stats from each of the log files
This is different from the incidents table:
    - incidents = specific problems in a record each
    - metrics = overall stats and measurements of each log file -> one to one relation
Example metrics:
- Total Requests
- Error rate (as a float, of the entire log file)
- Average response time
- Peak traffic hour
'''
class AnalysisMetric(Base):
    __tablename__ = 'analysis_metrics'

    id = Column(Integer, primary_key=True, autoincrement=True)

    log_batch_id = Column(Integer,
                          ForeignKey('log_batches.id', ondelete="CASCADE"),
                          nullable=False,
                          unique=True)      # maintains a one to one relation (One log batch -> one analysis metric)


    # ============================================
    # ===============HTTP METRICS=================
    total_requests = Column(Integer, default=0)

    successful_2xx = Column(Integer, default=0)

    redirects_3xx = Column(Integer, default=0)

    client_errors_4xx = Column(Integer, default=0)

    server_errors_5xx = Column(Integer, default=0)


    # ============================================
    # ============PERFORMANCE METRICS=============
    '''
    Keep in mind that it doesn't matter if only 1 user is getting high latency
    1 user is still YOUR user and they shouldn't be having a bad experience
    
    so in this case:
    pNumber gives you the scope or insight into HOW MANY are experiencing the giving ms latency
    the ms value gives you an understanding of if we're experiencing heavy latency for 1 or a small group or a huge group
    
    low ms for all pNumbers is ideal
    '''
    avg_response_time_ms = Column(Float, nullable=True)

    p50_response_time_ms = Column(Float, nullable=True)

    p95_response_time_ms = Column(Float, nullable=True)

    p99_response_time_ms = Column(Float, nullable=True)

    max_response_time_ms = Column(Float, nullable=True)


    # ============================================
    # =============DATABASE METRICS===============
    total_db_queries = Column(Integer, default=0)

    slow_queries = Column(Integer, default=0)

    db_errors = Column(Integer, default=0)


    # ============================================
    # ============CALCULATED_RATES================
    error_rate = Column(Float, nullable=True)       # calculated as ((4xx + 5xx) / total_requests)

    success_rate = Column(Float, nullable=True)     # counting all successful requests - logic later


    # ============================================
    # =================TOP LISTS==================
    '''
    All represented as a JSON for more than one bit of information
    Ex:
    Example: [
      {"path": "/api/users", "count": 50000, "avg_time": 120},
      {"path": "/api/products", "count": 30000, "avg_time": 200}
    ]
    Example: [
      {"code": 404, "count": 1000, "message": "Not Found"},
      {"code": 500, "count": 500, "message": "Internal Server Error"}
    ]
    Example: [
      {"agent": "Chrome/120.0", "count": 400000},
      {"agent": "Firefox/121.0", "count": 300000}
    ]
    '''
    top_endpoints = Column(JSON, nullable=True)     # Most frequently accessed endpoints

    top_errors = Column(JSON, nullable=True)        # Most common errors

    top_user_agents = Column(JSON, nullable=True)   # Most common browser/clients


    # =============================================
    # ==============TIME PATTERNS==================
    peak_hour = Column(Integer, nullable=True)      # 0-23, Ex. "14" meaning 2pm is peak hour

    peak_requests_per_minute = Column(Integer, nullable=True)


    # =============================================
    # ==================METADATA===================
    created_at = Column(DateTime(timezone=True),                                   # when these metrics were calculated
                        default=lambda: datetime.now(timezone.utc),
                        server_default=text("CURRENT_TIMESTAMP"))


    # =============================================
    # ================RELATIONSHIP=================
    log_batch = relationship("LogBatch", back_populates="metric")


    # =============================================
    # ==================INDEXES====================
    __table_args__ = (
        Index('idx_analysis_metrics_log_batch_id', 'log_batch_id'),
    )


    # =============================================
    # ================REPRESENTATION===============
    def __repr__(self):
        return f"<AnalysisMetric(id={self.id}, log_batch_id={self.log_batch_id}, total_requests={self.total_requests})>"

    # different from property because the arithmetic below stores information in the database
    def calculate_rates(self):
        total = int(self.total_requests or 0)
        if total > 0:
            errors = (int(self.client_errors_4xx or 0) + int(self.server_errors_5xx or 0))
            self.error_rate = round(errors / self.total_requests, 4)
            self.success_rate = round(int(self.successful_2xx or 0) / float(total), 4)
        else:
            self.error_rate = 0.0
            self.success_rate = 0.0
