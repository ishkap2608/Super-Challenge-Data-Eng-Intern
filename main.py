import argparse
from pathlib import Path
from src.processor import process_path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Path to events.json (JSON Lines)")
    ap.add_argument("--out", default="sessions.csv", help="Output CSV for session summary")
    ap.add_argument("--skips_out", default="skipped.csv", help="Output CSV for skipped lines")
    args = ap.parse_args()

    sessions_df, skipped_df, stats = process_path(Path(args.input))

    sessions_df.to_csv(args.out, index=False)
    skipped_df.to_csv(args.skips_out, index=False)

    print("Done.")
    for k, v in stats.items():
        print(f"{k}: {v}")

if __name__ == "__main__":
    main()