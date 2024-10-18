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
from .SceneObjects.SceneObject import SceneObject

## Class to keep editable parameters
class TracerProperties(bpy.types.PropertyGroup):

    def update_character_editable(self, context):
        bpy.data.objects[self.character_name]["TRACER-Editable"] = self.character_editable_flag

    def update_IK_flag(self, context):
        character_obj: bpy.types.Object = bpy.data.objects[self.character_name] if len(self.character_name) > 0 else None
        control_rig: bpy.types.Object = bpy.data.objects[self.control_rig_name] if len(self.control_rig_name) > 0 else None

        if character_obj != None:
            character_obj["IK-Flag"] = self.character_IK_flag
            for bone in character_obj.pose.bones:
                for bone_constraint in bone.constraints:
                    bone_constraint.enabled = bpy.data.objects[self.character_name]["IK-Flag"]
        else:
            bpy.ops.wm.ik_toggle_report_handler('EXEC_DEFAULT')
            #bpy.types.Operator.report({'ERROR'}, 'Assign a value to the TRACER Character field')

        if control_rig != None:
            control_rig_armature: bpy.types.Armature = control_rig.data
            for bone in control_rig.pose.bones:
                if  bone.name not in control_rig_armature.collections["ORG"].bones and\
                    bone.name not in control_rig_armature.collections["MCH"].bones and\
                    bone.name not in control_rig_armature.collections["DEF"].bones:
                    for bone_constraint in bone.constraints:
                        bone_constraint.enabled = not character_obj["IK-Flag"]
                else:
                    print(bone.name)
        else:
            bpy.ops.wm.ik_toggle_report_handler('EXEC_DEFAULT')
            #bpy.types.Operator.report({'ERROR'}, 'Assign a value to the TRACER Control Rig field')

        # Forcing update visualisation of Property Panel
        for area in bpy.context.screen.areas:
            if area.type == 'PROPERTIES':
                area.tag_redraw()

    close_connection: bool = False
    server_ip: bpy.props.StringProperty(name='Server IP', default = '127.0.0.1', description='IP adress of the machine you are running Blender on. \'127.0.0.1\' for tests only on this machine.')                                                                          # type: ignore
    dist_port: bpy.props.StringProperty(default = '5555')                                                                                                                                                                                                                   # type: ignore
    sync_port: bpy.props.StringProperty(default = '5556')                                                                                                                                                                                                                   # type: ignore
    update_sender_port: bpy.props.StringProperty(default = '5557')                                                                                                                                                                                                          # type: ignore
    Command_Module_port: bpy.props.StringProperty(default = '5558')                                                                                                                                                                                                         # type: ignore
    humanoid_rig: bpy.props.BoolProperty(name="Humanoid Rig for Unity",description="Check if using humanoid rig and you need to send the character to Unity",default=False)                                                                                                 # type: ignore
    tracer_collection: bpy.props.StringProperty(name = 'TRACER Collection', default = 'TRACER_Collection', maxlen=30)                                                                                                                                                       # type: ignore
    overwrite_animation: bpy.props.BoolProperty(name="Overwrite Animation", description="When true, baking an animation received from AnimHost will overwrite the previous one; otherwhise, it writes it on a new layer", default=False)                                    # type: ignore                                                                                                  # type: ignore
    control_rig_name: bpy.props.StringProperty(name='Control Rig', default='', description='Name of the Control Rig used to edit the character in IK mode')                                                                                                                 # type: ignore
    character_name: bpy.props.StringProperty(name='Character', default='', description='Name of the Character to animate through the TRACER framework')                                                                                                                     # type: ignore
    control_path_name: bpy.props.StringProperty(name='Control Path', default='', description='Name of the Control Path that is used for generating a new animation')                                                                                                           # type: ignore
    character_editable_flag: bpy.props.BoolProperty(name='Editable from TRACER', default=False, description='Is the character allowed to be edited through the TRACER framework', update=update_character_editable)                                                         # type: ignore
    character_IK_flag: bpy.props.BoolProperty(name='IK Enabled', default=False, description='Is the character driven by the IK Control Rig?', update=update_IK_flag)                                                                                                        # type: ignore

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