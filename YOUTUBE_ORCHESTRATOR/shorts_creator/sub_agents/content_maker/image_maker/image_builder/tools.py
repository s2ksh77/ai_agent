import replicate
import requests
import asyncio
from replicate.exceptions import ReplicateError
from google.genai import types
from google.adk.tools.tool_context import ToolContext


async def generate_images(tool_context: ToolContext):
    """
    Replicate의 nano-banana 모델을 사용하여 각 장면에 대한 이미지를 생성합니다.
    9:16 비율의 세로형 이미지를 생성하며, 이미 생성된 이미지는 재사용합니다.

    Args:
        tool_context: 아티팩트를 조회하고 저장하기 위한 ToolContext 객체.

    Returns:
        생성된 모든 이미지 파일의 정보가 포함된 딕셔너리.
    """
    prompt_builder_output = tool_context.state.get("prompt_builder_output")
    opt_prompts = prompt_builder_output.get("opt_prompts")

    existing_artifacts = await tool_context.list_artifacts()

    image_results = []

    for prompt in opt_prompts:
        scene_id = prompt.get("scene_id")
        enhanced_prompt = prompt.get("enhanced_prompt")
        filename = f"scene_{scene_id}_image.jpg"

        if filename in existing_artifacts:
            image_results.append(
                {
                    "scene_id": scene_id,
                    "filename": filename,
                }
            )
            continue

        # Rate limiting 처리와 함께 이미지 생성
        max_retries = 3
        retry_delay = 10  # seconds

        for attempt in range(max_retries):
            try:
                image_url = replicate.run(
                    "google/nano-banana",
                    input={
                        "prompt": enhanced_prompt,
                        "image_input": [],
                        "aspect_ratio": "9:16",
                        "output_format": "jpg",
                    },
                )
                break  # 성공하면 루프 탈출
            except ReplicateError as e:
                if e.status == 429:  # Rate limit exceeded
                    if attempt < max_retries - 1:  # 마지막 시도가 아니면
                        print(f"Rate limit exceeded, waiting {retry_delay} seconds before retry {attempt + 1}/{max_retries}")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # 지수 백오프
                        continue
                    else:
                        raise e  # 마지막 시도에서도 실패하면 에러 발생
                else:
                    raise e  # 다른 Replicate 에러는 그대로 발생

        if image_url:
            response = requests.get(str(image_url))
            image_byte_data = response.content
        else:
            raise ValueError("Failed to generate image")

        artifact = types.Part(
            inline_data=types.Blob(
                mime_type="image/jpg",
                data=image_byte_data,
            )
        )

        await tool_context.save_artifact(
            filename=filename,
            artifact=artifact,
        )

        image_results.append(
            {
                "scene_id": scene_id,
                "filename": filename,
            }
        )

    return {
        "success": True,
        "image_results": image_results,
        "total_images": len(image_results),
    }
