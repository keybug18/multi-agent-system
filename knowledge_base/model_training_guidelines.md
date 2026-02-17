# Model Training Guidelines

## Overview

This document defines the standard practices and requirements for training, evaluating, and registering machine learning models within the AI platform. All teams must follow these guidelines before promoting any model to the staging or production environment.

## Data Preparation Standards

All training datasets must be versioned using DVC (Data Version Control) and stored in the designated S3 training bucket. A minimum of 80/10/10 train/validation/test split is required. For time-series data, chronological splits must be used — random shuffling across time boundaries is strictly prohibited as it leads to data leakage.

## Experiment Tracking

All experiments must be logged in MLflow with the following mandatory fields: dataset version, feature list, hyperparameters, training duration, and all evaluation metrics (at minimum: primary metric, secondary metric, and confusion matrix for classification tasks). Experiments not logged in MLflow will not be considered for production promotion.

## Model Evaluation Criteria

Before a model can be promoted to staging, it must meet the following minimum thresholds:
- It must outperform the current production model on the primary metric by at least 1%.
- It must not degrade any secondary metric by more than 3%.
- Inference latency (P95) must not exceed 100ms for online serving models.
- The model must pass a fairness audit if it is used in customer-facing applications.

## Model Card Requirement

Every model promoted to the MLflow registry must have an associated Model Card document that includes: model description, intended use cases, out-of-scope uses, training data summary, evaluation results, and known limitations. This is a mandatory compliance requirement.

## Retraining Triggers

Models are eligible for retraining under the following conditions:
1. Primary metric degrades by more than 5% on the production monitoring dataset.
2. Data drift (PSI > 0.2) is detected on any of the top-10 most important features.
3. A scheduled quarterly retraining date is reached.