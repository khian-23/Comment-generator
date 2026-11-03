"""Predefined comment templates for the desktop application."""

TEMPLATES = [
    {
        "id": "job-skip-details-logs",
        "name": "Job skip with detailed information and concurrent logs",
        "comment": "Job skip was performed with detailed information and concurrent logs:\n\nDetailed Information: {detailedInformation}\nConcurrent Logs: {concurrentLogs}\nOperator: {operator}\nAlert ID: {alertId}",
        "fields": [
            {"id": "detailedInformation", "label": "Detailed Information", "multiline": True},
            {"id": "concurrentLogs", "label": "Concurrent Logs", "multiline": True},
            {"id": "operator", "label": "Operator"},
            {"id": "alertId", "label": "Alert ID"},
        ],
    },
    {
        "id": "job-skip-no-details-logs",
        "name": "Job skip without detailed information and concurrent logs",
        "comment": "Job skip without detailed information and concurrent logs\n\nOperator: {operator}\nAlert ID: {alertId}",
        "fields": [
            {"id": "operator", "label": "Operator"},
            {"id": "alertId", "label": "Alert ID"},
        ],
    },
    {
        "id": "job-skip-long-logs",
        "name": "Job skip with detailed information but concurrent logs is too long",
        "comment": "Job skip was performed with detailed information but concurrent logs is too long and will be sent via email.\n\nDetailed Information: {detailedInformation}\nOperator: {operator}\nAlert ID: {alertId}",
        "fields": [
            {"id": "detailedInformation", "label": "Detailed Information", "multiline": True},
            {"id": "operator", "label": "Operator"},
            {"id": "alertId", "label": "Alert ID"},
        ],
    },
    {
        "id": "sql-update",
        "name": "SQL Update",
        "comment": "SQL data update was performed\n\nTime started: {timeStarted}\nTime ended: {timeEnded}",
        "fields": [
            {"id": "timeStarted", "label": "Time started"},
            {"id": "timeEnded", "label": "Time ended"},
        ],
    },
    {
        "id": "sql-extraction",
        "name": "SQL Extraction",
        "comment": "SQL extraction was performed and data wa stored on specific location.\n\nTime started: {timeStarted}\nTime ended: {timeEnded}\nLogs: {logs}",
        "fields": [
            {"id": "timeStarted", "label": "Time started"},
            {"id": "timeEnded", "label": "Time ended"},
            {"id": "logs", "label": "Logs", "multiline": True},
        ],
    },
]
