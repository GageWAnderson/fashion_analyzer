# ADR 001: Clothing Search Graph Testing

## Status
Accepted

## Context
Testing the clothing search graph tool fully requires far too much compute for a single GPU instance
to test all the test cases. Therefore, these tests will be skipped until much more compute is available.

## Decision
Test suite for test tools skips clothing search graph tool.

## Consequences
- Positive: Saves on compute while testing
- Negative: Missing out on testing the clothing search graph tool
- Risk: Need to do more user acceptance testing to make sure the clothing search graph tool works as expected

## Date
2024-11-24