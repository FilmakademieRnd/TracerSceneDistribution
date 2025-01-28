'''
TRACER Scene Distribution Plugin Blender
 
Copyright (c) 2024 Filmakademie Baden-Wuerttemberg, Animationsinstitut R&D Labs
https://research.animationsinstitut.de/tracer
https://github.com/FilmakademieRnd/TracerSceneDistribution
 
TRACER Scene Distribution Plugin Blender is a development by Filmakademie
Baden-Wuerttemberg, Animationsinstitut R&D Labs in the scope of the EU funded
project MAX-R (101070072) and funding on the own behalf of Filmakademie
Baden-Wuerttemberg.  Former EU projects Dreamspace (610005) and SAUCE (780470)
have inspired the TRACER Scene Distribution Plugin Blender development.
 
The TRACER Scene Distribution Plugin Blender is intended for research and
development purposes only. Commercial use of any kind is not permitted.
 
There is no support by Filmakademie. Since the TRACER Scene Distribution Plugin
Blender is available for free, Filmakademie shall only be liable for intent
and gross negligence; warranty is limited to malice. TRACER Scene Distribution
Plugin Blender may under no circumstances be used for racist, sexual or any
illegal purposes. In all non-commercial productions, scientific publications,
prototypical non-commercial software tools, etc. using the TRACER Scene
Distribution Plugin Blender Filmakademie has to be named as follows: 
"TRACER Scene Distribution Plugin Blender by Filmakademie
Baden-Württemberg, Animationsinstitut (http://research.animationsinstitut.de)".
 
In case a company or individual would like to use the TRACER Scene Distribution
Plugin Blender in a commercial surrounding or for commercial purposes,
software based on these components or  any part thereof, the company/individual
will have to contact Filmakademie (research<at>filmakademie.de) for an
individual license agreement.
 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
'''
#import bpy
#import bmesh
#import logging
#import functools
#import math
import mathutils
import struct


class SceneDataMesh():

    def __init__(self):
        self.name: str = ''
        self.vertices:  list[mathutils.Vector] = []
        self.normals:   list[mathutils.Vector] = []
        self.uvs:       list[mathutils.Vector] = []

        self.original_indices:  list[int] = []
        self.indices:           list[int] = []

        self.bone_weights: list[list[float]]    = [[]]
        self.bone_indices: list[list[int]]      = [[]]

    def serialise(self) -> bytearray:
        mesh_binary = bytearray([])

        # Serialise vertices
        size_vertices: int = len(self.vertices)
        mesh_binary.extend(struct.pack('i', size_vertices))
        mesh_binary.extend(struct.pack('%sf' % size_vertices*3, *self.vertices))

        # Serialise indices
        size_indices: int = len(self.indices)
        mesh_binary.extend(struct.pack('i', size_indices))
        mesh_binary.extend(struct.pack('%sf' % size_indices*3, *self.indices))

        # Serialise normals
        size_normals: int = len(self.normals)
        mesh_binary.extend(struct.pack('i', size_normals))
        mesh_binary.extend(struct.pack('%sf' % size_normals*3, *self.normals))

        # Serialise UVs
        size_uvs: int = len(self.uvs)
        mesh_binary.extend(struct.pack('i', size_uvs))
        mesh_binary.extend(struct.pack('%sf' % size_uvs*2, *self.uvs))

        # Serialise bone weights and bone indices
        size_bone_infos: int = len(self.bone_weights)
        mesh_binary.extend(struct.pack('i', size_bone_infos))
        if size_bone_infos > 0:
            mesh_binary.extend(struct.pack('%sf' % size_bone_infos*4, *self.bone_weights))
            mesh_binary.extend(struct.pack('%sf' % size_bone_infos*4, *self.bone_indices))

        return mesh_binary