SHADERTOY_HEADER = """
#version 440

precision highp float;

uniform vec3	iResolution;
uniform vec4	iMouse;
uniform float	iTime;
uniform float	iTimeDelta;
uniform float	iFrameRate;
uniform int	    iFrame;

uniform sampler2D   iChannel0;
uniform sampler2D   iChannel1;
uniform sampler2D   iChannel2;
uniform sampler2D   iChannel3;

#define texture2D texture

"""

SHADERTOY_FOOTER = """

layout(location = 0) out vec4 _fragColor;

void main()
{
	mainImage(_fragColor, gl_FragCoord.xy);
}
"""

SHADERTOY_DEFAULT = """
void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    // Normalized pixel coordinates (from 0 to 1)
    vec2 uv = fragCoord/iResolution.xy;

    // Time varying pixel color
    vec3 col = 0.5 + 0.5*cos(iTime+uv.xyx+vec3(0,2,4));

    // Output to screen
    fragColor = vec4(col,1.0);
}
"""

SHADERTOY_PASSTHROUGH = """
void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    vec2 uv = fragCoord.xy / iResolution.xy;

    // Sample the input texture
    vec4 texColor = texture(iChannel0, uv);

    // Output the color without any modifications
    fragColor = texColor;
}
"""
