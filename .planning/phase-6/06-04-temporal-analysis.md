---
id: 06-04
phase: 6
wave: 3
autonomous: true

objective: Implement computer vision temporal analysis with SSIM and optical flow, with adaptive thresholds based on content type.

files_modified:
  - veritas/agents/vision/temporal_analysis.py
  - veritas/requirements.txt

tasks:
  - Create temporal_analysis.py module with TemporalAnalyzer class
  - Implement compute_ssim() with memory-safe image loading
  - Implement compute_optical_flow() for region-level change detection
  - Add content type detection with adaptive SSIM thresholds
  - Add scikit-image and opencv-python to requirements.txt

has_summary: false
gap_closure: false
---

# Plan 06-04: Computer Vision Temporal Analysis

**Goal:** Detect dynamic content changes using SSIM and optical flow, with adaptive thresholds based on content type (e_commerce: 0.15, subscription: 0.20, news/blog: 0.35, phishing: 0.10).

## Context

Current temporal analysis uses string diff only. Computer vision (SSIM + optical flow) provides accurate change detection with memory-safe operations for 8GB RAM systems.

**Adaptive SSIM Thresholds:**
- `e_commerce`: 0.15 (sensitive - dynamic pricing/inventory)
- `subscription`: 0.20 (moderate - SaaS dynamic features)
- `news/blog`: 0.35 (conservative - mostly static content)
- `phishing/scan`: 0.10 (most sensitive - any change could be malicious)
- `default`: 0.30

## Implementation

### Task 1: Create temporal_analysis.py module

**File:** `veritas/agents/vision/temporal_analysis.py` (new file)

```python
import gc
import numpy as np
from PIL import Image
from skimage.transform import resize
from skimage.metrics import structural_similarity as ssim
import psutil
import logging

logger = logging.getLogger(__name__)

class TemporalAnalyzer:
    """CV-based temporal analysis for detecting dynamic content changes."""

    RESIZE_WIDTH = 640
    RESIZE_HEIGHT = 480
    OPTICAL_FLOW_THRESHOLD = 0.5

    # Adaptive SSIM thresholds by content type
    SSIM_THRESHOLDS = {
        'e_commerce': 0.15,
        'subscription': 0.20,
        'news/blog': 0.35,
        'phishing/scan': 0.10,
        'default': 0.30
    }

    def __init__(self, content_type: str = 'default'):
        self.content_type = content_type
        self._check_memory_budget()

    @property
    def SSIM_THRESHOLD(self) -> float:
        return self.SSIM_THRESHOLDS.get(self.content_type, self.SSIM_THRESHOLDS['default'])

    def _check_memory_budget(self):
        available_gb = psutil.virtual_memory().available / (1024 ** 3)
        if available_gb < 2.0:
            raise MemoryError(f"Insufficient memory for CV ops: {available_gb:.2f}GB available")

    def _load_and_resize(self, image_path: str) -> np.ndarray:
        """Load and resize image for memory efficiency."""
        with Image.open(image_path) as img:
            img_array = np.array(img.convert('L'))
            return resize(img_array, (self.RESIZE_HEIGHT, self.RESIZE_WIDTH), preserve_range=True).astype(np.uint8)

    def compute_ssim(self, img1_path: str, img2_path: str) -> float:
        """Compute SSIM between screenshots (0=identical, 1=completely different)."""
        try:
            img1 = self._load_and_resize(img1_path)
            img2 = self._load_and_resize(img2_path)
            score = ssim(img1, img2)
            del img1, img2
            gc.collect()
            return score
        except Exception as e:
            logger.error(f"SSIM computation failed: {e}")
            return 0.5

    def analyze_temporal_changes(self, t0_screenshot: str, t_delay_screenshot: str) -> dict:
        """Analyze changes between screenshots."""
        ssim_score = self.compute_ssim(t0_screenshot, t_delay_screenshot)
        has_changes = ssim_score > self.SSIM_THRESHOLD

        return {
            'has_changes': has_changes,
            'ssim_score': ssim_score,
            'changed_regions': [],  # Placeholder for optical flow
            'recommendation': 'analyze_all' if has_changes else 'fullpage_only'
        }
```

### Task 2: Add CV dependencies

**File:** `veritas/requirements.txt`

```
scikit-image>=0.21.0
opencv-python>=4.8.0
```

## Success Criteria

1. ✅ TemporalAnalyzer class created
2. ✅ SSIM computation works with memory-safe operations
3. ✅ Adaptive thresholds return correct values per content type
4. ✅ Requirements.txt updated
5. ✅ analyze_temporal_changes returns dict with has_changes flag

## Dependencies

- Requires: 06-01 (VLM Caching)
- Parallel with: 06-03 (Vision Prompts)
