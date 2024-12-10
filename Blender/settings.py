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

import bpy
import json
from .SceneObjects.SceneObject import SceneObject
from .AbstractParameter import AnimHostRPC

## Class to keep editable parameters
class TracerProperties(bpy.types.PropertyGroup):

    def update_control_rig_name(self, context):
        if self.control_rig_name == '':
            return
        elif self.control_rig_name in bpy.data.objects and bpy.data.objects[self.control_rig_name].type == 'ARMATURE':
            control_rig: bpy.types.Object = bpy.data.objects[self.control_rig_name]
            control_rig_armature: bpy.types.Armature = control_rig.data
            control_rig_constraints: dict[str, list[tuple[str, str, str, float, str, str, bool, bool, bool]]] = {}
            # Save constraints in dictionary
            for bone in control_rig.pose.bones:
                if  bone.name not in control_rig_armature.collections["ORG"].bones and\
                    bone.name not in control_rig_armature.collections["MCH"].bones and\
                    bone.name not in control_rig_armature.collections["DEF"].bones:
                    
                    control_rig_constraints[bone.name] = []
                    if "Copy Location" in bone.constraints:
                        clc: bpy.types.CopyLocationConstraint = bone.constraints.get("Copy Location")
                        copy_loc_constr = (str(clc.type), clc.target.name, clc.subtarget, clc.head_tail, clc.target_space, clc.owner_space, clc.use_x, clc.use_y, clc.use_z)
                        control_rig_constraints[bone.name].append(copy_loc_constr)
                    if "Copy Rotation" in bone.constraints:
                        crc: bpy.types.CopyRotationConstraint = bone.constraints.get("Copy Rotation")
                        copy_rot_constr = (str(crc.type), crc.target.name, crc.subtarget, 0.0, crc.target_space, crc.owner_space, crc.use_x, crc.use_y, crc.use_z)
                        control_rig_constraints[bone.name].append(copy_rot_constr)
                    if "Copy Transforms" in bone.constraints:
                        ctc: bpy.types.CopyTransformsConstraint = bone.constraints.get("Copy Transforms")
                        copy_trans_constr = (str(ctc.type), ctc.target.name, ctc.subtarget, ctc.head_tail, ctc.target_space, ctc.owner_space, False, False, False)
                        control_rig_constraints[bone.name].append(copy_trans_constr)
            control_rig_constraints_string = json.dumps(control_rig_constraints, separators=(',', ':'))
            control_rig["Constraint Dictionary"] = control_rig_constraints_string

            if self.character_name != '':
                self.update_IK_flag(context)
        else:
            self.control_rig_name = ''

    def update_character_editable(self, context):
        bpy.data.objects[self.character_name]["TRACER-Editable"] = self.character_editable_flag

    def update_character_name(self, context):
        if self.character_name == '':
            return
        elif self.character_name in bpy.data.objects and bpy.data.objects[self.character_name].type == 'ARMATURE':
            character = bpy.data.objects[self.character_name]
            character["TRACER Setup Done"] = ('hip' in bpy.data.objects) and bpy.data.objects['hip'] in bpy.data.objects[self.character_name].children
            
            
            character_constraints: dict[str, list[tuple[str, str, str, float, str, str, bool, bool, bool]]] = {}
            # Save constraints in dictionary
            for bone in character.pose.bones:
                character_constraints[bone.name] = []
                if "Copy Location" in bone.constraints:
                    clc: bpy.types.CopyLocationConstraint = bone.constraints.get("Copy Location")
                    copy_loc_constr = (str(clc.type), clc.target.name, clc.subtarget, clc.head_tail, clc.target_space, clc.owner_space, clc.use_x, clc.use_y, clc.use_z)
                    character_constraints[bone.name].append(copy_loc_constr)
                if "Copy Rotation" in bone.constraints:
                    crc: bpy.types.CopyRotationConstraint = bone.constraints.get("Copy Rotation")
                    copy_rot_constr = (str(crc.type), crc.target.name, crc.subtarget, 0.0, crc.target_space, crc.owner_space, crc.use_x, crc.use_y, crc.use_z)
                    character_constraints[bone.name].append(copy_rot_constr)
                if "Copy Transforms" in bone.constraints:
                    ctc: bpy.types.CopyTransformsConstraint = bone.constraints.get("Copy Transforms")
                    copy_trans_constr = (str(ctc.type), ctc.target.name, ctc.subtarget, ctc.head_tail, ctc.target_space, ctc.owner_space, False, False, False)
                    character_constraints[bone.name].append(copy_trans_constr)
            character_constraints_string = json.dumps(character_constraints, separators=(',', ':'))
            character["Constraint Dictionary"] = character_constraints_string

            if self.control_rig_name != '':
                self.update_IK_flag(context)
            
        else:
            self.character_name = ''

    def update_IK_flag(self, context):
        character_obj: bpy.types.Object = bpy.data.objects[self.character_name] if len(self.character_name) > 0 else None
        control_rig: bpy.types.Object = bpy.data.objects[self.control_rig_name] if len(self.control_rig_name) > 0 else None

        if character_obj != None:
            character_obj["IK-Flag"] = self.character_IK_flag

            character_constraints: dict[str, list[tuple[str, str, str, float, str, str]]] = json.loads(character_obj["Constraint Dictionary"])
            for bone in character_obj.pose.bones:
                bone_constraints = character_constraints[bone.name]
                if character_obj["IK-Flag"]:
                    # Add back constraints to armature if IK-Flag is true
                    for constraint_description in bone_constraints:
                        bone.constraints.new(type=constraint_description[0])
                        constraint_name = constraint_description[0].replace("_", " ").lower().title()   # Converting the constraint type enum string to the actual constraint name (e.g. "COPY_ROTATION" -> "Copy Rotation")
                        bone.constraints[constraint_name].target = bpy.data.objects[constraint_description[1]]
                        bone.constraints[constraint_name].subtarget = constraint_description[2]
                        if constraint_name != "Copy Rotation":
                            bone.constraints[constraint_name].head_tail = constraint_description[3]
                        bone.constraints[constraint_name].target_space = constraint_description[4]
                        bone.constraints[constraint_name].owner_space = constraint_description[5]
                        if constraint_name != "Copy Transforms":
                            bone.constraints[constraint_name].use_x = constraint_description[6]
                            bone.constraints[constraint_name].use_y = constraint_description[7]
                            bone.constraints[constraint_name].use_z = constraint_description[8]
                else:
                    # Remove constraints from armature if IK-Flag is false
                    for constraint in bone.constraints:
                        bone.constraints.remove(constraint)
            
        else:
            bpy.ops.wm.ik_toggle_report_handler('EXEC_DEFAULT')

        if control_rig != None:
            control_rig_constraints: dict[str, list[tuple[str, str, str, float, str, str]]] = json.loads(control_rig["Constraint Dictionary"])
            control_rig_armature: bpy.types.Armature = control_rig.data
            for bone in control_rig.pose.bones:
                if  bone.name not in control_rig_armature.collections["ORG"].bones and\
                    bone.name not in control_rig_armature.collections["MCH"].bones and\
                    bone.name not in control_rig_armature.collections["DEF"].bones:
                    
                    bone_constraints = control_rig_constraints[bone.name]
                    if not character_obj["IK-Flag"]:
                        # Add back constraints to control rig if IK-Flag is false
                        for constraint_description in bone_constraints:
                            bone.constraints.new(type=constraint_description[0])
                            constraint_name = constraint_description[0].replace("_", " ").lower().title()
                            bone.constraints[constraint_name].target = bpy.data.objects[constraint_description[1]]
                            bone.constraints[constraint_name].subtarget = constraint_description[2]
                            if constraint_name != "Copy Rotation":
                                bone.constraints[constraint_name].head_tail = constraint_description[3]
                            bone.constraints[constraint_name].target_space = constraint_description[4]
                            bone.constraints[constraint_name].owner_space = constraint_description[5]
                            if constraint_name != "Copy Transforms":
                                bone.constraints[constraint_name].use_x = constraint_description[6]
                                bone.constraints[constraint_name].use_y = constraint_description[7]
                                bone.constraints[constraint_name].use_z = constraint_description[8]
                    else:
                        # Remove constraints from control rig if IK-Flag is true
                        for constraint in bone.constraints:
                            bone.constraints.remove(constraint)
                        #bone_constraint.enabled = not character_obj["IK-Flag"]
        else:
            bpy.ops.wm.ik_toggle_report_handler('EXEC_DEFAULT')
            #bpy.types.Operator.report({'ERROR'}, 'Assign a value to the TRACER Control Rig field')

        # Forcing update visualisation of Property Panel
        for area in bpy.context.screen.areas:
            if area.type == 'PROPERTIES':
                area.tag_redraw()
    
    def get_all_armatures(self, context, edit_text):
        list_of_armatures: list[str] = []
        # Search names of all Characters in the TRACER Scene
        for obj in bpy.data.objects:
            if obj.type == 'ARMATURE':
                list_of_armatures.append(obj.name)
        return list_of_armatures
    
    def get_all_armatures_in_tracer(self, context, edit_text):
        list_of_armatures: list[str] = []
        # Search names of all Characters in the TRACER Scene
        for obj in bpy.data.collections[self.tracer_collection].objects:
            if obj.type == 'ARMATURE':
                list_of_armatures.append(obj.name)
        
        if len(list_of_armatures) == 0:
            list_of_armatures = self.get_all_armatures(context, edit_text)

        return list_of_armatures
    
    def get_all_paths(self, context, edit_text):
        list_of_paths: list[str] = []
        # Search names of all Control Paths in the TRACER Scene
        for obj in bpy.data.objects:
            if obj.get("Control Points", None) != None:
                list_of_paths.append(obj.name)
        return list_of_paths
    
    animation_request_modes_items = [   ('BLOCK',  'As a Block',       'Set to request the animation from AnimHost to be sent as one block',           AnimHostRPC.BLOCK.value),
                                        ('STREAM', 'Stream',           'Set to request the animation from AnimHost to be sent as a stream',            AnimHostRPC.STREAM.value),
                                        ('LOOP',   'Looping Stream',   'Set to request the animation from AnimHost to be sent as looping stream',      AnimHostRPC.STREAM_LOOP.value),
                                        ('STOP',   'Stop Stream',      'Set to request the animation from AnimHost to stop the current pose stream',   AnimHostRPC.STOP.value)]

    server_ip: bpy.props.StringProperty(name='Server IP', default = '127.0.0.1', description='IP adress of the machine you are running Blender on. \'127.0.0.1\' for tests only on this machine.')                                                                          # type: ignore
    dist_port: bpy.props.StringProperty(default = '5555')                                                                                                                                                                                                                   # type: ignore
    sync_port: bpy.props.StringProperty(default = '5556')                                                                                                                                                                                                                   # type: ignore
    update_sender_port: bpy.props.StringProperty(default = '5557')                                                                                                                                                                                                          # type: ignore
    Command_Module_port: bpy.props.StringProperty(default = '5558')                                                                                                                                                                                                         # type: ignore
    humanoid_rig: bpy.props.BoolProperty(name="Humanoid Rig for Unity",description="Check if using humanoid rig and you need to send the character to Unity", default=False)                                                                                                # type: ignore
    tracer_collection: bpy.props.StringProperty(name = 'TRACER Collection', default = 'TRACER_Collection', maxlen=30)                                                                                                                                                       # type: ignore
    overwrite_animation: bpy.props.BoolProperty(name="Overwrite Animation", description="When true, baking an animation received from AnimHost will overwrite the previous one; otherwhise, it writes it on a new layer", default=False)                                    # type: ignore                                                                                                  # type: ignore
    control_rig_name: bpy.props.StringProperty(name='Control Rig', default='', description='Name of the Control Rig used to edit the character in IK mode', update=update_control_rig_name, search=get_all_armatures)                                                       # type: ignore
    character_name: bpy.props.StringProperty(name='Character', default='', description='Name of the Character to animate through the TRACER framework', update=update_character_name, search=get_all_armatures_in_tracer)                                                   # type: ignore
    control_path_name: bpy.props.StringProperty(name='Control Path', default='', description='Name of the Control Path that is used for generating a new animation', search=get_all_paths)                                                                                  # type: ignore
    character_editable_flag: bpy.props.BoolProperty(name='Editable from TRACER', default=True, description='Is the character allowed to be edited through the TRACER framework', update=update_character_editable)                                                          # type: ignore
    character_IK_flag: bpy.props.BoolProperty(name='IK Enabled', default=False, description='Is the character driven by the IK Control Rig?', update=update_IK_flag)                                                                                                        # type: ignore
    animation_request_modes: bpy.props.EnumProperty(items=animation_request_modes_items, name='Animation Request Modes', default='BLOCK')                                                                                                                                   # type: ignore
    slide_frames: bpy.props.BoolProperty(name='Slide Next Frames Forward', default=False)                                                                                                                                                                                   # type: ignore
    # Future feature: Neural Network Parameters
    mix_root_translation: bpy.props.FloatProperty(name='Mix Root Translation', description='?', default=0.5, min=0, max=1)                                                                                                                                                         # type: ignore
    mix_root_rotation: bpy.props.FloatProperty(name='Mix Root Rotation', description='?', default=0.5, min=0, max=1)                                                                                                                                                               # type: ignore
    mix_control_path: bpy.props.FloatProperty(name='Mix Control Path', description='?', default=1, min=0.000001, max=5)                                                                                                                                                            # type: ignore

    new_control_point_pos_offset: bpy.props.FloatProperty(name='Distance Offset (in meters)', description='Distance of the newly created control point and the currently selected one', default=0.5, min=0.25, max=100)                                                                     # type: ignore
    new_control_point_frame_offset: bpy.props.IntProperty(name='Frame Offset', description='Frame offset of the newly created control point and the currently selected one', default=10, min=0, max=500)                                                                   # type: ignore

## Class to keep data
#
class TracerData():

    scene_obj_map: dict[int, SceneObject] = {}
    sceneLight = {}
    sceneCamera = {}
    sceneMesh = {}

    geoPackage = {}
    materialPackage = {}
    texturePackage = {}
    characterPackage = {}

    points_for_frames = {}

    objectsToTransfer = []
    nodeList = []
    geoList = []
    materialList = []
    textureList = []
    editableList = []
    characterList = []
    curveList = []
    editable_objects = []

    SceneObjects: list[SceneObject] = []

    rootChildCount = 0
    
    socket_d = None
    socket_s = None
    socket_c = None
    socket_u = None
    poller = None
    ctx = None
    cID = None
    time = 0
    pingStartTime = 0

    nodesByteData = bytearray([])
    geoByteData = bytearray([])
    texturesByteData = bytearray([])
    headerByteData = bytearray([])
    materialsByteData = bytearray([])
    charactersByteData = bytearray([])
    curvesByteData = bytearray([])
    pingByteMSG = bytearray([])
    ParameterUpdateMSG = bytearray([])

    debugCounter = 0