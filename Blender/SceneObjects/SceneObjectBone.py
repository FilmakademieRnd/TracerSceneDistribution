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
from bpy.types import Object, PoseBone, Armature
import bpy
import functools
import math
import copy
from mathutils import Vector, Quaternion, Matrix

from .AbstractParameter import Parameter, Key, KeyList, KeyType
from .SceneObjectBase import SceneObjectBase
from ..Core.ServerAdapter import send_parameter_update


### Class defining the properties and exposed functionalities of any object in a TRACER scene
#   
class SceneObjectBone(SceneObjectBase):
    
    def __init__(self, bl_bone: PoseBone, bl_armature_obj: Object):
        super().__init__()
        
        self.is_root: bool = (bl_bone.parent == None)
        self.bone_matrix_global: Matrix         = bl_armature_obj.matrix_world @ bl_bone.matrix
        self.bone_matrix_pose: Matrix           = bl_bone.matrix_basis
        self.bone_location_global: Vector       = self.bone_matrix_global.to_translation()
        self.bone_rotation_global: Quaternion   = self.bone_matrix_global.to_quaternion()
        self.bone_scale_global: Vector          = self.bone_matrix_global.to_scale()
        
        #PSEUDO CODE
        # bone_pos = bone_location_global
        # bone_rot = bone_rotation_global
        # bone_scl = bone_scale_global

        # Populating with TRS (Translation-Rotation-Scale) the list of TRACER parameters of the Scene Object. They will be parameters 0, 1 and 2 in the list
        # tracer_pos = Parameter(bone_pos, bl_bone.name+"-location", self)
        # self.parameter_list.append(tracer_pos)
        # tracer_rot = Parameter(bone_rot, bl_bone.name+"-rotation_euler", self)
        # self.parameter_list.append(tracer_rot)
        # tracer_scl = Parameter(bone_scl, bl_bone.name+"-scale", self)
        # self.parameter_list.append(tracer_scl)

        # Bind functions to update parameters to the corresponding instance of the parameter using functools.partial
        # tracer_pos.parameter_handler.append(functools.partial(self.update_position, tracer_pos))
        # tracer_rot.parameter_handler.append(functools.partial(self.update_rotation, tracer_rot))
        # tracer_scl.parameter_handler.append(functools.partial(self.update_scale,    tracer_scl))




    ### Function that updates the value of the position of Scene Objects and updates the connected TRACER clients if the change is made locally
    #   @param  tracer_pos  the instance of the parameter to update
    #   @param  new_value   the 3D vector describing the new position of this Scene Object  
    def update_position(self, tracer_pos: Parameter, new_value: Vector):
        pass

    ### Function that updates the value of the roatation of Scene Objects and updates the connected TRACER clients if the change is made locally
    #   @param  tracer_rot  the instance of the parameter to update
    #   @param  new_value   the quaternion describing the new rotation of this Scene Object
    def update_rotation(self, tracer_rot: Parameter, new_value: Quaternion):
        pass

    ### Function that updates the value of the scale of Scene Objects and updates the connected TRACER clients if the change is made locally
    #   @param  tracer_scl  the instance of the parameter to update
    #   @param  new_value   the 3D vector describing the new scale of this Scene Object
    def update_scale(self, tracer_scl: Parameter, new_value: Vector):
        pass
