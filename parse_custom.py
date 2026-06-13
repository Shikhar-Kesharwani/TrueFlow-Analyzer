import os
import re
import pandas as pd
from scapy.all import IP, IPv6, TCP, UDP
from scapy.utils import PcapReader
from collections import defaultdict

DATASET_DIR = "dataset"
OUTPUT_CSV = "real_features.csv"
TARGET_FILES = {"youtube.pcap": "youtube", "idle1.pcap": "idle"}

def extract_flow_features(pcap_path, label):
    print(f"  Parsing: {os.path.basename(pcap_path)} -> Label: {label}")
    flows = defaultdict(list)
    flow_start_times = {}
    rows = []
    
    try:
        with PcapReader(pcap_path) as pcap_reader:
            for pkt in pcap_reader:
                if IP in pkt or IPv6 in pkt:
                    layer = IP if IP in pkt else IPv6
                    src_ip = pkt[layer].src
                    dst_ip = pkt[layer].dst
                    src_port, dst_port = 0, 0
                    if TCP in pkt:
                        src_port, dst_port = pkt[TCP].sport, pkt[TCP].dport
                    elif UDP in pkt:
                        src_port, dst_port = pkt[UDP].sport, pkt[UDP].dport
                        
                    flow_tuple = tuple(sorted([f"{src_ip}:{src_port}", f"{dst_ip}:{dst_port}"]))
                    pkt_size = len(pkt)
                    pkt_time = float(pkt.time)
                    
                    if flow_tuple not in flow_start_times:
                        flow_start_times[flow_tuple] = pkt_time
                        
                    direction = 1 if flow_tuple[0] == f"{src_ip}:{src_port}" else -1
                    flows[flow_tuple].append({"size": pkt_size * direction, "time": pkt_time})
                    
                    if len(flows[flow_tuple]) == 50:
                        sizes, iats = [], []
                        last_t = flow_start_times[flow_tuple]
                        for p in flows[flow_tuple][:50]:
                            sizes.append(p["size"])
                            iats.append(int((p["time"] - last_t) * 1000000))
                            last_t = p["time"]
                            
                        row = {'app_type': label}
                        for i in range(50): row[f'size_{i}'] = sizes[i]
                        for i in range(50): row[f'iat_{i}'] = iats[i]
                        rows.append(row)
                        del flows[flow_tuple]
    except Exception as e:
        print(f"  [!] Error reading PCAP: {e}")
    return rows

def main():
    print("========================================")
    print("      APPENDING MODERN 2026 DATA")
    print("========================================")
    all_data = []
    
    for file, label in TARGET_FILES.items():
        pcap_path = os.path.join(DATASET_DIR, file)
        if os.path.exists(pcap_path):
            flow_data = extract_flow_features(pcap_path, label)
            all_data.extend(flow_data)
        else:
            print(f"Warning: {file} not found in {DATASET_DIR}")

    if all_data:
        print(f"  [+] Extracted {len(all_data)} modern flows. Appending to existing dataset...")
        df = pd.DataFrame(all_data)
        # Always append (mode='a') without header so we don't destroy the existing 400,000 flows!
        df.to_csv(OUTPUT_CSV, mode='a', header=False, index=False)
        print("[SUCCESS] Modern data appended to real_features.csv!")
    else:
        print("No new flows were extracted.")

if __name__ == "__main__":
    main()
