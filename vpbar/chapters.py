"""Chapter string parsing."""


def parse_chapters(chapter_str: str | None) -> list[dict] | None:
    """Parse chapter string like '0-6:Intro,6-11:结尾' into list of dicts."""
    if not chapter_str:
        return None
    chapters = []
    for part in chapter_str.split(','):
        parts = part.strip().split(':')
        if len(parts) == 2:
            time_range, label = parts
            start, end = time_range.split('-')
            chapters.append({
                'start': float(start),
                'end': float(end),
                'label': label.strip()
            })
    return chapters if chapters else None


def generate_chapters_from_srt(
    srt_path: str,
    min_chapters: int = 2,
    max_chapters: int = 4,
    max_label_length: int = 5,
) -> str | None:
    from vpbar.srt import parse_srt
    from vpbar.llm import call_llm, parse_llm_json

    entries, duration = parse_srt(srt_path)
    subtitle_lines = "\n".join(
        f"{e['start_sec']:.1f} → {e['end_sec']:.1f} : {e['text']}"
        for e in entries
    )
    user_content = f"字幕内容如下（每行格式：开始时间 → 结束时间 : 文本）：\n\n{subtitle_lines}\n\n视频总时长：{duration:.1f} 秒"

    system_prompt = (
        "你是一个视频章节分析助手。根据用户提供的字幕内容（含时间戳），\n"
        f"将视频内容分成 {min_chapters} 到 {max_chapters} 个章节。\n\n"
        "要求：\n"
        f"- 每个章节起一个简短的名称（1-{max_label_length} 个字），\n"
        "  使用与字幕相同的语言，概括该段落的核心内容\n"
        "- 章节之间的边界要合理，不要打断一个完整的论述或句子\n"
        "- 第一个章节从 0 秒开始，最后一个章节到视频结束\n"
        "- 只返回 JSON 数组，不要多余的文字或解释\n\n"
        "JSON 格式：\n"
        '[\n'
        '  {"start": 0, "end": 108.5, "label": "开场"},\n'
        '  {"start": 108.5, "end": 300.0, "label": "实战"}\n'
        "]\n\n"
        "其中 start 和 end 为浮点数秒，label 为字符串。"
    )

    raw = call_llm(system_prompt, user_content)
    if raw is None:
        return None

    data = parse_llm_json(raw)
    if data is None:
        raw = call_llm(system_prompt, user_content)
        if raw is None:
            return None
        data = parse_llm_json(raw)
        if data is None:
            return None

    chapters_str = ",".join(
        f"{c['start']:.1f}-{c['end']:.1f}:{c['label']}"
        for c in data
    )
    return chapters_str
