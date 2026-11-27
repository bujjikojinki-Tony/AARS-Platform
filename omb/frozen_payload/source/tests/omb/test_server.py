import json, subprocess, sys
import pytest
from aars_omb.server import call,Session

def test_health(): assert call('aars_health',{})['status']=='HEALTHY'
def test_certify():
    r=call('aars_graph_certify',{'scenario':'valid'}); assert r['report']['valid'] and r['report']['object_count']==9 and not r['execution_authorized']
def test_missing(): assert not call('aars_graph_certify',{'scenario':'missing_observation'})['report']['valid']
@pytest.mark.parametrize('name,args',[('execute',{}),('aars_health',{'path':'/etc/passwd'}),('aars_graph_certify',{'scenario':'real'}),('aars_graph_certify',{'scenario':'valid','file':'/tmp/x'})])
def test_deny(name,args):
    with pytest.raises(ValueError): call(name,args)
def test_not_ready(): assert 'error' in Session().handle({'jsonrpc':'2.0','id':1,'method':'tools/list'})
def test_stdio():
    msgs=[{'id':1,'method':'initialize','params':{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'test','version':'1'}}},{'method':'notifications/initialized'},{'id':2,'method':'tools/list'},{'id':3,'method':'tools/call','params':{'name':'aars_health','arguments':{}}}]
    from protocol_helper import exchange
    a=exchange(msgs); assert len(a)==3 and len(a[1]['result']['tools'])==2 and not a[2]['result']['isError']
