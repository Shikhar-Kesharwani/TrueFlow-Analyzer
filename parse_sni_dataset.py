import os
import pandas as pd
from scapy.all import IP, IPv6, TCP, UDP
from scapy.utils import PcapReader
from collections import defaultdict

# ──────────────────────────────────────────────
# SNI → App Label mapping
# ──────────────────────────────────────────────
SNI_MAP = {
    'googlevideo.com': 'youtube',
    'youtube.com': 'youtube',
    'ytimg.com': 'youtube',
    'youtu.be': 'youtube',
    'netflix.com': 'netflix',
    'nflxvideo.net': 'netflix',
    'nflximg.net': 'netflix',
    'spotify.com': 'spotify',
    'scdn.co': 'spotify',
    'facebook.com': 'facebook',
    'fbcdn.net': 'facebook',
    'instagram.com': 'instagram',
    'cdninstagram.com': 'instagram',
    'twitch.tv': 'twitch',
    'twitchsvc.net': 'twitch',
    'discord.com': 'discord',
    'discordapp.com': 'discord',
    'zoom.us': 'zoom',
    'teams.microsoft.com': 'teams',
    'skype.com': 'skype',
    'live.com': 'microsoft',
    'microsoft.com': 'microsoft',
    'google.com': 'google',
    'googleapis.com': 'google',
    'gstatic.com': 'google',
}

PACKET_THRESHOLD = 20
INPUT_PCAP      = "dataset/youtube_modern.pcap"
OUTPUT_CSV      = "modern_features.csv"

# ──────────────────────────────────────────────
# Step 1: Extract SNI from TLS Client Hello
# ──────────────────────────────────────────────
def extract_sni(payload: bytes):
    try:
        if len(payload) < 5 or payload[0] != 0x16: return None
        pos = 5 + 1 + 3 + 2 + 32
        if pos >= len(payload): return None
        pos += 1 + payload[pos]
        if pos + 2 >= len(payload): return None
        pos += 2 + int.from_bytes(payload[pos:pos+2], 'big')
        if pos + 1 >= len(payload): return None
        pos += 1 + payload[pos]
        if pos + 2 >= len(payload): return None
        extensions_end = pos + 2 + int.from_bytes(payload[pos:pos+2], 'big')
        pos += 2
        while pos + 4 <= extensions_end and pos + 4 <= len(payload):
            ext_type = int.from_bytes(payload[pos:pos+2], 'big')
            ext_len  = int.from_bytes(payload[pos+2:pos+4], 'big')
            pos += 4
            if ext_type == 0 and pos + 5 <= len(payload):
                name_len = int.from_bytes(payload[pos+3:pos+5], 'big')
                if pos + 5 + name_len <= len(payload):
                    return payload[pos+5:pos+5+name_len].decode('ascii', errors='ignore')
            pos += ext_len
    except Exception:
        pass
    return None

def sni_to_label(sni: str):
    if not sni: return None
    sni = sni.lower()
    for pattern, label in SNI_MAP.items():
        if sni.endswith(pattern): return label
    return None

# ──────────────────────────────────────────────
# Step 2: Build flows and assign SNI labels
# ──────────────────────────────────────────────
def process_pcap(pcap_path):
    print(f"\n[1/3] Reading: {pcap_path}")
    flows        = defaultdict(list)
    flow_times   = {}
    ip_labels    = {}   # IP -> label (maps the whole server to the app)
    total_pkts   = 0

    with PcapReader(pcap_path) as reader:
        for pkt in reader:
            total_pkts += 1
            if total_pkts % 500000 == 0:
                print(f"    Processed {total_pkts:,} packets...")

            layer = IP if IP in pkt else IPv6 if IPv6 in pkt else None
            if not layer: continue

            src_ip, dst_ip = pkt[layer].src, pkt[layer].dst
            sp, dp = 0, 0
            proto = 'other'
            payload = b''

            if TCP in pkt:
                sp, dp = pkt[TCP].sport, pkt[TCP].dport
                proto = 'tcp'
                payload = bytes(pkt[TCP].payload)
            elif UDP in pkt:
                sp, dp = pkt[UDP].sport, pkt[UDP].dport
                proto = 'udp'

            flow_tuple = tuple(sorted([f"{src_ip}:{sp}", f"{dst_ip}:{dp}"])) + (proto,)
            
            if flow_tuple not in flow_times:
                flow_times[flow_tuple] = float(pkt.time)

            # Optimization: Stop keeping packets in RAM once we hit threshold
            if len(flows[flow_tuple]) < PACKET_THRESHOLD:
                direction = 1 if flow_tuple[0] == f"{src_ip}:{sp}" else -1
                flows[flow_tuple].append({"size": len(pkt) * direction, "time": float(pkt.time)})

            # Extract SNI to label the IP (solves the UDP QUIC problem)
            if proto == 'tcp' and dst_ip not in ip_labels and len(payload) > 5:
                sni = extract_sni(payload)
                label = sni_to_label(sni)
                if label:
                    ip_labels[dst_ip] = label
                    ip_labels[src_ip] = label

    print(f"    Packets read   : {total_pkts:,}")
    print(f"    Unique flows   : {len(flows):,}")
    print(f"    Labeled IPs    : {len(ip_labels):,}")
    return flows, flow_times, ip_labels

# ──────────────────────────────────────────────
# Step 3: Extract features for labeled flows
# ──────────────────────────────────────────────
def extract_features(flows, flow_times, ip_labels):
    print(f"\n[2/3] Extracting {PACKET_THRESHOLD}-packet features for labeled flows...")
    rows = []
    label_counts = defaultdict(int)

    for flow_tuple, pkts in flows.items():
        if len(pkts) < PACKET_THRESHOLD: continue

        src_ip = flow_tuple[0].split(':')[0]
        dst_ip = flow_tuple[1].split(':')[0]
        
        # If either IP in the flow belongs to a known server, label it!
        label = ip_labels.get(src_ip) or ip_labels.get(dst_ip)
        if not label: continue

        sizes, iats = [], []
        last_t = flow_times[flow_tuple]
        for p in pkts:
            sizes.append(p["size"])
            iats.append(int((p["time"] - last_t) * 1_000_000))
            last_t = p["time"]

        row = {'app_type': label}
        for i in range(PACKET_THRESHOLD):
            row[f'size_{i}'] = sizes[i]
            row[f'iat_{i}']  = iats[i]
        rows.append(row)
        label_counts[label] += 1

    print("    Flows extracted per app:")
    for app, count in sorted(label_counts.items()):
        print(f"      {app:20s}: {count:,} flows")
    return rows

def main():
    print("=" * 55)
    print("   SNI-BASED MODERN TRAFFIC LABELLER (OPTIMIZED)")
    print("=" * 55)
    flows, flow_times, ip_labels = process_pcap(INPUT_PCAP)
    rows = extract_features(flows, flow_times, ip_labels)

    if rows:
        print(f"\n[3/3] Saving {len(rows):,} modern flows to {OUTPUT_CSV} ...")
        df = pd.DataFrame(rows)
        for i in range(PACKET_THRESHOLD, 50):
            df[f'size_{i}'] = 0
            df[f'iat_{i}']  = 0
        df.to_csv(OUTPUT_CSV, index=False)
        print(f"\n[SUCCESS] Saved to {OUTPUT_CSV}")
    else:
        print("\n[!] No labeled flows extracted.")

if __name__ == "__main__":
    main()
