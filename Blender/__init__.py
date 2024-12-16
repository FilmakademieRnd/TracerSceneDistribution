"""
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
"""

bl_info = {
    "name" : "TRACER for Blender",
    "author" : "Tonio Freitag, Alexandru Schwartz, Francesco Andreussi",
    "description" : "",
    "blender" : (4, 2, 1),
    "version" : (1, 5, 0),
    "location" : "VIEW3D",
    "warning" : "",
    "category" : "Animationsinstitut"
}

from typing import Set
import bpy
import os
from .bl_op import  DoDistribute, UpdateScene, SetupScene, InstallZMQ, SetupCharacter, MakeEditable, ParentToRoot, ParentCharacterToRoot, InteractionListener, SendRpcCall,\
                    AddPath, AddPointAfter, AddPointBefore, ToggleAutoUpdate, UpdateCurveViz, EvaluateSpline, ControlPointProps, ControlPointSelect, EditControlPointHandle,\
                    AnimationRequest, AnimationSave
from .bl_panel import ZMQ_PT_Panel, TRACER_PT_Panel, TRACER_PT_Object_Panel, TRACER_PT_Character_Panel, TRACER_PT_Anim_Path_Panel, TRACER_PT_Control_Points_Panel, TRACER_PT_Anim_Path_Menu
from .tools import draw_pointer_numbers_callback
from .settings import TracerData, TracerProperties
from .updateTRS import RealTimeUpdaterOperator
from .singleSelect import OBJECT_OT_single_select
from .SceneObjects.SceneObjectCharacter import ReportReceivedAnimation
from .AbstractParameter import Parameter, AnimHostRPC

# Imported classes to register
classes = ( ZMQ_PT_Panel, TRACER_PT_Panel, TRACER_PT_Object_Panel, TRACER_PT_Character_Panel, TRACER_PT_Anim_Path_Panel, TRACER_PT_Control_Points_Panel, TRACER_PT_Anim_Path_Menu,
            DoDistribute, UpdateScene, SetupScene, TracerProperties, InstallZMQ, RealTimeUpdaterOperator, OBJECT_OT_single_select,
            SetupCharacter, MakeEditable, ParentToRoot, ParentCharacterToRoot, AddPath, AddPointAfter, AddPointBefore, ControlPointProps, ControlPointSelect, EditControlPointHandle, UpdateCurveViz, EvaluateSpline, ToggleAutoUpdate,
            AnimationRequest, AnimationSave, InteractionListener, SendRpcCall, ReportReceivedAnimation) 

# Container for font information (id and handler object) for drawing text
font_info = {
    "font_id": 0,
    "handler": None,
}

# Function adding an operator entry to add a control path to the scene in a menu
def add_menu_path(self, context):
    print("Registering Add Path Menu Entry")
    self.layout.menu(TRACER_PT_Anim_Path_Panel.bl_idname, icon='PLUGIN')

# Register classes and TRACER-related Data Settings
# Adding Entries to Menus and enabling callback functions and listeners to "translate" user input in Blender UI into TRACER-oriented actions 
def register():
    bpy.types.WindowManager.tracer_data = TracerData()
    bpy.types.Object.tracer_id = bpy.props.IntProperty(name="TRACER ID", default=-1, description="The ID of the corresponding TRACER Object in the Scene")
    from bpy.utils import register_class
    for cls in classes:
        try:
            register_class(cls)
            print(f"Registering {cls.__name__}")
        except Exception as e:
            print(f"{cls.__name__} "+ str(e))

    bpy.types.Scene.tracer_properties = bpy.props.PointerProperty(type=TracerProperties)
    bpy.types.Scene.control_point_settings = bpy.props.PointerProperty(type=ControlPointProps)

    AbstractParameter.AbstractParameter.start_animhost_rpc_id = 0
    TracerProperties.animation_request = Parameter(AnimHostRPC.BLOCK.value, "Request New Animation", parent_object=None, distribute=False, is_RPC=True)
    TracerProperties.mix_root_translation_param = Parameter(0.5, "Mix Root Translation", parent_object=None, distribute=False, is_RPC=True)
    TracerProperties.mix_root_rotation_param    = Parameter(0.5, "Mix Root Rotation",    parent_object=None, distribute=False, is_RPC=True)
    TracerProperties.mix_control_path_param     = Parameter(1,   "Mix Control Path",     parent_object=None, distribute=False, is_RPC=True)

    bpy.types.VIEW3D_MT_mesh_add.append(add_menu_path)      # Adding a submenu with buttons to add a new Control Path and a new Control Point to the Add-Mesh Menu
    bpy.types.VIEW3D_MT_curve_add.append(add_menu_path)     # Adding a submenu with buttons to add a new Control Path and a new Control Point to the Add-Curve Menu

    bpy.app.handlers.depsgraph_update_post.append(UpdateCurveViz.on_delete_update_handler)  # Adding auto update handler for the animation path. Called any time the scene graph is updated
    bpy.app.handlers.depsgraph_update_post.append(ControlPointProps.update_property_ui)     # Adding auto update handler for the collection of control point properties. Called any time the scene graph is updated
    
    #bpy.app.handlers.load_post.append(InteractionListener.invoke)                           # Re-starting the Interacion Listener every time a new blender scene-file is loaded
    #bpy.app.handlers.load_factory_startup_post.append(InteractionListener.invoke)

    # set the font drawing routine to run every frame
    font_info["handler"] = bpy.types.SpaceView3D.draw_handler_add(draw_pointer_numbers_callback, (font_info["font_id"], font_info["handler"]), 'WINDOW', 'POST_PIXEL')

    print("Registered TRACER Add-On")

## Unregister for removal of Addon
#
def unregister():
    # Check whether the custom attribute is there before deleting it to avoid errors being raised
    if hasattr(bpy.types.WindowManager, "tracer_data"):
        del bpy.types.WindowManager.tracer_data

    from bpy.utils import unregister_class
    for cls in classes:
        try:
            unregister_class(cls)
        except Exception as e:
            print(f"{cls.__name__} "+ str(e))

    bpy.types.VIEW3D_MT_mesh_add.remove(add_menu_path)
    print("Unregistered TRACER Add-On")