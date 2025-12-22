import os
import tempfile
import subprocess
import requests
import replicate
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from openai import OpenAI

MODEL_ID = "kwaivgi/kling-v2.5-turbo-pro"
DEFAULT_DURATION_SECONDS = 10
DEFAULT_ASPECT_RATIO = "9:16"
TTS_MODEL = "tts-1-hd"
TTS_VOICE = "nova"


def _env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y"}


def _build_video_prompt(planner_output: dict) -> str:
    topic = str(planner_output.get("topic", "")).strip()
    scenes = planner_output.get("scenes", []) or []
    reference_url = str(planner_output.get("reference_video_url", "")).strip()

    parts = []
    if topic:
        parts.append(f"Topic: {topic}.")
    if reference_url:
        parts.append(f"Reference video (style only): {reference_url}.")

    for scene in scenes:
        image_desc = str(scene.get("image_description", "")).strip()
        narration = str(scene.get("narration", "")).strip()
        if image_desc:
            parts.append(image_desc)
        if narration:
            parts.append(narration)

    summary = " ".join(parts).strip()
    return (
        "Create a 10-second vertical 9:16 video. "
        "Follow the scene durations in the plan (e.g., 3s/3s/4s). "
        "Show a cute or mind-blowing animal moment with cinematic realism. "
        "Animals must act like humans (using tools, mimicking human gestures, sitting at tables) while still looking like real animals. "
        "No on-screen text or subtitles. "
        f"{summary}"
    ).strip()


def _build_narration_text(planner_output: dict) -> str:
    scenes = planner_output.get("scenes", []) or []
    lines = []
    for scene in scenes:
        narration = str(scene.get("narration", "")).strip()
        if narration:
            lines.append(narration)
    return " ".join(lines).strip()


def _generate_tts_audio(narration_text: str) -> bytes:
    client = OpenAI()
    response = client.audio.speech.create(
        model=TTS_MODEL,
        voice=TTS_VOICE,
        input=narration_text,
    )
    return response.content


def _mux_audio(video_bytes: bytes, audio_bytes: bytes) -> bytes:
    cleanup_paths = []
    try:
        video_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        video_file.write(video_bytes)
        video_file.close()
        cleanup_paths.append(video_file.name)

        audio_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        audio_file.write(audio_bytes)
        audio_file.close()
        cleanup_paths.append(audio_file.name)

        output_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        output_file.close()
        cleanup_paths.append(output_file.name)

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            video_file.name,
            "-i",
            audio_file.name,
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-shortest",
            output_file.name,
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)

        with open(output_file.name, "rb") as merged_file:
            return merged_file.read()
    finally:
        for path in cleanup_paths:
            try:
                if os.path.exists(path):
                    os.unlink(path)
            except OSError:
                pass


async def generate_video(tool_context: ToolContext) -> dict:
    try:
        if tool_context.state.get("video_attempted") is True:
            return {"success": False, "error": "video already attempted; skipping"}
        tool_context.state["video_attempted"] = True

        planner_output = tool_context.state.get("content_planner_output", {})
        if not planner_output:
            return {"success": False, "error": "content_planner_output is missing"}

        prompt_text = _build_video_prompt(planner_output)
        duration_seconds = int(
            os.getenv("VIDEO_DURATION_SECONDS", DEFAULT_DURATION_SECONDS)
        )
        aspect_ratio = os.getenv("VIDEO_ASPECT_RATIO", DEFAULT_ASPECT_RATIO)

        input_payload = {
            "prompt": prompt_text,
            "duration": duration_seconds,
            "aspect_ratio": aspect_ratio,
            "output_format": "mp4",
        }

        video_result = replicate.run(MODEL_ID, input=input_payload)
        video_url = None
        if isinstance(video_result, list):
            if video_result:
                video_url = video_result[0]
        else:
            video_url = video_result

        if not video_url:
            return {"success": False, "error": "Replicate returned empty video URL"}

        response = requests.get(str(video_url))
        response.raise_for_status()
        video_bytes = response.content

        critic_output = tool_context.state.get("critic_ouput", {})
        critic_score = critic_output.get("score") if isinstance(critic_output, dict) else None
        notes = "video generated"
        if critic_score is not None:
            notes = f"video generated (plan score {critic_score})"
        if _env_flag("VIDEO_ADD_AUDIO", False):
            narration_text = _build_narration_text(planner_output)
            if narration_text:
                try:
                    audio_bytes = _generate_tts_audio(narration_text)
                    video_bytes = _mux_audio(video_bytes, audio_bytes)
                    notes = "video generated with narration audio"
                except Exception as exc:  # noqa: BLE001
                    notes = f"audio skipped: {exc}"
            else:
                notes = "video generated (no narration text)"

        artifact = types.Part(
            inline_data=types.Blob(
                mime_type="video/mp4",
                data=video_bytes,
            )
        )

        filename = "shorts.mp4"
        await tool_context.save_artifact(filename=filename, artifact=artifact)

        return {
            "success": True,
            "output_file": filename,
            "duration": duration_seconds,
            "aspect_ratio": aspect_ratio,
            "model": MODEL_ID,
            "notes": notes,
        }
    except Exception as exc:  # noqa: BLE001
        return {"success": False, "error": str(exc)}
