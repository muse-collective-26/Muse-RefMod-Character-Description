import asyncio, importlib.util, os
from pathlib import Path
from unittest.mock import patch
p=Path(__file__).resolve().parents[1]/'providers.py'
spec=importlib.util.spec_from_file_location('providers',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
calls=[]
result={'choices':[{'message':{'content':'A woman wearing a blue jacket.'}}]}
status=200
class Response:
    async def __aenter__(self):return self
    async def __aexit__(self,*args):pass
    @property
    def status(self):return status
    async def json(self):return result
class Session:
    async def __aenter__(self):return self
    async def __aexit__(self,*args):pass
    def post(self,url,**kwargs):calls.append((url,kwargs));return Response()
async def run():
    global result,status
    with patch.object(m.aiohttp,'ClientSession',Session),patch.dict(os.environ,{'OPENAI_API_KEY':'test-only','GEMINI_API_KEY':'test-only','MUSE_REFMOD_API_KEY':'custom-test'}):
        for provider in m.DEFAULTS:
            result={'response':'A woman wearing a blue jacket.'} if provider=='ollama' else {'choices':[{'message':{'content':'A woman wearing a blue jacket.'}}]}
            args=m.resolve_provider({'provider':provider,'base_url':'http://localhost:1234/v1' if provider in ('custom','lmstudio') else '', 'model':'vision-model'})
            ok,text=await m.call_vlm(*args,'Describe character',['abc'])
            assert ok and text.startswith('A woman')
            url,kw=calls[-1];assert not kw['allow_redirects'];assert 'abc' in str(kw['json'])
            assert '/v1/v1/' not in url
            if provider=='ollama':assert kw['json']['keep_alive']==0
        for provider in ('openai','gemini'):
            assert m.resolve_provider({'provider':provider,'base_url':'https://untrusted.invalid'})[1]==m.DEFAULTS[provider][0]
        status=401
        assert not (await m.call_vlm('ollama','http://localhost:11434','vision','x',['abc']))[0]
        status=200;result={'choices':[]}
        assert not (await m.call_vlm('lmstudio','http://localhost:1234','vision','x',['abc']))[0]
        result={'choices':[{'message':{'content':''}}]}
        assert not (await m.call_vlm('lmstudio','http://localhost:1234','vision','x',['abc']))[0]
    with patch.dict(os.environ,{},clear=True):
        for provider in ('gemini','openai'):
            assert not (await m.call_vlm(provider,m.DEFAULTS[provider][0],m.DEFAULTS[provider][1],'x',['abc']))[0]
asyncio.run(run())
print('PASS: all five provider payloads, endpoint normalization, cloud credential isolation, missing keys, HTTP failure, malformed and empty replies')
