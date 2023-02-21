# PTST Summariser

Takes the test files and summarises all of the results into a single file consisting of the following headings:

- latency
- total_throughput
- total_sample_rate
- total_samples_received
- total_samples_lost

This file will be called `summary.csv` and is stored directly in the test directory.

## Usage
Run:
```bash
python summarise.py <test_dir>
```