from .shader_const import SHADERTOY_DEFAULT

class Shader:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": { "source": ("STRING", {"default": SHADERTOY_DEFAULT, "multiline": True, "dynamicPrompts": False})}}

    RETURN_TYPES = ("SHADER", )
    CATEGORY = "Shader"
    FUNCTION = "shader"

    def shader(self, source: str):
        source = source
        return (source,)
