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

import functools
import math
from mathutils import Matrix, Quaternion, Vector, Euler
import bpy

from ..settings import VpetProperties
from ..AbstractParameter import Parameter, KeyList, Key
from .SceneObject import SceneObject
from ..serverAdapter import SendParameterUpdate

class SceneCharacterObject(SceneObject):

    boneMap = {}
    local_bone_rest_transform = {}      # Stores the local resting bone space transformations in a dictionary (type = dict[str, Matrix])
    local_rotation_map =        {}      # Stores the values updated by TRACER local bone space transformations in a dictionary (may cause issues with values updated in a TRACER non-compliant way) (type = dict[str, Matrix])
    local_translation_map =     {}      # (type = dict[str, Matrix])
    root_bone_name:             str
    armature_obj_name:          str
    armature_obj_pose_bones = None # type = bpy.types.bpy_prop_collection[bpy.types.PoseBone]
    armature_obj_bones_rest_data = None
    path_to_follow = None

    def __init__(self, obj: bpy.types.Object):
        super().__init__(obj)

        self.armature_obj_name = obj.name
        self.armature_obj_pose_bones = obj.pose.bones   # The pose bones (to which the rotations have to be applied)
        self.armature_obj_bones_rest_data = obj.data.bones              # The rest data of the armature bones (to compute the rest pose offsets)
        self.matrix_world = obj.matrix_world
        # self.edit_bones = obj.data.edit_bones

        # Saving initial/resting armature bone transforms in local **bone** space
        # Necessary for then applying animation displacements in the correct transform space
        for abone in self.armature_obj_bones_rest_data:
            if abone.parent:  # Check if the bone has a parent
                # Get the relative position of the bone to its parent
                self.local_bone_rest_transform[abone.name] = abone.parent.matrix_local.inverted() @ abone.matrix_local
            else:
                self.local_bone_rest_transform[abone.name] = abone.matrix_local
        
        for bone in self.armature_obj_pose_bones:
            # finding root bone for hierarchy traversal
            if not bone.parent:
                self.root_bone_name = bone.name

            bone_matrix_global = self.matrix_world @ bone.matrix
            bone_rotation_quaternion = bone_matrix_global.to_quaternion()
            localBoneRotationParameter = Parameter(bone_rotation_quaternion, bone.name+"-rotation_quaternion", self)
            self._parameterList.append(localBoneRotationParameter)
            localBoneRotationParameter.hasChanged.append(functools.partial(self.UpdateBoneRotation, localBoneRotationParameter))
            #localBoneRotationParameter.animation_has_changed.append(functools.partial(self.bake_bone_rotations, localBoneRotationParameter))
            self.boneMap[localBoneRotationParameter.get_parameter_id] = bone_rotation_quaternion

        for bone in self.armature_obj_pose_bones:
            # finding root bone for hierarchy traversal
            if not bone.parent:
                self.root_bone_name = bone.name

            bone_location = bone.location
            localBonePositionParameter = Parameter(bone_location, bone.name+"-location", self)
            self._parameterList.append(localBonePositionParameter)
            localBonePositionParameter.hasChanged.append(functools.partial(self.UpdateBonePosition, localBonePositionParameter))
            #localBoneRotationParameter.animation_has_changed.append(functools.partial(self.bake_bone_locations, localBoneRotationParameter))
            # print(str(localBonePositionParameter.get_parameter_id()) + "   " + str(localBonePositionParameter.name) + "   " + str(localBonePositionParameter.value))

    def set_pose_matrices(self, pose_bone_obj: bpy.types.PoseBone):
        pose_bone: bpy.types.Bone
        if pose_bone_obj.name in self.local_rotation_map:
            rotation_matrix = self.local_rotation_map[pose_bone_obj.name]
            translation_matrix = self.local_translation_map[pose_bone_obj.name]
            pose_bone = pose_bone_obj.bone

            # Getting the translation matrix (only for the hip bone object)
            # translation_matrix = translation_matrix if pose_bone.name == "hip" else Matrix.Identity(4)
            # Composing translation and rotation matrices
            new_matrix: Matrix = translation_matrix @ rotation_matrix
            # Assigning the correct local transformation matrix to the Pose Bone Object (given the parent transform, if there is one)
            if pose_bone_obj.parent:
                parent_rotation_matrix = self.local_rotation_map[pose_bone_obj.parent.name]
                pose_bone_obj.matrix_basis = pose_bone.convert_local_to_pose( new_matrix, pose_bone.matrix_local,
                                                                              parent_matrix = parent_rotation_matrix,
                                                                              parent_matrix_local = pose_bone.parent.matrix_local,
                                                                              invert=True )
            else:
                pose_bone_obj.matrix_basis = pose_bone.convert_local_to_pose( new_matrix, pose_bone.matrix_local, invert=True )

    def UpdateBoneRotation(self, tracer_rot: Parameter, new_quat: Quaternion):
        bone_name = tracer_rot.name.partition("-")[0] # Extracting the name of the bone from the name of the parameter (e.g: spine_1-rotation_quat -> hip)
        target_bone: bpy.types.PoseBone = self.armature_obj_pose_bones[bone_name]
        local_rest_transform: Matrix = self.local_bone_rest_transform[bone_name]
        
        # Initialize the local parent rotation matrix (4x4 identity matrix, if the target bone has no parent bone)
        parent_rotation = self.local_rotation_map[target_bone.parent.name] if target_bone.parent else Matrix.Identity(4)
        new_rotation_matrix =   parent_rotation @\
                                Matrix.Translation(local_rest_transform.to_translation()) @\
                                new_quat.to_matrix().to_4x4()
        # Set the new transform, given by the new quaternion value, as the local rotation for the current target_bone
        self.local_rotation_map[bone_name] = new_rotation_matrix
        self.set_pose_matrices(target_bone)
        
    def UpdateBonePosition(self, tracer_pos: Parameter, new_value: Vector):
        bone_name = tracer_pos.name.split("-")[0] # Extracting the name of the bone from the name of the parameter (e.g: hip-location -> hip)
        target_bone: bpy.types.Bone = self.armature_obj_pose_bones[bone_name]

        if bone_name == "hip":
            #print(targetBone.name + " Position =  " + str(targetBone.location) + " - New Value = " + str(new_value))
            bone_rest_transform: Matrix  = self.local_bone_rest_transform[bone_name]
            rest_t, rest_r, rest_s = bone_rest_transform.decompose()
            self.local_translation_map[bone_name] = Matrix.Translation(new_value.xzy - rest_t)
        else:
            self.local_translation_map[bone_name] = Matrix.Identity(4)

    ## Writing the animation data received from TRACER (usually AnimHost) and replacing the previous animation data
    def populate_timeline_with_animation(self):
        # Retrieve the character object's armature on which to apply the animation data
        target_character_obj: bpy.types.Armature = self.editableObject
        # Clear the timeline from the old animation if there is one or initialise the data structure if there isn't one yet
        if target_character_obj.animation_data == None:
            target_character_obj.animation_data_create().action = bpy.data.actions.new("AnimHost Output")
        elif target_character_obj.animation_data.action:
            target_character_obj.animation_data.action.name = "Old Animation"
            old_action = self.editableObject.animation_data.action
            target_character_obj.animation_data_clear()
            target_character_obj.animation_data_create().action = bpy.data.actions.new("AnimHost Output")
            bpy.data.actions.remove(old_action)

        # Matrices encoding the positional offsets form rest pose for every keyframe of the hip bone (the other bones won't get displaced)
        local_pos_offest_from_rest: dict[str, dict[int, Matrix]] = {}
        for parameter in self._parameterList:
            bone_name, param_type = parameter.name.split("-")
            if parameter.is_animated and bone_name == "hip" and param_type == "location":
                offsets = {}
                for key in parameter.get_key_list():
                    # Compute the positional offset of the current bone from the rest position as a matrix 
                    bone_rest_transform: Matrix  = self.local_bone_rest_transform[bone_name]
                    rest_t, rest_r, rest_s = bone_rest_transform.decompose()
                    offsets[key.time] = (Matrix.Translation(key.value.xzy - rest_t))
                local_pos_offest_from_rest[bone_name] = offsets

        # Matrices encoding the rotational offsets form rest pose for every keyframe in every bone parameter
        local_rot_offest_from_rest: dict[str, dict[int, Matrix]] = {}
        for parameter in self._parameterList:
            bone_name, param_type = parameter.name.split("-")
            if parameter.is_animated and param_type == "rotation_quaternion":
                offsets = {}
                target_bone: bpy.types.PoseBone = self.armature_obj_pose_bones[bone_name]
                local_rest_transform: Matrix = self.local_bone_rest_transform[bone_name]
                for key in parameter.get_key_list():
                    # Compute the rotational offset of the current bone from the rest position as a matrix
                    parent_rotation = local_rot_offest_from_rest[target_bone.parent.name][key.time] if target_bone.parent else Matrix.Identity(4)
                    new_rotation_matrix =   parent_rotation @\
                                            Matrix.Translation(local_rest_transform.to_translation()) @\
                                            key.value.to_matrix().to_4x4()
                    offsets[key.time] = new_rotation_matrix
                local_rot_offest_from_rest[bone_name] = offsets

        # For every keyframe in every parameter, compute the combination of positional and rotational offsets,
        # convert the resulting local matrix into pose space and add keyframe for location and rotation in the timeline at the right time
        for parameter in self._parameterList:
            if parameter.is_animated:
                for key in parameter.get_key_list():
                    bone_name, param_type = parameter.name.split("-")
                    target_bone: bpy.types.PoseBone = self.armature_obj_pose_bones[bone_name]

                    rotation_matrix = local_rot_offest_from_rest[bone_name][key.time]
                    translation_matrix = local_pos_offest_from_rest[bone_name][key.time] if bone_name == "hip" else Matrix.Identity(4) # The translation matrix is defined only for the hip bone
                    pose_bone: bpy.types.Bone = target_bone.bone
                    new_matrix: Matrix = translation_matrix @ rotation_matrix
                    # Assigning the correct local transformation matrix to the Pose Bone Object (given the parent transform, if there is one)
                    if target_bone.parent:
                        parent_rotation_matrix = local_rot_offest_from_rest[target_bone.parent.name][key.time]
                        target_bone.matrix_basis = pose_bone.convert_local_to_pose( new_matrix, pose_bone.matrix_local,
                                                                                      parent_matrix = parent_rotation_matrix,
                                                                                      parent_matrix_local = pose_bone.parent.matrix_local,
                                                                                      invert=True )
                    else:
                        target_bone.matrix_basis = pose_bone.convert_local_to_pose( new_matrix, pose_bone.matrix_local, invert=True )
                    # Write keyframe for both location and rotation of the current bone at the current frame
                    target_character_obj.keyframe_insert('pose.bones["'+ bone_name +'"].location', frame=key.time)
                    target_character_obj.keyframe_insert('pose.bones["'+ bone_name +'"].rotation_quaternion', frame=key.time)
        
    def push_down_action(self):
        '''Baking the animation as a new animation layer'''
        # new_action = bpy.data.actions.new("AnimHost Output")

        # if self.editableObject.animation_data == None:
        #     self.editableObject.animation_data_create()
        #     self.editableObject.animation_data.use_nla = True
        #     new_track: bpy.types.NlaTrack = self.editableObject.animation_data.nla_tracks.active
        #     new_track.select = True
        #     new_track.name = "AnimHost Output"
        # else:
        #     if bpy.context.scene.vpet_properties.overwrite_animation:
        #         self.editableObject.animation_data.use_nla = True
        #         old_action_name = self.editableObject.animation_data.action.name
        #         self.editableObject.animation_data_clear()
        #         bpy.data.actions.remove(old_action_name)
        #     new_track = self.editableObject.animation_data.nla_tracks.new()
        #     new_track.select = True
        #     new_track.name = "AnimHost Output"
        
        
        # self.bake_parameter(self._parameterList[69], "location", self.armature_obj_pose_bones["hip"], new_action)

        # for parameter in self._parameterList:
        #     bone_name, parameter_type = parameter.name.split("-")
        #     if parameter.key_list.has_changed and not (bone_name == "hip" and parameter_type == "location"):
        #         target_bone = self.armature_obj_pose_bones[bone_name]
        #         self.bake_parameter(parameter, parameter_type, target_bone, new_action)

        # # Assign the newly filled action to the corresponding track of the current object
        # new_track.strips.new(name="AnimHost Output", start=0, action=new_action)
        pass