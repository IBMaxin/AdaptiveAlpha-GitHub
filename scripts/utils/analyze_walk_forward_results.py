#!/usr/bin/env python3
"""
Walk-Forward Validation Results Analyzer
Analyzes and visualizes walk-forward validation results
"""

import argparse
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime


class WalkForwardAnalyzer:
    """Analyze walk-forward validation results."""
    
    def __init__(self, results_dir: str = "user_data/walk_forward_results"):
        self.results_dir = Path(results_dir)
        self.periods = []
        self.metrics = []
        
    def load_results(self) -> bool:
        """Load all validation results."""
        if not self.results_dir.exists():
            print(f"Results directory not found: {self.results_dir}")
            return False
            
        period_dirs = [d for d in self.results_dir.iterdir() if d.is_dir() and d.name.startswith("period_")]
        
        if not period_dirs:
            print("No period results found")
            return False
            
        print(f"Found {len(period_dirs)} period results")
        
        for period_dir in sorted(period_dirs):
            period_num = int(period_dir.name.split("_")[1])
            metrics = self._extract_period_metrics(period_dir)
            if metrics:
                self.periods.append(period_num)
                self.metrics.append(metrics)
                
        return len(self.metrics) > 0
    
    def _extract_period_metrics(self, period_dir: Path) -> Optional[Dict]:
        """Extract metrics from a period directory."""
        metrics_file = period_dir / "metrics.txt"
        validation_log = period_dir / "validation_backtest.log"
        
        metrics = {
            "period": int(period_dir.name.split("_")[1]),
            "training_success": (period_dir / "training_log.txt").exists(),
            "validation_success": validation_log.exists(),
        }
        
        # Extract metrics from validation log
        if validation_log.exists():
            try:
                content = validation_log.read_text()
                
                # Extract key metrics using regex
                profit_match = re.search(r'Tot Profit.*?(-?\d+\.?\d*)', content)
                if profit_match:
                    metrics["total_profit"] = float(profit_match.group(1))
                
                profit_pct_match = re.search(r'Tot Profit.*?(-?\d+\.?\d*)%', content)
                if profit_pct_match:
                    metrics["profit_percent"] = float(profit_pct_match.group(1))
                
                trades_match = re.search(r'Trades.*?(\d+)', content)
                if trades_match:
                    metrics["trades"] = int(trades_match.group(1))
                
                win_rate_match = re.search(r'Win.*?(\d+\.?\d*)%', content)
                if win_rate_match:
                    metrics["win_rate"] = float(win_rate_match.group(1))
                
                drawdown_match = re.search(r'Drawdown.*?(-?\d+\.?\d*)', content)
                if drawdown_match:
                    metrics["max_drawdown"] = float(drawdown_match.group(1))
                    
            except Exception as e:
                print(f"Error parsing metrics for period {metrics['period']}: {e}")
        
        return metrics
    
    def generate_summary(self) -> Dict:
        """Generate summary statistics."""
        if not self.metrics:
            return {}
        
        df = pd.DataFrame(self.metrics)
        
        summary = {
            "total_periods": len(self.metrics),
            "successful_periods": df["validation_success"].sum(),
            "success_rate": df["validation_success"].mean() * 100,
        }
        
        # Calculate performance metrics for successful periods
        successful_df = df[df["validation_success"]]
        
        if len(successful_df) > 0:
            summary.update({
                "avg_profit_percent": successful_df["profit_percent"].mean() if "profit_percent" in successful_df.columns else 0,
                "total_trades": successful_df["trades"].sum() if "trades" in successful_df.columns else 0,
                "avg_win_rate": successful_df["win_rate"].mean() if "win_rate" in successful_df.columns else 0,
                "avg_drawdown": successful_df["max_drawdown"].mean() if "max_drawdown" in successful_df.columns else 0,
                "best_period": successful_df.loc[successful_df["profit_percent"].idxmax(), "period"] if "profit_percent" in successful_df.columns else None,
                "worst_period": successful_df.loc[successful_df["profit_percent"].idxmin(), "period"] if "profit_percent" in successful_df.columns else None,
            })
        
        return summary
    
    def create_visualization(self, output_file: str = "user_data/walk_forward_analysis.png"):
        """Create visualization of results."""
        if not self.metrics:
            print("No metrics to visualize")
            return
            
        df = pd.DataFrame(self.metrics)
        successful_df = df[df["validation_success"]]
        
        if len(successful_df) == 0:
            print("No successful periods to visualize")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle("Walk-Forward Validation Results", fontsize=16)
        
        # Profit over time
        if "profit_percent" in successful_df.columns:
            axes[0, 0].plot(successful_df["period"], successful_df["profit_percent"], marker='o')
            axes[0, 0].set_title("Profit % by Period")
            axes[0, 0].set_xlabel("Period")
            axes[0, 0].set_ylabel("Profit %")
            axes[0, 0].grid(True)
        
        # Win rate over time
        if "win_rate" in successful_df.columns:
            axes[0, 1].plot(successful_df["period"], successful_df["win_rate"], marker='o', color='green')
            axes[0, 1].set_title("Win Rate by Period")
            axes[0, 1].set_xlabel("Period")
            axes[0, 1].set_ylabel("Win Rate %")
            axes[0, 1].grid(True)
        
        # Drawdown over time
        if "max_drawdown" in successful_df.columns:
            axes[1, 0].plot(successful_df["period"], successful_df["max_drawdown"], marker='o', color='red')
            axes[1, 0].set_title("Max Drawdown by Period")
            axes[1, 0].set_xlabel("Period")
            axes[1, 0].set_ylabel("Max Drawdown")
            axes[1, 0].grid(True)
        
        # Trades per period
        if "trades" in successful_df.columns:
            axes[1, 1].bar(successful_df["period"], successful_df["trades"])
            axes[1, 1].set_title("Trades per Period")
            axes[1, 1].set_xlabel("Period")
            axes[1, 1].set_ylabel("Number of Trades")
            axes[1, 1].grid(True)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Visualization saved to: {output_file}")
        
    def export_csv(self, output_file: str = "user_data/walk_forward_results.csv"):
        """Export results to CSV."""
        if not self.metrics:
            print("No metrics to export")
            return
            
        df = pd.DataFrame(self.metrics)
        df.to_csv(output_file, index=False)
        print(f"Results exported to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Analyze walk-forward validation results")
    parser.add_argument("--results-dir", default="user_data/walk_forward_results", help="Results directory")
    parser.add_argument("--output-dir", default="user_data", help="Output directory for reports")
    parser.add_argument("--format", choices=["console", "json", "csv", "all"], default="console", help="Output format")
    
    args = parser.parse_args()
    
    analyzer = WalkForwardAnalyzer(args.results_dir)
    
    if not analyzer.load_results():
        print("Failed to load results")
        return 1
    
    summary = analyzer.generate_summary()
    
    if args.format in ["console", "all"]:
        print("\n=== WALK-FORWARD VALIDATION ANALYSIS ===")
        print(f"Total Periods: {summary['total_periods']}")
        print(f"Successful Periods: {summary['successful_periods']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        
        if summary['successful_periods'] > 0:
            print(f"\nPerformance Metrics (Successful Periods):")
            print(f"Average Profit: {summary.get('avg_profit_percent', 0):.2f}%")
            print(f"Total Trades: {summary.get('total_trades', 0)}")
            print(f"Average Win Rate: {summary.get('avg_win_rate', 0):.1f}%")
            print(f"Average Max Drawdown: {summary.get('avg_drawdown', 0):.2f}%")
            print(f"Best Period: {summary.get('best_period', 'N/A')}")
            print(f"Worst Period: {summary.get('worst_period', 'N/A')}")
    
    if args.format in ["json", "all"]:
        json_file = Path(args.output_dir) / "walk_forward_summary.json"
        with open(json_file, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"\nSummary saved to: {json_file}")
    
    if args.format in ["csv", "all"]:
        analyzer.export_csv(Path(args.output_dir) / "walk_forward_results.csv")
    
    # Always try to create visualization
    try:
        analyzer.create_visualization(Path(args.output_dir) / "walk_forward_analysis.png")
    except ImportError:
        print("Matplotlib not available - skipping visualization")
    except Exception as e:
        print(f"Error creating visualization: {e}")
    
    return 0


if __name__ == "__main__":
    exit(main())
