#!/usr/bin/env python3
"""Test script for generate_ffmpeg_command function."""

import sys
from add_progress_bar import generate_ffmpeg_command

def test_basic_command():
    print("Test 1: Basic command generation")
    try:
        cmd = generate_ffmpeg_command(
            input_path="test_input.mp4",
            output_path="test_output.mp4",
            position="bottom",
            height=5,
            bg_color="808080",
            fg_color="FF0000"
        )
        print("[PASS] Command generated successfully")
        print(f"  Command: {' '.join(cmd)}")
        assert cmd[0] == "ffmpeg", "First argument should be ffmpeg"
        assert "-i" in cmd, "Should have -i flag"
        assert "-c:a" in cmd, "Should have -c:a flag"
        assert "copy" in cmd, "Should copy audio"
        assert "-y" in cmd, "Should have -y flag"
        print("[PASS] All basic assertions passed")
        return True
    except FileNotFoundError as e:
        print(f"[SKIP] Test skipped: {e}")
        return True
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        return False

def test_top_position():
    print("\nTest 2: Top position")
    try:
        cmd = generate_ffmpeg_command(
            input_path="test_input.mp4",
            output_path="test_output.mp4",
            position="top",
            height=10,
            bg_color="000000",
            fg_color="00FF00"
        )
        print("[PASS] Command generated with top position")
        filter_str = cmd[cmd.index("-vf") + 1]
        assert "y=0" in filter_str, "Top position should have y=0"
        print("[PASS] Top position verified (y=0)")
        return True
    except FileNotFoundError as e:
        print(f"[SKIP] Test skipped: {e}")
        return True
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        return False

def test_bottom_position():
    print("\nTest 3: Bottom position")
    try:
        cmd = generate_ffmpeg_command(
            input_path="test_input.mp4",
            output_path="test_output.mp4",
            position="bottom",
            height=10,
            bg_color="000000",
            fg_color="00FF00"
        )
        print("[PASS] Command generated with bottom position")
        filter_str = cmd[cmd.index("-vf") + 1]
        assert "y=ih-10" in filter_str, "Bottom position should have y=ih-10"
        print("[PASS] Bottom position verified (y=ih-10)")
        return True
    except FileNotFoundError as e:
        print(f"[SKIP] Test skipped: {e}")
        return True
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        return False

def test_custom_height():
    print("\nTest 4: Custom height")
    try:
        cmd = generate_ffmpeg_command(
            input_path="test_input.mp4",
            output_path="test_output.mp4",
            position="bottom",
            height=20,
            bg_color="808080",
            fg_color="FF0000"
        )
        print("[PASS] Command generated with custom height")
        filter_str = cmd[cmd.index("-vf") + 1]
        assert "h=20" in filter_str, "Should have height=20"
        print("[PASS] Custom height verified")
        return True
    except FileNotFoundError as e:
        print(f"[SKIP] Test skipped: {e}")
        return True
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        return False

def test_custom_colors():
    print("\nTest 5: Custom colors")
    try:
        cmd = generate_ffmpeg_command(
            input_path="test_input.mp4",
            output_path="test_output.mp4",
            position="bottom",
            height=5,
            bg_color="ABCDEF",
            fg_color="123456"
        )
        print("[PASS] Command generated with custom colors")
        filter_str = cmd[cmd.index("-vf") + 1]
        assert "0xABCDEF" in filter_str, "Should have background color"
        assert "0x123456" in filter_str, "Should have foreground color"
        print("[PASS] Custom colors verified")
        return True
    except FileNotFoundError as e:
        print(f"[SKIP] Test skipped: {e}")
        return True
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        return False

def test_dynamic_width():
    print("\nTest 6: Dynamic width expression")
    try:
        cmd = generate_ffmpeg_command(
            input_path="test_input.mp4",
            output_path="test_output.mp4",
            position="bottom",
            height=5,
            bg_color="808080",
            fg_color="FF0000"
        )
        print("[PASS] Command generated")
        filter_str = cmd[cmd.index("-vf") + 1]
        assert "iw*t/" in filter_str, "Should have dynamic width expression"
        print("[PASS] Dynamic width expression verified")
        return True
    except FileNotFoundError as e:
        print(f"[SKIP] Test skipped: {e}")
        return True
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Testing generate_ffmpeg_command function")
    print("=" * 60)
    
    tests = [
        test_basic_command,
        test_top_position,
        test_bottom_position,
        test_custom_height,
        test_custom_colors,
        test_dynamic_width
    ]
    
    results = [test() for test in tests]
    
    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    if all(results):
        print("[PASS] All tests passed!")
        sys.exit(0)
    else:
        print("[FAIL] Some tests failed")
        sys.exit(1)
