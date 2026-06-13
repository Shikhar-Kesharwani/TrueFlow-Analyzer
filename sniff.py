import socket
import struct
import sys
import time

def main():
    try:
        # Get the local IP address
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        # Create a raw socket and bind it to the public interface
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)
        s.bind((local_ip, 0))
        
        # Include IP headers
        s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        
        # Receive all packages
        s.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)
        
    except PermissionError:
        print("ERROR: Administrator privileges are required to capture live packets on Windows.", file=sys.stderr)
        print("Please open a new PowerShell or Command Prompt as Administrator and try again.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Failed to create raw socket: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Capturing live traffic on {local_ip}...", file=sys.stderr)
    print("Press Ctrl+C to stop.", file=sys.stderr)
    print("-" * 50, file=sys.stderr)
    
    # Write PCAP Global Header to stdout (binary)
    # Magic number, version 2.4, timezone 0, sigfigs 0, snaplen 65535, linktype Ethernet (1)
    pcap_global_header = struct.pack('<IHHIIII', 0xa1b2c3d4, 2, 4, 0, 0, 65535, 1)
    sys.stdout.buffer.write(pcap_global_header)
    sys.stdout.buffer.flush()

    # Fake Ethernet header (14 bytes) since raw IP sockets on Windows don't capture Ethernet frames
    # Dst MAC (6) + Src MAC (6) + IPv4 EtherType (0x0800)
    fake_eth_header = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00'

    try:
        while True:
            # Receive a packet
            packet, _ = s.recvfrom(65535)
            
            # Combine fake ethernet header and the captured IP packet
            full_packet = fake_eth_header + packet
            
            # Create PCAP packet header
            t = time.time()
            ts_sec = int(t)
            ts_usec = int((t - ts_sec) * 1000000)
            incl_len = len(full_packet)
            orig_len = len(full_packet)
            
            pcap_packet_header = struct.pack('<IIII', ts_sec, ts_usec, incl_len, orig_len)
            
            # Write to stdout
            sys.stdout.buffer.write(pcap_packet_header)
            sys.stdout.buffer.write(full_packet)
            sys.stdout.buffer.flush()
            
    except KeyboardInterrupt:
        print("\nStopping capture.", file=sys.stderr)
        # Turn off promiscuous mode
        s.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)
        sys.exit(0)

if __name__ == '__main__':
    main()
