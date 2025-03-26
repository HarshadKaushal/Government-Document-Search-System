import os

def list_downloads():
    base_dir = 'downloads'
    for root, dirs, files in os.walk(base_dir):
        print(f"\nDirectory: {root}")
        for file in files:
            if file.endswith('.pdf'):
                print(f"- {file}")

if __name__ == "__main__":
    list_downloads()