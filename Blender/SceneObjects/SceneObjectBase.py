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
from bpy.types import Object, Bone
import bpy
import functools
import math
import copy
from ..AbstractParameter import Parameter, Key, KeyList, KeyType
from mathutils import Vector, Quaternion


### Class defining the properties and exposed functionalities of any object in a TRACER scene
#   
class SceneObjectBase():
    
    # PUBLIC STATIC variables
    start_id = 1
    scene_ID = 254

    def __init__(self):
        self.parameter_list: list[Parameter] = []
        self.object_id = SceneObjectBase.start_id
        SceneObjectBase.start_id += 1
        
        
    def update_position(self, tracer_pos: Parameter, new_value: Vector):
        pass
  
    def update_rotation(self, tracer_rot: Parameter, new_value: Quaternion):
        pass
        
    def update_scale(self, tracer_scale: Parameter, new_value: Vector):
        pass