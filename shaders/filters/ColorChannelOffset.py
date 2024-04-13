class ColorChannelOffset:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": { "colorChannel": ("INT", {"default": 0, "min": 0, "max": 3}),
                              "x": ("FLOAT", {"default": 0, "min": -1, "max": 1, "step": 0.05}),
                              "y": ("FLOAT", {"default": 0, "min": -1, "max": 1, "step": 0.05}),
                              }}

    RETURN_TYPES = ("SHADER", "FLOAT")
    CATEGORY = "Shader"
    FUNCTION = "shader"

    def shader_text(self, channel: int, x: float, y: float):
        return f"""
        // Uniforms
        uniform vec2 offset = vec2(0, 0);
        uniform float colorChannel = 0;

        void mainImage(out vec4 fragColor, in vec2 fragCoord)
        {{
            vec2 texCoord = fragCoord.xy / iResolution.xy;
            fragColor = texture(iChannel0, texCoord);
            int channel = int(colorChannel);
            fragColor[channel] = texture(iChannel0, texCoord - offset)[channel];
        }}
        """

    def shader(self, colorChannel:int, x: float, y: float):
        source = self.shader_text(colorChannel, x, y)
        return (source,x)
