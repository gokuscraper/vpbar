"""Video to GIF conversion with optional green screen removal."""

import subprocess
import shutil
import tempfile
from pathlib import Path

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def convert_video_to_gif(
    input_path: str, output_path: str,
    height: int = 60, green_screen: bool = False,
    green_threshold: int = 150
) -> bool:
    if not PIL_AVAILABLE:
        print("Error: Need Pillow: pip install Pillow")
        return False
    temp_dir = Path(tempfile.mkdtemp(prefix='video_to_gif_'))
    try:
        print(f'Extracting frames (height={height})...')
        subprocess.run([
            'ffmpeg', '-i', input_path,
            '-vf', f'scale=-2:{height}:flags=neighbor',
            '-vsync', 'cfr', '-y',
            str(temp_dir / 'frame_%04d.png')
        ], capture_output=True, check=True)
        frame_files = sorted(temp_dir.glob('frame_*.png'))
        if not frame_files:
            print('Error: No frames extracted')
            return False
        print(f'Extracted {len(frame_files)} frames')
        sample = Image.open(frame_files[0])
        print(f'Actual size: {sample.size}')
        print('Processing frames...')
        frames = []
        for frame_path in frame_files:
            img = Image.open(frame_path).convert('RGBA')
            if green_screen:
                pixels = img.load()
                for y in range(img.height):
                    for x in range(img.width):
                        r, g, b, a = pixels[x, y]
                        if g > green_threshold and g > r and g > b:
                            pixels[x, y] = (0, 0, 0, 0)
            frames.append(img)
        result = subprocess.run([
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=r_frame_rate',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            input_path
        ], capture_output=True, text=True)
        try:
            fps_str = result.stdout.strip()
            if '/' in fps_str:
                num, den = map(int, fps_str.split('/'))
                fps = num / den
            else:
                fps = float(fps_str)
            duration = int(1000 / fps)
        except:
            duration = 41
        print(f'Frame delay: {duration}ms ({1000/duration:.1f} fps)')
        print('Saving GIF...')
        frames[0].save(
            output_path, save_all=True,
            append_images=frames[1:],
            duration=duration, loop=0, disposal=2
        )
        print(f'Done! Output: {output_path}')
        print(f'Size: {Path(output_path).stat().st_size / 1024:.1f} KB')
        return True
    except Exception as e:
        print(f'Error: {e}')
        return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
