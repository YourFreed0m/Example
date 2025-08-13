from __future__ import annotations
import math
from typing import Dict, Tuple
import numpy as np
import moderngl
import pyglet

VERT_SRC = """
#version 330
layout (location = 0) in vec3 in_position;
layout (location = 1) in vec2 in_uv;
layout (location = 2) in float in_light;

uniform mat4 u_view;
uniform mat4 u_proj;
uniform vec3 u_chunk_offset;

out vec2 v_uv;
out float v_light;

void main() {
    vec3 world_pos = in_position + u_chunk_offset;
    gl_Position = u_proj * u_view * vec4(world_pos, 1.0);
    v_uv = in_uv;
    v_light = in_light;
}
"""

FRAG_SRC = """
#version 330
in vec2 v_uv;
in float v_light;

uniform sampler2D u_atlas;
uniform vec3 u_sun_color;
uniform float u_ambient;

out vec4 fragColor;

void main() {
    vec4 tex = texture(u_atlas, v_uv);
    float light = clamp(v_light * 0.7 + u_ambient * 0.3, 0.05, 1.0);
    vec3 color = tex.rgb * (u_sun_color * light);
    fragColor = vec4(color, tex.a);
}
"""

// Fullscreen sky quad shaders
SKY_VERT = """
#version 330
layout (location = 0) in vec2 in_position;
out vec2 v_pos;
void main() {
    v_pos = in_position;
    gl_Position = vec4(in_position, 0.0, 1.0);
}
"""

SKY_FRAG = """
#version 330
in vec2 v_pos;
uniform float u_time;
uniform vec3 u_sun_dir;
out vec4 fragColor;

vec3 sky_color(vec3 dir, vec3 sun_dir) {
    float t = clamp(dir.y * 0.5 + 0.5, 0.0, 1.0);
    vec3 dayTop = vec3(0.1, 0.3, 0.8);
    vec3 dayHorizon = vec3(0.7, 0.9, 1.0);
    vec3 nightTop = vec3(0.02, 0.02, 0.08);
    vec3 nightHorizon = vec3(0.05, 0.05, 0.1);

    float sun_ele = clamp(dot(normalize(dir), normalize(sun_dir)), 0.0, 1.0);
    float day_factor = clamp(sun_dir.y * 0.5 + 0.5, 0.0, 1.0);

    vec3 top = mix(nightTop, dayTop, day_factor);
    vec3 horizon = mix(nightHorizon, dayHorizon, day_factor);

    vec3 base = mix(horizon, top, t);
    base += pow(sun_ele, 400.0) * vec3(1.0, 0.9, 0.6);
    return base;
}

void main() {
    vec3 dir = normalize(vec3(v_pos, 1.0));
    vec3 sun_dir = normalize(u_sun_dir);
    vec3 col = sky_color(dir, sun_dir);
    fragColor = vec4(col, 1.0);
}
"""


def _set_uniform_safe(program: moderngl.Program, name: str, value) -> None:
    try:
        program[name].value = value
    except KeyError:
        pass


class Renderer:
    def __init__(self, window: pyglet.window.Window):
        self.ctx = moderngl.create_context()
        self.window = window

        self.program = self.ctx.program(vertex_shader=VERT_SRC, fragment_shader=FRAG_SRC)
        self.sky_program = self.ctx.program(vertex_shader=SKY_VERT, fragment_shader=SKY_FRAG)

        # Fullscreen quad for sky
        sky_vertices = np.array([
            -1.0, -1.0,
             1.0, -1.0,
             1.0,  1.0,
            -1.0,  1.0,
        ], dtype='f4')
        self.sky_vbo = self.ctx.buffer(sky_vertices.tobytes())
        self.sky_vao = self.ctx.vertex_array(
            self.sky_program,
            [ (self.sky_vbo, '2f', 'in_position') ]
        )

        self.atlas_texture = None
        self.uvs: Dict[str, Tuple[float, float, float, float]] = {}
        self.chunk_vaos: Dict[Tuple[int, int], moderngl.VertexArray] = {}
        self.chunk_vbos: Dict[Tuple[int, int], moderngl.Buffer] = {}
        self.chunk_vertex_counts: Dict[Tuple[int, int], int] = {}

    def upload_atlas(self, image, uvs):
        self.uvs = uvs
        from PIL import Image
        if not isinstance(image, Image.Image):
            raise ValueError("Atlas must be a PIL Image")
        self.atlas_texture = self.ctx.texture(image.size, 4, image.tobytes())
        self.atlas_texture.build_mipmaps()
        self.atlas_texture.use(location=0)
        # Bind sampler uniform to texture unit 0
        _set_uniform_safe(self.program, 'u_atlas', 0)

    def rebuild_chunk(self, world, chunk):
        key = chunk.coords
        if chunk.vertex_data is None or chunk.index_count == 0:
            if key in self.chunk_vaos:
                self.chunk_vaos.pop(key).release()
                self.chunk_vbos.pop(key).release()
                self.chunk_vertex_counts.pop(key)
            return

        vbo = self.ctx.buffer(chunk.vertex_data.tobytes())
        vao = self.ctx.vertex_array(
            self.program,
            [
                (vbo, '3f 2f 1f', 'in_position', 'in_uv', 'in_light')
            ],
        )
        self.chunk_vaos[key] = vao
        self.chunk_vbos[key] = vbo
        self.chunk_vertex_counts[key] = chunk.index_count

    def draw_world(self, world, camera, time_of_day: float):
        width, height = self.window.get_size()
        aspect = width / max(1, height)
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.disable(moderngl.CULL_FACE)

        # Projection and view
        import glm
        proj = glm.perspective(glm.radians(70.0), aspect, 0.1, 1024.0)
        view = camera.view_matrix()

        # Sun direction and ambient from time_of_day [0..1]
        sun_angle = (time_of_day * 2.0 * math.pi) - math.pi / 2.0
        sun_dir = (math.cos(sun_angle), math.sin(sun_angle), 0.0)
        day_factor = max(0.0, sun_dir[1])
        sun_color = (0.9 * day_factor + 0.1, 0.85 * day_factor + 0.15, 0.8 * day_factor + 0.2)
        ambient = 0.2 + 0.5 * day_factor

        # Sky (draw first without depth test)
        self.ctx.disable(moderngl.DEPTH_TEST)
        _set_uniform_safe(self.sky_program, 'u_time', time_of_day)
        _set_uniform_safe(self.sky_program, 'u_sun_dir', sun_dir)
        self.sky_vao.render(mode=moderngl.TRIANGLE_STRIP, vertices=4)

        # World
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.program['u_proj'].write(bytes(proj))
        self.program['u_view'].write(bytes(view))
        self.program['u_sun_color'].value = sun_color
        self.program['u_ambient'].value = ambient
        _set_uniform_safe(self.program, 'u_atlas', 0)

        for key, vao in self.chunk_vaos.items():
            cx, cz = key
            self.program['u_chunk_offset'].value = (cx * 16, 0.0, cz * 16)
            vao.render(moderngl.TRIANGLES, vertices=self.chunk_vertex_counts[key])

    def release(self):
        for vao in self.chunk_vaos.values():
            vao.release()
        for vbo in self.chunk_vbos.values():
            vbo.release()
        if self.atlas_texture is not None:
            self.atlas_texture.release()