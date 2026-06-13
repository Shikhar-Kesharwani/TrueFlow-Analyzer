import os
import pandas as pd
from scapy.all import IP, IPv6, TCP, UDP
from scapy.utils import PcapReader
from collections import defaultdict

INPUT_PCAP       = "dataset/youtube_modern.pcap"
OUTPUT_CSV       = "modern_features.csv"
PACKET_THRESHOLD = 50
MIN_FLOW_BYTES   = 50 * 1024 * 1024  # 50 MB minimum to be considered a "video stream"

def main():
    print("=" * 60)
    print("   HEAVY-FLOW YOUTUBE EXTRACTOR (QUIC/UDP BYPASS)")
    print("   Step 1: Find flows > 50 MB (Guaranteed video streams)")
    print("   Step 2: Chunk ONLY those massive flows")
    print("=" * 60)

    if not os.path.exists(INPUT_PCAP):
        print(f"[!] File not found: {INPUT_PCAP}")
        return

    # ── PASS 1: Identify Massive Flows by Byte Count ──────
    print("\n[Pass 1/2] Scanning for massive flows (>50 MB)...")
    flow_bytes = defaultdict(int)
    total_pkts = 0

    with PcapReader(INPUT_PCAP) as reader:
        for pkt in reader:
            total_pkts += 1
            if total_pkts % 500000 == 0:
                print(f"    Scanned {total_pkts:,} pkts...")

            layer = IP if IP in pkt else IPv6 if IPv6 in pkt else None
            if not layer: continue

            sp, dp = 0, 0
            if TCP in pkt:   sp, dp = pkt[TCP].sport, pkt[TCP].dport
            elif UDP in pkt: sp, dp = pkt[UDP].sport, pkt[UDP].dport
            else: continue

            src_ip, dst_ip = pkt[layer].src, pkt[layer].dst
            flow_tuple = tuple(sorted([f"{src_ip}:{sp}", f"{dst_ip}:{dp}"]))
            flow_bytes[flow_tuple] += len(pkt)

    # Filter flows that downloaded more than 50 MB
    massive_flows = {f for f, b in flow_bytes.items() if b > MIN_FLOW_BYTES}

    print(f"\n  Found {len(massive_flows)} massive video flows:")
    for f in massive_flows:
        print(f"    {f[0]} <-> {f[1]} ({flow_bytes[f] / (1024*1024):.1f} MB)")

    if not massive_flows:
        print("\n[!] No flows > 50 MB found. Cannot isolate video stream.")
        return

    # ── PASS 2: Chunk ONLY the massive video flows ───
    print("\n[Pass 2/2] Chunking massive flows into 50-pkt segments...")
    flows = defaultdict(list)
    rows = []
    total_pkts = 0

    with PcapReader(INPUT_PCAP) as reader:
        for pkt in reader:
            total_pkts += 1
            if total_pkts % 500000 == 0:
                print(f"    Processed {total_pkts:,} pkts... Chunks: {len(rows):,}")

            layer = IP if IP in pkt else IPv6 if IPv6 in pkt else None
            if not layer: continue

            sp, dp = 0, 0
            if TCP in pkt:   sp, dp = pkt[TCP].sport, pkt[TCP].dport
            elif UDP in pkt: sp, dp = pkt[UDP].sport, pkt[UDP].dport
            else: continue

            src_ip, dst_ip = pkt[layer].src, pkt[layer].dst
            flow_tuple = tuple(sorted([f"{src_ip}:{sp}", f"{dst_ip}:{dp}"]))

            if flow_tuple not in massive_flows:
                continue

            direction = 1 if flow_tuple[0] == f"{src_ip}:{sp}" else -1
            flows[flow_tuple].append({"size": len(pkt) * direction, "time": float(pkt.time)})

            if len(flows[flow_tuple]) == PACKET_THRESHOLD:
                pkts = flows[flow_tuple]
                sizes = [p["size"] for p in pkts]
                iats, last_t = [], pkts[0]["time"]
                for p in pkts:
                    iats.append(int((p["time"] - last_t) * 1_000_000))
                    last_t = p["time"]

                row = {'app_type': 'youtube'}
                for i in range(PACKET_THRESHOLD): row[f'size_{i}'] = sizes[i]
                for i in range(PACKET_THRESHOLD): row[f'iat_{i}']  = iats[i]
                rows.append(row)
                flows[flow_tuple] = []  # clear for next chunk

    print(f"\n  Extracted {len(rows):,} massive video chunks.")

    if rows:
        print(f"\n[Saving] Writing to {OUTPUT_CSV}...")
        df = pd.DataFrame(rows)
        df.to_csv(OUTPUT_CSV, index=False)
        print(f"[SUCCESS] {len(rows):,} clean YouTube flows saved.")
    else:
        print("\n[!] No chunks extracted.")

if __name__ == "__main__":
    main()
