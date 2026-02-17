# Infrastructure Overview

## Overview

This document provides a high-level overview of the cloud infrastructure that supports the AI/ML platform. All resources are hosted on AWS and managed using Terraform for infrastructure-as-code.

## Compute

Model training workloads run on AWS EMR (Apache Spark) and AWS SageMaker Training Jobs. Online inference is handled by a Kubernetes cluster (EKS) running KServe. The cluster currently has 20 nodes of type ml.g4dn.xlarge (NVIDIA T4 GPUs), with autoscaling configured to add up to 10 additional nodes during peak hours (8 AM–10 PM UTC).

## Storage

- **S3:** Primary object store for raw data, training datasets, model artifacts, and offline feature store partitions. Total current usage: 48TB.
- **RDS (PostgreSQL):** Operational database for metadata, experiment tracking (MLflow backend), and feature registry.
- **ElastiCache (Redis):** Online feature store and model prediction cache. Current size: 500GB.
- **EBS Volumes:** Attached to individual Kubernetes nodes for ephemeral scratch storage during inference.

## Networking

All inter-service communication within the VPC uses private subnets. The model serving API is exposed via an Application Load Balancer (ALB) with SSL termination. WAF rules are applied to reject malformed requests and rate-limit external clients to 1,000 requests per minute per IP.

## CI/CD

The platform uses GitHub Actions for CI/CD. On every pull request, automated tests (unit, integration, and a smoke test against a staging endpoint) are triggered. Model deployment is handled by a custom GitOps workflow: merging to the `main` branch triggers a Helm chart update in the staging environment. Production promotion requires a manual approval step from two senior engineers.

## Cost Management

Current monthly infrastructure cost is approximately $42,000. The largest cost centers are EKS compute ($18,000) and S3 storage/transfer ($11,000). A cost optimization review is scheduled for Q4 to evaluate reserved instance purchasing for steady-state workloads.