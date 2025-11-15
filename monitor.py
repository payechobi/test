import requests
import time
from datetime import datetime
import json

WALLET = "43jqgNCGAZQYwnk4s7Lt7P93S2sDkdN5bLKgUsGqVMoD6Bftsc5VVcHNy3mRBr7aBg5KgtFDHfYqK1MF8HEgSGucLbCCPeS"
CHECK_INTERVAL = 300

def clear_screen():
    print("\033[H\033[J", end="")

def get_supportxmr_stats():
    try:
        url = f"https://supportxmr.com/api/miner/{WALLET}/stats"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "pool": "SupportXMR",
                "hashrate": data.get("hash", 0) / 1000,
                "balance": data.get("amtDue", 0) / 1000000000000,
                "paid": data.get("amtPaid", 0) / 1000000000000,
                "workers": data.get("activeWorkers", 0),
                "last_share": data.get("lastHash", 0),
                "valid_shares": data.get("validShares", 0),
                "invalid_shares": data.get("invalidShares", 0),
                "status": "online"
            }
    except Exception as e:
        return {"pool": "SupportXMR", "status": "error", "error": str(e)}
    return {"pool": "SupportXMR", "status": "offline"}

def get_minexmr_stats():
    try:
        url = f"https://minexmr.com/api/stats_address?address={WALLET}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "pool": "MineXMR",
                "hashrate": data.get("hash", 0) / 1000,
                "balance": data.get("amtDue", 0) / 1000000000000,
                "paid": data.get("amtPaid", 0) / 1000000000000,
                "workers": len(data.get("workers", [])),
                "valid_shares": data.get("validShares", 0),
                "status": "online"
            }
    except Exception as e:
        return {"pool": "MineXMR", "status": "error", "error": str(e)}
    return {"pool": "MineXMR", "status": "offline"}

def get_nanopool_stats():
    try:
        url = f"https://api.nanopool.org/v1/xmr/user/{WALLET}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("status"):
                user_data = data.get("data", {})
                return {
                    "pool": "Nanopool",
                    "hashrate": user_data.get("hashrate", 0),
                    "balance": user_data.get("balance", 0),
                    "paid": user_data.get("paid", 0),
                    "workers": len(user_data.get("workers", [])),
                    "status": "online"
                }
    except Exception as e:
        return {"pool": "Nanopool", "status": "error", "error": str(e)}
    return {"pool": "Nanopool", "status": "offline"}

def format_hashrate(h):
    if h >= 1000000:
        return f"{h/1000000:.2f} MH/s"
    elif h >= 1000:
        return f"{h/1000:.2f} KH/s"
    else:
        return f"{h:.2f} H/s"

def format_xmr(amount):
    return f"{amount:.8f} XMR"

def format_usd(xmr_amount, xmr_price=155):
    return f"${xmr_amount * xmr_price:.4f} USD"

def calculate_time_to_payout(balance, hashrate, threshold):
    if hashrate == 0:
        return "∞"
    remaining = threshold - balance
    if remaining <= 0:
        return "Ready!"
    hashes_per_day = hashrate * 86400
    xmr_per_day = hashes_per_day / 1500000000000
    days = remaining / xmr_per_day if xmr_per_day > 0 else 999999
    if days < 1:
        return f"{days*24:.1f} hours"
    elif days < 30:
        return f"{days:.1f} days"
    else:
        return f"{days/30:.1f} months"

def print_header():
    print("=" * 100)
    print(f"{'XMR MINING MONITOR':^100}")
    print(f"{'Wallet: ' + WALLET[:20] + '...' + WALLET[-20:]:^100}")
    print(f"{'Updated: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'):^100}")
    print("=" * 100)

def print_pool_stats(stats):
    pool = stats.get("pool", "Unknown")
    status = stats.get("status", "unknown")
    
    print(f"\n┌─ {pool} Pool " + "─" * (90 - len(pool)))
    
    if status == "online":
        print(f"│ Status:          ✅ ONLINE")
        print(f"│ Hashrate:        {format_hashrate(stats.get('hashrate', 0))}")
        print(f"│ Balance:         {format_xmr(stats.get('balance', 0))} ({format_usd(stats.get('balance', 0))})")
        print(f"│ Total Paid:      {format_xmr(stats.get('paid', 0))} ({format_usd(stats.get('paid', 0))})")
        print(f"│ Active Workers:  {stats.get('workers', 0)}")
        
        if 'valid_shares' in stats:
            valid = stats.get('valid_shares', 0)
            invalid = stats.get('invalid_shares', 0)
            total = valid + invalid
            if total > 0:
                acceptance = (valid / total) * 100
                print(f"│ Valid Shares:    {valid} ({acceptance:.2f}% acceptance)")
                print(f"│ Invalid Shares:  {invalid}")
        
        threshold = 0.1 if pool == "SupportXMR" else (0.004 if pool == "MineXMR" else 0.3)
        progress = (stats.get('balance', 0) / threshold) * 100
        print(f"│ Threshold:       {format_xmr(threshold)} ({progress:.2f}% reached)")
        print(f"│ Time to Payout:  {calculate_time_to_payout(stats.get('balance', 0), stats.get('hashrate', 0), threshold)}")
        
    elif status == "error":
        print(f"│ Status:          ⚠️  ERROR")
        print(f"│ Error:           {stats.get('error', 'Unknown error')}")
    else:
        print(f"│ Status:          ⭕ OFFLINE")
    
    print("└" + "─" * 99)

def print_summary(all_stats):
    total_hashrate = sum(s.get('hashrate', 0) for s in all_stats if s.get('status') == 'online')
    total_balance = sum(s.get('balance', 0) for s in all_stats if s.get('status') == 'online')
    total_paid = sum(s.get('paid', 0) for s in all_stats if s.get('status') == 'online')
    total_workers = sum(s.get('workers', 0) for s in all_stats if s.get('status') == 'online')
    active_pools = sum(1 for s in all_stats if s.get('status') == 'online')
    
    print("\n" + "=" * 100)
    print(f"{'SUMMARY':^100}")
    print("=" * 100)
    print(f"│ Total Hashrate:     {format_hashrate(total_hashrate)}")
    print(f"│ Total Balance:      {format_xmr(total_balance)} ({format_usd(total_balance)})")
    print(f"│ Total Paid:         {format_xmr(total_paid)} ({format_usd(total_paid)})")
    print(f"│ Total Workers:      {total_workers}")
    print(f"│ Active Pools:       {active_pools}/3")
    print(f"│ Total Earnings:     {format_xmr(total_balance + total_paid)} ({format_usd(total_balance + total_paid)})")
    print("=" * 100)

def print_estimated_earnings(total_hashrate):
    if total_hashrate == 0:
        return
    
    xmr_per_day = (total_hashrate * 86400) / 1500000000000
    
    print(f"\n{'ESTIMATED EARNINGS':^100}")
    print("─" * 100)
    print(f"│ Per Day:      {format_xmr(xmr_per_day)} ({format_usd(xmr_per_day)})")
    print(f"│ Per Week:     {format_xmr(xmr_per_day * 7)} ({format_usd(xmr_per_day * 7)})")
    print(f"│ Per Month:    {format_xmr(xmr_per_day * 30)} ({format_usd(xmr_per_day * 30)})")
    print(f"│ Per Year:     {format_xmr(xmr_per_day * 365)} ({format_usd(xmr_per_day * 365)})")
    print("─" * 100)

def main():
    print("🚀 Starting XMR Mining Monitor...")
    print(f"📊 Checking every {CHECK_INTERVAL} seconds")
    print(f"💼 Wallet: {WALLET[:20]}...{WALLET[-20:]}\n")
    
    iteration = 0
    
    while True:
        try:
            iteration += 1
            clear_screen()
            
            print_header()
            
            supportxmr = get_supportxmr_stats()
            time.sleep(1)
            minexmr = get_minexmr_stats()
            time.sleep(1)
            nanopool = get_nanopool_stats()
            
            all_stats = [supportxmr, minexmr, nanopool]
            
            for stats in all_stats:
                print_pool_stats(stats)
            
            print_summary(all_stats)
            
            total_hashrate = sum(s.get('hashrate', 0) for s in all_stats if s.get('status') == 'online')
            print_estimated_earnings(total_hashrate)
            
            print(f"\n{'⏰ Next update in ' + str(CHECK_INTERVAL) + ' seconds... (Iteration #' + str(iteration) + ')':^100}")
            print(f"{'Press Ctrl+C to stop':^100}\n")
            
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped by user.")
            break
        except Exception as e:
            print(f"\n❌ Error in main loop: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()
