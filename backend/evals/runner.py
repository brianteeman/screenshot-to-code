from typing import Any, Coroutine, List
import asyncio
import os
from llm import Llm
from .core import generate_code_for_image
from .utils import image_to_data_url
from .config import EVALS_DIR
from typing_extensions import Literal

Stack = Literal['html_css', 'html_tailwind', 'react_tailwind', 'bootstrap', 'ionic_tailwind', 'vue_tailwind', 'svg']

async def run_image_evals(
    stack: Stack = "html_tailwind", 
    model: Llm = Llm.CLAUDE_3_5_SONNET_2024_10_22, 
    n: int = 1
) -> List[str]:
    INPUT_DIR = EVALS_DIR + "/inputs"
    OUTPUT_DIR = EVALS_DIR + "/outputs"

    # Get all the files in the directory (only grab pngs)
    evals = [f for f in os.listdir(INPUT_DIR) if f.endswith(".png")]

    tasks: list[Coroutine[Any, Any, str]] = []
    for filename in evals:
        filepath = os.path.join(INPUT_DIR, filename)
        data_url = await image_to_data_url(filepath)
        for n_idx in range(n):  # Generate N tasks for each input
            if n_idx == 0:
                task = generate_code_for_image(
                    image_url=data_url,
                    stack=stack,
                    model=model,
                )
            else:
                task = generate_code_for_image(
                    image_url=data_url, stack=stack, model=Llm.GPT_4O_2024_05_13
                )
            tasks.append(task)

    print(f"Generating {len(tasks)} codes")

    results = await asyncio.gather(*tasks)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    output_files: List[str] = []
    for i, content in enumerate(results):
        # Calculate index for filename and output number
        eval_index = i // n
        output_number = i % n
        filename = evals[eval_index]
        # File name is derived from the original filename in evals with an added output number
        output_filename = f"{os.path.splitext(filename)[0]}_{output_number}.html"
        output_filepath = os.path.join(OUTPUT_DIR, output_filename)
        with open(output_filepath, "w") as file:
            file.write(content)
        output_files.append(output_filename)

    return output_files 