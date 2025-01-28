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


class SceneDataCharacter():

    def __init__(self):
        self.character_root_id: int = -1

        self.bone_position: list[mathutils.Vector] = []
        self.bone_rotation: list[mathutils.Vector] = []
        self.bone_scale:    list[mathutils.Vector] = []

        self.bone_map: list[int]        = []
        self.skeleton_map: list[int]    = []

    def serialise(self) -> bytearray:
        character_binary = bytearray([])

        bone_map_len: int = len(self.bone_map)
        skel_map_len: int = len(self.skeleton_map)

        character_binary.extend(struct.pack('i', bone_map_len))
        character_binary.extend(struct.pack('i', skel_map_len))
        character_binary.extend(struct.pack('i', self.character_root_id))

        character_binary.extend(struct.pack(f'{bone_map_len}i'), *self.bone_map)
        character_binary.extend(struct.pack(f'{skel_map_len}i'), *self.skeleton_map)

        character_binary.extend(struct.pack('%sf' % skel_map_len*3, *self.bone_position))
        character_binary.extend(struct.pack('%sf' % skel_map_len*4, *self.bone_rotation))
        character_binary.extend(struct.pack('%sf' % skel_map_len*3, *self.bone_scale))

        return character_binary