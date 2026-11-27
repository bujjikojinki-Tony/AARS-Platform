"""Local synthetic MCP adapter. Official SDK transport; optional private SQLite store."""
import json
import sys
import os
from aars_omb.store import Store, task_check
from dataclasses import asdict
from aars_sdk import AARSClient
from aars_core.runtime.config import RuntimeConfig
from aars_core.runtime.platform import build_runtime

TOOLS = [
    {'name':'aars_health','description':'Check isolated AARS runtime health.','inputSchema':{'type':'object','properties':{},'additionalProperties':False}},
    {'name':'aars_graph_certify','description':'Certify a fixed synthetic graph, never real evidence or execution authority.','inputSchema':{'type':'object','properties':{'scenario':{'type':'string','enum':['valid','missing_observation']}},'required':['scenario'],'additionalProperties':False}},
]

def graph():
    c=AARSClient(source_id='omb-synthetic-fixture',source_type='test_fixture')
    o=c.create_observation(subject='reference',payload={'value':10})
    e=c.create_evidence(observations=[o],code='aars.reference.VALUE_HIGH',category='measurement',direction='positive',weight=.8,confidence=.9)
    cl=c.create_claim(evidence=[e],statement='Synthetic condition',scope={'domain':'reference'})
    d=c.create_decision(claims=[cl],level='spot',posture='wait',confidence=.7,rationale='Synthetic review only')
    out=c.create_outcome(decisions=[d],claims=[cl],measurements={'value':12},classification='supported')
    l=c.create_lesson(outcomes=[out],alignment='supported',codes=['DECISION_SUPPORTED'],narrative='Synthetic outcome')
    m=c.create_memory(observations=[o],evidence=[e],claims=[cl],decisions=[d],outcomes=[out],lessons=[l])
    k=c.create_knowledge(lessons=[l],claim='Synthetic knowledge',scope={'domain':'reference'})
    p=c.create_policy(knowledge=[k],rule='Synthetic review',authority='reference.governance',scope={'domain':'reference'})
    return c,(o,e,cl,d,out,l,m,k,p)

STORE_TOOLS = [
    {'name':n,'description':d,'inputSchema':{'type':'object','properties':{'task_id':{'type':'string','pattern':'^OMB-SIM-[A-Za-z0-9_-]{1,64}$'}},'required':['task_id'],'additionalProperties':False}}
    for n,d in [('aars_fixture_store','Persist a fixed synthetic graph for a test task; idempotent.'),('aars_evidence_query','Query synthetic evidence and provenance by task ID.'),('aars_task_objects','Query all synthetic objects for a task ID.')]
]

def call(name,args,store=None):
    if not isinstance(args,dict): raise ValueError('Invalid arguments')
    if name=='aars_health' and not args:
        rt=build_runtime(RuntimeConfig({'core':{'api_version':'1'}}))
        checks=rt.health.run()
        return {'status':rt.health.overall_status(checks),'checks':[asdict(x) for x in checks],'mode':'ISOLATED_IN_MEMORY','execution_authorized':False}
    if name=='aars_graph_certify' and set(args)=={'scenario'} and args['scenario'] in ('valid','missing_observation'):
        c,g=graph(); report=c.certify(g if args['scenario']=='valid' else g[1:])
        return {'mode':'SYNTHETIC_ONLY','execution_authorized':False,'report':report.to_dict()}
    if store is not None and name in {t['name'] for t in STORE_TOOLS} and set(args)=={'task_id'}:
        task=args['task_id']; task_check(task)
        if name=='aars_fixture_store':
            c,g=graph(); result=store.seed(task,c,g)
        else: result=store.query(task,'evidence' if name=='aars_evidence_query' else None)
        return {**result,'mode':'SYNTHETIC_ONLY','execution_authorized':False}
    raise ValueError('Unknown tool or invalid arguments')

class Session:
    """Legacy in-process compatibility helper; never used by the stdio entry point."""
    def __init__(self,store=None): self.state='new'; self.store=store
    def handle(self,req):
        if not isinstance(req,dict): return {'jsonrpc':'2.0','id':None,'error':{'code':-32600,'message':'Invalid request'}}
        rid=req.get('id'); method=req.get('method'); params=req.get('params',{})
        def reply(result=None,error=None):
            return {'jsonrpc':'2.0','id':rid,**({'error':error} if error else {'result':result})}
        def err(code,msg): return reply(error={'code':code,'message':msg})
        if req.get('jsonrpc')!='2.0' or not isinstance(method,str): return err(-32600,'Invalid request')
        if 'id' not in req:
            if method=='notifications/initialized' and self.state=='negotiated': self.state='ready'
            return None
        if not isinstance(params,dict): return err(-32602,'Invalid params')
        if method=='initialize' and self.state=='new':
            self.state='negotiated'
            return reply({'protocolVersion':'2024-11-05','capabilities':{'tools':{}},'serverInfo':{'name':'aars-omb','version':'0.2.0'}})
        if method=='ping': return reply({})
        if self.state!='ready': return err(-32002,'Session not initialized')
        if method=='tools/list': return reply({'tools':TOOLS+(STORE_TOOLS if self.store is not None else [])})
        if method=='tools/call':
            try:
                result=call(params.get('name'),params.get('arguments',{}),self.store)
                return reply({'content':[{'type':'text','text':json.dumps(result)}],'isError':False})
            except ValueError:
                return reply({'content':[{'type':'text','text':'Unknown tool or invalid arguments'}],'isError':True})
            except Exception:
                return reply({'content':[{'type':'text','text':'SDK operation failed'}],'isError':True})
        return err(-32601,'Method not found')

async def serve():
    """Official SDK owns negotiation, framing and JSON-RPC lifecycle."""
    import anyio
    from mcp import types
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    path = os.environ.get("AARS_OMB_DB")
    store = Store(path) if path else None
    tools = TOOLS + (STORE_TOOLS if store is not None else [])

    async def list_tools(context, params):
        return types.ListToolsResult(tools=[types.Tool(**tool) for tool in tools])

    async def call_tool(context, params):
        try:
            result = await anyio.to_thread.run_sync(call, params.name, params.arguments or {}, store)
            return types.CallToolResult(content=[types.TextContent(type="text", text=json.dumps(result))], isError=False)
        except ValueError:
            return types.CallToolResult(content=[types.TextContent(type="text", text="Unknown tool, invalid arguments or integrity failure")], isError=True)
        except Exception:
            return types.CallToolResult(content=[types.TextContent(type="text", text="SDK operation failed")], isError=True)

    server = Server("aars-omb", version="0.2.1-fix", on_list_tools=list_tools, on_call_tool=call_tool,
                    get_tool_input_schema=lambda name: next((t['inputSchema'] for t in tools if t['name'] == name), None))
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def main():
    import anyio
    anyio.run(serve)

if __name__=='__main__': main()
