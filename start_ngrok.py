import time
from pyngrok import ngrok

def start_tunnel():
    print("Starting ngrok tunnel to port 5000...")
    public_url = ngrok.connect(5000)
    print(f"\n==================================================")
    print(f"YOUR NEW PUBLIC URL IS: {public_url.public_url}")
    print(f"==================================================\n")
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Closing tunnel...")
        ngrok.kill()

if __name__ == "__main__":
    start_tunnel()
