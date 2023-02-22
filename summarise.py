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

tests = [ os.path.join(testdir, _) for _ in os.listdir(testdir) if os.path.isdir( os.path.join(testdir, _) )]

def get_latencies(pubfile):
    try:
        df = pd.read_csv(pubfile, on_bad_lines="skip", skiprows=2, skipfooter=5, engine="python")
    except Exception as e:
        console.print(f"Error looking at {pubfile}:", style="bold red")
        console.print(e, style="bold red")
        return
    
    try:
        lat_header = [_ for _ in df.columns if "latency" in _.lower()][0]
        df = df[lat_header]
    except Exception as e:
        print(e)
        return

    return df

def get_metric_per_sub(sub_file, metric):
    df = pd.read_csv(sub_file, on_bad_lines='skip', skiprows=2, skipfooter=3, engine='python')
    sub_head = [x for x in df.columns if metric in x.lower()][0]
    df = df[sub_head]
    df.rename(os.path.basename(sub_file).replace(".csv", ""), inplace=True)
    # ? Take off the last number because its an average produced by perftest
    df = df[:-2]
    
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

def test_summary_exists(test):
    testname = os.path.basename(test)
    return os.path.exists(f"./summaries/{testname}_summary.csv")

for i in track( range( len(tests) ), description="Summarising tests..." ):
    test = tests[i]
    # TODO: Uncomment below.
    # if test_summary_exists(test):
    #    continue 
    
    testpath = os.path.join(test, "run_1")
    pub_files = [(os.path.join( testpath, _ )) for _ in os.listdir(testpath) if "pub" in _]
    
    if len(pub_files) == 0:
        console.print(f"{test} has 0 pub files.", style="bold red")
        continue

    pub0_csv = pub_files[0]
    
    sub_files = [(os.path.join( testpath, _ )) for _ in os.listdir(testpath) if "sub" in _]

    df_cols = [
        "latency",
        "total_throughput_mbps",
        "total_sample_rate",
        "total_samples_received",
        "total_samples_lost"
    ]

    for sub_file in sub_files:
        sub_name = os.path.basename(sub_file).replace(".csv", '')
        df_cols.append(f"{sub_name}_throughput_mbps")
        df_cols.append(f"{sub_name}_sample_rate")
        df_cols.append(f"{sub_name}_samples_received")
        df_cols.append(f"{sub_name}_samples_lost")
    
    test_df = pd.DataFrame(columns=df_cols)

    test_df["latency"] = get_latencies(pub0_csv)
    test_df["total_throughput_mbps"] = get_total_sub_metric(sub_files, "mbps")
    test_df["total_sample_rate"] = get_total_sub_metric(sub_files, "samples/s")
    # ? Only put the value on the first row instead of repeating on every column (taking up extra storage)
    test_df.loc[test_df.index[0], 'total_samples_received'] = get_total_sub_metric(sub_files, "total samples").max()
    test_df.loc[test_df.index[0], 'total_samples_lost'] = get_total_sub_metric(sub_files, "lost samples").max()
    
    sub_cols = [_ for _ in test_df.columns if 'sub' in _]
    sub_count = int(len(sub_cols) / 4)

    for i in range(sub_count):
        sub_file = [_ for _ in sub_files if f"sub_{i}.csv" in _][0]
        test_df[f"sub_{i}_throughput_mbps"] = get_metric_per_sub(sub_file, "mbps")
        test_df[f"sub_{i}_sample_rate"] = get_metric_per_sub(sub_file, "samples/s")
        test_df.loc[test_df.index[0], f"sub_{i}_samples_received"] = get_metric_per_sub(sub_file, "total samples").max()
        test_df.loc[test_df.index[0], f"sub_{i}_samples_lost"] = get_metric_per_sub(sub_file, "lost samples").max()

    # ? Replace NaN with ""
    test_df = test_df.fillna("")

    if not os.path.exists("./summaries"):
        os.mkdir("./summaries")

    summary_csv_path = os.path.join("./summaries", f"{os.path.basename(test)}_summary.csv")
    
    if not os.path.exists(summary_csv_path):
        test_df.to_csv(summary_csv_path, sep=",")
    