from typing import Optional
import nodes as comfy_nodes
import torch
from .shader_const import (
    SHADERTOY_DEFAULT,
    SHADERTOY_FOOTER,
    SHADERTOY_HEADER,
    SHADERTOY_PASSTHROUGH,
)
from .ShadertoyGLContext import ShadertoyGLContext

shadertoyGLContext = ShadertoyGLContext()

class Shadertoy:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "width": ("INT", {"default": 512, "min": 64, "max": comfy_nodes.MAX_RESOLUTION, "step": 8}),
            "height": ("INT", {"default": 512, "min": 64, "max": comfy_nodes.MAX_RESOLUTION, "step": 8}),
            "frame_count": ("INT", {"default": 1, "min": 1, "max": 262144}),
            "fps": ("INT", {"default": 1, "min": 1, "max": 120}),
        },
        "optional": {
            "x": ("FLOAT", {"array": True}),
            "shader": ("SHADER",),
            "channel_0": ("IMAGE",),
            "channel_1": ("IMAGE",),
            "channel_2": ("IMAGE",),
            "channel_3": ("IMAGE",)}}

    RETURN_TYPES = ("IMAGE", )
    CATEGORY = "Shader"
    FUNCTION = "render"

    def render(self, width: int, height: int, frame_count: int, fps: int,
               x: Optional[list] = None,
               shader:Optional[str] = None,
               channel_0: Optional[torch.Tensor] = None,
               channel_1: Optional[torch.Tensor] = None,
               channel_2: Optional[torch.Tensor] = None,
               channel_3: Optional[torch.Tensor] = None):
        if shader == None:
            if channel_0 == None:
                shader = SHADERTOY_DEFAULT
            else:
                shader = SHADERTOY_PASSTHROUGH

        source = shader
        fragment_source = SHADERTOY_HEADER
        fragment_source += source
        fragment_source += SHADERTOY_FOOTER

        ctx, fbo, shader, textures = shadertoyGLContext.setup_render_resources(width, height, fragment_source)

        images = []
        frame = 0
        for _ in range(frame_count):
            shadertoyGLContext.shadertoy_vars_update(shader, width, height, frame * (1.0 / fps), (1.0 / fps), fps, frame)
            if x is not None:
                shadertoyGLContext.set_uniform_2f(shader, "offset", (x[frame], 0))
            if channel_0 != None: shadertoyGLContext.shadertoy_texture_update(textures[0], channel_0, frame)
            if channel_1 != None: shadertoyGLContext.shadertoy_texture_update(textures[1], channel_1, frame)
            if channel_2 != None: shadertoyGLContext.shadertoy_texture_update(textures[2], channel_2, frame)
            if channel_3 != None: shadertoyGLContext.shadertoy_texture_update(textures[3], channel_3, frame)
            shadertoyGLContext.shadertoy_texture_bind(shader, textures)
            image = shadertoyGLContext.render(width, height, fbo, shader)
            image = torch.from_numpy(image)[None,]
            images.append(image)
            frame += 1

        shadertoyGLContext.render_resources_cleanup(ctx)

        return (torch.cat(images, dim=0),)
