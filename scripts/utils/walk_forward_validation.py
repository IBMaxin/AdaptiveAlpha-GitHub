#!/usr/bin/env python3
"""
Walk-Forward Validation Generator
Generates proper train/test splits for time series validation
"""

import argparse
from datetime import datetime, timedelta
from typing import List, Tuple


def generate_walk_forward_periods(
    start_date: str,
    end_date: str,
    train_months: int = 3,
    test_months: int = 1,
    step_months: int = 1
) -> List[Tuple[str, str, str, str]]:
    """
    Generate walk-forward validation periods.
    
    Returns: List of (train_start, train_end, test_start, test_end) tuples
    """
    start = datetime.strptime(start_date, "%Y%m%d")
    end = datetime.strptime(end_date, "%Y%m%d")
    
    periods = []
    current = start
    
    while current < end:
        # Training period
        train_start = current
        train_end = train_start + timedelta(days=train_months * 30)
        
        # Test period
        test_start = train_end
        test_end = test_start + timedelta(days=test_months * 30)
        
        # Stop if test period exceeds end date
        if test_end > end:
            break
            
        periods.append((
            train_start.strftime("%Y%m%d"),
            train_end.strftime("%Y%m%d"),
            test_start.strftime("%Y%m%d"),
            test_end.strftime("%Y%m%d")
        ))
        
        # Move forward by step_months
        current += timedelta(days=step_months * 30)
    
    return periods


def main():
    parser = argparse.ArgumentParser(description="Generate walk-forward validation periods")
    parser.add_argument("--start", default="20220101", help="Start date (YYYYMMDD)")
    parser.add_argument("--end", default="20250115", help="End date (YYYYMMDD)")
    parser.add_argument("--train-months", type=int, default=3, help="Training period in months")
    parser.add_argument("--test-months", type=int, default=1, help="Test period in months")
    parser.add_argument("--step-months", type=int, default=1, help="Step size in months")
    parser.add_argument("--format", choices=["json", "csv", "bash"], default="bash", help="Output format")
    
    args = parser.parse_args()
    
    periods = generate_walk_forward_periods(
        args.start, args.end, args.train_months, args.test_months, args.step_months
    )
    
    print(f"# Generated {len(periods)} walk-forward validation periods")
    print(f"# Train: {args.train_months} months, Test: {args.test_months} months, Step: {args.step_months} months")
    print()
    
    if args.format == "bash":
        for i, (train_start, train_end, test_start, test_end) in enumerate(periods, 1):
            print(f"# Period {i}")
            print(f"TRAIN_RANGE_{i}=\"{train_start}-{train_end}\"")
            print(f"TEST_RANGE_{i}=\"{test_start}-{test_end}\"")
            print()
    
    elif args.format == "json":
        import json
        output = []
        for i, (train_start, train_end, test_start, test_end) in enumerate(periods, 1):
            output.append({
                "period": i,
                "train_start": train_start,
                "train_end": train_end,
                "test_start": test_start,
                "test_end": test_end
            })
        print(json.dumps(output, indent=2))
    
    elif args.format == "csv":
        print("period,train_start,train_end,test_start,test_end")
        for i, (train_start, train_end, test_start, test_end) in enumerate(periods, 1):
            print(f"{i},{train_start},{train_end},{test_start},{test_end}")


if __name__ == "__main__":
    main()
