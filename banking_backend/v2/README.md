# Banking Backend Context Update

This folder supports the second-version update by improving fraud payload quality sent to the fraud backend.

## New module

- transaction_context_builder.py

## Purpose

ML quality is strongly tied to input quality. This module enriches transaction payloads with:

- device/session metadata
- user profile metrics (account age, average amount)
- ratio features (transaction amount vs user baseline)

These features can improve anomaly precision and reduce false positives when consumed by the smart ML analysis module in the backend version-2 folder.
