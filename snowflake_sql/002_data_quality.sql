USE DATABASE RETAILPULSE;
USE SCHEMA AUDIT;

CREATE TABLE IF NOT EXISTS AUDIT.DATA_QUALITY_RESULTS (
    run_id           VARCHAR,
    executed_at      TIMESTAMP_NTZ,
    total_tests      NUMBER,
    passed_tests     NUMBER,
    failed_tests     NUMBER,
    warned_tests     NUMBER,
    pass_rate_pct    NUMBER(5, 2),
    status           VARCHAR     -- 'PASS' / 'FAIL'
);