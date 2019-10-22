"""Bunch of OpenGL heavy code for rendering vmfs"""
import colorsys
import ctypes
import itertools

import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileShader, compileProgram
##from OpenGL.GLU import *

from . import camera, solid, vector, vmf


def vmf_setup(viewport, vmf_object, ctx):
    string_solids = [] # need per solid line numbers for snappy updates
    if hasattr(vmf_object.world, "solid"):
        vmf_object.world.solids = [vmf_object.world.solid]
    if not hasattr(vmf_object.world, "solids"):
        vmf_object.world.solids = []
    for brush in vmf_object.world.solids:
        string_solids.append(brush)
    if hasattr(vmf_object, "entity"):
        vmf_object.entities = [vmf_object.world.entity]
    if not hasattr(vmf_object, "entities"):
        vmf_object.entities = []
    for entity in vmf_object.entities: # do some of these cases never occur?
        if hasattr(entity, "solid"):
            if isinstance(entity.solid, vmf.namespace):
                string_solids.append(entity.solid)
        if hasattr(entity, "solids"):
            if isinstance(entity.solids[0], vmf.namespace):
                string_solids += entity.solids

    solids = []
    global solid
    for ss in string_solids:
        try:
            solids.append(solid.solid(ss))
        except Exception as exc:
            print("Invalid solid! (id {})".format(ss.id))
            print(exc)

    GLES_MODE = False
    # check the supported GLSL versions & settings instead of try: except!
    try: # GLSL 450
        # Vertex Shaders
        vert_shader_brush = compileShader(open(ctx.get_resource("shaders/GLSL_450/brush.vert"), "rb"), GL_VERTEX_SHADER)
        vert_shader_displacement = compileShader(open(ctx.get_resource("shaders/GLSL_450/displacement.vert"), "rb"), GL_VERTEX_SHADER)
        # Fragment Shaders
        frag_shader_flat_brush = compileShader(open(ctx.get_resource("shaders/GLSL_450/flat_brush.frag"), "rb"), GL_FRAGMENT_SHADER)
        frag_shader_flat_displacement = compileShader(open(ctx.get_resource("shaders/GLSL_450/flat_displacement.frag"), "rb"), GL_FRAGMENT_SHADER)
        frag_shader_stripey_brush = compileShader(open(ctx.get_resource("shaders/GLSL_450/stripey_brush.frag"), "rb"), GL_FRAGMENT_SHADER)
    except RuntimeError as exc: # try GLES 3.00
        GLES_MODE = True
        # Vertex Shaders
        vert_shader_brush = compileShader(open(ctx.get_resource("shaders/GLES_300/brush.vert"), "rb"), GL_VERTEX_SHADER)
        vert_shader_displacement = compileShader(open(ctx.get_resource("shaders/GLES_300/displacement.vert"), "rb"), GL_VERTEX_SHADER)
        # Fragment Shaders
        frag_shader_flat_brush = compileShader(open(ctx.get_resource("shaders/GLES_300/flat_brush.frag"), "rb"), GL_FRAGMENT_SHADER)
        frag_shader_flat_displacement = compileShader(open(ctx.get_resource("shaders/GLES_300/flat_displacement.frag"), "rb"), GL_FRAGMENT_SHADER)
        frag_shader_stripey_brush = compileShader(open(ctx.get_resource("shaders/GLES_300/stripey_brush.frag"), "rb"), GL_FRAGMENT_SHADER)
##        raise exc # to debug GLSL 4.5 shaders
    # Programs
    program_flat_brush = compileProgram(vert_shader_brush, frag_shader_flat_brush)
    program_flat_displacement = compileProgram(vert_shader_displacement, frag_shader_flat_displacement)
    program_stripey_brush = compileProgram(vert_shader_brush, frag_shader_stripey_brush)
    glLinkProgram(program_flat_brush)
    glLinkProgram(program_flat_displacement)
    glLinkProgram(program_stripey_brush)

    if GLES_MODE == True:
        glUseProgram(program_flat_brush)
        uniform_brush_matrix = glGetUniformLocation(program_flat_brush, 'ModelViewProjectionMatrix')
        glUseProgram(program_flat_displacement)
        uniform_displacement_matrix = glGetUniformLocation(program_flat_displacement, 'ModelViewProjectionMatrix')
        glUseProgram(program_stripey_brush)
        uniform_stripey_matrix = glGetUniformLocation(program_flat_brush, 'ModelViewProjectionMatrix')
        glUseProgram(0)

    vertices = []
    indices = []
    solid_map = dict()
    displacement_ids = []
    for brush in solids:
        if brush.is_displacement:
            displacement_ids.append(brush.id)
        solid_map[brush.id] = (len(indices), len(brush.indices))
        vertices += brush.vertices
        indices += [len(vertices) + i for i in brush.indices]
    vertices = tuple(itertools.chain(*vertices))

    # Vertex Buffer
    VERTEX_BUFFER, INDEX_BUFFER = glGenBuffers(2)
    glBindBuffer(GL_ARRAY_BUFFER, VERTEX_BUFFER)
    glBufferData(GL_ARRAY_BUFFER, len(vertices) * 4,
                 np.array(vertices, dtype=np.float32), GL_STATIC_DRAW)
    # Index Buffer
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, INDEX_BUFFER)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(indices) * 4,
                 np.array(indices, dtype=np.uint32), GL_STATIC_DRAW)
    # Vertex Format
    glEnableVertexAttribArray(0) # vertex_position
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 44, GLvoidp(0))
    glEnableVertexAttribArray(1) # vertex_normal (brush only)
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_TRUE, 44, GLvoidp(12))
    # glEnableVertexAttribArray(5) # blend_alpha (displacement only)
    glVertexAttribPointer(5, 1, GL_FLOAT, GL_FALSE, 44, GLvoidp(12))
    # ^ replaces vertex_normal / vertexNormal ^
    glEnableVertexAttribArray(2) # vertex_uv
    glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 44, GLvoidp(24))
    glEnableVertexAttribArray(4) # editor_colour
    glVertexAttribPointer(4, 3, GL_FLOAT, GL_FALSE, 44, GLvoidp(32))

    # keep handles to the new GL objects
    # dictionaries might be more convenient
    viewport.buffers = [VERTEX_BUFFER, INDEX_BUFFER]
    viewport.programs = [program_flat_brush, program_flat_displacement,
                         program_stripey_brush]
    viewport.draw_calls[viewport.programs[2]] = (0, len(indices))
    viewport.GLES_MODE = GLES_MODE
    if GLES_MODE:
        viewport.uniforms = {program_flat_brush: uniform_brush_matrix,
                             program_stripey_brush: uniform_stripey_matrix,
                             program_flat_displacement: uniform_displacement_matrix}