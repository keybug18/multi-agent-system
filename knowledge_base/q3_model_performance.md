# Q3 Model Performance Report

## Overview

This report summarizes the performance metrics of all production machine learning models for Q3 (July–September 2024). The evaluation covers accuracy, latency, and drift indicators across three core models deployed in the recommendation and fraud detection pipelines.

## Model A: Recommendation Engine (RecSys-v3)

RecSys-v3 is a two-tower neural network model deployed in the product recommendation pipeline. During Q3, it achieved a mean average precision (MAP@10) of 0.74, a 6% improvement over the Q2 baseline of 0.698. Average inference latency dropped to 42ms per request (P95), down from 61ms in Q2, due to the ONNX runtime migration completed in late July. No significant data drift was detected in user embedding distributions during this quarter.

## Model B: Fraud Detection Classifier (FDC-v2)

FDC-v2 is a gradient-boosted tree ensemble model. In Q3, it recorded a precision of 0.91 and recall of 0.87 on the held-out validation set, yielding an F1-score of 0.89. A concept drift event was detected in mid-August when the false positive rate spiked to 14% following a promotional campaign that altered typical transaction patterns. An emergency retraining was triggered on August 19th using the updated transaction data, which brought the false positive rate back to 4.2% by August 25th.

## Model C: Customer Churn Predictor (CCP-v1)

CCP-v1 is a logistic regression model with L2 regularization used to predict 30-day churn. Its AUC-ROC score for Q3 was 0.81, consistent with Q2 performance. No retraining was required this quarter. However, a scheduled retraining is planned for October to incorporate new behavioral features from the updated data pipeline.

## Key Observations

- RecSys-v3 showed the most significant performance improvement due to infrastructure optimization.
- FDC-v2 requires closer monitoring around promotional periods to detect concept drift early.
- CCP-v1 remains stable but will benefit from new feature integration in Q4.

## Recommended Actions

1. Implement automated drift detection alerts for FDC-v2 with a 7% false-positive threshold trigger.
2. Prioritize A/B testing for RecSys-v4 in Q4.
3. Schedule CCP-v1 retraining for the first week of October with the new behavioral feature set.