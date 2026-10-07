from __future__ import annotations

import argparse
import json

from src.models.training import train_impact_model


def main() -> None:
    parser = argparse.ArgumentParser(description='Train CPU XGBoost impact regression on historical event outcomes')
    parser.add_argument('--data', required=True, help='EDT JSON/JSONL or prepared CSV with historical forward returns')
    parser.add_argument('--output-dir', default='models')
    parser.add_argument('--max-rows', type=int, default=50000)
    parser.add_argument('--batch-size', type=int, default=128)
    parser.add_argument('--device', choices=['cpu', 'cuda'], default=None, help='Embedding device; XGBoost stays on CPU')
    args = parser.parse_args()
    report = train_impact_model(args.data, args.output_dir, args.max_rows, args.batch_size, args.device)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
