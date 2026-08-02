import time
import sys
import os
import requests
import joblib
import pandas as pd
import numpy as np
import argparse
import ipaddress
from scapy.all import rdpcap, IP, IPv6, TCP, UDP, DNS, DNSRR, sniff
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# ── DNS-based IP → App mapping (snoops DNS responses in real time) ──────────
# This is the most reliable way to identify modern encrypted apps.
# When the OS resolves 'googlevideo.com', we record that IP = YouTube.
DNS_APP_MAP = {
    # YouTube / Google Video
    'googlevideo.com':       'YouTube',
    'youtube.com':           'YouTube',
    'ytimg.com':             'YouTube',
    'youtu.be':              'YouTube',
    'ggpht.com':             'YouTube',
    # Netflix
    'netflix.com':           'Netflix',
    'nflxvideo.net':         'Netflix',
    'nflximg.net':           'Netflix',
    'nflxext.com':           'Netflix',
    # Spotify
    'spotify.com':           'Spotify',
    'scdn.co':               'Spotify',
    'spotifycdn.com':        'Spotify',
    # Discord
    'discord.com':           'Discord',
    'discordapp.com':        'Discord',
    'discordapp.net':        'Discord',
    # Facebook / Instagram / WhatsApp
    'facebook.com':          'Facebook',
    'fbcdn.net':             'Facebook',
    'instagram.com':         'Instagram',
    'cdninstagram.com':      'Instagram',
    'whatsapp.com':          'WhatsApp',
    'whatsapp.net':          'WhatsApp',
    'web.whatsapp.com':      'WhatsApp',
    'mmg.whatsapp.net':      'WhatsApp',
    # Microsoft / Teams
    'teams.microsoft.com':   'Teams',
    'skype.com':             'Skype',
    'live.com':              'Microsoft',
    # Twitch
    'twitch.tv':             'Twitch',
    'twitchsvc.net':         'Twitch',
    'jtvnw.net':             'Twitch',
    # Zoom
    'zoom.us':               'Zoom',
    'zoomgov.com':           'Zoom',
    # Google
    'googleapis.com':        'Google',
    'gstatic.com':           'Google',
    'google.com':            'Google',
    # Cloudflare (generic)
    'cloudflare.com':        'Cloudflare',
    'cloudflarestream.com':  'Cloudflare',
    # WhatsApp
    'whatsapp.com':          'WhatsApp',
    'whatsapp.net':          'WhatsApp',
}

# Live IP -> App label cache (populated by sniffing DNS responses)
dns_ip_cache = {}  # ip_string -> label

# Statically known subnets for major apps (solves the DoH/Encrypted DNS problem)
KNOWN_SUBNETS = {
    'YouTube': [
        '142.250.0.0/15', '172.217.0.0/16', '216.58.192.0/19', '74.125.0.0/16',
        '2001:4860::/32', '2404:6800::/32', '2405:200::/32', '2607:f8b0::/32', 
        '2800:3f0::/32', '2a00:1450::/32', '2c0f:fb50::/32'  # Global Google IPv6
    ],
    'Facebook': [
        '157.240.0.0/16', '31.13.24.0/21', '69.63.176.0/20', '69.171.224.0/19',
        '74.119.76.0/22', '103.4.96.0/22', '129.134.0.0/16', '173.252.64.0/18', 
        '204.15.20.0/22', '163.70.0.0/16',
        '2a03:2880::/32', '2620:0:1c00::/40', '2620:107:c000::/40', '2404:f340::/32'
    ],
    'Cloudflare': [
        '104.16.0.0/12', '162.159.0.0/16', '2606:4700::/32'
    ]
}

# Pre-compile the networks for fast lookup
COMPILED_SUBNETS = {}
for app, subnets in KNOWN_SUBNETS.items():
    COMPILED_SUBNETS[app] = [ipaddress.ip_network(n) for n in subnets]

def get_app_by_ip_subnet(ip_str):
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        for app, nets in COMPILED_SUBNETS.items():
            for net in nets:
                if ip_obj in net:
                    return app
    except ValueError:
        pass
    return None

def dns_lookup(hostname: str):
    """Return app label for a hostname, or None if not in our map."""
    hostname = hostname.rstrip('.').lower()
    for pattern, label in DNS_APP_MAP.items():
        if hostname == pattern or hostname.endswith('.' + pattern):
            return label
    return None

def process_dns_packet(pkt):
    """Sniff DNS responses and populate dns_ip_cache."""
    try:
        if DNS not in pkt or pkt[DNS].qr != 1:  # only DNS responses
            return
        for i in range(pkt[DNS].ancount):
            rr = pkt[DNS].an[i]
            if rr.type in (1, 28):  # A or AAAA record
                name = rr.rrname.decode('utf-8', errors='ignore').rstrip('.')
                ip   = rr.rdata if isinstance(rr.rdata, str) else rr.rdata.decode('utf-8', errors='ignore')
                label = dns_lookup(name)
                if label and ip not in dns_ip_cache:
                    dns_ip_cache[ip] = label
    except Exception:
        pass

API_URL = os.environ.get("API_URL", "http://localhost:3001/telemetry")

def send_log(msg, is_alert=False):
    try:
        requests.post(API_URL, json={"action": "log", "message": msg, "isAlert": is_alert})
        print(msg)
    except:
        pass

def send_stats(total_packets, active_flows, pps, bandwidth_mbps, app_counts):
    try:
        apps_payload = [{"name": k, "count": v} for k, v in app_counts.items()]
        requests.post(API_URL, json={
            "action": "stats",
            "totalPackets": total_packets,
            "activeFlows": active_flows,
            "pps": pps,
            "bandwidth": bandwidth_mbps,
            "apps": apps_payload
        })
    except:
        pass

# Global state for Live Mode
live_flows = defaultdict(list)
live_flow_start_times = {}
live_total_packets = 0
live_total_bytes = 0
live_app_counts = defaultdict(int)
live_start_time = time.time()
live_packet_batch = 0
global_clf = None

def process_packet(pkt):
    # Always process DNS first to build IP->app cache
    process_dns_packet(pkt)
    global live_total_packets, live_total_bytes, live_start_time, live_packet_batch, global_clf
    
    if IP in pkt or IPv6 in pkt:
        layer = IP if IP in pkt else IPv6
        src_ip = pkt[layer].src
        dst_ip = pkt[layer].dst
        
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
        pkt_time = float(time.time()) # Real current time
        
        if flow_tuple not in live_flow_start_times:
            live_flow_start_times[flow_tuple] = pkt_time
            send_log(f"New Live Flow: {src_ip}:{src_port} <-> {dst_ip}:{dst_port}")
            
        direction = 1 if flow_tuple[0] == f"{src_ip}:{src_port}" else -1
        
        live_flows[flow_tuple].append({
            "size": pkt_size * direction,
            "time": pkt_time
        })
        
        live_total_packets += 1
        live_packet_batch += 1
        live_total_bytes += pkt_size
        
        flow_len = len(live_flows[flow_tuple])
        # BUG FIX 1: Classify every 50-packet CHUNK (not just the first 50).
        # This makes continuous UDP/QUIC streams (YouTube) classify repeatedly.
        # BUG FIX 2: Clear the flow after classification so RAM doesn't grow forever.
        if flow_len == 50:
            pkts_chunk = live_flows[flow_tuple]
            sizes = [p["size"] for p in pkts_chunk]
            iats, last_t = [], pkts_chunk[0]["time"]
            for p in pkts_chunk:
                iats.append(int((p["time"] - last_t) * 1_000_000))
                last_t = p["time"]

            # ── Step 1: Check DNS cache for certain identification ──────────
            dns_label = dns_ip_cache.get(src_ip) or dns_ip_cache.get(dst_ip)
            
            # ── Step 1.5: Check Static IP Subnets (Bypasses DoH Encryption) ──
            if not dns_label:
                dns_label = get_app_by_ip_subnet(src_ip) or get_app_by_ip_subnet(dst_ip)

            # --- CRITICAL FIX: DIFFERENTIATE YOUTUBE FROM GOOGLE BACKGROUND ---
            # Google uses the same IPs for everything (Search, Drive, Sync, YouTube).
            # We must use chunk size to know if it's actually a video stream!
            chunk_total_bytes = sum(abs(s) for s in sizes)
            if dns_label == 'YouTube':
                if chunk_total_bytes > 40000:
                    dns_label = 'YouTube'
                else:
                    dns_label = 'Google Background'
            elif dns_label == 'Facebook':
                if chunk_total_bytes > 40000:
                    dns_label = 'Facebook'
                else:
                    dns_label = 'Meta Background'

            if dns_label:
                # DNS/IP-identified traffic: 100% accurate, no ML needed
                prediction = dns_label
                # HIDE BACKGROUND TRAFFIC FROM DASHBOARD COMPLETELY
                if prediction not in ('Google Background', 'Meta Background'):
                    send_log(f"IP/DNS Classification: Flow {src_ip} <-> {dst_ip} is {prediction}")
                    live_app_counts[prediction] += 1
            else:
                # ── Step 2: Fall back to ML for legacy protocols ────────────
                row = {}
                for i in range(50): row[f'size_{i}'] = sizes[i]
                for i in range(50): row[f'iat_{i}']  = iats[i]
                df_row = pd.DataFrame([row])
                try:
                    prediction = global_clf.predict(df_row)[0]
                    # Suppress modern-app labels from ML (they'll be caught by DNS)
                    # ML is only trusted for legacy protocol classifications
                    suppressed = {'youtube', 'netflix', 'spotify', 'discord',
                                  'instagram', 'twitch', 'zoom', 'teams', 'whatsapp'}
                    if prediction.lower() not in suppressed:
                        send_log(f"ML Classification: Flow {src_ip} is {prediction}")
                        live_app_counts[prediction] += 1
                    prediction = None
                except Exception:
                    prediction = None

            if prediction:
                live_app_counts[prediction] += 1

            # Clear so next 50 packets form a fresh chunk
            live_flows[flow_tuple] = []
            live_flow_start_times[flow_tuple] = pkt_time
        
        elapsed = time.time() - live_start_time
        if elapsed >= 1.0:
            pps = int(live_packet_batch / elapsed) if elapsed > 0 else 0
            bandwidth = (live_total_bytes * 8) / (elapsed * 1000000) if elapsed > 0 else 0
            
            send_stats(live_total_packets, len(live_flows), pps, round(bandwidth, 2), live_app_counts)
            
            live_start_time = time.time()
            live_packet_batch = 0
            live_total_bytes = 0
            live_app_counts.clear()  # BUG FIX: Reset counts so apps vanish when closed!

def run_demo_mode(clf):
    pcap_file = "test_dpi.pcap"
    if not os.path.exists(pcap_file):
        send_log(f"Error: {pcap_file} not found!", True)
        return

    send_log(f"Reading packets from {pcap_file} (DEMO MODE)...")
    packets = rdpcap(pcap_file)
    
    # State tracking
    flows = defaultdict(list)
    flow_start_times = {}
    
    total_packets = 0
    total_bytes = 0
    app_counts = defaultdict(int)
    
    while True:
        start_time = time.time()
        packet_batch = 0
        
        for pkt in packets:
            time.sleep(0.05) # Playback speed
            
            # BUG FIX 4: Demo mode also needs IPv6 support (was IPv4-only)
            if IP in pkt or IPv6 in pkt:
                layer = IP if IP in pkt else IPv6
                src_ip = pkt[layer].src
                dst_ip = pkt[layer].dst
                
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
                    send_log(f"New flow: {src_ip}:{src_port} <-> {dst_ip}:{dst_port}")
                    
                direction = 1 if flow_tuple[0] == f"{src_ip}:{src_port}" else -1
                
                flows[flow_tuple].append({
                    "size": pkt_size * direction,
                    "time": pkt_time
                })
                
                total_packets += 1
                packet_batch += 1
                total_bytes += pkt_size
                
                flow_len = len(flows[flow_tuple])
                if flow_len > 0 and (flow_len % 10 == 0 or flow_len == 50):
                    sizes = []
                    iats = []
                    last_t = flow_start_times[flow_tuple]
                    
                    for p in flows[flow_tuple][:50]:
                        sizes.append(p["size"])
                        iat = int((p["time"] - last_t) * 1000000)
                        iats.append(iat)
                        last_t = p["time"]
                        
                    while len(sizes) < 50: sizes.append(0)
                    while len(iats) < 50: iats.append(0)
                    
                    # BUG FIX 3 (demo): Same fix — only pass 100 features
                    row = {}
                    for i in range(50): row[f'size_{i}'] = sizes[i]
                    for i in range(50): row[f'iat_{i}'] = iats[i]
                    
                    df_row = pd.DataFrame([row])
                    try:
                        prediction = clf.predict(df_row)[0]
                        send_log(f"ML Classification: Flow {src_ip} is {prediction}")
                        app_counts[prediction] += 1
                    except Exception as e:
                        pass
                
                if packet_batch >= 10:
                    elapsed = time.time() - start_time
                    pps = int(packet_batch / elapsed) if elapsed > 0 else 0
                    bandwidth = (total_bytes * 8) / (elapsed * 1000000) if elapsed > 0 else 0
                    
                    send_stats(total_packets, len(flows), pps, round(bandwidth, 2), app_counts)
                    
                    start_time = time.time()
                    packet_batch = 0
                    total_bytes = 0

def main():
    global global_clf
    parser = argparse.ArgumentParser(description='Python DPI Bridge')
    parser.add_argument('--mode', choices=['demo', 'live'], default='demo', help='Execution mode')
    args = parser.parse_args()

    send_log(f"Initializing Python DPI Engine in {args.mode.upper()} mode...")
    
    # Check for the model
    if os.path.exists("real_rf_model.joblib"):
        global_clf = joblib.load("real_rf_model.joblib")
        send_log("Loaded REAL-WORLD ML Model (real_rf_model.joblib)")
    elif os.path.exists("rf_model.joblib"):
        global_clf = joblib.load("rf_model.joblib")
        send_log("Loaded Synthetic ML Model (rf_model.joblib)")
    else:
        send_log("Error: No ML Model found.", True)
        return

    if args.mode == 'demo':
        run_demo_mode(global_clf)
    elif args.mode == 'live':
        send_log("Starting LIVE packet capture on default Wi-Fi interface! (Requires Admin)")
        # Start sniffing endlessly
        sniff(prn=process_packet, store=False)

if __name__ == "__main__":
    main()
