# Muse RefMod Character Description

A compact ComfyUI node for describing a character from one image. Analyze, review or edit the description, then approve it for your RefMod workflow.

**Director V2 is not required.** The node connects directly to Ollama, Google Gemini, OpenAI, LM Studio or an OpenAI-compatible server. It returns a normal STRING, so it can also be used wherever a text description is needed.

## Install

Clone this repository into your ComfyUI `custom_nodes` folder, or download the ZIP and extract it there. Keep one copy installed. If you already have a folder named `Muse-RefMod-Description`, replace that copy rather than installing a second copy under a different name.

Install `requirements.txt` using the Python environment that runs ComfyUI, if its dependencies are not already installed:

```sh
python -m pip install -r requirements.txt
```

Restart ComfyUI and refresh the browser. Add **Muse RefMod Character Description** from the **Muse / RefMod** category. No Torch, SageAttention, Triton or model-weight installation is performed by this node.

## Use

1. Upload or select one character image.
2. Choose your analysis provider. Expand **Connection settings** to set a vision model or local server URL.
3. Click **Analyze character**. This analyzes the image without queueing the workflow.
4. Read the description. Edit it directly or click **Reanalyze character**.
5. Connect the `description` output to the `description` input on your Create H3 RefMod node. If that input is a text widget, convert it to an input using the node's context menu.
6. Click **Continue to create RefMod** when ready. This approves the current text and queues the workflow, including its connected downstream nodes.

Editing the description revokes approval. Running the workflow with unapproved text blocks the description output until Continue is clicked. The description is saved as part of the ComfyUI workflow.

The uploaded image is used for **analysis only**. Connect the intended character images or folder separately to Create H3 RefMod. This node outputs text; it does not supply image conditioning or create the RefMod itself. The H3 RefMod creation nodes and their models must be installed separately if you want to create RefMods.

## Providers

| Provider | Setup |
| --- | --- |
| Ollama | Start Ollama with a vision-capable model installed. Default URL: `http://127.0.0.1:11434`. Enter your installed model's name in Connection settings; the initial default is `huihui_ai/qwen3.5-abliterated:2b`. The request asks Ollama to unload the model afterward. |
| Google Gemini | Set `GEMINI_API_KEY` in the environment that starts ComfyUI. Default model: `gemini-2.5-flash`. |
| OpenAI | Set `OPENAI_API_KEY` in the environment that starts ComfyUI. Default model: `gpt-5.4`. API access and billing are separate from a ChatGPT subscription. |
| LM Studio | Start its local server with a vision model loaded. Enter that model's name. Default URL: `http://127.0.0.1:1234`. |
| Custom | Enter an OpenAI-compatible server URL and vision model name. Optional authentication uses `MUSE_REFMOD_API_KEY`. URLs with or without a final `/v1` are accepted. |

Restart ComfyUI after changing environment variables. Cloud providers use their official endpoints; the custom URL field cannot redirect their credentials. API keys are not stored in the workflow. Cloud analysis sends the selected image to the chosen provider and may incur provider charges. Local analysis uses the configured local server's resources.

## Description scope

The analyzer requests one compact paragraph describing visible character features and the current outfit, without background, camera instructions or imagined alternative outfits. Responses over 100 words are rejected, keeping the previous text available. A clear image showing the relevant clothing and face works best. Review the result before approving it.

## Checks

Run `python tests/test_node.py` and `python tests/test_providers.py` in an environment with the requirements installed. These cover standalone imports with mocked ComfyUI services, uploads, the approval gate, provider requests and error handling. Provider tests use simulated HTTP replies: they do not make paid calls or establish compatibility with every server/model combination.
