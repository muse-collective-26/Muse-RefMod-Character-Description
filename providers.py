"""Independent HTTP vision clients. No Director imports or model loading."""
import asyncio
import os
from urllib.parse import urlsplit

import aiohttp

DEFAULTS = {
    'ollama': ('http://127.0.0.1:11434', 'huihui_ai/qwen3.5-abliterated:2b'),
    'gemini': ('https://generativelanguage.googleapis.com/v1beta/openai', 'gemini-2.5-flash'),
    'openai': ('https://api.openai.com/v1', 'gpt-5.4'),
    'lmstudio': ('http://127.0.0.1:1234', ''),
    'custom': ('', ''),
}


def resolve_provider(data):
    provider = str(data.get('provider') or 'ollama').lower()
    if provider not in DEFAULTS:
        raise ValueError('Choose a supported vision provider.')
    default_url, default_model = DEFAULTS[provider]
    model = str(data.get('model') or '').strip()
    url = str(data.get('base_url') or default_url).strip().rstrip('/')
    if provider in ('openai', 'gemini'):
        # Never send cloud credentials to a host supplied by a workflow.
        url = default_url
        if ':' in model:
            model = ''
    model = model or default_model
    if not model:
        raise ValueError('Enter the name of your loaded vision model in Connection settings.')
    parsed = urlsplit(url)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError('Enter a valid HTTP or HTTPS server URL without credentials or query parameters.')
    return provider, url, model


async def call_vlm(provider, base_url, model_name, instruction, images, max_tokens=512):
    provider, base_url, model_name = resolve_provider({'provider': provider, 'base_url': base_url, 'model': model_name})
    images = [image.split(',', 1)[-1] for image in images]
    headers = {}
    if provider == 'ollama':
        base_url = base_url.removesuffix('/api')
        url = base_url + '/api/generate'
        payload = {'model': model_name, 'prompt': instruction, 'images': images,
                   'stream': False, 'keep_alive': 0, 'options': {'num_predict': max_tokens}}
    else:
        content = [{'type': 'text', 'text': instruction}]
        content += [{'type': 'image_url', 'image_url': {'url': 'data:image/jpeg;base64,' + image}} for image in images]
        payload = {'model': model_name, 'messages': [{'role': 'user', 'content': content}], 'stream': False}
        if provider in ('openai', 'gemini'):
            env = 'OPENAI_API_KEY' if provider == 'openai' else 'GEMINI_API_KEY'
            key = os.environ.get(env, '').strip()
            if not key:
                return False, f'Set {env} in the ComfyUI environment, then restart ComfyUI.'
            headers['Authorization'] = 'Bearer ' + key
        elif provider == 'custom':
            key = os.environ.get('MUSE_REFMOD_API_KEY', '').strip()
            if key:
                headers['Authorization'] = 'Bearer ' + key
        if provider == 'openai':
            payload['max_completion_tokens'] = max(4096, max_tokens * 2)
        else:
            payload['max_tokens'] = max_tokens
        if provider == 'gemini':
            payload['reasoning_effort'] = 'none'
        if provider in ('lmstudio', 'custom') and not base_url.endswith('/v1'):
            base_url += '/v1'
        url = base_url + '/chat/completions'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=180, allow_redirects=False) as response:
                if response.status != 200:
                    return False, f'{provider} HTTP {response.status}. Check server availability, model name, credentials and API quota.'
                data = await response.json()
        if provider == 'ollama':
            text = data.get('response', '')
            stop = data.get('done_reason')
        else:
            choice = data['choices'][0]
            text = choice['message'].get('content', '')
            stop = choice.get('finish_reason')
        if stop == 'length':
            return False, 'The model reached its output limit. Try another vision model or reanalyze.'
        if not isinstance(text, str):
            return False, 'The provider returned an unexpected response.'
        if '<think>' in text:
            text = text.split('</think>')[-1] if '</think>' in text else ''
        text = text.strip()
        return (True, text) if text else (False, 'The provider returned no character description.')
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return False, f'Could not complete the request to {provider}. Check that the server is reachable and the vision model is running.'
    except (KeyError, IndexError, TypeError, ValueError):
        return False, 'The provider returned an unexpected response.'
