from .shaders.filters.ColorChannelOffset import ColorChannelOffset
from .shaders.Shader import Shader
from .shaders.Shadertoy import Shadertoy

NODE_CLASS_MAPPINGS = {
    "Shadertoy": Shadertoy,
    "Shader": Shader,
    "ColorChannelOffset": ColorChannelOffset,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "Shadertoy": "Shadertoy",
    "Shader": "Shader",
    "ColorChannelOffset": "ColorChannelOffset",
}
