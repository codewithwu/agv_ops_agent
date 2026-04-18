#!/usr/bin/env python3
"""简单的并发压力测试脚本 - 仅使用标准库"""

import urllib.request
import urllib.error
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import json

API_BASE = "http://localhost:8000/api/v1"


def make_request(url: str) -> Dict:
    """发起单个GET请求"""
    start = time.time()
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return {"status": resp.status, "time": time.time() - start}
    except Exception as e:
        return {"status": 0, "time": time.time() - start, "error": str(e)}


def make_post_request(url: str, json_data: dict) -> Dict:
    """发起POST请求"""
    start = time.time()
    try:
        data = json.dumps(json_data).encode("utf-8")
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return {"status": resp.status, "time": time.time() - start}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "time": time.time() - start}
    except Exception as e:
        return {"status": 0, "time": time.time() - start, "error": str(e)}


def stress_test(url: str, total: int, concurrency: int):
    """压力测试"""
    print(f"测试目标: {url}")
    print(f"总请求数: {total}, 并发数: {concurrency}")
    print("-" * 50)

    results: List[Dict] = []
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(make_request, url) for _ in range(total)]

        for i, future in enumerate(as_completed(futures)):
            results.append(future.result())
            if (i + 1) % 100 == 0:
                print(f"\r进度: {i + 1}/{total}", end="", flush=True)

    total_time = time.time() - start_time

    # 统计结果
    print()
    print("-" * 50)
    print("测试结果:")
    print(f"  总耗时: {total_time:.2f}s")
    print(f"  QPS: {total / total_time:.2f}")
    print(
        f"  平均响应时间: {sum(r['time'] for r in results) / len(results) * 1000:.2f}ms"
    )

    statuses = {}
    for r in results:
        statuses[r["status"]] = statuses.get(r["status"], 0) + 1
    print(f"  状态码分布: {statuses}")

    errors = [r for r in results if r.get("error")]
    if errors:
        print(f"  错误数: {len(errors)}")


def login_test(total: int, concurrency: int):
    """登录接口测试"""
    print("\n=== 登录接口压力测试 ===")

    url = f"{API_BASE}/auth/login"
    payload = {"username": "cooper", "password": "158168"}

    results: List[Dict] = []
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(make_post_request, url, payload) for _ in range(total)
        ]

        for i, future in enumerate(as_completed(futures)):
            results.append(future.result())
            if (i + 1) % 10 == 0:
                print(f"\r进度: {i + 1}/{total}", end="", flush=True)

    total_time = time.time() - start_time

    print()
    print("-" * 50)
    print("测试结果:")
    print(f"  总耗时: {total_time:.2f}s")
    print(f"  QPS: {total / total_time:.2f}")
    print(
        f"  平均响应时间: {sum(r['time'] for r in results) / len(results) * 1000:.2f}ms"
    )

    statuses = {}
    for r in results:
        statuses[r["status"]] = statuses.get(r["status"], 0) + 1
    print(f"  状态码分布: {statuses}")

    errors = [r for r in results if r.get("error")]
    if errors:
        print(f"  错误数: {len(errors)}")


def main():
    import sys

    if len(sys.argv) < 2:
        print("用法:")
        print("  python load_test.py health [total] [concurrency]  # 测试健康检查")
        print("  python load_test.py login  [total] [concurrency]  # 测试登录")
        print("\n默认: 1000请求, 100并发")
        return

    cmd = sys.argv[1]
    total = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    concurrency = int(sys.argv[3]) if len(sys.argv) > 3 else 100

    if cmd == "health":
        stress_test(f"{API_BASE}/health", total, concurrency)
    elif cmd == "login":
        login_test(total, concurrency)
    else:
        stress_test(cmd, total, concurrency)


if __name__ == "__main__":
    main()
