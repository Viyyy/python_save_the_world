# -*- coding: utf-8 -*-
# Author: Vi
# Created on: 2025-02-14 10:57:53
# Description: Demucs audio separation demo using Gradio.

''' python=3.10, Requirments:
pip install --upgrade pip==25.0.1
pip install "demucs[dev] @ git+https://kkgithub.com/adefossez/demucs"
pip install rich gradio
pip install numpy==1.26.0
'''

import os
import sys
import gc
from datetime import datetime
import torch
from rich.console import Console
import gradio as gr

# Append parent paths so that demucs modules can be imported
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from demucs.audio import save_audio
from torch.cuda import is_available as is_cuda_available
from demucs.api import Separator
from demucs.apply import BagOfModels

# Directories and file names for outputs
AUDIO_DIR = os.path.join(os.path.dirname(__file__), "output/audio")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
RAW_AUDIO_OUTPUT = os.path.join(AUDIO_DIR, "raw_{}.mp3")
VOCAL_AUDIO_OUTPUT = os.path.join(AUDIO_DIR, "vocal_{}.mp3")
BACKGROUND_AUDIO_OUTPUT = os.path.join(AUDIO_DIR, "background_{}.mp3")


# Preload the Demucs model globally to avoid reloading for each request.
console = Console()
console.print("🤖 Preloading <htdemucs> model...")

# demucs 会把模型下载到缓存里
# from demucs.pretrained import get_model
# model = get_model("htdemucs") #

# 直接下载到指定文件夹
from demucs.states import load_model

url = "https://dl.fbaipublicfiles.com/demucs/hybrid_transformer/955717e8-8726e21a.th"
pkg = torch.hub.load_state_dict_from_url(
    url, map_location="cpu", check_hash=True, model_dir=MODEL_DIR
)  # type: ignore
model = load_model(pkg)


class PreloadedSeparator(Separator):
    """
    Custom Separator class that preloads the Demucs model.
    """

    def __init__(
        self,
        model: BagOfModels,
        shifts: int = 1,
        overlap: float = 0.25,
        split: bool = True,
        segment: int = None,
        jobs: int = 0,
    ):
        self._model = model
        self._audio_channels = model.audio_channels
        self._samplerate = model.samplerate
        device = (
            "cuda"
            if is_cuda_available()
            else ("mps" if torch.backends.mps.is_available() else "cpu")
        )
        self.update_parameter(
            device=device,
            shifts=shifts,
            overlap=overlap,
            split=split,
            segment=segment,
            jobs=jobs,
            progress=True,
            callback=None,
            callback_arg=None,
        )


def demucs_separate(input_audio_path: str) -> dict:
    """
    Main Demucs separation function without plotting functionality.
    """
    # Generate a unique timestamp for output file names.
    operation_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_audio_output = RAW_AUDIO_OUTPUT.format(operation_time)
    vocal_audio_output = VOCAL_AUDIO_OUTPUT.format(operation_time)
    background_audio_output = BACKGROUND_AUDIO_OUTPUT.format(operation_time)

    console.print("🎵 Separating audio...")
    separator = PreloadedSeparator(model=model, shifts=1, overlap=0.25)

    # Separate the input audio file.
    raw_signal, outputs = separator.separate_audio_file(input_audio_path)

    kwargs = {
        "samplerate": model.samplerate,
        "bitrate": 64,
        "preset": 2,
        "clip": "rescale",
        "as_float": False,
        "bits_per_sample": 16,
    }

    # Save original audio and separated tracks.
    save_audio(raw_signal.cpu(), raw_audio_output, **kwargs)
    console.print("🎤 Saving vocals track...")
    save_audio(outputs["vocals"].cpu(), vocal_audio_output, **kwargs)

    console.print("🎹 Saving background music...")
    # Combine all sources except vocals to form background.
    background = sum(audio for source, audio in outputs.items() if source != "vocals")
    save_audio(background.cpu(), background_audio_output, **kwargs)

    # Free up memory.
    del outputs, background, separator
    gc.collect()

    console.print("[green]✨ Audio separation completed![/green]")
    return {
        "raw": raw_audio_output,
        "vocal": vocal_audio_output,
        "background": background_audio_output,
    }


def process_audio(uploaded_audio):
    """
    Gradio interface function. It accepts an uploaded audio file and returns three audio outputs.
    uploaded_audio may be a dict with a key "name" (indicating file path)
    or a file path string.
    """
    if isinstance(uploaded_audio, dict) and "name" in uploaded_audio:
        input_audio_path = uploaded_audio["name"]
    elif isinstance(uploaded_audio, str):
        input_audio_path = uploaded_audio
    else:
        raise ValueError("Unsupported audio input format")

    files = demucs_separate(input_audio_path)
    return files["raw"], files["vocal"], files["background"]


# Define Gradio Interface with three audio components:
# - Input audio box for uploading the audio.
# - Three output audio boxes for raw, vocal, and background tracks.
with gr.Blocks(title="Audio Separation with Demucs") as demo:
    gr.Markdown(
        "## Audio Separation with Demucs\n上传音频后，将会返回分离后的原始音频、vocal 音频和 background 音频。"
    )

    # with gr.Row():
    with gr.Column():
        input_audio = gr.Audio(sources=["upload"], type="filepath", label="上传音频")
        submit_btn = gr.Button("分离音频")
    with gr.Column():
        raw_audio_output = gr.Audio(label="原始音频")
        vocal_audio_output = gr.Audio(label="Vocal 音频")
        background_audio_output = gr.Audio(label="Background 音频")

    submit_btn.click(
        fn=process_audio,
        inputs=input_audio,
        outputs=[raw_audio_output, vocal_audio_output, background_audio_output],
    )

if __name__ == "__main__":
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(AUDIO_DIR, exist_ok=True)
    demo.launch(server_name="0.0.0.0", server_port=7860)
