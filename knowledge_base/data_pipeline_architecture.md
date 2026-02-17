# Data Pipeline Architecture

## Overview

This document describes the current data ingestion, transformation, and serving architecture used by the AI/ML platform. The pipeline is designed for high-throughput, low-latency feature delivery to both online inference services and offline model training jobs.

## Ingestion Layer

Raw data enters the system from three primary sources: transactional databases (PostgreSQL), clickstream event streams (Apache Kafka), and third-party CRM exports (S3 batch files). The Kafka consumer group is configured with 12 partitions and a retention window of 7 days to allow replay in case of downstream failures. Batch imports from S3 are scheduled every 4 hours via Apache Airflow DAGs.

## Transformation Layer

The transformation layer uses Apache Spark running on a managed cluster (AWS EMR). Streaming jobs use Spark Structured Streaming with micro-batch intervals of 30 seconds. Key transformations include sessionization of clickstream events, feature engineering (rolling aggregates, lag features), and data quality checks using Great Expectations. Any records failing quality checks are routed to a dead-letter queue in S3 for manual review.

## Feature Store

Processed features are written to a dual-store Feature Store architecture:
- **Online Store (Redis):** Serves low-latency (<5ms) feature lookups for real-time inference. TTL is set to 24 hours.
- **Offline Store (Apache Parquet on S3):** Used for model training, stored in columnar format partitioned by date and entity type.

The Feature Store API is built on FastAPI and exposes endpoints for feature retrieval, feature registration, and lineage tracking.

## Serving Layer

The serving layer consists of a model registry (MLflow) and a model serving cluster (Kubernetes with KServe). Models are versioned and promoted through staging, canary, and production environments. Canary deployments receive 5% of live traffic before full promotion.

## Known Limitations

- The Redis online store has a hard limit of 500GB due to current instance sizing. Projected growth will require scaling by Q1 2025.
- Airflow DAG scheduling has a known race condition when S3 imports and Kafka streams produce conflicting feature values for the same entity within the same micro-batch window.