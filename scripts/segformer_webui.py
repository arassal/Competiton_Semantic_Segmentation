import argparse
import base64
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import cv2
import numpy as np
import torch
from PIL import Image as PilImage
from transformers import SegformerForSemanticSegmentation, SegformerImageProcessor


DEFAULT_MODEL_ID = 'nvidia/segformer-b0-finetuned-cityscapes-512-1024'


HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SegFormer Dashcam Viewer</title>
  <style>
    :root {
      color-scheme: light;
      font-family: Arial, Helvetica, sans-serif;
      background: #f6f7f8;
      color: #161a1d;
    }
    body {
      margin: 0;
    }
    header {
      padding: 18px 24px;
      background: #ffffff;
      border-bottom: 1px solid #d6d9dc;
    }
    h1 {
      margin: 0 0 6px;
      font-size: 24px;
      line-height: 1.2;
    }
    p {
      margin: 0;
      color: #4a535b;
      line-height: 1.45;
    }
    main {
      padding: 18px 24px 28px;
    }
    .toolbar {
      display: flex;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
      margin-bottom: 16px;
    }
    button, select {
      border: 1px solid #aeb6bf;
      border-radius: 6px;
      background: #ffffff;
      color: #161a1d;
      padding: 9px 12px;
      font-size: 15px;
    }
    button {
      cursor: pointer;
    }
    button:disabled {
      opacity: 0.55;
      cursor: default;
    }
    .status {
      min-height: 22px;
      color: #4a535b;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }
    figure {
      margin: 0;
      background: #ffffff;
      border: 1px solid #d6d9dc;
      border-radius: 6px;
      overflow: hidden;
    }
    figcaption {
      padding: 10px 12px;
      font-weight: 700;
      border-bottom: 1px solid #e4e6e8;
    }
    img {
      display: block;
      width: 100%;
      height: auto;
      background: #111;
    }
    pre {
      white-space: pre-wrap;
      background: #ffffff;
      border: 1px solid #d6d9dc;
      border-radius: 6px;
      padding: 12px;
      margin: 14px 0 0;
      color: #20262b;
    }
    @media (max-width: 900px) {
      .grid {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <header>
    <h1>SegFormer Dashcam Viewer</h1>
    <p>Raw image in, SegFormer semantic overlay and road/sidewalk masks out. No YOLO is used in this viewer.</p>
  </header>
  <main>
    <div class="toolbar">
      <button id="prev">Previous</button>
      <button id="next">Next</button>
      <select id="imageSelect"></select>
      <button id="run">Run SegFormer</button>
      <span class="status" id="status">Loading image list...</span>
    </div>
    <div class="grid">
      <figure>
        <figcaption>RAW INPUT - unmodified</figcaption>
        <img id="raw" alt="Raw input">
      </figure>
      <figure>
        <figcaption>SegFormer + HSV overlay</figcaption>
        <img id="overlay" alt="SegFormer overlay">
      </figure>
      <figure>
        <figcaption>Road mask raw</figcaption>
        <img id="roadRaw" alt="Raw road mask">
      </figure>
      <figure>
        <figcaption>Road mask refined</figcaption>
        <img id="road" alt="Road mask">
      </figure>
      <figure>
        <figcaption>Sidewalk mask</figcaption>
        <img id="sidewalk" alt="Sidewalk mask">
      </figure>
      <figure>
        <figcaption>Lane hint mask</figcaption>
        <img id="laneHint" alt="Lane hint mask">
      </figure>
    </div>
    <pre id="metadata">Select an image and run SegFormer.</pre>
  </main>
  <script>
    let images = [];
    let index = 0;
    const select = document.getElementById('imageSelect');
    const statusEl = document.getElementById('status');
    const rawEl = document.getElementById('raw');
    const overlayEl = document.getElementById('overlay');
    const roadRawEl = document.getElementById('roadRaw');
    const roadEl = document.getElementById('road');
    const sidewalkEl = document.getElementById('sidewalk');
    const laneHintEl = document.getElementById('laneHint');
    const metadataEl = document.getElementById('metadata');

    function setStatus(text) {
      statusEl.textContent = text;
    }

    function current() {
      return images[index];
    }

    function refreshRaw() {
      if (!current()) return;
      select.value = String(index);
      rawEl.src = `/image?index=${index}&t=${Date.now()}`;
      overlayEl.removeAttribute('src');
      roadRawEl.removeAttribute('src');
      roadEl.removeAttribute('src');
      sidewalkEl.removeAttribute('src');
      laneHintEl.removeAttribute('src');
      metadataEl.textContent = 'Segmentation not run for this selection yet.';
      setStatus(`Selected ${current().name}`);
    }

    async function loadImages() {
      const res = await fetch('/api/images');
      const data = await res.json();
      images = data.images;
      select.innerHTML = '';
      images.forEach((img, i) => {
        const option = document.createElement('option');
        option.value = String(i);
        option.textContent = img.name;
        select.appendChild(option);
      });
      if (images.length === 0) {
        setStatus('No images found.');
        return;
      }
      refreshRaw();
    }

    async function runSegmentation() {
      if (!current()) return;
      setStatus('Running SegFormer...');
      document.getElementById('run').disabled = true;
      try {
        const res = await fetch(`/api/segment?index=${index}`);
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.error || 'Segmentation failed');
        }
        overlayEl.src = data.overlay;
        roadRawEl.src = data.road_mask_raw;
        roadEl.src = data.road_mask;
        sidewalkEl.src = data.sidewalk_mask;
        laneHintEl.src = data.lane_hint_mask;
        metadataEl.textContent = JSON.stringify(data.metadata, null, 2);
        setStatus(`Done in ${data.metadata.timing_ms.toFixed(1)} ms`);
      } catch (err) {
        setStatus(err.message);
      } finally {
        document.getElementById('run').disabled = false;
      }
    }

    document.getElementById('prev').addEventListener('click', () => {
      if (!images.length) return;
      index = (index - 1 + images.length) % images.length;
      refreshRaw();
    });
    document.getElementById('next').addEventListener('click', () => {
      if (!images.length) return;
      index = (index + 1) % images.length;
      refreshRaw();
    });
    select.addEventListener('change', () => {
      index = Number(select.value);
      refreshRaw();
    });
    document.getElementById('run').addEventListener('click', runSegmentation);

    loadImages().catch(err => setStatus(err.message));
  </script>
</body>
</html>
"""


def parse_args():
    parser = argparse.ArgumentParser(description='Local SegFormer image viewer.')
    parser.add_argument('--image-dir', default='proof/segformer_raw_dashcam_inputs')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=7861)
    parser.add_argument('--model-id', default=DEFAULT_MODEL_ID)
    parser.add_argument('--device', default='cpu')
    parser.add_argument('--enable-hsv-refinement', action='store_true', default=True)
    parser.add_argument('--disable-hsv-refinement', action='store_false', dest='enable_hsv_refinement')
    return parser.parse_args()


def collect_images(image_dir):
    root = Path(image_dir)
    images = []
    for pattern in ('*.jpg', '*.jpeg', '*.png', '*.bmp'):
        images.extend(root.glob(pattern))
    return sorted(images)


def encode_image(image, extension='.jpg'):
    ok, buffer = cv2.imencode(extension, image)
    if not ok:
        raise RuntimeError('Failed to encode image')
    encoded = base64.b64encode(buffer).decode('ascii')
    mime = 'image/png' if extension == '.png' else 'image/jpeg'
    return f'data:{mime};base64,{encoded}'


class SegFormerRunner:
    def __init__(self, model_id, device, enable_hsv_refinement):
        self.model_id = model_id
        self.device = torch.device(device if device != 'cpu' else 'cpu')
        self.enable_hsv_refinement = enable_hsv_refinement
        self.processor = SegformerImageProcessor.from_pretrained(model_id)
        self.model = SegformerForSemanticSegmentation.from_pretrained(model_id).to(self.device)
        self.model.eval()
        self.id2label = {int(k): v for k, v in self.model.config.id2label.items()}
        self.label2id = {label.lower(): idx for idx, label in self.id2label.items()}
        self.lock = threading.Lock()

    def segment(self, image_path):
        frame = cv2.imread(str(image_path))
        if frame is None:
            raise RuntimeError(f'Failed to read {image_path}')
        start = time.perf_counter()
        with self.lock, torch.no_grad():
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            inputs = self.processor(images=PilImage.fromarray(frame_rgb), return_tensors='pt')
            inputs = {key: value.to(self.device) for key, value in inputs.items()}
            logits = self.model(**inputs).logits
            logits = torch.nn.functional.interpolate(
                logits,
                size=frame.shape[:2],
                mode='bilinear',
                align_corners=False,
            )
            class_mask = logits.argmax(dim=1)[0].cpu().numpy().astype(np.uint8)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        road_raw = self._binary_mask(class_mask, 'road')
        sidewalk = self._binary_mask(class_mask, 'sidewalk')
        road, lane_hint = self._refine_masks(frame, road_raw, sidewalk)
        overlay = self._overlay(frame, class_mask, road, lane_hint)
        unique, counts = np.unique(class_mask, return_counts=True)
        class_counts = {
            self.id2label.get(int(class_id), str(class_id)): int(count)
            for class_id, count in zip(unique.tolist(), counts.tolist())
        }
        top_classes = sorted(class_counts.items(), key=lambda item: item[1], reverse=True)[:8]
        return {
            'overlay': encode_image(overlay),
            'road_mask_raw': encode_image(road_raw, '.png'),
            'road_mask': encode_image(road, '.png'),
            'sidewalk_mask': encode_image(sidewalk, '.png'),
            'lane_hint_mask': encode_image(lane_hint, '.png'),
            'metadata': {
                'image': str(image_path),
                'model_id': self.model_id,
                'hsv_refinement_enabled': self.enable_hsv_refinement,
                'road_pixels_raw': int(np.count_nonzero(road_raw)),
                'road_pixels': int(np.count_nonzero(road)),
                'sidewalk_pixels': int(np.count_nonzero(sidewalk)),
                'lane_hint_pixels': int(np.count_nonzero(lane_hint)),
                'top_classes': top_classes,
                'timing_ms': elapsed_ms,
                'yolo_used': False,
            },
        }

    def _binary_mask(self, class_mask, label):
        class_id = self.label2id.get(label)
        if class_id is None:
            return np.zeros(class_mask.shape, dtype=np.uint8)
        return (class_mask == class_id).astype(np.uint8) * 255

    def _refine_masks(self, frame, road_raw, sidewalk):
        if not self.enable_hsv_refinement:
            return road_raw, np.zeros_like(road_raw)

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        height, width = road_raw.shape
        roi = np.zeros((height, width), dtype=np.uint8)
        roi[int(height * 0.35):, :] = 255

        asphalt = cv2.inRange(hsv, (0, 0, 35), (179, 80, 185))
        white = cv2.inRange(hsv, (0, 0, 180), (179, 55, 255))
        yellow = cv2.inRange(hsv, (12, 55, 110), (42, 255, 255))
        lane_hint = cv2.bitwise_or(white, yellow)

        kernel_large = np.ones((21, 21), np.uint8)
        kernel_small = np.ones((5, 5), np.uint8)
        road_neighborhood = cv2.dilate(road_raw, kernel_large, iterations=1)
        asphalt_support = cv2.bitwise_and(asphalt, road_neighborhood)
        asphalt_support = cv2.bitwise_and(asphalt_support, roi)
        asphalt_support = cv2.bitwise_and(asphalt_support, cv2.bitwise_not(sidewalk))

        road = cv2.bitwise_or(road_raw, asphalt_support)
        road = cv2.morphologyEx(road, cv2.MORPH_CLOSE, kernel_large)
        road = cv2.morphologyEx(road, cv2.MORPH_OPEN, kernel_small)

        lane_hint = cv2.bitwise_and(lane_hint, roi)
        lane_hint = cv2.bitwise_and(lane_hint, cv2.dilate(road, kernel_large, iterations=1))
        lane_hint = cv2.morphologyEx(lane_hint, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        lane_hint = cv2.dilate(lane_hint, kernel_small, iterations=1)
        return road, lane_hint

    def _overlay(self, frame, class_mask, road_mask, lane_hint):
        colors = {
            'road': (70, 70, 70),
            'sidewalk': (120, 120, 120),
            'person': (0, 220, 255),
            'car': (255, 130, 0),
            'truck': (255, 80, 0),
            'bus': (255, 80, 80),
            'traffic light': (60, 220, 60),
            'traffic sign': (30, 180, 30),
            'building': (180, 180, 180),
            'vegetation': (60, 160, 60),
            'fence': (120, 90, 80),
        }
        color_mask = np.zeros_like(frame)
        for label, color in colors.items():
            class_id = self.label2id.get(label)
            if class_id is not None:
                color_mask[class_mask == class_id] = color
        color_mask[road_mask > 0] = (80, 80, 80)
        color_mask[lane_hint > 0] = (0, 255, 255)
        active = np.any(color_mask != 0, axis=2)
        overlay = frame.copy()
        blended = cv2.addWeighted(frame, 0.55, color_mask, 0.45, 0)
        overlay[active] = blended[active]
        return overlay


def make_handler(images, runner):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, status, content_type, body):
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, status, payload):
            self._send(status, 'application/json', json.dumps(payload).encode('utf-8'))

        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == '/':
                self._send(200, 'text/html; charset=utf-8', HTML.encode('utf-8'))
                return
            if parsed.path == '/api/images':
                payload = {
                    'images': [
                        {'index': idx, 'name': path.name, 'path': str(path)}
                        for idx, path in enumerate(images)
                    ]
                }
                self._send_json(200, payload)
                return
            if parsed.path == '/image':
                try:
                    index = int(parse_qs(parsed.query).get('index', ['0'])[0])
                    path = images[index]
                    data = path.read_bytes()
                    content_type = 'image/png' if path.suffix.lower() == '.png' else 'image/jpeg'
                    self._send(200, content_type, data)
                except Exception as exc:
                    self._send_json(400, {'error': str(exc)})
                return
            if parsed.path == '/api/segment':
                try:
                    index = int(parse_qs(parsed.query).get('index', ['0'])[0])
                    self._send_json(200, runner.segment(images[index]))
                except Exception as exc:
                    self._send_json(500, {'error': str(exc)})
                return
            self._send_json(404, {'error': 'not found'})

        def log_message(self, fmt, *args):
            return

    return Handler


def main():
    args = parse_args()
    images = collect_images(args.image_dir)
    if not images:
        raise RuntimeError(f'No images found in {args.image_dir}')
    print(f'Loading SegFormer model: {args.model_id}')
    runner = SegFormerRunner(args.model_id, args.device, args.enable_hsv_refinement)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(images, runner))
    print(f'Serving {len(images)} images from {args.image_dir}')
    print(f'Open http://{args.host}:{args.port}')
    server.serve_forever()


if __name__ == '__main__':
    main()
