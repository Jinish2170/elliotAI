import multiprocessing as mp, pickle, base64, sys, os
if len(sys.argv) == 1:
    m = mp.Manager()
    q = m.Queue()
    q.put('hello from proxy')
    p = base64.b64encode(pickle.dumps(q)).decode()
    os.environ['Q'] = p
    os.system(sys.executable + ' ' + sys.argv[0] + ' child')
else:
    q = pickle.loads(base64.b64decode(os.environ['Q']))
    print(q.get())
