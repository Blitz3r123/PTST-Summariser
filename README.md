# PTST Summariser

Takes the test files and summarises all of the results into a single file consisting of the following headings:

- latency
- total_throughput_mbps
- total_sample_rate
- total_samples_received
- total_samples_lost
- sub_0_throughputs_mbps
- sub_0_sample_rate
- sub_0_samples_received
- sub_0_samples_lost
- ...
- sub_n_throughput_mbps
- sub_n_sample_rate
- sub_n_samples_received
- sub_n_samples_lost

This file will be called `summary.csv` and is stored directly in the summaries directory.

## Usage
Run:
```bash
python summarise.py <test_dir>
```