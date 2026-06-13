import csv
import random
import os

def generate_dummy_data(filename):
    apps = ['YouTube', 'Facebook', 'Netflix', 'Discord', 'Cloudflare']
    
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Header
        header = ['app_type']
        for i in range(50): header.append(f'size_{i}')
        for i in range(50): header.append(f'iat_{i}')
        writer.writerow(header)
        
        # Generate 1000 rows
        for _ in range(1000):
            app = random.choice(apps)
            row = [app]
            
            # Simulate realistic traffic profiles
            for i in range(50):
                if app in ['YouTube', 'Netflix']:
                    # Video streaming: Massive downloads (MTU size), small ACKs uploaded
                    direction = -1 if random.random() > 0.1 else 1
                    size = random.gauss(1400, 100) if direction == -1 else random.gauss(64, 10)
                    iat = random.gauss(5000, 1000) # Fast, steady packets
                elif app == 'Discord':
                    # VoIP/Chat: Small symmetrical packets, highly consistent timing (20ms)
                    direction = 1 if random.random() > 0.5 else -1
                    size = random.gauss(150, 20)
                    iat = random.gauss(20000, 500) # ~20ms ping
                elif app == 'Facebook':
                    # Web Browsing: Highly variable bursts
                    direction = -1 if random.random() > 0.3 else 1
                    size = random.gauss(800, 400)
                    iat = random.expovariate(1/50000) # Exponential distribution (bursty)
                else: # Cloudflare
                    # General HTTPS
                    direction = -1 if random.random() > 0.5 else 1
                    size = random.gauss(600, 300)
                    iat = random.gauss(30000, 15000)
                
                # Ensure physical limits
                size = max(40, min(1500, abs(int(size)))) * direction
                iat = max(0, int(iat))
                
                row.append(size)
                
            # Inter-arrival times
            for i in range(50):
                row.append(iat)
            
            writer.writerow(row)
            
    print(f"Generated dummy dataset with 1000 rows at {filename}")

if __name__ == '__main__':
    generate_dummy_data('features.csv')
