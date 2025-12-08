import csv
import requests
import concurrent.futures
from typing import List, Tuple

TEST_URL = "https://www.youtube.com"
TIMEOUT = 10  # seconds

def load_proxies_from_csv(filepath: str) -> List[str]:
    """Parse CSV proxy list and return formatted proxy URLs."""
    proxies = []
    
    with open(filepath, "r", encoding="utf-8") as f:
        first_line = f.readline()
        f.seek(0)
        
        if "ip" in first_line and "port" in first_line:
            reader = csv.DictReader(f)
            for row in reader:
                ip = row.get("ip", "").replace('"', '').strip()
                port = row.get("port", "").replace('"', '').strip()
                protocols = row.get("protocols", "").replace('"', '').strip()
                
                if ip and port:
                    proto = "http"
                    if "socks5" in protocols:
                        proto = "socks5"
                    elif "socks4" in protocols:
                        proto = "socks4"
                    
                    proxy_url = f"{proto}://{ip}:{port}"
                    proxies.append(proxy_url)
    
    return proxies

def test_proxy(proxy_url: str) -> Tuple[str, bool, str]:
    """Test if a proxy can connect to YouTube. Returns (proxy_url, success, error_msg)."""
    proxy_dict = {"http": proxy_url, "https": proxy_url}
    
    try:
        response = requests.get(TEST_URL, proxies=proxy_dict, timeout=TIMEOUT)
        if response.status_code == 200:
            return (proxy_url, True, "OK")
        else:
            return (proxy_url, False, f"HTTP {response.status_code}")
    except requests.exceptions.ProxyError as e:
        return (proxy_url, False, f"ProxyError: {str(e)[:50]}")
    except requests.exceptions.Timeout:
        return (proxy_url, False, "Timeout")
    except requests.exceptions.ConnectionError as e:
        return (proxy_url, False, f"ConnectionError: {str(e)[:50]}")
    except Exception as e:
        return (proxy_url, False, f"Error: {str(e)[:50]}")

def main():
    input_file = "../Free_Proxy_List.txt"
    output_file = "working_proxies.txt"
    
    print(f"Loading proxies from {input_file}...")
    proxies = load_proxies_from_csv(input_file)
    print(f"Found {len(proxies)} proxies to test.\n")
    
    working = []
    failed = []
    
    print("Testing proxies (this may take a few minutes)...")
    print("=" * 60)
    
    # Test proxies in parallel for speed
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(test_proxy, proxy): proxy for proxy in proxies}
        
        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            proxy_url, success, msg = future.result()
            
            if success:
                working.append(proxy_url)
                status = "✓ WORKING"
            else:
                failed.append((proxy_url, msg))
                status = f"✗ FAILED ({msg})"
            
            print(f"[{i}/{len(proxies)}] {proxy_url[:40]:40} {status}")
    
    print("=" * 60)
    print(f"\nResults:")
    print(f"  Working: {len(working)}")
    print(f"  Failed:  {len(failed)}")
    
    if working:
        with open(output_file, "w") as f:
            for proxy in working:
                f.write(proxy + "\n")
        print(f"\n✓ Saved {len(working)} working proxies to {output_file}")
    else:
        print("\n✗ No working proxies found.")

if __name__ == "__main__":
    main()
