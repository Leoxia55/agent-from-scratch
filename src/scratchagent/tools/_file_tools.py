"""一组给Agent 提供简单的文件操作工具"""

import base64
import os
import zipfile
from pathlib import Path
from typing import Any, cast

from dotenv import find_dotenv, load_dotenv

# Load environment variables from .env file
# load_dotenv(find_dotenv()) 在jupyter 文件中可以简单的加载环境变量

TEXT_EXTENSIONS = [
    ".txt",
    ".py",
    ".js",
    ".json",
    ".md",
    ".html",
    ".css",
    ".xml",
    ".yaml",
    ".yml",
    ".log",
    ".sh",
]
SPREADSHEET_EXTENSIONS = [".xlsx", ".xls", ".csv"]
IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"]
AUDIO_EXTENSIONS = [".mp3", ".wav", ".m4a", ".flac", ".ogg", ".webm"]
PDF_EXTENSIONS = [".pdf"]


def load_project_env() -> None:
    """加载最近的.env 文件，且不暴露或覆盖已有变量值。
    已存在的进程环境变量优先级高于.env 文件内的变量。
    此举可保证测试、持续集成以及手动导出的 Shell 变量结果可复现。
    """
    env_file = find_dotenv(usecwd=True)
    if env_file:
        load_dotenv(env_file, override=False)


def unzip_file(zip_path: str, extract_to: str | None = None) -> str:
    """将压缩包文件解压至指定目录."""
    archive_path = Path(zip_path)

    if not archive_path.exists():
        return f"File not found: {archive_path}"

    # Default extraction path: create folder with zip filename
    extraction_path = (
        archive_path.parent / archive_path.stem
        if extract_to is None
        else Path(extract_to)
    )

    extraction_path.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(archive_path, "r") as zip_ref:
        file_list = zip_ref.namelist()
        zip_ref.extractall(extraction_path)

    # Format results
    result = f"Extracted {len(file_list)} files to {extraction_path}/\n\n"
    result += "Contents:\n"
    for f in file_list[:20]:
        result += f"  - {f}\n"
    if len(file_list) > 20:
        result += f"  ... and {len(file_list) - 20} more files\n"

    return result


def list_files(path: str = ".") -> str:
    """列出给定路径中的文件和目录."""
    directory = Path(path)

    if not directory.exists():
        return f"Path not found: {directory}"

    if not directory.is_dir():
        return f"Not a directory: {directory}"

    items: list[str] = []
    for item in sorted(directory.iterdir()):
        if item.name.startswith("."):
            continue

        if item.is_dir():
            items.append(f"{item.name}/")
        else:
            items.append(f"{item.name}")

    # Sort directories first
    dirs = [i for i in items if i.endswith("/")]
    files = [i for i in items if not i.endswith("/")]

    result = f"Directory: {directory}\n"
    for item in dirs + files:
        result += f"  {item}\n"

    return result


def read_file(file_path: str, start_line: int = 1, end_line: int = -1) -> str:
    """读取文件内容。支持 txt、py、json、md、csv、xlsx."""
    path = Path(file_path)

    if not path.exists():
        return f"File not found: {file_path}"

    ext = path.suffix.lower()

    if ext in TEXT_EXTENSIONS:
        return _read_text_file(file_path, start_line, end_line)
    elif ext == ".csv":
        return _read_csv(file_path)
    elif ext in SPREADSHEET_EXTENSIONS:
        return _read_excel(file_path)
    else:
        return _read_text_file(file_path, start_line, end_line)


def read_media_file(file_path: str, query: str) -> str:
    """使用大语言模型分析图像、音频或 PDF 文件."""
    ext = Path(file_path).suffix.lower()
    # 加载环境变量 .env
    load_project_env()

    if ext in IMAGE_EXTENSIONS:
        return _analyze_image(file_path, query)
    elif ext in AUDIO_EXTENSIONS:
        return _analyze_audio(file_path, query)
    elif ext in PDF_EXTENSIONS:
        return _analyze_pdf(file_path, query)
    else:
        return f"Unsupported media format: {ext}"


def _read_text_file(file_path: str, start_line: int, end_line: int) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Adjust line numbers (1-indexed to 0-indexed)
    start_idx = max(0, start_line - 1)
    end_idx = len(lines) if end_line == -1 else min(end_line, len(lines))

    selected_lines = lines[start_idx:end_idx]

    result: list[str] = []
    for i, line in enumerate(selected_lines, start=start_line):
        result.append(f"{i:4d} | {line.rstrip()}")
    return "\n".join(result)


def _read_csv(file_path: str) -> str:
    import pandas as pd

    df = pd.read_csv(file_path)
    return str(df.to_markdown(index=False))


def _read_excel(file_path: str) -> str:
    import pandas as pd

    df = pd.read_excel(file_path)
    return str(df.to_markdown(index=False))


def _analyze_image(file_path: str, query: str) -> str:
    from openai import OpenAI

    with open(file_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    ext = Path(file_path).suffix.lower().lstrip(".")
    media_type = "image/jpeg" if ext == "jpg" else f"image/{ext}"

    client = OpenAI(
        api_key=os.environ.get("OPENROUTER_API_KEY"),
        base_url=os.environ.get("OPENROUTER_BASE_URL"),
    )
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=cast(
            Any,
            [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": query},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_data}"
                            },
                        },
                    ],
                }
            ],
        ),
    )
    return response.choices[0].message.content or ""


def _analyze_audio(file_path: str, query: str) -> str:
    from openai import OpenAI

    with open(file_path, "rb") as f:
        audio_data = base64.b64encode(f.read()).decode("utf-8")

    audio_format = Path(file_path).suffix.lower().lstrip(".")

    client = OpenAI(
        api_key=os.environ.get("OPENROUTER_API_KEY"),
        base_url=os.environ.get("OPENROUTER_BASE_URL"),
    )
    response = client.chat.completions.create(
        model="gpt-4o-audio-preview",
        messages=cast(
            Any,
            [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": query},
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": audio_data,
                                "format": audio_format,
                            },
                        },
                    ],
                }
            ],
        ),
    )
    return response.choices[0].message.content or ""


def _analyze_pdf(file_path: str, query: str) -> str:
    import fitz  # PyMuPDF
    from openai import OpenAI

    doc = fitz.open(file_path)

    # Extract text for context
    text_content = ""
    for page in doc:
        extracted_text = page.get_text()
        if isinstance(extracted_text, str):
            text_content += extracted_text

    # Convert pages to images
    images: list[str] = []
    for page in doc[:5]:  # First 5 pages
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_bytes = pix.tobytes("png")
        images.append(base64.b64encode(img_bytes).decode("utf-8"))

    # Build content with text and images
    content: list[dict[str, Any]] = [
        {"type": "text", "text": f"{query}\n\nExtracted text:\n{text_content[:3000]}"}
    ]

    for img_b64 in images:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{img_b64}"},
            }
        )

    client = OpenAI(
        api_key=os.environ.get("OPENROUTER_API_KEY"),
        base_url=os.environ.get("OPENROUTER_BASE_URL"),
    )
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=cast(Any, [{"role": "user", "content": content}]),
    )
    return response.choices[0].message.content or ""


def delete_file(file_path: str) -> str:
    """删除一个文件或者目录."""
    path = Path(file_path)

    if not path.exists():
        return f"File not found: {file_path}"

    try:
        if path.is_dir():
            import shutil

            shutil.rmtree(path)
            return f"Directory deleted: {file_path}"
        else:
            path.unlink()
            return f"File deleted: {file_path}"
    except Exception as e:
        return f"Error deleting {file_path}: {str(e)}"
