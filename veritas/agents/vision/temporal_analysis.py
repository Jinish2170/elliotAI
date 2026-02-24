"""
Veritas Vision Module — Computer Vision Temporal Analysis

Detects dynamic content changes using SSIM and optical flow,
with adaptive thresholds based on content type.

Memory-safe operations designed for 8GB RAM systems:
- Uses 640x480 resize for efficient memory usage
- Explicit garbage collection after image processing
- Memory budget check at initialization
"""

import gc
import logging
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import psutil

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("PIL not available - temporal analysis will be limited")

try:
    from skimage.transform import resize
    from skimage.metrics import structural_similarity as ssim
    SKIMAGE_AVAILABLE = True
except ImportError:
    SKIMAGE_AVAILABLE = False
    logging.warning("scikit-image not available - SSIM computation disabled")

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logging.warning("opencv-python not available - optical flow computation disabled")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from config.site_types import SiteType

logger = logging.getLogger("veritas.temporal.cv")


class TemporalAnalyzer:
    """
    CV-based temporal analysis for detecting dynamic content changes.

    Uses:
    1. SSIM (Structural Similarity Index) for overall change detection
    2. Optical flow for region-level change detection

    Adaptive thresholds based on content type ensure appropriate sensitivity:
    - E-commerce: 0.15 (sensitive - dynamic pricing/inventory)
    - Subscription: 0.20 (moderate - SaaS dynamic features)
    - News/blog: 0.35 (conservative - mostly static content)
    - Phishing/scan: 0.10 (most sensitive - any change could be malicious)
    - Default: 0.30

    Usage:
        analyzer = TemporalAnalyzer(content_type="ecommerce")
        result = analyzer.analyze_temporal_changes("t0.jpg", "t10.jpg")
        print(result['has_changes'], result['ssim_score'])
    """

    # Image resize dimensions for memory efficiency (640x480 = 0.3MP)
    RESIZE_WIDTH = 640
    RESIZE_HEIGHT = 480

    # Optical flow threshold for motion detection
    OPTICAL_FLOW_THRESHOLD = 0.5

    # Minimum memory requirement for CV operations (2GB)
    MIN_MEMORY_GB = 2.0

    # Adaptive SSIM thresholds by content type
    # Lower thresholds = more sensitive to changes
    SSIM_THRESHOLDS: dict[str, float] = {
        'e_commerce': 0.15,
        'subscription': 0.20,
        'news/blog': 0.35,
        'phishing/scan': 0.10,
        'default': 0.30
    }

    def __init__(self, content_type: str = 'default'):
        """
        Initialize the temporal analyzer.

        Args:
            content_type: Content type for adaptive SSIM thresholds.
                Options: 'e_commerce', 'subscription', 'news/blog',
                'phishing/scan', 'default'

        Raises:
            MemoryError: If insufficient memory for CV operations
            ImportError: If required dependencies missing
        """
        self.content_type = content_type
        self._check_dependencies()
        self._check_memory_budget()

    @property
    def SSIM_THRESHOLD(self) -> float:
        """Get the SSIM threshold for the current content type."""
        return self.SSIM_THRESHOLDS.get(
            self.content_type,
            self.SSIM_THRESHOLDS['default']
        )

    @staticmethod
    def get_threshold_for_site_type(site_type: SiteType) -> float:
        """
        Get SSIM threshold for a SiteType enum value.

        Args:
            site_type: SiteType enum value

        Returns:
            SSIM threshold for the site type
        """
        # Map SiteType to content_type keys
        type_mapping = {
            SiteType.ECOMMERCE: 'e_commerce',
            SiteType.SAAS_SUBSCRIPTION: 'subscription',
            SiteType.COMPANY_PORTFOLIO: 'news/blog',
            SiteType.FINANCIAL: 'news/blog',
            SiteType.DARKNET_SUSPICIOUS: 'phishing/scan'
        }
        content_type = type_mapping.get(site_type, 'default')
        return TemporalAnalyzer.SSIM_THRESHOLDS.get(
            content_type,
            TemporalAnalyzer.SSIM_THRESHOLDS['default']
        )

    def _check_dependencies(self) -> None:
        """Verify required dependencies are available."""
        if not PIL_AVAILABLE:
            raise ImportError("PIL is required for temporal analysis")
        if not SKIMAGE_AVAILABLE:
            log_msg = "scikit-image not installed - SSIM will use fallback"
            logger.warning(log_msg)

    def _check_memory_budget(self) -> None:
        """Ensure sufficient memory for CV operations."""
        available_gb = psutil.virtual_memory().available / (1024 ** 3)
        if available_gb < self.MIN_MEMORY_GB:
            raise MemoryError(
                f"Insufficient memory for CV operations: "
                f"{available_gb:.2f}GB available, "
                f"{self.MIN_MEMORY_GB:.2f}GB required"
            )

    def _load_and_resize(self, image_path: str) -> Optional[np.ndarray]:
        """
        Load image and resize for memory efficiency.

        Args:
            image_path: Path to the image file

        Returns:
            Grayscale numpy array (640x480) or None if loading fails
        """
        try:
            if not PIL_AVAILABLE:
                return None

            with Image.open(image_path) as img:
                # Convert to grayscale
                img_gray = img.convert('L')
                img_array = np.array(img_gray)

                # Resize to target dimensions if needed
                if (img_array.shape[0] != self.RESIZE_HEIGHT or
                    img_array.shape[1] != self.RESIZE_WIDTH):
                    using_resize = resize(
                        img_array,
                        (self.RESIZE_HEIGHT, self.RESIZE_WIDTH),
                        preserve_range=True,
                        anti_aliasing=False
                    )
                    return using_resize.astype(np.uint8)

                return img_array.astype(np.uint8)

        except FileNotFoundError:
            logger.error(f"Image file not found: {image_path}")
            return None
        except Exception as e:
            logger.error(f"Image loading failed: {e}")
            return None

    def compute_ssim(self, img1_path: str, img2_path: str) -> float:
        """
        Compute SSIM between two screenshots.

        SSIM returns a value between -1 and 1:
        - 1.0 = identical images
        - 0.0 = no structural similarity
        - -1.0 = completely dissimilar

        Note: scikit-image SSIM returns similarity, not distance.
        Lower value = more different, higher value = more similar.

        Args:
            img1_path: Path to first image (t0)
            img2_path: Path to second image (t+delay)

        Returns:
            SSIM score (0-1, where 0 = completely different, 1 = identical)
            Returns 0.5 on error (midpoint, indicating uncertainty)
        """
        if not SKIMAGE_AVAILABLE:
            # Fallback to normalized cross-correlation
            return self._compute_cross_correlation(img1_path, img2_path)

        try:
            img1 = self._load_and_resize(img1_path)
            img2 = self._load_and_resize(img2_path)

            if img1 is None or img2 is None:
                logger.warning("Failed to load images for SSIM computation")
                return 0.5

            # Compute SSIM (similarity score)
            # Using data_range=255 because images are uint8 (0-255)
            score = ssim(img1, img2, data_range=255)

            # Clean up memory immediately
            del img1, img2
            gc.collect()

            # Ensure score is in [0, 1] range
            return float(max(0.0, min(1.0, score)))

        except Exception as e:
            logger.error(f"SSIM computation failed: {e}")
            return 0.5

    def _compute_cross_correlation(
        self,
        img1_path: str,
        img2_path: str
    ) -> float:
        """
        Fallback method: Compute normalized cross-correlation between images.

        Used when scikit-image is not available.

        Args:
            img1_path: Path to first image
            img2_path: Path to second image

        Returns:
            Correlation score (0-1, where 0 = completely different, 1 = identical)
        """
        try:
            img1 = self._load_and_resize(img1_path)
            img2 = self._load_and_resize(img2_path)

            if img1 is None or img2 is None:
                return 0.5

            # Normalized cross-correlation
            mean1, std1 = img1.mean(), img1.std()
            mean2, std2 = img2.mean(), img2.std()

            # Avoid division by zero
            if std1 < 1e-8 or std2 < 1e-8:
                del img1, img2
                gc.collect()
                return 0.5

            norm1 = (img1 - mean1) / std1
            norm2 = (img2 - mean2) / std2

            correlation = (norm1 * norm2).mean()

            del img1, img2, norm1, norm2
            gc.collect()

            # Clamp to [0, 1] range
            return float(max(0.0, min(1.0, correlation)))

        except Exception as e:
            logger.error(f"Cross-correlation computation failed: {e}")
            return 0.5

    def compute_optical_flow(
        self,
        img1_path: str,
        img2_path: str
    ) -> tuple[np.ndarray, float]:
        """
        Compute optical flow between two images for region-level change detection.

        Uses Farneback method (dense optical flow) to detect motion between frames.

        Args:
            img1_path: Path to first image (t0)
            img2_path: Path to second image (t+delay)

        Returns:
            Tuple of (flow_magnitude, max_magnitude):
            - flow_magnitude: 2D numpy array of flow magnitudes per pixel
            - max_magnitude: Maximum flow magnitude in the image

            Returns (None, 0.0) if opencv-python not available or computation fails
        """
        if not CV2_AVAILABLE:
            logger.debug("opencv-python not available - optical flow computation skipped")
            return None, 0.0

        try:
            img1 = self._load_and_resize(img1_path)
            img2 = self._load_and_resize(img2_path)

            if img1 is None or img2 is None:
                logger.warning("Failed to load images for optical flow computation")
                return None, 0.0

            # Compute dense optical flow using Farneback algorithm
            # flow is a 2D array of (dx, dy) vectors for each pixel
            flow = cv2.calcOpticalFlowFarneback(
                img1, img2, None,
                pyr_scale=0.5,
                levels=3,
                winsize=15,
                iterations=3,
                poly_n=5,
                poly_sigma=1.2,
                flags=0
            )

            # Compute magnitude of flow vectors
            # flow is (height, width, 2): last dim contains (x_flow, y_flow)
            magnitude, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])

            max_magnitude = float(np.max(magnitude)) if magnitude.size > 0 else 0.0

            # Clean up memory
            del img1, img2, flow
            gc.collect()

            return magnitude, max_magnitude

        except Exception as e:
            logger.error(f"Optical flow computation failed: {e}")
            return None, 0.0

    def detect_changed_regions(
        self,
        img1_path: str,
        img2_path: str,
        threshold: Optional[float] = None
    ) -> list[dict]:
        """
        Detect regions with significant visual changes using optical flow.

        Args:
            img1_path: Path to first image (t0)
            img2_path: Path to second image (t+delay)
            threshold: Optional custom threshold (defaults to OPTICAL_FLOW_THRESHOLD)

        Returns:
            List of dictionaries describing changed regions:
            [
                {
                    'bbox': [x, y, width, height],
                    'center': [cx, cy],
                    'magnitude': float,
                    'area_percent': float
                },
                ...
            ]

            Returns empty list if opencv-python not available
        """
        if threshold is None:
            threshold = self.OPTICAL_FLOW_THRESHOLD

        flow_magnitude, max_magnitude = self.compute_optical_flow(img1_path, img2_path)

        if flow_magnitude is None:
            return []

        # Create binary mask for significant motion
        # Pixels with magnitude above threshold are considered "changed"
        changed_mask = flow_magnitude > threshold

        # Find connected components (contiguous changed regions)
        if not CV2_AVAILABLE:
            # Fallback: simple thresholding without region detection
            changed_pixels = np.sum(changed_mask)
            total_pixels = flow_magnitude.size
            return [{
                'bbox': [0, 0, self.RESIZE_WIDTH, self.RESIZE_HEIGHT],
                'center': [self.RESIZE_WIDTH // 2, self.RESIZE_HEIGHT // 2],
                'magnitude': max_magnitude,
                'num_changed': int(changed_pixels),
                'total_pixels': total_pixels,
                'area_percent': float(changed_pixels / total_pixels * 100)
            }]

        try:
            # Find contours of changed regions
            mask_uint8 = (changed_mask * 255).astype(np.uint8)
            contours, _ = cv2.findContours(
                mask_uint8,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )

            changed_regions = []

            for contour in contours:
                if cv2.contourArea(contour) < 100:  # Ignore very small regions
                    continue

                # Get bounding box
                x, y, w, h = cv2.boundingRect(contour)
                cx, cy = x + w // 2, y + h // 2

                # Get average flow magnitude in this region
                roi_magnitude = flow_magnitude[y:y+h, x:x+w]
                avg_magnitude = float(np.mean(roi_magnitude)) if roi_magnitude.size > 0 else 0.0

                area_percent = float((w * h) / (flow_magnitude.size) * 100)

                changed_regions.append({
                    'bbox': [int(x), int(y), int(w), int(h)],
                    'center': [int(cx), int(cy)],
                    'magnitude': avg_magnitude,
                    'area_percent': area_percent
                })

            # Clean up
            del flow_magnitude, changed_mask, mask_uint8
            gc.collect()

            return sorted(changed_regions, key=lambda r: r['magnitude'], reverse=True)

        except Exception as e:
            logger.error(f"Region detection failed: {e}")
            return []

    def analyze_temporal_changes(
        self,
        t0_screenshot: str,
        t_delay_screenshot: str,
        detect_regions: bool = False
    ) -> dict:
        """
        Analyze temporal changes between two screenshots.

        Combines SSIM (global similarity) and optional optical flow
        (region-level changes) to determine if meaningful visual
        changes occurred.

        Args:
            t0_screenshot: Path to initial screenshot
            t_delay_screenshot: Path to delayed screenshot
            detect_regions: If True, compute optical flow for region analysis

        Returns:
            Dictionary with analysis results:
            {
                'has_changes': bool,
                'ssim_score': float,
                'ssim_threshold': float,
                'changed_regions': list[dict],  # Only if detect_regions=True
                'recommendation': str  # 'analyze_all' or 'fullpage_only'
            }
        """
        # Compute SSIM similarity
        ssim_score = self.compute_ssim(t0_screenshot, t_delay_screenshot)

        # Determine if changes detected
        # Note: Higher SSIM = more similar
        # SSIM > threshold means MORE similar than expected change threshold
        # So has_changes should be True when SSIM < threshold (less similar)
        has_changes = ssim_score < self.SSIM_THRESHOLD

        # Determine recommendation for downstream processing
        if has_changes:
            recommendation = 'analyze_all'
        else:
            recommendation = 'fullpage_only'

        result = {
            'has_changes': has_changes,
            'ssim_score': ssim_score,
            'ssim_threshold': self.SSIM_THRESHOLD,
            'changed_regions': [],
            'recommendation': recommendation
        }

        # Optionally compute optical flow for region-level analysis
        if detect_regions and CV2_AVAILABLE:
            changed_regions = self.detect_changed_regions(
                t0_screenshot,
                t_delay_screenshot
            )
            result['changed_regions'] = changed_regions

        return result

    def get_content_type_config(self) -> dict:
        """
        Get configuration for the current content type.

        Returns:
            Dictionary with content-type specific settings
        """
        return {
            'content_type': self.content_type,
            'ssim_threshold': self.SSIM_THRESHOLD,
            'optical_flow_threshold': self.OPTICAL_FLOW_THRESHOLD,
            'resize_dimensions': (self.RESIZE_WIDTH, self.RESIZE_HEIGHT),
            'min_memory_gb': self.MIN_MEMORY_GB
        }


# ============================================================
# Utility Functions
# ============================================================

def get_all_available_thresholds() -> dict[str, float]:
    """
    Get all available SSIM thresholds.

    Returns:
        Dictionary of content_type -> threshold mappings
    """
    return TemporalAnalyzer.SSIM_THRESHOLDS.copy()


def is_cv_module_available() -> dict[str, bool]:
    """
    Check which CV modules are available.

    Returns:
        Dictionary with availability status of each module
    """
    return {
        'pillow': PIL_AVAILABLE,
        'scikit-image': SKIMAGE_AVAILABLE,
        'opencv-python': CV2_AVAILABLE
    }