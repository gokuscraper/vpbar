"""Streamlit GUI for vpbar — dual-mode: quick (one-click) and pro (3-step workflow)."""

import os
from pathlib import Path

import streamlit as st

from vpbar.gui_utils import (
    PROJECT_ROOT, STYLE_DISPLAY_NAMES, DEFAULT_STYLE_DISPLAY, resolve_style_name,
    TEMP_DIR, SCRUBBER_DIR, SCRUBBER_DEFAULT,
    WHISPER_MODELS, get_video_duration, estimate_eta, run_cli_streaming,
    save_upload, parse_chapters, fmt_chapters, hex_no_hash, list_scrubbers,
)

SCRUBBERS = list_scrubbers()  # [(name, path), ...]
SCRUBBER_CHOICES = ["无", "默认 (scrubber_final.gif)", *[s[0] for s in SCRUBBERS], "自定义上传..."]

st.set_page_config(page_title="视频进度条生成器", page_icon="🎬", layout="wide")

for k, v in dict(video_path="", video_duration=0.0, srt_path="", srt_content="",
                 chapters_text="", output_path="", gif_path="", pro_step="① 转写").items():
    st.session_state.setdefault(k, v)

# ── Title & upload ──
st.title("视频进度条生成器")
uploaded_file = st.file_uploader("上传视频文件", type=["mp4", "mov", "mkv", "avi", "webm"])

if not uploaded_file:
    st.info("请先上传视频文件")
    st.markdown("**支持格式:** MP4, MOV, MKV, AVI, WebM  |  **功能:** 33 种进度条样式 · FunASR/Whisper 转写 · AI 分章 · GIF 拖拽头")
    st.stop()

vid_path = str(TEMP_DIR / uploaded_file.name)
if st.session_state.video_path != vid_path or not os.path.isfile(vid_path):
    st.session_state.video_path = save_upload(uploaded_file)
    try:
        st.session_state.video_duration = get_video_duration(vid_path)
    except Exception:
        st.session_state.video_duration = 0.0

# ── Video preview ──
st.markdown("""
<style>
[data-testid="stVideo"] { max-width: 300px; margin: 0 auto; }
</style>
""", unsafe_allow_html=True)
col_l, col_r = st.columns(2)
with col_l:
    st.caption("原始视频")
    st.video(st.session_state.video_path)
with col_r:
    st.caption("结果预览")
    op = st.session_state.output_path
    if op and os.path.isfile(op):
        st.video(op)
        st.download_button("下载成品视频", open(op, "rb").read(), file_name=Path(op).name,
                           mime="video/mp4", use_container_width=True)
    else:
        st.info("生成后这里显示结果")

# ── Modes ──
qt, pt = st.tabs(["⚡ 快捷模式", "🔧 专业模式"])

# ════════════════════════════════════
# QUICK MODE
# ════════════════════════════════════
with qt:
    st.subheader("快捷模式 — 一键全自动")
    c1, c2, c3 = st.columns(3)
    with c1:
        q_eng = st.selectbox("转写引擎", ["funasr", "whisper"], key="q_eng")
    with c2:
        q_sty = st.selectbox("样式", STYLE_DISPLAY_NAMES, index=STYLE_DISPLAY_NAMES.index(DEFAULT_STYLE_DISPLAY), key="q_sty")
    with c3:
        q_out = st.text_input("输出文件名", key="q_out")

    cc1, cc2 = st.columns(2)
    with cc1:
        q_gif = st.checkbox("GIF 拖拽头", value=True, key="q_gif")
    with cc2:
        q_chp = st.checkbox("AI 自动分章", value=True, key="q_chp")

    q_gif_path = ""
    q_gif_f_up = None
    if q_gif:
        q_gif_sel = st.selectbox("选择拖拽头 GIF", SCRUBBER_CHOICES, index=1, key="q_gif_sel")
        if q_gif_sel == "自定义上传...":
            q_gif_f_up = st.file_uploader("上传自定义 GIF", type=["gif"], key="q_gif_f_up")
            if q_gif_f_up:
                q_gif_path = save_upload(q_gif_f_up)
        elif q_gif_sel == "默认 (scrubber_final.gif)":
            q_gif_path = SCRUBBER_DEFAULT if os.path.isfile(SCRUBBER_DEFAULT) else ""
        # Show preview
        if q_gif_path:
            st.image(q_gif_path, width=100)
        elif q_gif_sel == "无":
            pass
        else:
            for name, path in SCRUBBERS:
                if name == q_gif_sel:
                    q_gif_path = path
                    break
            if q_gif_path:
                st.image(q_gif_path, width=100)

    q_srt_f = st.file_uploader("上传 SRT（可选）", type=["srt"], key="q_srt_f") if not q_chp else None

    dur = st.session_state.video_duration
    if dur:
        st.caption(f"**视频时长:** {dur:.0f}s ({dur / 60:.1f}min)  |  **预计处理:** {estimate_eta(dur, q_eng, q_gif)}")

    if st.button("⚡ 一键生成", type="primary", use_container_width=True):
        out_name = (q_out.strip() or f"{Path(uploaded_file.name).stem}_progress") + ".mp4"
        out_path = str(TEMP_DIR / out_name)
        st.session_state.output_path = out_path

        cmd = ["progress", "add", st.session_state.video_path,
               "-o", out_path, "--engine", q_eng, "--style", resolve_style_name(q_sty)]

        if q_gif and q_gif_path:
            cmd += ["--scrubber-image", q_gif_path]

        if q_srt_f:
            cmd += ["--srt", save_upload(q_srt_f)]
        elif q_chp:
            cmd += ["--transcribe", "--engine", q_eng]

        status = st.status("正在处理...", expanded=True)
        rc, output = run_cli_streaming(cmd, status.empty())
        status.update(label="完成" if rc == 0 else "失败", state="complete" if rc == 0 else "error")

        if rc == 0:
            st.success("✅ 生成成功！")
            st.rerun()
        else:
            st.error(f"❌ 处理失败 (code={rc})")

# ════════════════════════════════════
# PRO MODE
# ════════════════════════════════════
with pt:
    st.subheader("专业模式 — 三步工作流")
    step = st.segmented_control(
        "步骤", ["① 转写", "② 章节", "③ 渲染"],
        default="① 转写", key="pro_step",
        label_visibility="collapsed",
    )
    st.divider()

    if step == "① 转写":
        p1e = st.selectbox("转写引擎", ["funasr", "whisper"], key="p1e")
        is_whisper = p1e == "whisper"
        p1m = st.selectbox("Whisper 模型", WHISPER_MODELS, key="p1m", disabled=not is_whisper)
        p1d = st.radio("设备", ["auto", "cuda", "cpu"], horizontal=True, key="p1d",
                       disabled=not is_whisper, help=None if is_whisper else "FunASR 固定使用 CPU")
        p1c = st.selectbox("计算类型", ["default", "float16", "int8"], key="p1c",
                          disabled=not is_whisper, help=None if is_whisper else "仅 Whisper 支持")

        st.info("已有字幕？点击上方 **② 章节** 直接上传 SRT 文件")

        if st.button("开始转写", type="primary", key="p1b"):
            srt_out = str(TEMP_DIR / f"{Path(uploaded_file.name).stem}.srt")
            cmd = ["transcribe", st.session_state.video_path, "-o", srt_out,
                   "--engine", p1e, "--model", p1m, "--device", p1d, "--compute-type", p1c]
            status = st.status("正在转写...", expanded=True)
            rc, _ = run_cli_streaming(cmd, status.empty())
            status.update(label="转写完成" if rc == 0 else "转写失败",
                          state="complete" if rc == 0 else "error")
            if rc == 0:
                st.session_state.srt_path = srt_out
                st.session_state.srt_content = Path(srt_out).read_text(encoding="utf-8")
                st.success(f"转写完成 → {srt_out}")

    elif step == "② 章节":
        up_srt = st.file_uploader("上传 SRT 文件", type=["srt"], key="p2srt")
        if up_srt:
            st.session_state.srt_path = save_upload(up_srt)
            st.session_state.srt_content = Path(st.session_state.srt_path).read_text(encoding="utf-8")
            st.success(f"已加载 SRT：{up_srt.name}")

        if st.session_state.srt_content:
            st.text_area("SRT 预览（可编辑）", st.session_state.srt_content, height=200, key="p2edit")
            if st.button("保存 SRT 修改", key="p2save"):
                st.session_state.srt_content = st.session_state.p2edit
                Path(st.session_state.srt_path).write_text(st.session_state.srt_content, encoding="utf-8")
                st.toast("SRT 已保存", icon="✅")

        if not st.session_state.srt_content:
            st.warning("请先在第一步转写或上传 SRT 文件")
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                p2min = st.number_input("最小章节数", value=2, min_value=1, key="p2min")
            with c2:
                p2max = st.number_input("最大章节数", value=4, min_value=1, key="p2max")
            with c3:
                p2ml = st.number_input("标签最大长度", value=7, min_value=3, key="p2ml")

            if st.button("AI 生成章节", type="primary", key="p2gen"):
                cmd = ["chapters", "generate", "--srt", st.session_state.srt_path,
                       "--min-chapters", str(p2min), "--max-chapters", str(p2max),
                       "--max-label-length", str(p2ml)]
                status = st.status("正在生成章节...", expanded=True)
                rc, output = run_cli_streaming(cmd, status.empty())
                status.update(label="章节生成完成" if rc == 0 else "生成失败",
                              state="complete" if rc == 0 else "error")
                if rc == 0 and output:
                    st.session_state.chapters_text = output
                    st.toast("章节已生成，可继续编辑", icon="✅")

            if st.session_state.chapters_text:
                items = parse_chapters(st.session_state.chapters_text) or [{"start": 0, "end": 0, "label": ""}]
                edited = st.data_editor(
                    items,
                    column_config={
                        "start": st.column_config.NumberColumn("开始(秒)", min_value=0, format="%d"),
                        "end": st.column_config.NumberColumn("结束(秒)", min_value=0, format="%d"),
                        "label": st.column_config.TextColumn("章节名", max_chars=20),
                    },
                    num_rows="dynamic",
                    use_container_width=True,
                    key="p2tbl",
                )
                if st.button("确认章节", type="primary", key="p2cf"):
                    st.session_state.chapters_text = fmt_chapters(edited)
                    st.session_state.pro_step = "③ 渲染"
                    st.rerun()

            st.text_area("章节文本（也可直接粘贴）", st.session_state.chapters_text, height=130, key="p2raw")

    elif step == "③ 渲染":
        c1, c2 = st.columns(2)
        with c1:
            p3s = st.selectbox("样式", STYLE_DISPLAY_NAMES, index=STYLE_DISPLAY_NAMES.index(DEFAULT_STYLE_DISPLAY), key="p3s")
        with c2:
            p3p = st.radio("位置", ["bottom", "top", "middle"], horizontal=True, key="p3p")
        p3h = st.slider("高度 (px)", 3, 50, 10, key="p3h")

        ccc1, ccc2, ccc3, ccc4 = st.columns(4)
        with ccc1:
            p3bg = st.color_picker("背景色", "#808080", key="p3bg")
        with ccc2:
            p3fg = st.color_picker("前景色", "#333333", key="p3fg")
        with ccc3:
            p3ba = st.slider("背景透明度", 0.0, 1.0, 0.4, key="p3ba")
        with ccc4:
            p3fa = st.slider("前景透明度", 0.0, 1.0, 0.7, key="p3fa")

        p3cr = st.slider("圆角 (px)", 0, 25, 4, key="p3cr")
        p3gr = st.text_input("渐变色（逗号分隔, 如 FF0000,00FF00）", key="p3gr")
        p3gf = st.checkbox("GIF 拖拽头", value=True, key="p3gf")
        p3_gif_path = ""
        p3_gif_up = None
        if p3gf:
            p3_gif_sel = st.selectbox("选择拖拽头 GIF", SCRUBBER_CHOICES, index=1, key="p3_gif_sel")
            if p3_gif_sel == "自定义上传...":
                p3_gif_up = st.file_uploader("上传自定义 GIF", type=["gif"], key="p3_gif_up")
                if p3_gif_up:
                    p3_gif_path = save_upload(p3_gif_up)
            elif p3_gif_sel == "默认 (scrubber_final.gif)":
                p3_gif_path = SCRUBBER_DEFAULT if os.path.isfile(SCRUBBER_DEFAULT) else ""
            if p3_gif_path:
                st.image(p3_gif_path, width=100)
            elif p3_gif_sel == "无":
                pass
            else:
                for name, path in SCRUBBERS:
                    if name == p3_gif_sel:
                        p3_gif_path = path
                        break
                if p3_gif_path:
                    st.image(p3_gif_path, width=100)
        p3sg = st.number_input("分段间隔 (秒, 0=自动)", value=0, key="p3sg")
        p3dw = st.number_input("分隔线宽度", value=3, min_value=0, key="p3dw")
        p3dr = st.slider("分隔线高度比例", 0.0, 1.0, 0.8, key="p3dr")

        if st.button("开始渲染", type="primary", use_container_width=True, key="p3r"):
            out_name = f"{Path(uploaded_file.name).stem}_pro.mp4"
            out_path = str(TEMP_DIR / out_name)
            st.session_state.output_path = out_path

            cmd = ["progress", "add", st.session_state.video_path, "-o", out_path,
                   "--style", resolve_style_name(p3s), "--position", p3p, "--height", str(p3h),
                   "--bg-color", hex_no_hash(p3bg), "--fg-color", hex_no_hash(p3fg),
                   "--bg-alpha", str(p3ba), "--fg-alpha", str(p3fa),
                   "--corner-radius", str(p3cr), "--segment-interval", str(p3sg),
                   "--divider-width", str(p3dw), "--divider-height-ratio", str(p3dr)]

            if p3gr.strip():
                cmd += ["--gradient", p3gr.strip()]

            if p3gf and p3_gif_path:
                cmd += ["--scrubber-image", p3_gif_path]

            if st.session_state.chapters_text:
                cmd += ["--chapters", st.session_state.chapters_text]

            status = st.status("正在渲染...", expanded=True)
            rc, _ = run_cli_streaming(cmd, status.empty())
            status.update(label="渲染完成" if rc == 0 else "渲染失败",
                          state="complete" if rc == 0 else "error")

            if rc == 0:
                st.success("✅ 渲染成功！")
                st.rerun()
            else:
                st.error(f"❌ 渲染失败 (code={rc})")
