from PIL import Image

def restricted_resize_image(
        image: Image.Image,
        target_width: int,
        target_height: int
) -> Image.Image:
    """
    Resize the image to fully fit within the target dimensions while preserving its original aspect ratio.
    The image is always scaled up or down to maximize use of the target box without exceeding it.

    Process:
        - Compute original aspect ratio
        - Scale image to match target height and compute corresponding width
        - If resulting width exceeds target width, clamp width and recalculate height
        - Resize the image using the final dimensions
    """

    # Original dimensions and aspect ratio
    orig_width: int
    orig_height: int
    orig_width, orig_height = image.size

    aspect_ratio: float = orig_width / orig_height

    # Calculate new dimensions before scaling
    # Scale by height
    new_height = target_height
    new_width = int(target_height * aspect_ratio)

    if new_width > target_width:
        new_width = target_width
        new_height = int(target_width / aspect_ratio)

    # Scale image by calculated dimensions
    return image.resize((new_width, new_height), Image.LANCZOS)
