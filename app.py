"""Streamlit GUI for vpbar 鈥?dual-mode: quick (one-click) and pro (3-step workflow)."""

import os
from pathlib import Path

import streamlit as st

from vpbar.gui_utils import (
    PROJECT_ROOT, STYLE_DISPLAY_NAMES, DEFAULT_STYLE_DISPLAY, resolve_style_name,
    TEMP_DIR, SCRUBBER_DIR, SCRUBBER_DEFAULT,
    WHISPER_MODELS, get_video_duration, estimate_eta, run_cli_streaming,
    save_upload, parse_chapters, fmt_chapters, list_scrubbers,
)

SCRUBBERS = list_scrubbers()  # [(name, path), ...]
SCRUBBER_CHOICES = ["鏃?, "榛樿 (scrubber_final.gif)", *[s[0] for s in SCRUBBERS], "鑷畾涔変笂浼?.."]

st.set_page_config(page_title="瑙嗛杩涘害鏉＄敓鎴愬櫒", page_icon="馃幀", layout="wide")

for k, v in dict(video_path="", video_duration=0.0, srt_path="", srt_content="",
                 chapters_text="", output_path="", gif_path="", pro_step="鈶?杞啓").items():
    st.session_state.setdefault(k, v)

# 鈹€鈹€ Title & upload 鈹€鈹€
st.title("瑙嗛杩涘害鏉＄敓鎴愬櫒")
uploaded_file = st.file_uploader("涓婁紶瑙嗛鏂囦欢", type=["mp4", "mov", "mkv", "avi", "webm"])

if not uploaded_file:
    st.info("璇峰厛涓婁紶瑙嗛鏂囦欢")
    st.markdown("**鏀寔鏍煎紡:** MP4, MOV, MKV, AVI, WebM  |  **鍔熻兘:** 33 绉嶈繘搴︽潯鏍峰紡 路 FunASR/Whisper 杞啓 路 AI 鍒嗙珷 路 GIF 鎷栨嫿澶?)
    st.stop()

vid_path = str(TEMP_DIR / uploaded_file.name)
if st.session_state.video_path != vid_path or not os.path.isfile(vid_path):
    st.session_state.video_path = save_upload(uploaded_file)
    try:
        st.session_state.video_duration = get_video_duration(vid_path)
    except Exception:
        st.session_state.video_duration = 0.0

# 鈹€鈹€ Video preview 鈹€鈹€
st.markdown("""
<style>
[data-testid="stVideo"] { max-width: 300px; margin: 0 auto; }
</style>
""", unsafe_allow_html=True)
col_l, col_r = st.columns(2)
with col_l:
    st.caption("鍘熷瑙嗛")
    st.video(st.session_state.video_path)
with col_r:
    st.caption("缁撴灉棰勮")
    op = st.session_state.output_path
    if op and os.path.isfile(op):
        st.video(op)
        st.download_button("涓嬭浇鎴愬搧瑙嗛", open(op, "rb").read(), file_name=Path(op).name,
                           mime="video/mp4", use_container_width=True)
    else:
        st.info("鐢熸垚鍚庤繖閲屾樉绀虹粨鏋?)

# 鈹€鈹€ Modes 鈹€鈹€
qt, pt = st.tabs(["鈿?蹇嵎妯″紡", "馃敡 涓撲笟妯″紡"])

# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲
# QUICK MODE
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲
with qt:
    st.subheader("蹇嵎妯″紡 鈥?涓€閿叏鑷姩")
    c1, c2, c3 = st.columns(3)
    with c1:
        q_eng = st.selectbox("杞啓寮曟搸", ["funasr", "whisper"], key="q_eng")
    with c2:
        q_sty = st.selectbox("鏍峰紡", STYLE_DISPLAY_NAMES, index=STYLE_DISPLAY_NAMES.index(DEFAULT_STYLE_DISPLAY), key="q_sty")
    with c3:
        q_out = st.text_input("杈撳嚭鏂囦欢鍚?, key="q_out")

    cc1, cc2 = st.columns(2)
    with cc1:
        q_gif = st.checkbox("GIF 鎷栨嫿澶?, value=True, key="q_gif")
    with cc2:
        q_chp = st.checkbox("AI 鑷姩鍒嗙珷", value=True, key="q_chp")

    q_gif_path = ""
    q_gif_f_up = None
    if q_gif:
        q_gif_sel = st.selectbox("閫夋嫨鎷栨嫿澶?GIF", SCRUBBER_CHOICES, index=1, key="q_gif_sel")
        if q_gif_sel == "鑷畾涔変笂浼?..":
            q_gif_f_up = st.file_uploader("涓婁紶鑷畾涔?GIF", type=["gif"], key="q_gif_f_up")
            if q_gif_f_up:
                q_gif_path = save_upload(q_gif_f_up)
        elif q_gif_sel == "榛樿 (scrubber_final.gif)":
            q_gif_path = SCRUBBER_DEFAULT if os.path.isfile(SCRUBBER_DEFAULT) else ""
        # Show preview
        if q_gif_path:
            st.image(q_gif_path, width=100)
        elif q_gif_sel == "鏃?:
            pass
        else:
            for name, path in SCRUBBERS:
                if name == q_gif_sel:
                    q_gif_path = path
                    break
            if q_gif_path:
                st.image(q_gif_path, width=100)

    q_srt_f = st.file_uploader("涓婁紶 SRT锛堝彲閫夛級", type=["srt"], key="q_srt_f") if not q_chp else None

    dur = st.session_state.video_duration
    if dur:
        st.caption(f"**瑙嗛鏃堕暱:** {dur:.0f}s ({dur / 60:.1f}min)  |  **棰勮澶勭悊:** {estimate_eta(dur, q_eng, q_gif)}")

    if st.button("鈿?涓€閿敓鎴?, type="primary", use_container_width=True):
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

        status = st.status("姝ｅ湪澶勭悊...", expanded=True)
        rc, output = run_cli_streaming(cmd, status.empty())
        status.update(label="瀹屾垚" if rc == 0 else "澶辫触", state="complete" if rc == 0 else "error")

        if rc == 0:
            st.success("鉁?鐢熸垚鎴愬姛锛?)
            st.rerun()
        else:
            st.error(f"鉂?澶勭悊澶辫触 (code={rc})")

# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲
# PRO MODE
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲
with pt:
    st.subheader("涓撲笟妯″紡 鈥?涓夋宸ヤ綔娴?)
    cs1, cs2, cs3 = st.columns(3)
    with cs1:
        if st.button("鈶?杞啓", use_container_width=True,
                     type="primary" if st.session_state.pro_step == "鈶?杞啓" else "secondary"):
            st.session_state.pro_step = "鈶?杞啓"
            st.rerun()
    with cs2:
        if st.button("鈶?绔犺妭", use_container_width=True,
                     type="primary" if st.session_state.pro_step == "鈶?绔犺妭" else "secondary"):
            st.session_state.pro_step = "鈶?绔犺妭"
            st.rerun()
    with cs3:
        if st.button("鈶?娓叉煋", use_container_width=True,
                     type="primary" if st.session_state.pro_step == "鈶?娓叉煋" else "secondary"):
            st.session_state.pro_step = "鈶?娓叉煋"
            st.rerun()
    st.divider()

    if st.session_state.pro_step == "鈶?杞啓":
        p1e = st.selectbox("杞啓寮曟搸", ["funasr", "whisper"], key="p1e")
        is_whisper = p1e == "whisper"
        p1m = st.selectbox("Whisper 妯″瀷", WHISPER_MODELS, key="p1m", disabled=not is_whisper)
        p1d = st.radio("璁惧", ["auto", "cuda", "cpu"], horizontal=True, key="p1d",
                       disabled=not is_whisper, help=None if is_whisper else "FunASR 鍥哄畾浣跨敤 CPU")
        p1c = st.selectbox("璁＄畻绫诲瀷", ["default", "float16", "int8"], key="p1c",
                          disabled=not is_whisper, help=None if is_whisper else "浠?Whisper 鏀寔")

        st.info("宸叉湁瀛楀箷锛熺偣鍑讳笂鏂?**鈶?绔犺妭** 鐩存帴涓婁紶 SRT 鏂囦欢")

        c1, c2 = st.columns(2)
        with c1:
            p1_clicked = st.button("寮€濮嬭浆鍐?, type="primary", use_container_width=True, key="p1b")
        with c2:
            if st.session_state.srt_content and st.button("涓嬩竴姝?鈫?鈶?绔犺妭", use_container_width=True, key="p1_next"):
                st.session_state.pro_step = "鈶?绔犺妭"
                st.rerun()

        st.divider()

        if p1_clicked:
            srt_out = str(TEMP_DIR / f"{Path(uploaded_file.name).stem}.srt")
            cmd = ["transcribe", st.session_state.video_path, "-o", srt_out,
                   "--engine", p1e, "--model", p1m, "--device", p1d, "--compute-type", p1c]
            status = st.status("姝ｅ湪杞啓...", expanded=True)
            rc, _ = run_cli_streaming(cmd, status.empty())
            status.update(label="杞啓瀹屾垚" if rc == 0 else "杞啓澶辫触",
                          state="complete" if rc == 0 else "error")
            if rc == 0:
                st.session_state.srt_path = srt_out
                st.session_state.srt_content = Path(srt_out).read_text(encoding="utf-8")
                st.rerun()
        elif st.session_state.srt_content:
            st.success("鉁?杞啓瀹屾垚锛岀偣鍑讳笂鏂广€屼笅涓€姝?鈫?鈶?绔犺妭銆嶇户缁?)

    elif st.session_state.pro_step == "鈶?绔犺妭":
        up_srt = st.file_uploader("涓婁紶 SRT 鏂囦欢", type=["srt"], key="p2srt")
        if up_srt:
            st.session_state.srt_path = save_upload(up_srt)
            st.session_state.srt_content = Path(st.session_state.srt_path).read_text(encoding="utf-8")
            st.success(f"宸插姞杞?SRT锛歿up_srt.name}")

        if st.session_state.srt_content:
            st.text_area("SRT 棰勮锛堝彲缂栬緫锛?, st.session_state.srt_content, height=200, key="p2edit")
            if st.button("淇濆瓨 SRT 淇敼", key="p2save"):
                st.session_state.srt_content = st.session_state.p2edit
                Path(st.session_state.srt_path).write_text(st.session_state.srt_content, encoding="utf-8")
                st.toast("SRT 宸蹭繚瀛?, icon="鉁?)

        if not st.session_state.srt_content:
            st.warning("璇峰厛鍦ㄧ涓€姝ヨ浆鍐欐垨涓婁紶 SRT 鏂囦欢")
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                p2min = st.number_input("鏈€灏忕珷鑺傛暟", value=2, min_value=1, key="p2min")
            with c2:
                p2max = st.number_input("鏈€澶х珷鑺傛暟", value=4, min_value=1, key="p2max")
            with c3:
                p2ml = st.number_input("鏍囩鏈€澶ч暱搴?, value=7, min_value=3, key="p2ml")

            if st.button("AI 鐢熸垚绔犺妭", type="primary", key="p2gen"):
                cmd = ["chapters", "generate", "--srt", st.session_state.srt_path,
                       "--min-chapters", str(p2min), "--max-chapters", str(p2max),
                       "--max-label-length", str(p2ml)]
                status = st.status("姝ｅ湪鐢熸垚绔犺妭...", expanded=True)
                rc, output = run_cli_streaming(cmd, status.empty())
                status.update(label="绔犺妭鐢熸垚瀹屾垚" if rc == 0 else "鐢熸垚澶辫触",
                              state="complete" if rc == 0 else "error")
                if rc == 0 and output:
                    st.session_state.chapters_text = output
                    st.toast("绔犺妭宸茬敓鎴愶紝鍙户缁紪杈?, icon="鉁?)

            if st.session_state.chapters_text:
                items = parse_chapters(st.session_state.chapters_text) or [{"start": 0, "end": 0, "label": ""}]
                edited = st.data_editor(
                    items,
                    column_config={
                        "start": st.column_config.NumberColumn("寮€濮?绉?", min_value=0, format="%d"),
                        "end": st.column_config.NumberColumn("缁撴潫(绉?", min_value=0, format="%d"),
                        "label": st.column_config.TextColumn("绔犺妭鍚?, max_chars=20),
                    },
                    num_rows="dynamic",
                    use_container_width=True,
                    key="p2tbl",
                )
                if st.button("纭绔犺妭", type="primary", key="p2cf"):
                    st.session_state.chapters_text = fmt_chapters(edited)
                    st.session_state.pro_step = "鈶?娓叉煋"
                    st.rerun()

            st.text_area("绔犺妭鏂囨湰锛堜篃鍙洿鎺ョ矘璐达級", st.session_state.chapters_text, height=130, key="p2raw")

    elif st.session_state.pro_step == "鈶?娓叉煋":
        c1, c2 = st.columns(2)
        with c1:
            p3s = st.selectbox("鏍峰紡", STYLE_DISPLAY_NAMES, index=STYLE_DISPLAY_NAMES.index(DEFAULT_STYLE_DISPLAY), key="p3s")
        with c2:
            p3p = st.radio("浣嶇疆", ["bottom", "top", "middle"], horizontal=True, key="p3p")
        p3h = st.slider("楂樺害 (px)", 3, 100, 50, key="p3h")

        p3cr = st.slider("鍦嗚 (px)", 0, 25, 15, key="p3cr")
        p3gf = st.checkbox("GIF 鎷栨嫿澶?, value=True, key="p3gf")
        p3_gif_path = ""
        p3_gif_up = None
        if p3gf:
            p3_gif_sel = st.selectbox("閫夋嫨鎷栨嫿澶?GIF", SCRUBBER_CHOICES, index=1, key="p3_gif_sel")
            if p3_gif_sel == "鑷畾涔変笂浼?..":
                p3_gif_up = st.file_uploader("涓婁紶鑷畾涔?GIF", type=["gif"], key="p3_gif_up")
                if p3_gif_up:
                    p3_gif_path = save_upload(p3_gif_up)
            elif p3_gif_sel == "榛樿 (scrubber_final.gif)":
                p3_gif_path = SCRUBBER_DEFAULT if os.path.isfile(SCRUBBER_DEFAULT) else ""
            if p3_gif_path:
                st.image(p3_gif_path, width=100)
            elif p3_gif_sel == "鏃?:
                pass
            else:
                for name, path in SCRUBBERS:
                    if name == p3_gif_sel:
                        p3_gif_path = path
                        break
                if p3_gif_path:
                    st.image(p3_gif_path, width=100)
        p3sg = st.number_input("鍒嗘闂撮殧 (绉? 0=鑷姩)", value=0, key="p3sg")
        p3dw = st.number_input("鍒嗛殧绾垮搴?, value=3, min_value=0, key="p3dw",
                               help="0 = 涓嶆樉绀哄垎闅旂嚎")
        p3dr = st.slider("鍒嗛殧绾块珮搴︽瘮渚?, 0.0, 1.0, 0.8, key="p3dr")

        if st.button("寮€濮嬫覆鏌?, type="primary", use_container_width=True, key="p3r"):
            out_name = f"{Path(uploaded_file.name).stem}_pro.mp4"
            out_path = str(TEMP_DIR / out_name)
            st.session_state.output_path = out_path

            cmd = ["progress", "add", st.session_state.video_path, "-o", out_path,
                   "--style", resolve_style_name(p3s), "--position", p3p, "--height", str(p3h),
                   "--corner-radius", str(p3cr), "--segment-interval", str(p3sg),
                   "--divider-width", str(p3dw), "--divider-height-ratio", str(p3dr)]

            if p3gf and p3_gif_path:
                cmd += ["--scrubber-image", p3_gif_path]

            if st.session_state.chapters_text:
                cmd += ["--chapters", st.session_state.chapters_text]

            status = st.status("姝ｅ湪娓叉煋...", expanded=True)
            rc, _ = run_cli_streaming(cmd, status.empty())
            status.update(label="娓叉煋瀹屾垚" if rc == 0 else "娓叉煋澶辫触",
                          state="complete" if rc == 0 else "error")

            if rc == 0:
                st.success("鉁?娓叉煋鎴愬姛锛?)
                st.rerun()
            else:
                st.error(f"鉂?娓叉煋澶辫触 (code={rc})")
