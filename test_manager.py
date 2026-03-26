import multiprocessing as mp
import subprocess
import sys
import os
import pickle
import base64

if __name__ == '__main__':
    if len(sys.argv) == 1:
        mp.current_process().authkey = b'mysecret'
        manager = mp.Manager()
        q = manager.Queue()
        q.put('hello from queue')
        
        # Serialize simply by pickling the proxy object!
        serialized = base64.b64encode(pickle.dumps(q)).decode()
        
        env = os.environ.copy()
        env['TEST_Q'] = serialized
        env['TEST_AUTHKEY'] = base64.b64encode(mp.current_process().authkey).decode()
        
        # run child
        cmd = [sys.executable, sys.argv[0], 'child']
        subprocess.run(cmd, env=env)
    else:
        authkey = base64.b64decode(os.environ['TEST_AUTHKEY'])
        mp.current_process().authkey = authkey
        q = pickle.loads(base64.b64decode(os.environ['TEST_Q']))
        with open('test_manager_out.txt', 'w') as f:
            f.write(q.get())
