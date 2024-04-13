import numpy as np
import os
import OpenGL.GL as gl
import sys
from ctypes import *

# Load the OpenGL framework
framework = CDLL("/System/Library/Frameworks/OpenGL.framework/OpenGL")

# Define CGL function prototypes
CGLChoosePixelFormat = framework.CGLChoosePixelFormat
CGLChoosePixelFormat.argtypes = [POINTER(c_int), POINTER(c_int), POINTER(c_int)]
CGLChoosePixelFormat.restype = c_void_p

CGLCreateContext = framework.CGLCreateContext
CGLCreateContext.argtypes = [c_void_p, c_void_p]
CGLCreateContext.restype = c_void_p

CGLSetCurrentContext = framework.CGLSetCurrentContext
CGLSetCurrentContext.argtypes = [c_void_p]
CGLSetCurrentContext.restype = c_int

CGLDestroyContext = framework.CGLDestroyContext
CGLDestroyContext.argtypes = [c_void_p]
CGLDestroyContext.restype = None

CGLDestroyPixelFormat = framework.CGLDestroyPixelFormat
CGLDestroyPixelFormat.argtypes = [c_void_p]
CGLDestroyPixelFormat.restype = None

# Define CGL constants
kCGLPFAOpenGLProfile = 99
kCGLOGLPVersion_3_2_Core = 0x3200
kCGLPFAColorSize = 8
kCGLPFAAlphaSize = 11
kCGLPFADoubleBuffer = 5
kCGLPFASampleBuffers = 55
kCGLPFASamples = 56
kCGLPFAAccelerated = 73
kCGLPFANoRecovery = 72
kCGLPFABackingStore = 76
kCGLPFASupportsAutomaticGraphicsSwitching = 101

class ShadertoyGLContext:
    def __init__(self):
        self.is_mac = sys.platform.startswith("darwin")
        self.headless = os.name == "posix" and os.environ.get("DISPLAY", "") == ""
        if self.is_mac:
            a = 5
        elif self.headless:
            os.environ["PYOPENGL_PLATFORM"] = "egl"
            import OpenGL.EGL as egl
            self.egl = egl
        else:
            import glfw
            self.glfw = glfw

    def render_surface_and_context_init(self, width, height):
        if self.is_mac:
            attributes = [
                kCGLPFAOpenGLProfile, kCGLOGLPVersion_3_2_Core,
                kCGLPFAColorSize, 24,
                kCGLPFAAlphaSize, 8,
                kCGLPFADoubleBuffer,
                kCGLPFASampleBuffers, 1,
                kCGLPFASamples, 4,
                kCGLPFAAccelerated,
                kCGLPFANoRecovery,
                kCGLPFABackingStore,
                kCGLPFASupportsAutomaticGraphicsSwitching,
                0
            ]

            attributes_array = (c_int * len(attributes))(*attributes)
            pixel_format = c_void_p(CGLChoosePixelFormat(attributes_array, None, None))
            if pixel_format.value is None:
                raise RuntimeError("No suitable CGL pixel format found")

            context = c_void_p(CGLCreateContext(pixel_format, None))
            if context.value is None:
                raise RuntimeError("Unable to create CGL context")

            CGLSetCurrentContext(context)

            return {"context": context, "pixel_format": pixel_format}
        elif self.headless:
            egl_display = self.egl.eglGetDisplay(self.egl.EGL_DEFAULT_DISPLAY)
            if egl_display == self.egl.EGL_NO_DISPLAY:
                raise RuntimeError("No EGL display connection available")
            if not self.egl.eglInitialize(egl_display, None, None):
                raise RuntimeError("Unable to initialize EGL")

            config_attribs = [
                self.egl.EGL_SURFACE_TYPE, self.egl.EGL_PBUFFER_BIT,
                self.egl.EGL_BLUE_SIZE, 8,
                self.egl.EGL_GREEN_SIZE, 8,
                self.egl.EGL_RED_SIZE, 8,
                self.egl.EGL_DEPTH_SIZE, 24,
                self.egl.EGL_RENDERABLE_TYPE, self.egl.EGL_OPENGL_BIT,
                self.egl.EGL_NONE
            ]
            num_configs = self.egl.EGLint()
            if not self.egl.eglChooseConfig(egl_display, config_attribs, None, 0, num_configs) or num_configs.value == 0:
                raise RuntimeError("No suitable EGL configuration was found")

            egl_config = (self.egl.EGLConfig * num_configs.value)()
            self.egl.eglChooseConfig(egl_display, config_attribs, egl_config, 1, num_configs)
            egl_config = egl_config[0]

            egl_context = self.egl.eglCreateContext(egl_display, egl_config, self.egl.EGL_NO_CONTEXT, None)
            if egl_context == self.egl.EGL_NO_CONTEXT:
                raise RuntimeError("Unable to create EGL context")

            pbuffer_attribs = [
                self.egl.EGL_WIDTH, width,
                self.egl.EGL_HEIGHT, height,
                self.egl.EGL_NONE
            ]
            egl_surface = self.egl.eglCreatePbufferSurface(egl_display, egl_config, pbuffer_attribs)
            if egl_surface == self.egl.EGL_NO_SURFACE:
                raise RuntimeError("Unable to create offscreen EGL surface")

            if not self.egl.eglMakeCurrent(egl_display, egl_surface, egl_surface, egl_context):
                raise RuntimeError("Unable to make EGL context current")

            return {"egl_display": egl_display, "egl_surface": egl_surface, "egl_context": egl_context}
        else:
            if not self.glfw.init():
                raise RuntimeError("GLFW did not init")

            self.glfw.window_hint(self.glfw.VISIBLE, self.glfw.FALSE)  # hidden
            window = self.glfw.create_window(width, height, "hidden", None, None)
            if not window:
                raise RuntimeError("GLFW did not init window")

            self.glfw.make_context_current(window)
            return {}

    def render_surface_and_context_deinit(self, **kwargs):
        if self.is_mac:
            CGLSetCurrentContext(None)
            CGLDestroyContext(context)
            CGLDestroyPixelFormat(pixel_format)
        elif self.headless:
            self.egl.eglMakeCurrent(kwargs["egl_display"], self.egl.EGL_NO_SURFACE, self.egl.EGL_NO_SURFACE, self.egl.EGL_NO_CONTEXT)
            self.egl.eglDestroySurface(kwargs["egl_display"], kwargs["egl_surface"])
            self.egl.eglDestroyContext(kwargs["egl_display"], kwargs["egl_context"])
            self.egl.eglTerminate(kwargs["egl_display"])
        else:
            self.glfw.terminate()

    def compile_shader(self, source, shader_type):
        shader = gl.glCreateShader(shader_type)
        gl.glShaderSource(shader, source)
        gl.glCompileShader(shader)
        if gl.glGetShaderiv(shader, gl.GL_COMPILE_STATUS) != gl.GL_TRUE:
            raise RuntimeError(gl.glGetShaderInfoLog(shader))
        return shader

    def compile_program(self, vertex_source, fragment_source):
        vertex_shader = self.compile_shader(vertex_source, gl.GL_VERTEX_SHADER)
        fragment_shader = self.compile_shader(fragment_source, gl.GL_FRAGMENT_SHADER)
        program = gl.glCreateProgram()
        gl.glAttachShader(program, vertex_shader)
        gl.glAttachShader(program, fragment_shader)
        gl.glLinkProgram(program)
        if gl.glGetProgramiv(program, gl.GL_LINK_STATUS) != gl.GL_TRUE:
            raise RuntimeError(gl.glGetProgramInfoLog(program))
        return program

    def setup_framebuffer(self, width, height):
        texture = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, texture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, width, height, 0, gl.GL_RGB, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)

        fbo = gl.glGenFramebuffers(1)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, texture, 0)
        if gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER) != gl.GL_FRAMEBUFFER_COMPLETE:
            raise RuntimeError("Framebuffer is not complete")

        return fbo, texture

    def setup_render_resources(self, width, height, fragment_source: str):
        ctx = self.render_surface_and_context_init(width, height)

        vertex_source = """
        #version 330 core
        void main()
        {
            vec2 verts[3] = vec2[](vec2(-1, -1), vec2(3, -1), vec2(-1, 3));
            gl_Position = vec4(verts[gl_VertexID], 0, 1);
        }
        """
        shader = self.compile_program(vertex_source, fragment_source)

        fbo, texture = self.setup_framebuffer(width, height)

        textures = gl.glGenTextures(4)

        return (ctx, fbo, shader, textures)

    def render_resources_cleanup(self, ctx):
        if self.is_mac:
            self.render_surface_and_context_deinit(ctx["context"], ctx["pixel_format"])
        else:
            # assume all other resources get cleaned up with the context
            self.render_surface_and_context_deinit(**ctx)

    def render(self, width, height, fbo, shader):
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        gl.glUseProgram(shader)
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 3)

        data = gl.glReadPixels(0, 0, width, height, gl.GL_RGB, gl.GL_UNSIGNED_BYTE)
        image = np.frombuffer(data, dtype=np.uint8).reshape(height, width, 3)
        image = image[::-1, :, :]
        image = np.array(image).astype(np.float32) / 255.0

        return image

    def shadertoy_vars_update(self, shader, width, height, time, time_delta, frame_rate, frame):
        gl.glUseProgram(shader)
        iResolution_location = gl.glGetUniformLocation(shader, "iResolution")
        gl.glUniform3f(iResolution_location, width, height, 0)
        iMouse_location = gl.glGetUniformLocation(shader, "iMouse")
        gl.glUniform4f(iMouse_location, 0, 0, 0, 0)
        iTime_location = gl.glGetUniformLocation(shader, "iTime")
        gl.glUniform1f(iTime_location, time)
        iTimeDelta_location = gl.glGetUniformLocation(shader, "iTimeDelta")
        gl.glUniform1f(iTimeDelta_location, time_delta)
        iFrameRate_location = gl.glGetUniformLocation(shader, "iFrameRate")
        gl.glUniform1f(iFrameRate_location, frame_rate)
        iFrame_location = gl.glGetUniformLocation(shader, "iFrame")
        gl.glUniform1i(iFrame_location, frame)

    def shadertoy_texture_update(self, texture, image, frame):
        if len(image.shape) == 4:
            image = image[frame]
        image = image.cpu().numpy()
        image = image[::-1, :, :]
        gl.glBindTexture(gl.GL_TEXTURE_2D, texture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, image.shape[1], image.shape[0], 0, gl.GL_RGB, gl.GL_FLOAT, image)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)

    def shadertoy_texture_bind(self, shader, textures):
        gl.glUseProgram(shader)
        for i in range(4):
            gl.glActiveTexture(gl.GL_TEXTURE0 + i) # type: ignore
            gl.glBindTexture(gl.GL_TEXTURE_2D, textures[i])
            iChannel_location = gl.glGetUniformLocation(shader, f"iChannel{i}")
            gl.glUniform1i(iChannel_location, i)

    def set_uniform_1f(self, shader, name, value):
        location = gl.glGetUniformLocation(shader, name)
        gl.glUniform1f(location, value)

    def set_uniform_2f(self, shader, name, value):
        location = gl.glGetUniformLocation(shader, name)
        gl.glUniform2f(location, value[0], value[1])

    def set_uniform_3f(self, shader, name, value):
        location = gl.glGetUniformLocation(shader, name)
        gl.glUniform3f(location, value[0], value[1], value[2])

    def set_uniform_4f(self, shader, name, value):
        location = gl.glGetUniformLocation(shader, name)
        gl.glUniform4f(location, value[0], value[1], value[2], value[3])

    def set_uniform_1i(self, shader, name, value):
        location = gl.glGetUniformLocation(shader, name)
        gl.glUniform1i(location, value)

    def set_uniform_2i(self, shader, name, value):
        location = gl.glGetUniformLocation(shader, name)
        gl.glUniform2i(location, value[0], value[1])

    def set_uniform_3i(self, shader, name, value):
        location = gl.glGetUniformLocation(shader, name)
        gl.glUniform3i(location, value[0], value[1], value[2])

    def set_uniform_4i(self, shader, name, value):
        location = gl.glGetUniformLocation(shader, name)
        gl.glUniform4i(location, value[0], value[1], value[2], value[3])
