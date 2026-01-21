from __future__ import annotations

from dataclasses import dataclass

PROMPT_TEMPLATE = (
    "16:9 YouTube thumbnail. No humans, no faces, no figures. "
    "Background is an iconic Middle Eastern textile collage made from overlapping Persian/Arabic rugs "
    "and carpet patches (kilim + Persian motifs), arranged as a clean patchwork wall / flat-lay. "
    "Rich authentic patterns: medallions, floral arabesques, geometric borders. "
    "Palette: deep maroon, oxblood red, rust, dark brown, muted beige, slightly faded antique look. "
    "Ultra-detailed woven fibers, visible rug pile texture, subtle wear, premium editorial feel. "
    "Create clear negative space at center for text.\n\n"
    "Add one single word title: ‘[TITLE]’ in large elegant serif typography, centered, cream/ivory ink, "
    "crisp edges, perfect kerning, high legibility, slight emboss or subtle shadow for separation (minimal).\n\n"
    "Optional minimal accents (choose max 2): a small white crescent moon icon in a corner, "
    "one tiny dried flower press detail, or a thin cream paper label strip blank (no readable text). "
    "Soft film grain, gentle vignette, cinematic contrast, 4K, ultra sharp.\n\n"
    "VIBE VARIANT: [VIBE]"
)

NEGATIVE_PROMPT = (
    "people, human, face, hands, portraits, characters, animals, watermark, logos, social media UI, "
    "clutter, neon colors, oversaturated, blurry, low-res, plastic texture, repeating AI patterns, "
    "distorted text, misspelling, extra icons, busy typography, gradients, cartoon, anime."
)

VIBE_MAP = {
    "dark": "darker exposure, deeper shadows, stronger vignette, moody.",
    "clean": "more center negative space, simpler rug patches near text, slightly brighter ivory title.",
    "antique": "older worn rug edges, subtle dust, archival museum flat-lay lighting.",
}


@dataclass(frozen=True)
class ImagePrompt:
    prompt: str
    negative_prompt: str


def build_image_prompt(title: str, vibe: str) -> ImagePrompt:
    vibe_value = VIBE_MAP.get(vibe, VIBE_MAP["clean"])
    prompt = PROMPT_TEMPLATE.replace("[TITLE]", title).replace("[VIBE]", vibe_value)
    return ImagePrompt(prompt=prompt, negative_prompt=NEGATIVE_PROMPT)
