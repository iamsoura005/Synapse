"""Kafka topic name constants for SYNAPSE pipeline."""

TOPICS = {
    "RAW_EVENTS":         "pipeline.raw_events",
    "TENSION_SIGNALS":    "pipeline.tension_signals",
    "NEGOTIATION_START":  "pipeline.negotiation_start",
    "RESOLUTION_QUEUE":   "pipeline.resolution_queue",
    "DELIVERY_READY":     "pipeline.delivery_ready",
    "CONTRACT_EVENTS":    "pipeline.contract_events",
    "AUDIT_LOG":          "pipeline.audit_log",
    "DEAD_LETTERS":       "pipeline.dead_letters",
}

# Topics requiring exactly-once semantics
EXACTLY_ONCE_TOPICS = {
    TOPICS["NEGOTIATION_START"],
    TOPICS["CONTRACT_EVENTS"],
}
