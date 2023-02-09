import os
import sys
import pandas as pd

from pprint import pprint
from rich.console import Console
from rich.progress import track

console = Console()

if len(sys.argv) > 1:
    testdir = sys.argv[1]
else:
    testdir = "./data"

tests = [ os.path.join(testdir, _) for _ in os.listdir(testdir) ]

def get_latencies(pubfile):
    df = pd.read_csv(pubfile, on_bad_lines="skip", skiprows=2, skipfooter=5, engine="python")
    
    try:
        lat_header = [_ for _ in df.columns if "latency" in _.lower()][0]
        df = df[lat_header]
    except Exception as e:
        print(e)
        return

    return df

def get_total_sub_metric(sub_files, metric):
    sub_dfs = []
    
    for file in sub_files:
        df = pd.read_csv(file, on_bad_lines="skip", skiprows=2, skipfooter=3, engine="python")
        sub_head = [x for x in df.columns if metric in x.lower()][0]
        df = df[sub_head]
        df.rename(os.path.basename(file).replace(".csv", ""), inplace=True)
        sub_dfs.append(df)
        
    sub_df = pd.concat(sub_dfs, axis=1)
    
    # ? Add up all columns to create total column
    sub_df["total_" + metric] = sub_df[list(sub_df.columns)].sum(axis=1)
    
    # ? Take off the last number because its an average produced by perftest
    sub_df = sub_df[:-2]
    
    return sub_df["total_" + metric][:-1]

for i in track( range( len(tests) ), description="Summarising tests..." ):
    test = tests[i]
    
    testpath = os.path.join(test, "run_1")
    
    pub0_csv = [(os.path.join( testpath, _ )) for _ in os.listdir(testpath) if "pub" in _][0]
    
    sub_files = [(os.path.join( testpath, _ )) for _ in os.listdir(testpath) if "sub" in _]
    
    test_df = pd.DataFrame(columns=[
        "latency",
        "total_throughput",
        "total_sample_rate",
        "total_samples_received",
        "total_samples_lost"
    ])
    
    latencies = get_latencies(pub0_csv)
    total_throughputs = get_total_sub_metric(sub_files, "mbps")
    total_sample_rates = get_total_sub_metric(sub_files, "samples/s")
    total_samples_received = get_total_sub_metric(sub_files, "total samples").max()
    total_samples_lost = get_total_sub_metric(sub_files, "lost samples").max()
    
    test_df["latency"] = latencies
    test_df["total_throughput"] = total_throughputs
    test_df["total_sample_rate"] = total_sample_rates
    test_df["total_samples_received"] = total_samples_received
    test_df["total_samples_lost"] = total_samples_lost
    
    summary_csv_path = os.path.join(test, "summary.csv")
    
    if not os.path.exists(summary_csv_path):
        test_df.to_csv(summary_csv_path, sep=",")
    