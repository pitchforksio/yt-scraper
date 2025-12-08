#!/usr/bin/env python3
"""
Fetch fresh proxies from Proxifly's free proxy list and test them.
"""
import requests
import concurrent.futures
from typing import List, Tuple

PROXIFLY_HTTP_URL = "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/http/data.txt"
PROXIFLY_SOCKS5_URL = "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/socks5/data.txt"
TEST_URL = "https://www.youtube.com"
TIMEOUT = 10

def fetch_proxies_from_url(url: str, protocol: str) -> List[str]:
    """Fetch proxy list from Proxifly CDN."""
    print(f"Fetching {protocol} proxies from Proxifly...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        proxies = []
        for line in response.text.strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                # Format: ip:port, need to add protocol prefix
                proxies.append(f"{protocol}://{line}")
        return proxies
    except Exception as e:
        print(f"Error fetching proxies: {e}")
        return []

def test_proxy(proxy_url: str) -> Tuple[str, bool, str]:
    """Test if a proxy can connect to YouTube."""
    proxy_dict = {"http": proxy_url, "https": proxy_url}
    
    try:
        response = requests.get(TEST_URL, proxies=proxy_dict, timeout=TIMEOUT)
        if response.status_code == 200:
            return (proxy_url, True, "OK")
        else:
            return (proxy_url, False, f"HTTP {response.status_code}")
    except requests.exceptions.ProxyError as e:
        return (proxy_url, False, f"ProxyError")
    except requests.exceptions.Timeout:
        return (proxy_url, False, "Timeout")
    except requests.exceptions.ConnectionError:
        return (proxy_url, False, "ConnectionError")
    except Exception as e:
        return (proxy_url, False, f"Error: {type(e).__name__}")

def main():
    output_file = "proxifly_working.txt"
    
    # Fetch HTTP and SOCKS5 proxies
    http_proxies = fetch_proxies_from_url(PROXIFLY_HTTP_URL, "http")
    socks5_proxies = fetch_proxies_from_url(PROXIFLY_SOCKS5_URL, "socks5")
    
    all_proxies = http_proxies + socks5_proxies
    print(f"\nFetched {len(http_proxies)} HTTP + {len(socks5_proxies)} SOCKS5 = {len(all_proxies)} total proxies")
    
    if not all_proxies:
        print("No proxies fetched. Exiting.")
        return
    
    print(f"\nTesting {len(all_proxies)} proxies (this may take a few minutes)...")
    print("=" * 60)
    
    working = []
    failed = []
    
    # Test in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        futures = {executor.submit(test_proxy, proxy): proxy for proxy in all_proxies}
        
        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            proxy_url, success, msg = future.result()
            
            if success:
                working.append(proxy_url)
                status = "✓ WORKING"
                print(f"[{i}/{len(all_proxies)}] {proxy_url[:45]:45} {status}")
            else:
                failed.append((proxy_url, msg))
                # Only print failures occasionally to reduce noise
                if i % 50 == 0:
                    print(f"[{i}/{len(all_proxies)}] Tested {i} proxies, {len(working)} working so far...")
    
    print("=" * 60)
    print(f"\nResults:")
    print(f"  Working: {len(working)}")
    print(f"  Failed:  {len(failed)}")
    print(f"  Success Rate: {len(working)/len(all_proxies)*100:.1f}%")
    
    if working:
        with open(output_file, "w") as f:
            for proxy in working:
                f.write(proxy + "\n")
        print(f"\n✓ Saved {len(working)} working proxies to {output_file}")
        print(f"\nTo use these proxies, run:")
        print(f"  ../.venv/bin/python download_transcripts.py --proxies {output_file}")
    else:
        print("\n✗ No working proxies found.")

if __name__ == "__main__":
    main()
