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

from typing import Annotated, Set
import bpy
from bpy_extras import anim_utils
import os
import re
import time
from mathutils import Vector, Euler

from bpy.types import Context
from bpy.app.handlers import persistent

from .settings import TracerData
from .SceneObjects.SceneObject import SceneObject
from .SceneObjects.SceneCharacterObject import SceneCharacterObject
from .AbstractParameter import Parameter, AnimHostRPC
from .serverAdapter import send_RPC_msg, send_parameter_update, set_up_thread, close_socket_d, close_socket_s, close_socket_c, close_socket_u
from .tools import clean_up_tracer_data, install_ZMQ, check_ZMQ, setup_tracer_collection, parent_to_root, add_path, make_point, add_point, move_point, update_curve, path_points_check
from .sceneDistribution import gather_scene_data, process_control_path#, resendCurve
from .GenerateSkeletonObj import process_armature




## operator classes
#
class SetupScene(bpy.types.Operator):
    bl_idname = "object.setup_tracer"
    bl_label = "TRACER Scene Setup"
    bl_description = 'Create Collections for static and editable objects'

    def execute(self, context):
        print('setup scene')
        setup_tracer_collection()
        return {'FINISHED'}

class DoDistribute(bpy.types.Operator):
    bl_idname = "object.zmq_distribute"
    bl_label = "Connect to TRACER"
    bl_description = 'Distribute the scene to TRACER clients'

    is_distributed: bool = False

    def execute(self, context):
        print("do distribute")
        if check_ZMQ():
            reset_tracer_connection()
            if DoDistribute.is_distributed:
                clean_up_tracer_data(level=2)
                DoDistribute.is_distributed = False
                DoDistribute.bl_label = "Connect to TRACER"
                return {'FINISHED'}
            else:
                context.scene.tracer_properties.close_connection = False
                # In order to change the mode, an active object MUST be there
                if not context.active_object and len(context.view_layer.objects) > 0:
                    # If the context has no active object, set any non-hidden object as active object
                    a_valid_object = None
                    i = 0
                    while i < len(context.view_layer.objects) and a_valid_object == None:
                        if not context.view_layer.objects[i].hide_get():
                            a_valid_object = context.view_layer.objects[i]
                    a_valid_object.select_set(True)
                    context.view_layer.objects.active = a_valid_object

                # Get current mode
                current_mode = context.active_object.mode
                if current_mode != 'OBJECT':
                    bpy.ops.object.mode_set(mode = 'OBJECT', toggle= True)    # Force OBJECT mode
                bpy.ops.object.select_all(action='DESELECT')
                objCount = gather_scene_data()
                bpy.ops.wm.real_time_updater('INVOKE_DEFAULT')
                bpy.ops.object.single_select('INVOKE_DEFAULT')
                if objCount > 0:
                    set_up_thread()
                    DoDistribute.is_distributed = True
                    DoDistribute.bl_label = "Close connection to TRACER"
                    self.report({'INFO'}, f'Sending {str(objCount)} Objects to TRACER')
                else:
                    self.report({'ERROR'}, 'TRACER collections not found or empty')
                if current_mode != 'OBJECT':
                    bpy.ops.object.mode_set(mode = current_mode)    # Revert mode to previous one
        else:
            self.report({'ERROR'}, 'Please Install Zero MQ before continuing')
        
        return {'FINISHED'}

class UpdateScene(bpy.types.Operator):
    bl_idname = "object.update_scene"
    bl_label = "Send Scene"
    bl_description = 'Send the latest version of the scene to TRACER'

    def execute(self, context):
        print('Updating scene data...')
        clean_up_tracer_data(level=2)
        objCount = gather_scene_data()
        if objCount > 0:
            self.report({'INFO'}, f'Sending {str(objCount)} Objects to TRACER')
        return {'FINISHED'}

class InstallZMQ(bpy.types.Operator):
    bl_idname = "object.zmq_install"
    bl_label = "Install ZMQ"
    bl_description = 'Install Zero MQ. You need admin rights for this to work!'

    def execute(self, context):
        print('Installing ZMQ')
        zmq_result = install_ZMQ()
        if zmq_result == 'admin error':
            self.report({'ERROR'}, f'You need to be Admin to install ZMQ')
            return {'FINISHED'}
        if zmq_result == 'success':
            self.report({'INFO'}, f'Successfully Installed ZMQ')
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, str(zmq_result))
            return {'FINISHED'}

class SetupCharacter(bpy.types.Operator):
    bl_idname = "object.setup_character"
    bl_label = "TRACER Character Setup"
    bl_description = 'generate obj for each Character bone'

    def execute(self, context):
        print('Setup Character')
        character_name: str = bpy.context.scene.tracer_properties.character_name

        if character_name == '' or bpy.data.objects[character_name] == None:
            self.report({'ERROR'}, f'Invalid character to setup')
            return {'FINISHED'}
        
        if bpy.data.objects[character_name].type != 'ARMATURE':
            self.report({'ERROR'}, f'Invalid character to setup')
            return {'FINISHED'}

        if  not bpy.data.objects[character_name].get('TRACER Setup Done', False):
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = bpy.data.objects[character_name]
            process_armature(bpy.data.objects[character_name])
            bpy.data.objects[character_name]['TRACER Setup Done'] = True
        return {'FINISHED'}
    
class MakeEditable(bpy.types.Operator):
    bl_idname = "object.make_obj_editable"
    bl_label = "Make selected Editable"
    bl_description = 'generate a new custom property called Editable for all selected obj'

    def execute(self, context):
        print('Make obj Editable')
        selected_objects = bpy.context.selected_objects
        for obj in selected_objects:
            # Add custom property "Editable" with type bool and default value True
            obj["TRACER-Editable"] = True

        # Forcing update visualisation of Property Panel
        for area in bpy.context.screen.areas:
            if area.type == 'PROPERTIES':
                area.tag_redraw()
        return{'FINISHED'}
    
class ParentToRoot(bpy.types.Operator):
    bl_idname = "object.parent_selected_to_root"
    bl_label = "Add Object to TRACER"
    bl_description = 'Parent all the selected object to the TRACER Scene Root'

    def execute(self, context):
        print('Parent objects')
        parent_to_root(bpy.context.selected_objects)
        return {'FINISHED'}
    
class ParentCharacterToRoot(bpy.types.Operator):
    bl_idname = "object.parent_character_to_root"
    bl_label = "Add Character to TRACER"
    bl_description = 'Parent the chosen Character to the TRACER Scene Root'

    def execute(self, context):
        print('Parent character')
        if bpy.context.scene.tracer_properties.character_name in bpy.data.objects:
            character = bpy.data.objects[bpy.context.scene.tracer_properties.character_name]
            parent_to_root([character])
        else:
            self.report({'ERROR'}, 'Assign a valid value to the Character field.')
        return {'FINISHED'}
   
### Operator to add a new Animation Path
#   The execution is triggered by a button in the TRACER Panel or by an entry in the Add Menu
class AddPath(bpy.types.Operator):
    bl_idname = "object.add_path"
    bl_label = "Add Control Path"
    bl_description = 'Create an Object to act as a Control Path for a locomotion animation. The character will be animated by AnimHost to follow such path'
    bl_options = {'REGISTER', 'UNDO'}

    default_name = "AnimPath"

    def execute(self, context):
        print('Add Path START')
        #if context.active_object.get(""):
        report: tuple[set[str], str] = add_path(self.default_name)     # Call the function resposible of creating the animation path
        self.report(report[0], report[1])
        bpy.ops.path.interaction_listener("INVOKE_DEFAULT")             # Initialising and starting Interaction Listener modal operator, which handles user interactions on the Control Path
        return {'FINISHED'}

#! DEPRECATED
# class FKIKToggle(bpy.types.Operator):
#     bl_idname = "scene.fk_ik_toggle"
#     bl_label = "Switch to Inverse Kinematics"
#     bl_description = 'Switch between Forward and Inverse Kinematic for animating the character over its Control Path'

#     def execute(self, context):
#         # If the toggling should happen only when the chartacter is selected
#         if context.active_object and context.active_object.type == 'ARMATURE':
#             selected_character: bpy.types.Object = context.active_object
#             if selected_character.get("IK-Flag", None) != None:
#                 selected_character["IK-Flag"] = not selected_character["IK-Flag"]

#                 #if selected_character["IK-Flag"]:
#                 #    FKIKToggle.bl_label = "Switch to Forward Kinematics"
#                 #else:
#                 #    FKIKToggle.bl_label = "Switch to Inverse Kinematics"
#             #else:
#             #    selected_character["IK-Flag"] = 1
#             #    FKIKToggle.bl_label = "Switch to Forward Kinematics"

#             # Updating Bone Constraints Values for the currently selected Armature
#             for bone in selected_character.pose.bones:
#                 for bone_constraint in bone.constraints:
#                         bone_constraint.enabled = selected_character["IK-Flag"]

#             control_rig: bpy.types.Object = bpy.context.scene.tracer_properties.control_rig_name
#             if control_rig != None:
#                 control_rig_armature: bpy.types.Armature = control_rig.data
#                 for bone in control_rig.pose.bones:
#                     if  bone.name not in control_rig_armature.collections["ORG"].bones and\
#                         bone.name not in control_rig_armature.collections["MCH"].bones and\
#                         bone.name not in control_rig_armature.collections["DEF"].bones:
#                         for bone_constraint in bone.constraints:
#                             bone_constraint.enabled = not selected_character["IK-Flag"]
#                     else:
#                         print(bone.name)
#             else:
#                 self.report({'ERROR'}, 'Select a control rig for this character to use IK rigging')

#         # Forcing update visualisation of Property Panel
#         for area in bpy.context.screen.areas:
#             if area.type == 'PROPERTIES':
#                 area.tag_redraw()

#         return {'FINISHED'}

### Operator to add a new Animation Control Point
#   The execution is triggered by a button in the TRACER Panel or by an entry in the Add Menu
class AddPointAfter(bpy.types.Operator):
    bl_idname = "object.add_control_point_after"
    bl_label = "Add Point After"
    bl_description = 'Add a new Control Point to the (selected) Animation Path after the one currently selected'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        print('Add Point START')
        if bpy.context.scene.tracer_properties.control_path_name != '' and bpy.context.scene.tracer_properties.control_path_name in bpy.data.objects:
            anim_path = bpy.data.objects[bpy.context.scene.tracer_properties.control_path_name]
            new_point_index = anim_path["Control Points"].index(context.active_object)  if (context.active_object in anim_path["Control Points"] \
                                                                                            and anim_path["Control Points"].index(context.active_object) < len(anim_path["Control Points"])-1) \
                        else  -1

            report: tuple[set[str], str] = add_point(anim_path, pos=new_point_index, after=True)
            self.report(report[0], report[1])
        else:
            self.report({'ERROR'}, 'Assign a valid value to the Control Path field in the Panel to use this functionality.')
        return {'FINISHED'}
    
### Operator to add a new Animation Control Point
#   The execution is triggered by a button in the TRACER Panel or by an entry in the Add Menu
class AddPointBefore(bpy.types.Operator):
    bl_idname = "object.add_control_point_before"
    bl_label = "New Point Before"
    bl_description = 'Add a new Control Point to the (selected) Animation Path before the one currently selected'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        print('Add Point START')
        if bpy.context.scene.tracer_properties.control_path_name != '' and bpy.context.scene.tracer_properties.control_path_name in bpy.data.objects:
            anim_path = bpy.data.objects[bpy.context.scene.tracer_properties.control_path_name]
            new_point_index = anim_path["Control Points"].index(context.active_object) if (context.active_object in anim_path["Control Points"] \
                                                                                       and anim_path["Control Points"].index(context.active_object) < len(anim_path["Control Points"])) \
                        else  0

            report: tuple[set[str], str] = add_point(anim_path, pos=new_point_index, after=False)
            self.report(report[0], report[1])
        else:
            self.report({'ERROR'}, 'Assign a value to the Control Path field in the Panel to use this functionality.')
        return {'FINISHED'}
    
### Operator to manage the Properties of the Animation Control Points
class ControlPointProps(bpy.types.PropertyGroup):
    bl_idname = "path.control_point_props"
    bl_label = "Confirm Changes"
    #bl_options = {'REGISTER', 'UNDO'}

    def get_items():
        items = [("Walking", "Walking", "Walking Locomotion Style"),
                 ("Running", "Running", "Running Locomotion Style"),
                 ("Jumping", "Jumping", "Jumping Locomotion Style")]
        return items
    
    @persistent
    def update_property_ui(scene):
        if not bpy.context.active_object == None:
            active_obj = bpy.context.active_object
        else:
            return
        
        if bpy.context.scene.tracer_properties.control_path_name in bpy.data.objects:
            anim_path = bpy.data.objects[bpy.context.scene.tracer_properties.control_path_name]
        else:
            return

        # If a Path has been created in the scene AND the selected object is a Control Point AND the Auto Update (with the other advanced features) is enabled
        if (not anim_path == None) and (re.search(r'Pointer', active_obj.name)) and (anim_path["Auto Update"]):
            scene.control_point_settings.position = active_obj.parent["Control Points"].index(active_obj)
            scene.control_point_settings.frame = active_obj["Frame"]
            scene.control_point_settings.ease_in = active_obj["Ease In"]
            scene.control_point_settings.ease_out = active_obj["Ease Out"]
            #! Style label not currently used
            #scene.control_point_settings.style = active_obj["Style"]
            active_obj.select_set(True)
        else:
            return

    def update_position(self, context):
        if bpy.context.tool_settings.use_proportional_edit_objects:
            return
        context.active_object["Position"] = self.position
        move_point(context.active_object, self.position)
        print("Update! " + str(self.position))

    def update_frame(self, context):
        # Set the property of the active control point to the new UI value
        # TODO: update also following points keeping a constant delta to the previous ones ???
        context.active_object["Frame"] = self.frame
        print("Update! " + str(self.frame))

    def update_in(self, context):
        # Set the property of the active control point to the new UI value
        context.active_object["Ease In"] = self.ease_in
        print("Update! " + str(self.ease_in))

    def update_out(self, context):
        # Set the property of the active control point to the new UI value
        context.active_object["Ease Out"] = self.ease_out
        print("Update! " + str(self.ease_out))

    def update_style(self, context):
        context.active_object["Style"] = self.style
        print("Update! " + self.style)

    position: bpy.props.IntProperty(name="Position", min=0, update=update_position)                                                                                                                                                                                         # type: ignore
    frame: bpy.props.IntProperty(name="Frame", min=0, max=6000, update=update_frame)                                                                                                                                                                                        # type: ignore
    ease_in: bpy.props.IntProperty(name="Ease In", min=0, max=100, update=update_in)                                                                                                                                                                                        # type: ignore
    ease_out: bpy.props.IntProperty(name="Ease Out", min=0, max=100, update=update_out)                                                                                                                                                                                     # type: ignore
    style: bpy.props.EnumProperty(items=get_items(), name="Style", description="Choose a Locomotion Style", default="Running", update=update_style)                                                                                                                         # type: ignore

### Operator to add a new Animation Path
#   The execution is triggered by a button in the TRACER Panel or by an entry in the Add Menu
class UpdateCurveViz(bpy.types.Operator):
    bl_idname = "object.update_curve"
    bl_label = "Update Curve"
    bl_description = 'Update the Control Path given the new configuration of the Control Points'

    @persistent
    def execute(self, context):
        print('Evaluate Curve START')
        if bpy.context.scene.tracer_properties.control_path_name != '' and  bpy.context.scene.tracer_properties.control_path_name in bpy.data.objects:
            anim_path = bpy.data.objects[bpy.context.scene.tracer_properties.control_path_name]
            # Check for deleted control points and evtl. do some cleanup before updating the curve 
            for child in anim_path.children:
                if not bpy.context.scene in child.users_scene:
                    print(child.name + " IS NOT in the scene")
                    bpy.data.objects.remove(child, do_unlink=True)
            update_curve(anim_path)
            for area in bpy.context.screen.areas:
                if area.type == 'PROPERTIES':
                    area.tag_redraw()
        else:
            self.report({'ERROR'}, 'Assign a value to the Control Path field in the Panel to use this functionality.')
        
        return {'FINISHED'}
    
    @persistent
    def on_delete_update_handler(scene):
        if EvaluateSpline.anim_preview_obj_name not in bpy.data.objects:
            EvaluateSpline.bl_label = "Create Animation Preview"
        else:
            EvaluateSpline.bl_label = "Update Animation Preview"

        if bpy.context.scene.tracer_properties.control_path_name in bpy.data.objects:
            anim_path = bpy.data.objects[bpy.context.scene.tracer_properties.control_path_name]
            # Check for deleted control points and evtl. do some cleanup before updating the curve  
            for i, child in enumerate(anim_path.children):
                if not bpy.context.scene in child.users_scene:
                    print(child.name + " IS NOT in the scene")
                    bpy.data.objects.remove(child, do_unlink=True)
                    update_curve(anim_path)
                    if i < len(anim_path["Control Points"]) - 1:
                        # If the removed element was not the last point in the list
                        # Select the element that is now in that position
                        anim_path["Control Points"][i].select_set(True)
                    else:
                        # Select the new last element
                        anim_path["Control Points"][-1].select_set(True)

            for area in bpy.context.screen.areas:
                if area.type == 'PROPERTIES':
                    area.tag_redraw()

### Operator toggling the automatic updating of the animation path
#   Inverts value of the Auto Update bool property for the Control Path object. Triggered by a button in the TRACER Add On Panel
class ToggleAutoUpdate(bpy.types.Operator):
    bl_idname = "object.toggle_auto_eval"
    bl_label = "Enable Advanced Functionalities"
    bl_description = 'Enable/Disable advanced functionalities on the Control Path'

    def execute(self, context):
        # If the toggling should happen only when the path is selected, add also the following condition -> and bpy.data.objects[bpy.context.scene.tracer_properties.control_path_name].select_get()
        if bpy.context.scene.tracer_properties.control_path_name != '' and bpy.context.scene.tracer_properties.control_path_name in bpy.data.objects:

            anim_path = bpy.data.objects[bpy.context.scene.tracer_properties.control_path_name]
            anim_path["Auto Update"] = not anim_path["Auto Update"]

            # Forcing update visualisation of Property Panel
            for area in bpy.context.screen.areas:
                if area.type == 'PROPERTIES':
                    area.tag_redraw()

            if (not anim_path["Auto Update"]) or bpy.context.tool_settings.use_proportional_edit_objects:
                ToggleAutoUpdate.bl_label = "Enable Advanced Functionalities"
            else:
                ToggleAutoUpdate.bl_label = "Disable Advanced Functionalities"
                ControlPointProps.update_property_ui(context.scene)
        else:
            self.report({'ERROR'}, 'Assign a value to the Control Path field in the Panel to use this functionality.')

        return {'FINISHED'}

### Operator for selecting a Control Point.
#   The cp_name property is used to pass the name of the Control Point to be selected on to the Operator, at the click of the corresponding button in the TRACER Control Point UI Panel
class ControlPointSelect(bpy.types.Operator):
    bl_idname = "object.control_point_select"
    bl_label = ""
    bl_description = 'Select the signalled Control Point'

    cp_name: bpy.props.StringProperty()                                                                                                                                                                                                                                 # type: ignore

    def execute(self, context):
        if  bpy.context.scene.tracer_properties.control_path_name != '' and bpy.context.scene.tracer_properties.control_path_name in bpy.data.objects and\
            bpy.data.objects[bpy.context.scene.tracer_properties.control_path_name]["Auto Update"]:
            for obj in bpy.data.objects:
                obj.select_set(False)

            if not self.cp_name in context.view_layer.objects:
                bpy.data.objects.remove(bpy.data.objects[self.cp_name], do_unlink=True)
                path_points_check(bpy.data.objects[bpy.context.scene.tracer_properties.control_path_name])
            else:
                bpy.data.objects[self.cp_name].select_set(True)
                bpy.context.view_layer.objects.active = bpy.data.objects[self.cp_name]
                bpy.ops.object.mode_set(mode='OBJECT', toggle=False)     # Force Object Mode
        else:
            self.report({'ERROR'}, 'Assign a value to the Control Path field in the Panel to use this functionality.')

        return {'FINISHED'}

### Operator that allows the user to enter Edit Mode directly from the click of a button in the TRACER Control Points Panel
#   The user is going to edit the curve with the traditional Blender UX, the selected bezier point is the one corresponding to the currently selected Animation Path Control Point Object
#   If no point is selected, the button doesn't do anything other then checking that everything is up to date and eventually updating the appearance of the curve and
class EditControlPointHandle(bpy.types.Operator):
    bl_idname = "curve.edit_control_point_handle"
    bl_label = "Edit Selected Control Point Handles"
    bl_description = 'Edit the handles of the currently selected Control Point'

    last_selected_point_index = -1

    def execute(self, context):
        if bpy.context.scene.tracer_properties.control_path_name != '' and bpy.context.scene.tracer_properties.control_path_name in bpy.data.objects:
            anim_path = bpy.data.objects[bpy.context.scene.tracer_properties.control_path_name]

            update_curve(anim_path)
            if context.active_object in anim_path["Control Points"]:
                ptr_idx = anim_path["Control Points"].index(context.active_object)
                EditControlPointHandle.last_selected_point_index = ptr_idx
                for obj in bpy.data.objects:
                    obj.select_set(False)

                control_path_curve = anim_path.children[0]; control_path_curve.select_set(True) # Select Control Path Bezier Curve
                context.view_layer.objects.active = control_path_curve
                bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                bpy.ops.curve.select_all(action='DESELECT')

                bpy.context.scene.tool_settings.workspace_tool_type = 'DEFAULT'

                print(control_path_curve.name + " " + control_path_curve.id_type)
                control_path_curve.data.splines[0].bezier_points[ptr_idx].select_control_point = True
        else:
            self.report({'ERROR'}, 'Assign a value to the Control Path field in the Panel to use this functionality.')

        return {'FINISHED'}

### Operator to evaluate the timings of the animation on the path
#   Triggered by a button in the TRACER Animation Path Panel
#   Creates a new Object that is moved along the Animation Path
#   It uses the information given by the User (as the Control Point location, orientation, frame, Ease In and Ease Out, and the tangents/handles of the Bezier Points)  
class EvaluateSpline(bpy.types.Operator):
    bl_idname = "curve.evaluate_spline"
    bl_label = "Create Animation Preview"
    bl_description = "Compute an animation preview over the selected path"

    anim_preview_obj_name = "Animation Preview Object"
    fwd_vector = Vector((0, -1))

    def execute(self, context):
        if not AnimationRequest.valid_frames:
            self.report({'ERROR'}, "Invalid frame values for the Control Points")
            return {'FINISHED'}

        control_path_name: str = bpy.context.scene.tracer_properties.control_path_name
        if control_path_name != '' and bpy.data.objects[control_path_name] != None:           
            anim_path = bpy.data.objects[control_path_name]
            if EvaluateSpline.anim_preview_obj_name not in bpy.data.objects:
                anim_prev = make_point(spawn_location=anim_path["Control Points"][0].location + Vector((0, 0, 0.5)), name = EvaluateSpline.anim_preview_obj_name)
                bpy.context.scene.collection.objects.link(anim_prev)
            else:
                EvaluateSpline.bl_label = "Update Animation Preview"
                anim_prev = bpy.data.objects[EvaluateSpline.anim_preview_obj_name]
            
            curve_path = process_control_path(anim_path)
            context.scene.frame_start = 0
            context.scene.frame_end = curve_path.pointsLen - 1
            anim_prev.animation_data_clear()
            for i in range(curve_path.pointsLen):
                anim_prev.location          = Vector(( curve_path.points[i*3],  curve_path.points[i*3+1],  curve_path.points[i*3+2] + 0.5))
                look_at_vector              = Vector((curve_path.look_at[i*3], curve_path.look_at[i*3+1], curve_path.look_at[i*3+2]))
                look_at_vector_2d           = look_at_vector.xy # Rotations are only allowed around the Z-axis (up-axis), so the third component should always be 0. I read it for facilitate debugging
                look_at_angle               = look_at_vector_2d.angle_signed(EvaluateSpline.fwd_vector)
                anim_prev.rotation_euler    = Euler((0, 0, look_at_angle))

                anim_prev.keyframe_insert(data_path="location",         frame=i)
                anim_prev.keyframe_insert(data_path="rotation_euler",   frame=i)
        else:
            self.report({'ERROR'}, 'Assign a value to the Control Path field in the Panel to use this functionality.')

        return {'FINISHED'}

### Operator to request a new character animation from AnimHost given the designed path
#   Triggered by a button in the TRACER Animation Path Panel
#   Looks for the Control Path property of the currently selected character
#   If a Control Path is assigned, it sends the list Control Points to AnimHost
class AnimationRequest(bpy.types.Operator):
    bl_idname = "object.tracer_animation_request"
    bl_label = "Request Animation"
    bl_description = "Request new animation for the selected character from AnimHost"

    valid_frames: bool = False 
    animation_request = Parameter(AnimHostRPC.BLOCK.value, "Request New Animation", None, distribute=False, is_RPC=True)
    animation_request.__id = 1

    animation_request_mode: bpy.props.EnumProperty(items = [("BLOCK",       "As a Block",           "Send Animation as a Block",        AnimHostRPC.BLOCK.value),
                                                            ("STREAM",      "As a Stream",          "Start Animation Streaming",        AnimHostRPC.STREAM.value),
                                                            ("STREAM_LOOP", "As a Looped Stream",   "Start Loop Animation Streaming",   AnimHostRPC.STREAM_LOOP.value),
                                                            ("STOP",        "Stop Stream",          "Stop Animation Streaming",         AnimHostRPC.STOP.value)
                                                            ])                                                                                                                                                                                                                          # type: ignore

    @classmethod
    def poll(cls, context):
       control_path_name: str = bpy.context.scene.tracer_properties.control_path_name
       return control_path_name != '' and bpy.data.objects[control_path_name] != None

    def execute(self, context: Context):
        if not AnimationRequest.valid_frames:
            self.report({'ERROR'}, "Invalid frame values for the Control Points")
            return {'FINISHED'}
        
        if not DoDistribute.is_distributed:
            self.report({'ERROR'}, "Connect to TRACER before requesting a new animation")
            return {'FINISHED'}

        # TODO: check whether TRACER has been correctly being configured
        control_path_name: str = bpy.context.scene.tracer_properties.control_path_name
        character_name: str = bpy.context.scene.tracer_properties.character_name
        if  control_path_name != '' and bpy.data.objects[control_path_name] != None and\
            character_name != '' and bpy.data.objects[character_name] != None:
            print("Sending updated Animation Path, this triggers the sending of a new Animation Sequence")
            control_path_bl_obj: bpy.types.Object = bpy.data.objects[control_path_name]
            if control_path_bl_obj != None and control_path_bl_obj.get("Control Points", None) != None:
                tracer_data: TracerData = bpy.context.window_manager.tracer_data

                # Getting the Scene Character Object corresponding to the selected Blender Character in the Scene
                if bpy.data.objects[character_name].tracer_id < len(tracer_data.SceneObjects):
                    tracer_character_object: SceneCharacterObject = tracer_data.SceneObjects[bpy.data.objects[character_name].tracer_id]
                    # Ensure that the ID of the Control Path associated with the selected Character is up to date
                    tracer_character_object.update_control_path_id()

                if control_path_bl_obj.tracer_id < len(tracer_data.SceneObjects):
                    control_path_tracer_obj: SceneObject = tracer_data.SceneObjects[control_path_bl_obj.tracer_id]
                    # Ensure that the values of the Control Points exposed to TRACER are up to date
                    control_path_tracer_obj.update_control_points()
                
                    point_locations_param = control_path_tracer_obj.parameter_list[-2]
                    point_rotations_param = control_path_tracer_obj.parameter_list[-1]

                    send_parameter_update(point_locations_param)
                    send_parameter_update(point_rotations_param)

                    # [Deprecated - now realying on the ParameterUpdate Message] -> resendCurve()
                    # Request Animation from AnimHost through RPC call
                    match self.animation_request_mode:
                        case 'BLOCK':
                            self.animation_request.value = AnimHostRPC.BLOCK.value
                        case 'STREAM':
                            self.animation_request.value = AnimHostRPC.STREAM.value
                        case 'STREAM_LOOP':
                            self.animation_request.value = AnimHostRPC.STREAM_LOOP.value
                        case 'STOP':
                            self.animation_request.value = AnimHostRPC.STOP.value
                    send_RPC_msg(self.animation_request)
                
            else:
                self.report({'ERROR'}, "Assign a value to the Control Path field in the Panel to use this functionality.")
        else:
            self.report({'ERROR'}, "Assign a value to the Control Path field in the Panel to use this functionality.")
        return {'FINISHED'}

### Operator to save the latest received animation from AnimHost
#   Triggered by a button in the TRACER Animation Path Panel
#   Takes the active action of the selected Character Object, which should be the latest animation received from AnimHost
#   Creates a new NLA Track acting as an animation level and populate it with that action
class AnimationSave(bpy.types.Operator):
    bl_idname = "object.animation_save"
    bl_label = "Save Animation"
    bl_description = "Save the animation currently in the timeline into an NLA Track for its character"

    def execute(self, context: Context):
        character_name: str = bpy.context.scene.tracer_properties.character_name
        if len(character_name) > 0 and character_name in bpy.data.objects and bpy.data.objects[character_name].type == 'ARMATURE' and bpy.data.objects[character_name].animation_data.action != None:
            print("Animation Data Found!")
            # Save Animation on the Character Armature
            bpy.data.objects[character_name].animation_data.use_nla = True
            new_track = bpy.data.objects[character_name].animation_data.nla_tracks.new()
            new_track.select = True
            new_track.name = "AnimHost Output"
            new_track.strips.new(name="AnimHost Output", start=0, action=bpy.data.objects[character_name].animation_data.action)

        control_rig_name: str = bpy.context.scene.tracer_properties.control_rig_name
        if len(control_rig_name) > 0 and control_rig_name in bpy.data.objects and bpy.data.objects[control_rig_name].type == 'ARMATURE':# and bpy.data.objects[control_rig_name].animation_data.action != None:
            # Save Animation on the Control Rig Armature
            bpy.data.objects[control_rig_name].animation_data.use_nla = True
            new_track = bpy.data.objects[control_rig_name].animation_data.nla_tracks.new()
            new_track.select = True
            new_track.name = "AnimHost Output"
            new_track.strips.new(name="AnimHost Output", start=0, action=bpy.data.objects[character_name].animation_data.action)
            bpy.data.objects[control_rig_name].animation_data.action = new_track.strips[-1].action
            bpy.context.view_layer.objects.active = bpy.data.objects[control_rig_name]
            bpy.ops.object.mode_set(mode='POSE')
            bpy.ops.pose.select_all(action='SELECT')
            bpy.ops.nla.bake(frame_start=bpy.context.scene.frame_start, frame_end=bpy.context.scene.frame_end, visual_keying=True, use_current_action=True, only_selected=True, clear_constraints=False, bake_types={'POSE'}, channel_types={"ROTATION", "LOCATION"})
            #action_frames = new_track.strips[-1].action.frame_end - new_track.strips[-1].action.frame_start
            #anim_utils.bake_action(bpy.data.objects[control_rig_name], action=new_track.strips[-1].action, frames=int(action_frames), bake_options=anim_utils.BakeOptions(True, False, True, False, False, False, False, False, False, False, False, False))

        return {'FINISHED'}

### MODAL Operator. It is called every frame by default.
#   It executes specific functions when certain conditions are met:
#   - When DEL or X are pressed (a Control Point could have been deleted), it checks that the Animation Path is up to date. Eventually, it updates it and cleans up the data left over by the deleted point
#   - When Enter or the LMB are relesed (usually indicating that some modification has been confirmed) and Auto Update is enabled, the Path gets updated
#   - When + or shift+= are released while a Control Point Object is selected, add a new point after the selected one
#   - When ctrl+shift++ are released while a Control Point Object is selected, add a new point before the selected one
#   - When the user gets into Edit Mode while selcting a Control Point, trigger the Edit Mode on the corresponding Bezier Point of the spline
#   - When the user is into Edit Mode while selecting the Spline, record the various edits the user makes in order to be applied to later versions of the Control Path 
class InteractionListener(bpy.types.Operator):
    bl_idname = "path.interaction_listener"
    bl_label = "Start Path Operator"
    bl_description = "Listening to Interaction Events on the Animation Path Object and Sub-Objects"

    is_running = False

    def __init__(self):
        print("Start")

    def __del__(self):
        InteractionListener.is_running = False
        print("End")

    def edit_handles(self, context):
        self.layout.operator(EditControlPointHandle.bl_idname, text="Edit Handles", icon='HANDLE_ALIGNED')

    def modal(self, context, event):

        if not bpy.context.scene.tracer_properties.control_path_name in bpy.data.objects:
            return {'PASS_THROUGH'}
        elif self.anim_path == None:
            self.anim_path = bpy.data.objects[bpy.context.scene.tracer_properties.control_path_name]
        
        # If the active mode is *changing to* Object
        if self.mode != 'OBJECT' and context.mode == 'OBJECT':
            # If the active object is the control path, check which Bezier Point was being edited (if one)
            if context.active_object and context.active_object.name == "Control Path":
                active_cp_idx = EditControlPointHandle.last_selected_point_index
                EditControlPointHandle.last_selected_point_index = -1
            else:
                active_cp_idx = -1

            for cp in self.anim_path["Control Points"]:                 # For every Pointer Object
                bpy.context.view_layer.objects.active = cp              # Set it as the Active Object
                bpy.ops.object.mode_set(mode='OBJECT', toggle=False)    # Set its mode to Object
                cp.select_set(False)                                    # Deselect it, so that the operation is transparent to the user
            
            # If one of the Bezier Points of the Control Path was being edited, select the corresponding Control Point Object
            if active_cp_idx >= 0:
                self.anim_path["Control Points"][active_cp_idx].select_set(True)
                bpy.context.view_layer.objects.active = bpy.data.objects[bpy.context.scene.tracer_properties.control_path_name]["Control Points"][active_cp_idx]
        
        # Update the current saved mode
        self.mode = context.mode

        # If the Auto Update property is active, and Enter or the Left Mouse Button are clicked, update the animation curve
        if  (event.type == 'LEFTMOUSE' or event.type == 'RET' or event.type == 'NUMPAD_ENTER') and event.value == 'RELEASE' and \
            (not context.object == None and (context.object.name == bpy.context.scene.tracer_properties.control_path_name or ((not context.object.parent == None) and\
                 context.object.parent.name == bpy.context.scene.tracer_properties.control_path_name))) and \
            bpy.data.objects[self.tracer_props.control_path_name] != None and bpy.data.objects[self.tracer_props.control_path_name]["Auto Update"]:
            update_curve(bpy.data.objects[self.tracer_props.control_path_name])
        
        # If the active object is one of the children of the Control Path, listen to 'Shift + =' or 'Ctrl + +' Release events,
        # this will trigger the addition of a new point to the animation path, right after the currently selected points
        if  (context.active_object in bpy.data.objects[bpy.context.scene.tracer_properties.control_path_name].children) and \
            ((event.type == 'PLUS'and not event.ctrl and not event.shift) or (event.type == 'NUMPAD_PLUS' and event.ctrl and not event.shift) or (event.type == 'EQUAL' and event.shift and not event.ctrl)) and \
            event.value == 'RELEASE':
            bpy.ops.object.add_control_point_after()

        # If the active object is one of the children of the Control Path, listen to 'Ctrl + Shift + =' or 'Ctrl + Shift + +' Release events,
        # this will trigger the addition of a new point to the animation path, right before the currently selected points
        if  (context.active_object in bpy.data.objects[bpy.context.scene.tracer_properties.control_path_name].children) and \
            ((event.type == 'PLUS' and event.ctrl and event.shift) or (event.type == 'NUMPAD_PLUS' and event.ctrl and event.shift) or (event.type == 'EQUAL' and event.shift and event.ctrl)) and \
            event.value == 'RELEASE':
            bpy.ops.object.add_control_point_before()

        # If new_cp_location.w >= 0, it means that there is one point in the Bezier Spline that has been moved (i.e. it has a new location)
        #  - therefore, we need to updater the location of the corresponding Control Point!
        #  - The index of the affected Control Point is "saved" in the w component of new_cp_location, while xyz represent the location vector to be applied to the Control Point
        #  - The update should take place when the editing of the Bezier Point is done (=> context.mode != 'EDIT')
        if context.mode != 'EDIT':
            for i, cp in enumerate(self.anim_path["Control Points"]):
                if i < len(self.new_cp_locations) and self.new_cp_locations[i].w == 1:
                    cp.location = self.new_cp_locations[i].xyz
                    self.new_cp_locations[i].w = 0     # Setting the w to -1 in order to avoid overwriting the location multiple times

        if (context.active_object) and (context.active_object.mode == 'OBJECT') and (context.active_object in self.anim_path["Control Points"]) and bpy.data.objects[bpy.context.scene.tracer_properties.control_path_name]["Auto Update"]:
            # If the User is selecting a Control Point, the Object Menu will also display the possibility of jumping directly into Handles Editing
            #  - removing the entry before adding it (again) avoids duplicates
            bpy.types.VIEW3D_MT_object.remove(InteractionListener.edit_handles) # Checking whether the element is in the menu before removal takes time and does not improve the code operations
            bpy.types.VIEW3D_MT_object.append(InteractionListener.edit_handles)
        else:
            bpy.types.VIEW3D_MT_object.remove(InteractionListener.edit_handles)
            
        if context.active_object and (context.active_object.mode == 'EDIT') and (context.active_object in self.anim_path["Control Points"]):
            # If the User is trying to get into edit mode while selecting a pointer object redirect them to EDIT_CURVE mode while selecting the corresponding Curve Point
            #  - while in EDIT mode, blender will update the Left Handle and Right Handle properties od the Control Point object according to the User interactions with the Control Point
            if not ("Control Path" in bpy.data.objects and self.anim_path["Auto Update"]):
                # If the condition to enter handles edit mode are not met, switch back to object mode and emit warning
                self.report({"ERROR"}, "To edit the tangents of the path, first create one and enable Auto Update")
                bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
            else:
                bpy.ops.curve.edit_control_point_handle()    
            
        if context.active_object and context.active_object.mode == 'EDIT' and context.active_object.name == "Control Path":
            # If the User is editing the Control Path Bezier Spline, save their moifications in the Properties of the various Control Points

            path = context.active_object.data.splines[0]
            self.new_cp_locations = []
            # Get the index of the (first) control point that is currently being edited
            for i in range(len(path.bezier_points)):
                if i >= len(self.new_cp_locations):
                    self.new_cp_locations.append(Vector((0, 0, 0, 0)))

                if  path.bezier_points[i].select_control_point  or\
                    path.bezier_points[i].select_left_handle    or\
                    path.bezier_points[i].select_right_handle:

                    #selected_cp_idx = i

                    selected_curve_cp = path.bezier_points[i]
                    cp_list = bpy.data.objects[bpy.context.scene.tracer_properties.control_path_name]["Control Points"]
                    selected_cp = cp_list[i]

                    selected_cp["Left Handle Type"]  = selected_curve_cp.handle_left_type
                    selected_cp["Right Handle Type"] = selected_curve_cp.handle_right_type
                    selected_cp["Left Handle"]  = Vector(selected_curve_cp.handle_left - selected_curve_cp.co)
                    selected_cp["Right Handle"] = Vector(selected_curve_cp.handle_right - selected_curve_cp.co)

                    self.new_cp_locations[i].xyz = selected_curve_cp.co
                    self.new_cp_locations[i].w = 1

        return {'PASS_THROUGH'}
    
    def invoke(self, context, event):
        if not InteractionListener.is_running:
            # Add the modal listener to the list of called handlers and save the Animation Path object
            context.window_manager.modal_handler_add(self)
            self.tracer_props = bpy.context.scene.tracer_properties
            self.anim_path = None
            self.new_cp_locations = []
            self.mode = 'OBJECT'

            # Check for inconsistency in Panel UI w.r.t. Auto Update property
            if (bpy.context.scene.tracer_properties.control_path_name in bpy.data.objects) and\
                bool(bpy.data.objects[bpy.context.scene.tracer_properties.control_path_name]["Auto Update"]) != bool(ToggleAutoUpdate.bl_label == "Disable Path Auto Update"):

                ToggleAutoUpdate.bl_label = "Disable Path Auto Update" if bpy.data.objects[bpy.context.scene.tracer_properties.control_path_name]["Auto Update"] else "Enable Path Auto Update"
                self.anim_path = bpy.data.objects[bpy.context.scene.tracer_properties.control_path_name]
            InteractionListener.is_running = True
        return {'RUNNING_MODAL'}
    
class SendRpcCall(bpy.types.Operator):
    #TODO mod name dunctionality and txt
    bl_idname = "object.rpc"
    bl_label = "sendRPC"
    bl_description = 'send the call to generate and stream animation to animhost'
    
    def execute(self, context):
        print('rpc bep bop bep bop')
        #TODO add functionality 
        return {'FINISHED'}
       

def reset_tracer_connection():
    close_socket_d()
    close_socket_s()
    close_socket_c()
    close_socket_u()
    clean_up_tracer_data(level=2)