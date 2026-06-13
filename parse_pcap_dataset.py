import os
import re
import pandas as pd
from scapy.all import IP, TCP, UDP
from scapy.utils import PcapReader
from collections import defaultdict

DATASET_DIR = "dataset"
OUTPUT_CSV = "real_features.csv"

def extract_flow_features(pcap_path, label):
    print(f"  Parsing: {os.path.basename(pcap_path)} -> Label: {label}")
    
    flows = defaultdict(list)
    flow_start_times = {}
    rows = []
    
    try:
        with PcapReader(pcap_path) as pcap_reader:
            for pkt in pcap_reader:
                if IP in pkt:
                    src_ip = pkt[IP].src
                    dst_ip = pkt[IP].dst
                    
                    src_port = 0
                    dst_port = 0
                    if TCP in pkt:
                        src_port = pkt[TCP].sport
                        dst_port = pkt[TCP].dport
                    elif UDP in pkt:
                        src_port = pkt[UDP].sport
                        dst_port = pkt[UDP].dport
                        
                    flow_tuple = tuple(sorted([f"{src_ip}:{src_port}", f"{dst_ip}:{dst_port}"]))
                    pkt_size = len(pkt)
                    pkt_time = float(pkt.time)
                    
                    if flow_tuple not in flow_start_times:
                        flow_start_times[flow_tuple] = pkt_time
                        
                    direction = 1 if flow_tuple[0] == f"{src_ip}:{src_port}" else -1
                    
                    flows[flow_tuple].append({
                        "size": pkt_size * direction,
                        "time": pkt_time
                    })
                    
                    flow_len = len(flows[flow_tuple])
                    if flow_len == 50:
                        sizes = []
                        iats = []
                        last_t = flow_start_times[flow_tuple]
                        
                        for p in flows[flow_tuple][:50]:
                            sizes.append(p["size"])
                            iat = int((p["time"] - last_t) * 1000000)
                            iats.append(iat)
                            last_t = p["time"]
                            
                        row = {'app_type': label}
                        for i in range(50): row[f'size_{i}'] = sizes[i]
                        for i in range(50): row[f'iat_{i}'] = iats[i]
                        rows.append(row)
                        
                        # RAM Optimization: Stop tracking this flow once we hit 50 packets
                        del flows[flow_tuple]
                        
    except Exception as e:
        print(f"  [!] Error reading PCAP: {e}")
                
    return rows

def main():
    print("========================================")
    print("      REAL PCAP DATASET PARSER (RAM OPTIMIZED)")
    print("========================================")
    
    if not os.path.exists(DATASET_DIR):
        print(f"Error: {DATASET_DIR} directory not found.")
        return

    all_data = []
    files_found = 0
    
    for file in os.listdir(DATASET_DIR):
        if file.endswith(".pcap") or file.endswith(".pcapng"):
            files_found += 1
            # Infer label (e.g., 'skype_chat1.pcap' -> 'skype', 'AIMchat1.pcapng' -> 'aimchat')
            base_name = file.replace('.pcapng', '').replace('.pcap', '')
            label = re.split(r'[_\\d]', base_name)[0].lower()
            if not label: 
                label = "unknown"
                
            pcap_path = os.path.join(DATASET_DIR, file)
            flow_data = extract_flow_features(pcap_path, label)
            all_data.extend(flow_data)
            
            # Save incrementally to prevent computer from running out of RAM
            if len(all_data) > 5000:
                print(f"  [+] Saving checkpoint of {len(all_data)} flows...")
                df = pd.DataFrame(all_data)
                mode = 'a' if os.path.exists(OUTPUT_CSV) else 'w'
                header = False if mode == 'a' else True
                df.to_csv(OUTPUT_CSV, mode=mode, header=header, index=False)
                all_data = [] # clear RAM

    # Save any remaining data
    if all_data:
        df = pd.DataFrame(all_data)
        mode = 'a' if os.path.exists(OUTPUT_CSV) else 'w'
        header = False if mode == 'a' else True
        df.to_csv(OUTPUT_CSV, mode=mode, header=header, index=False)

    if files_found == 0:
        print(f"\\nNo .pcap files found in {DATASET_DIR}/.")
        return

    print(f"\\n[SUCCESS] Extraction complete!")
    print(f"[SUCCESS] Saved to {OUTPUT_CSV}")
    print("You can now run: python train_real_model.py")

if __name__ == "__main__":
    if os.path.exists(OUTPUT_CSV):
        os.remove(OUTPUT_CSV)
    main()
