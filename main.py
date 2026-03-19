import argparse
import subprocess
import sys
import time
from datetime import datetime, time as clock_time, timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

# 在代码第一次运行时，立即执行一次任务，之后再进入定时循环
FIRST_RUN = True


def get_next_run_time(now=None):
    now = now or datetime.now()
    target = datetime.combine(now.date(), clock_time(hour=9, minute=0))
    if now >= target:
        target += timedelta(days=1)
    return target


def run_daily_job():
    today = datetime.now().strftime("%Y-%m-%d")
    output_path = BASE_DIR / f"trending_{today}.json"

    subprocess.run(
        [sys.executable, str(BASE_DIR / "fetch_trending.py"), "--output", str(output_path)],
        cwd=str(BASE_DIR),
        check=True,
    )
    subprocess.run(
        [sys.executable, str(BASE_DIR / "extract_summary.py"), "--input", str(output_path)],
        cwd=str(BASE_DIR),
        check=True,
    )

    return output_path


def main():
    global FIRST_RUN

    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="立即执行一次后退出")
    args = parser.parse_args()

    if args.once:
        run_daily_job()
        return

    while True:
        if FIRST_RUN:
            try:
                output_path = run_daily_job()
                print(f"已完成: {output_path}")
            except subprocess.CalledProcessError as exc:
                print(f"任务执行失败: {exc}", file=sys.stderr)
            finally:
                FIRST_RUN = False

        next_run = get_next_run_time()
        wait_seconds = max(0, (next_run - datetime.now()).total_seconds())
        print(f"下一次执行时间: {next_run:%Y-%m-%d %H:%M:%S}")
        time.sleep(wait_seconds)

        try:
            output_path = run_daily_job()
            print(f"已完成: {output_path}")
        except subprocess.CalledProcessError as exc:
            print(f"任务执行失败: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
