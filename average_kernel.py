import os
import re
import numpy as np
from collections import defaultdict

def parse_lmbench_file(filepath):
    kernel = None
    metrics = {
        "Simple syscall": None,
        "Simple read": None,
        "Simple write": None,
        "Simple stat": None,
        "Simple fstat": None,
        "Simple open/close": None,
        "Signal handler installation": None,
        "Signal handler overhead": None,
        "Pipe latency": None,
        "Process fork+exit": None,
        "Process fork+execve": None,
        "Process fork+/bin/sh -c": None,
        "Pagefaults on /var/tmp/XXX": None,
        "mmap latency": None,
        "File create latency": None,
        "File delete latency": None,
        "Context switch latency": None,
    }
    
    with open(filepath, "r") as f:
        for line in f:
            # Extract kernel name
            if line.startswith("[lmbench3.0 results for Linux"):
                match = re.search(r'Linux \S+ ([^ ]+) ', line)
                if match:
                    kernel = match.group(1)
            
            # Extract regular benchmark values
            for key in metrics.keys():
                if key in line and "microseconds" in line:
                    match = re.search(r'([\d\.]+) microseconds', line)
                    if match:
                        metrics[key] = float(match.group(1))
            
            # Extract mmap latency (last row, second column)
            if line.startswith("1073.741824"):
                parts = line.split()
                if len(parts) > 1:
                    metrics["mmap latency"] = float(parts[1])
            
            # Extract file system latency (first row, 0k case)
            if line.startswith("0k"):
                parts = line.split()
                if len(parts) >= 4:
                    metrics["File create latency"] = 1000000 / float(parts[2])
                    metrics["File delete latency"] = 1000000 / float(parts[3])
            
            # Extract context switch latency (first row, second column)
            if line.startswith('"size=0k ovr='):
                next_line = next(f, None)
                if next_line:
                    parts = next_line.split()
                    if len(parts) > 1:
                        metrics["Context switch latency"] = float(parts[1])
    
    return kernel, metrics if kernel else None

def aggregate_results(directory):
    kernel_results = defaultdict(lambda: defaultdict(list))
    
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            result = parse_lmbench_file(filepath)
            if result:
                kernel, metrics = result
                for key, value in metrics.items():
                    if value is not None:
                        kernel_results[kernel][key].append(value)
    
    # Compute averages
    avg_results = {}
    for kernel, metrics in kernel_results.items():
        avg_results[kernel] = {key: np.mean(values) for key, values in metrics.items()}
    
    return avg_results

def main():
    results_dir = "results/x86_64-linux-gnu"
    averages = aggregate_results(results_dir)
    
    for kernel, metrics in averages.items():
        print(f"Kernel: {kernel}")
        for key, value in metrics.items():
            print(f"  {key}: {value:.4f} microseconds")
        print()

if __name__ == "__main__":
    main()
