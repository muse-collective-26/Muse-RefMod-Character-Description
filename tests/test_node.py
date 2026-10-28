import asyncio, importlib.util, json, sys, tempfile, types
from pathlib import Path
from PIL import Image
root=Path(__file__).resolve().parents[1]
class Routes:
    def post(self,path):return lambda fn:fn
class Block:
    def __init__(self,value):pass
sys.modules['server']=types.SimpleNamespace(PromptServer=types.SimpleNamespace(instance=types.SimpleNamespace(routes=Routes())))
sys.modules['comfy_execution.graph']=types.SimpleNamespace(ExecutionBlocker=Block)
with tempfile.TemporaryDirectory(dir=root) as directory:
    folder=Path(directory);Image.new('RGB',(40,80)).save(folder/'one.png')
    sys.modules['folder_paths']=types.SimpleNamespace(get_input_directory=lambda:directory,exists_annotated_filepath=lambda p:(folder/p).is_file(),get_annotated_filepath=lambda p:str(folder/p))
    spec=importlib.util.spec_from_file_location('description_node',root/'__init__.py', submodule_search_locations=[str(root)]);mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
    paths,total=mod.source_paths({'image':'one.png','source':'Image folder','folder':'unused'})
    assert total==1 and paths==[folder/'one.png']
    assert len(mod.encode_images(paths))==1
    node=mod.MuseRefModDescription()
    assert node.VALIDATE_INPUTS('one.png') is True
    (folder/'muse_refmod_description').mkdir()
    Image.new('RGB',(40,80)).save(folder/'muse_refmod_description'/'Alice_00002_.png')
    uploaded='muse_refmod_description/Alice_00002_.png'
    assert uploaded in node.INPUT_TYPES()['required']['image'][0]
    assert node.VALIDATE_INPUTS(uploaded) is True
    Image.new('RGB',(40,80)).save(folder/'muse_refmod_description'/'later.png')
    assert node.VALIDATE_INPUTS('muse_refmod_description/later.png') is True
    assert node.VALIDATE_INPUTS('missing.png') is not True
    assert isinstance(node.emit(description='Draft')[0],Block)
    assert isinstance(node.emit(description='Edited',approved_description='Draft')[0],Block)
    assert node.emit(description='Approved',approved_description='Approved')==('Approved',)
    calls=[]
    async def fake_call(*args,**kwargs):calls.append(args);return True,'A woman with dark hair wearing a gold fabric dress.'
    mod.providers=types.SimpleNamespace(resolve_provider=lambda d:('gemini','url','model'),call_vlm=fake_call)
    class Request:
        async def json(self):return {'image':'one.png','provider':'gemini'}
    response=asyncio.run(mod.analyze(Request()));assert response.status==200 and len(calls[0][4])==1
    async def verbose(*args,**kwargs):return True,'word '*101
    mod.providers.call_vlm=verbose
    response=asyncio.run(mod.analyze(Request()));assert response.status==400 and 'overlong' in response.text
print('PASS: single image only, provider routing, word limit, approval gate and edited draft blocking')
