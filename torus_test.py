import moderngl
import moderngl_window as mglw
import numpy as np
from pyrr import Matrix44, Vector3
import math
import random

print(r"""
+---------------------------------------------------------------------------------------------+
|                                                     *                                       |
|       (     (                  )                  (  `                  )      )       )    |
|   (    )\ )  )\ )    (       ( /( (    )      (    )\))(      )  (    ( /(   ( /(    ( /(   |
|  )\  (()/( (()/(   ))\  (   )\()))\  /((    ))\  ((_)()\  ( /(  )(   )\())  )(_))   )\())   |
| ((_)  /(_)) /(_)) /((_) )\ (_))/((_)(_))\  /((_) (_()((_) )(_))(()\ ((_)\  ((_)    ((_)\    |
| | __|(_) _|(_) _|(_))  ((_)| |_  (_)_)((_)(_))   |  \/  |((_)_  ((_)| |(_) |_  )   /  (_)   |
| | _|  |  _| |  _|/ -_)/ _| |  _| | |\ V / / -_)  | |\/| |/ _` || '_|| / /   / /  _| () |    |
| |___| |_|   |_|  \___|\__|  \__| |_| \_/  \___|  |_|  |_|\__,_||_|  |_\_\  /___|(_)\__/     |
+---------------------------------------------------------------------------------------------+""")


def generate_torus(
        R: float = 1.0,
        r: float = 0.3,
        segments: int = 32,
        rings: int = 16
) -> np.array:
    vertices = []
    normals = []
    indices = []

    # Generate torus
    for i in range(segments):
        theta = 2 * np.pi * i / segments
        cos_theta = np.cos(theta)
        sin_theta = np.sin(theta)

        for j in range(rings):
            phi = 2 * np.pi * j / rings
            cos_phi = np.cos(phi)
            sin_phi = np.sin(phi)

            x = (R + r * cos_phi) * cos_theta
            y = (R + r * cos_phi) * sin_theta
            z = r * sin_phi

            nx = cos_phi * cos_theta
            ny = cos_phi * sin_theta
            nz = sin_phi

            vertices += [x, y, z]
            normals += [nx, ny, nz]

    for i in range(segments):
        for j in range(rings):
            next_i = (i + 1) % segments
            next_j = (j + 1) % rings

            idx0 = i * rings + j
            idx1 = next_i * rings + j
            idx2 = next_i * rings + next_j
            idx3 = i * rings + next_j

            indices += [idx0, idx1, idx2, idx0, idx2, idx3]

    return (
        np.array(vertices, dtype='f4'),
        np.array(normals, dtype='f4'),
        np.array(indices, dtype='u4')
    )


class TorusTest(mglw.WindowConfig):
    gl_version = (3, 3)
    title = "EffectiveMark2 - 3D render test"
    window_size = (1280*2, 720*2)
    resource_dir = '.'
    aspect_ratio = 16 / 9

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        VShader = """
        #version 330
        uniform mat4 projection;
        uniform mat4 view;
        
        in vec3 in_position;
        in vec3 in_normal;
        
        in vec4 in_model_0;
        in vec4 in_model_1;
        in vec4 in_model_2;
        in vec4 in_model_3;
        
        out vec3 frag_pos;
        out vec3 normal;
        
        void main() {
            mat4 in_model = mat4(in_model_0, in_model_1, in_model_2, in_model_3);
            vec4 world_pos = in_model * vec4(in_position, 1.0);
            frag_pos = world_pos.xyz;
            normal = mat3(in_model) * in_normal;
            gl_Position = projection * view * world_pos;
        }"""


        FShader = """
        #version 330

        in vec3 frag_pos;
        in vec3 normal;
        
        out vec4 frag_color;
        
        uniform vec3 light_pos;
        uniform vec3 light_color;
        uniform vec3 view_pos;
        
        void main() {
            vec3 color = vec3(0.0, .3, 1.0); // base color
            vec3 norm = normalize(normal);
            vec3 light_dir = normalize(light_pos - frag_pos);
            float diff = max(dot(norm, light_dir), 0.0);
        
            vec3 diffuse = diff * light_color;
            frag_color = vec4(diffuse * color, 1.0);
        }"""

        # Create geometry
        vertices, normals, indices = generate_torus(3.0, .5, segments=512, rings=256)

        self.prog = self.ctx.program(
            vertex_shader=VShader,
            fragment_shader=FShader
        )

        vbo = self.ctx.buffer(vertices.tobytes())
        nbo = self.ctx.buffer(normals.tobytes())
        ibo = self.ctx.buffer(indices.tobytes())

        # number of toruses
        self.model_count = 600
        spacing = 4.0
        radius_increment = 7.0
        base_radius = .5

        self.model_matrices = []

        for i in range(self.model_count):
            scale_factor = base_radius + i * radius_increment
            angle = i * 15  # degrees or radians

            rotation = Matrix44.from_y_rotation(np.radians(angle))
            scale_matrix = Matrix44.from_scale([scale_factor] * 3)
            translation_matrix = Matrix44.identity()

            model_matrix = translation_matrix * rotation * scale_matrix
            self.model_matrices.append(model_matrix)

        self.instance_buffer = self.ctx.buffer(
            np.array([m for mat in self.model_matrices for m in mat.T.flatten()], dtype='f4').tobytes()
        )

        vao_content = [
            (vbo, '3f', 'in_position'),
            (nbo, '3f', 'in_normal'),
            (self.instance_buffer, '4f 4f 4f 4f/i', 'in_model_0', 'in_model_1', 'in_model_2', 'in_model_3')
        ]

        self.vao = self.ctx.vertex_array(self.prog, vao_content, ibo)

        # Setup Camera
        self.camera_pos = Vector3([0.0, 0.0, 10.0])

    def on_render(self, time: float, frame_time: float) -> None:
        self.ctx.clear(.05, .05, .05)
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.BLEND)

        if int(time) != getattr(self, "_last_time", -1):
            # self._last_time = int(time)
            try: print(f"FPS: {1/frame_time:.2f}", end='\r')
            except ZeroDivisionError: print("FPS: N/A", end='\r')
            # try: shared.fps_torus.append(1/frame_time)
            # except ZeroDivisionError: pass

        proj = Matrix44.perspective_projection(45.0, self.wnd.aspect_ratio, .1, 100.0)
        view = Matrix44.look_at(
            self.camera_pos,
            (.0, .0, .0),
            (.0, 1.0, .0)
        )

        # if random.randint(0, 1) == 0:

        for i, base_matrix in enumerate(self.model_matrices):
            idx = i % self.model_count
            multiplier1 = math.pi / 2
            multiplier2 = math.e / 2
            multiplier3 = math.tau / 2
            if idx == 0:
                # rotation = Matrix44.from_x_rotation(math.sin(time) * multiplier1)  # rotate around Y axis
                rotation = Matrix44.from_x_rotation(time * multiplier1)

            elif idx == 1:
                rotation = Matrix44.from_y_rotation(time * multiplier2)  # rotate around Y axis

            elif idx == 2:
                rotation = Matrix44.from_z_rotation(time * multiplier3)  # rotate around Y axis

            translation_vec = base_matrix[3, :3]
            translation = Matrix44.from_translation(translation_vec)
            self.model_matrices[i] = translation * rotation

        # else:
        #     for i, base_matrix in enumerate(self.model_matrices):
        #         rotation = Matrix44.from_y_rotation(time)  # rotate around Y axis
        #         translation_vec = base_matrix[3, :3]
        #         translation = Matrix44.from_translation(translation_vec)
        #         # translation = Matrix44.from_translation(base_matrix.translation)
        #
        #         self.model_matrices[i] = translation * rotation



        self.prog['projection'].write(proj.astype('f4').tobytes())
        self.prog['view'].write(view.astype('f4').tobytes())

        # Define light
        light_pos = (
            math.sin(time*math.pi),
            math.cos(time/2),
            abs(math.tan(time % 90))*10
        )

        self.prog['light_pos'].value = light_pos
        self.prog['light_color'].value = (0.2, .5, 0.25)
        # self.prog['view_pos'].value = tuple(self.camera_pos)

        # Update buffer with new model matrices
        flat = np.array([m for mat in self.model_matrices for m in mat.flatten()], dtype='f4')
        self.instance_buffer.write(flat.tobytes())

        self.vao.render(instances=self.model_count)
        # self.vao.render()


def run_torus_test():
    mglw.run_window_config(TorusTest)


if __name__ == '__main__':
    mglw.run_window_config(TorusTest)
    #    print("FPS Mean:", round(mean(shared.fps_torus), 2))
#    print("FPS Max: ", round(max(shared.fps_torus), 2))
#    print("FPS Min: ", round(min(shared.fps_torus), 2))
#    input()
