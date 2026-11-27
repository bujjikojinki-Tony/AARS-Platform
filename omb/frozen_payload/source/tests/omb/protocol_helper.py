import json, subprocess, sys, os, selectors

def exchange(messages, env=None):
    p = subprocess.Popen([sys.executable, '-m', 'aars_omb.server'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env or os.environ.copy())
    answers=[]
    try:
        for message in messages:
            if message['method']=='initialize':
                message={**message,'params':{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'regression','version':'1'}}}
            p.stdin.write(json.dumps({'jsonrpc':'2.0',**message})+'\n'); p.stdin.flush()
            if 'id' in message:
                with selectors.DefaultSelector() as sel:
                    sel.register(p.stdout, selectors.EVENT_READ)
                    if not sel.select(10): raise TimeoutError('MCP response timed out')
                answers.append(json.loads(p.stdout.readline()))
        p.stdin.close();p.wait(timeout=10)
        assert p.returncode==0
        return answers
    finally:
        if p.poll() is None: p.kill();p.wait()
        p.stdout.close();p.stderr.close()
