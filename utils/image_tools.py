from PIL import Image

def restricted_resize_image(
        image: Image.Image,
        target_width: int,
        target_height: int,
        priority: str = "height"
) -> Image.Image:
    """
    Resize the image to fit within the target dimensions with respect to its original aspect ratio.

    Process:
        - Compute original aspect ratio
        - If priority == "height":
            • If target_height > orig_height, scale image up to match target_height and width according to the aspect ratio.
            • Otherwise, keep original dimensions.
            • If new_width > target_width (i.e. you’ve blown out the width),
              clamp new_width to target_width and reduce height according to aspect ratio.
        - If priority == "width":
            • If target_width > orig_width, scale image up to match target_width and height according to the aspect ratio.
            • Otherwise, keep original dimensions.
            • If new_height > target_height (i.e. you’ve blown out the height),
              clamp new_height to target_height and reduce width according to aspect ratio.
        - Finally, call image.resize((new_width, new_height), Image.LANCZOS) and return.

    Args:
        image (Image.Image): The original PIL image.
        target_width (int): The maximum allowed width.
        target_height (int): The maximum allowed height.
        priority (str, optional): Either "height" or "width", determining the scaling priority.
                                  Defaults to "height".

    Returns:
        Image.Image: The resized image.

    Raises:
        ValueError: If `priority` is not either "height" or "width".
    """

    # Original dimensions and aspect ratio
    orig_width: int
    orig_height: int
    orig_width, orig_height = image.size

    new_height: int = orig_height
    new_width: int = orig_width

    aspect_ratio: float = orig_width / orig_height

    # Calculate new dimensions before scaling
    # Scale by height
    if priority == "height":
        # Scale to meet the target height first.
        if target_height > orig_height:
            new_height: int = target_height
            new_width: int = int(target_height * aspect_ratio)

        # If the width exceeds the target, scale down to meet target width.
        if new_width > target_width:
            new_width = target_width
            new_height = int(target_width / aspect_ratio)

    # Scale by width
    elif priority == "width":
        # Scale to meet the target width first.
        if target_width > orig_width:
            new_width: int = target_width
            new_height: int = int(target_width / aspect_ratio)

        # If the height exceeds the target, scale down to meet target height.
        if new_height > target_height:
            new_height = target_height
            new_width = int(target_height * aspect_ratio)
    else:
        raise ValueError("priority must be either 'height' or 'width'.")

    # Scale image by calculated dimensions
    return image.resize((new_width, new_height), Image.LANCZOS)