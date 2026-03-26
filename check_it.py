import os

files = os.listdir('.')
files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
print("Latest files:", files[:10])

if 'last_audit.txt' in files:
    print("last_audit.txt:", open('last_audit.txt').read())
    
if 'ws_output.log' in files:
    print("ws_output.log:")
    with open('ws_output.log') as f:
        print(f.read())
