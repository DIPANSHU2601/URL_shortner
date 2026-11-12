import concurrent.futures
import urllib.request
import urllib.error
import json

TARGET_URL = "http://localhost:8000/shorten"
PAYLOAD = json.dumps({"url": "https://www.google.com"}).encode("utf-8")

def hit_index(index):
    req = urllib.request.Request(
        TARGET_URL,
        data=PAYLOAD,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, ""
    except urllib.error.HTTPError as e:
        return e.code, e.reason
    except Exception as e:
        return 500, str(e)

def run_test():
    print("Firing 50 concurrent requests...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(hit_index, i) for i in range(50)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    status_counts = {}
    for status, _ in results:
        status_counts[status] = status_counts.get(status, 0) + 1

    print(f"Results breakdown -> {status_counts}")

if __name__ == "__main__":
    run_test()
