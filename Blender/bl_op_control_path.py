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

import bpy
import blf
from bpy_extras.view3d_utils import location_3d_to_region_2d
import re
import mathutils
from mathutils import Vector, Euler

from bpy.types import Context
from bpy.app.handlers import persistent

from .settings import TracerData, TracerProperties
from .SceneObjects.SceneObjectCharacter import SceneObjectCharacter
from .SceneObjects.SceneObjectPath import SceneObjectPath
from .SceneObjects.AbstractParameter import Parameter, AnimHostRPC
from .Core.ServerAdapter import send_RPC_msg, send_parameter_update
from .Core.SceneManager import SceneManager

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
        report: tuple[set[str], str] = add_path(self.default_name)     # Call the function resposible of creating the animation path - See line 504
        self.report(report[0], report[1])
        bpy.ops.path.interaction_listener("INVOKE_DEFAULT")             # Initialising and starting Interaction Listener modal operator, which handles user interactions on the Control Path
        return {'FINISHED'}

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
            new_point_index = anim_path.get("Control Points").index(context.active_object)  if (context.active_object in anim_path.get("Control Points") \
                                                                                            and anim_path.get("Control Points").index(context.active_object) < len(anim_path.get("Control Points"))-1) \
                        else  -1

            report: tuple[set[str], str] = add_point(anim_path, pos=new_point_index, after=True)    # See line 617
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
            new_point_index = anim_path.get("Control Points").index(context.active_object) if (context.active_object in anim_path.get("Control Points") \
                                                                                       and anim_path.get("Control Points").index(context.active_object) < len(anim_path.get("Control Points"))) \
                        else  0

            report: tuple[set[str], str] = add_point(anim_path, pos=new_point_index, after=False)   # See line 617
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

    def update_position(self, context: bpy.types.Context):
        if bpy.context.tool_settings.use_proportional_edit_objects:
            return
        if self.position >= len(context.active_object.parent.get('Control Points')):
            bpy.context.window.modal_operators[-1].report({'ERROR'}, "Position Value Out of Bounds")
            return
        context.active_object["Position"] = self.position
        move_point(context.active_object, self.position)        # See line 700

    def update_frame(self, context):
        # Set the property of the active control point to the new UI value
        delta_frame = self.frame - context.active_object["Frame"]
        context.active_object["Frame"] = self.frame
        if bpy.context.scene.tracer_properties.slide_frames:
            control_points: list[bpy.types.Object] = bpy.data.objects[bpy.context.scene.tracer_properties.control_path_name]["Control Points"]
            for cp in control_points:
                if control_points.index(cp) > self.position:
                    cp["Frame"] = cp["Frame"] + delta_frame     

    def update_in(self, context):
        # Set the property of the active control point to the new UI value
        context.active_object["Ease In"] = self.ease_in

    def update_out(self, context):
        # Set the property of the active control point to the new UI value
        context.active_object["Ease Out"] = self.ease_out

    def update_style(self, context):
        context.active_object["Style"] = self.style

    position: bpy.props.IntProperty(name="Position", min=0, update=update_position)                                                                                                                                                                                         # type: ignore
    frame: bpy.props.IntProperty(name="Frame", min=0, max=6000, update=update_frame) #set=set_new_frame                                                                                                                                                                                        # type: ignore
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
                    bpy.context.window.modal_operators[-1].report({'ERROR'}, child.name + " IS NOT in the scene")
                    bpy.data.objects.remove(child, do_unlink=True)
            update_curve(anim_path)     # See line 740
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
                    bpy.context.window.modal_operators[-1].report({'ERROR'}, child.name + " IS NOT in the scene")
                    bpy.data.objects.remove(child, do_unlink=True)
                    update_curve(anim_path)     # See line 740
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
                path_points_check(bpy.data.objects[bpy.context.scene.tracer_properties.control_path_name])      # See line 724
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

            update_curve(anim_path)     # See line 740
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
        control_path_name: str = bpy.context.scene.tracer_properties.control_path_name
        if control_path_name != '' and bpy.data.objects[control_path_name] != None:           
            anim_path = bpy.data.objects[control_path_name]
            if EvaluateSpline.anim_preview_obj_name not in bpy.data.objects:
                anim_prev = make_point(spawn_location=anim_path["Control Points"][0].location + Vector((0, 0, 0.5)), name = EvaluateSpline.anim_preview_obj_name)   # See line 568
                bpy.context.scene.collection.objects.link(anim_prev)
            else:
                EvaluateSpline.bl_label = "Update Animation Preview"
                anim_prev = bpy.data.objects[EvaluateSpline.anim_preview_obj_name]
            
            curve_path: SceneObjectPath = bpy.context.window_manager.scene_manager.get_scene_object(anim_path.name) #process_control_path(anim_path)
            context.scene.frame_start = 0
            context.scene.frame_end = (len(curve_path.sampled_points) / 3) - 1
            anim_prev.animation_data_clear()
            for i in range(context.scene.frame_end):
                anim_prev.location          = Vector((curve_path.sampled_points[i*3],  curve_path.sampled_points[i*3+1],  curve_path.sampled_points[i*3+2] + 0.5))
                look_at_vector: Vector      = Vector((curve_path.sampled_look_at[i*3], curve_path.sampled_look_at[i*3+1], curve_path.sampled_look_at[i*3+2]))
                look_at_vector_2d: Vector   = look_at_vector.xy # Rotations are only allowed around the Z-axis (up-axis), so the third component should always be 0. I read it for facilitate debugging
                look_at_angle: float        = look_at_vector_2d.angle_signed(EvaluateSpline.fwd_vector)
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
    #animation_request = Parameter(AnimHostRPC.BLOCK.value, "Request New Animation", None, distribute=False, is_RPC=True)

    tracer_props: TracerProperties = None
    #animation_request.__id = 1

    @classmethod
    def poll(cls, context):
       control_path_name: str = bpy.context.scene.tracer_properties.control_path_name
       return control_path_name != '' and bpy.data.objects[control_path_name] != None

    def execute(self, context: Context):
        if not AnimationRequest.valid_frames:
            self.report({'ERROR'}, "Invalid frame values for the Control Points")
            return {'FINISHED'}
        
        if not context.window_manager.scene_manager.is_distributed:
            self.report({'ERROR'}, "Connect to TRACER before requesting a new animation")
            return {'FINISHED'}
        
        self.tracer_props = bpy.context.scene.tracer_properties

        # TODO: check whether TRACER has been correctly being configured
        control_path_name: str = self.tracer_props.control_path_name
        character_name: str = self.tracer_props.character_name
        if  control_path_name != '' and bpy.data.objects[control_path_name] != None and\
            character_name != '' and bpy.data.objects[character_name] != None:
            character_bl_obj: bpy.types.Object = bpy.data.objects[character_name]
            control_path_bl_obj: bpy.types.Object = bpy.data.objects[control_path_name]
            if control_path_bl_obj != None and control_path_bl_obj.get("Control Points", None) != None:
                scene_manager: SceneManager = bpy.context.window_manager.scene_manager

                # Getting the Scene Character Object corresponding to the selected Blender Character in the Scene
                tracer_character_object: SceneObjectCharacter = scene_manager.get_scene_object(character_name)
                if  tracer_character_object != None:
                    # Ensure that the ID of the Control Path associated with the selected Character is up to date
                    tracer_character_object.update_control_path_id()
                
                tracer_control_path_object: SceneObjectPath = scene_manager.get_scene_object(control_path_name)
                if  tracer_control_path_object != None:
                    # Ensure that the values of the Control Points exposed to TRACER are up to date
                    tracer_control_path_object.update_control_points()
                
                    point_locations_param = tracer_control_path_object.parameter_list[-2]
                    point_rotations_param = tracer_control_path_object.parameter_list[-1]

                    send_parameter_update(point_locations_param)
                    send_parameter_update(point_rotations_param)

                    # [Deprecated - now realying on the ParameterUpdate Message] -> resendCurve()
                    # Request Animation from AnimHost through RPC call
                    match self.tracer_props.animation_request_modes:
                        case 'BLOCK':
                            self.tracer_props.animation_request.value = AnimHostRPC.BLOCK.value
                        case 'STREAM':
                            self.tracer_props.animation_request.value = AnimHostRPC.STREAM.value
                        case 'LOOP':
                            self.tracer_props.animation_request.value = AnimHostRPC.STREAM_LOOP.value
                        case 'STOP':
                            self.tracer_props.animation_request.value = AnimHostRPC.STOP.value
                    send_RPC_msg(self.tracer_props.animation_request)

                    self.tracer_props.mix_root_translation_param.value   = self.tracer_props.mix_root_translation
                    self.tracer_props.mix_root_rotation_param.value      = self.tracer_props.mix_root_rotation
                    self.tracer_props.mix_control_path_param.value       = self.tracer_props.mix_control_path
                    #! To be tested
                    send_RPC_msg(self.tracer_props.mix_root_translation_param)
                    send_RPC_msg(self.tracer_props.mix_root_rotation_param)
                    send_RPC_msg(self.tracer_props.mix_control_path_param)
                
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
    
''' --------------------------------------------------------------------------------------------------------------------
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
++++++++++++++++++++++++++++++++        HELPER FUNCTIONS FOR THE PATH OPERATORS        +++++++++++++++++++++++++++++++++
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
-------------------------------------------------------------------------------------------------------------------- '''

### Constructs and adds to the scene a new Control Path Object, parallely creating data structures that will be used to store information to be sent over TRACER
#   @param      path_name   The name of the Path to be created
#   @returns    report of the status of the execution to be displayed on screen. It is either an INFO when everything goes as planned or an ERROR when the operator cannot be executed as intented.
def add_path(path_name: str) -> tuple[set[str], str]:
    report_type = {'INFO'}
    report_string = "New Control Path added to TRACER Scene"

    if "TRACER_Collection" not in bpy.data.collections or "TRACER Scene Root" not in bpy.data.objects:
        report_type = {'ERROR'}
        report_string = "Set up TRACER hierarchy before creating a new Control Path"
        return (report_type, report_string)

    # Check whether an Animation Preview object is already present in the scene
    if path_name in bpy.data.objects:
        # If yes, save it
        print("Animation Preview object found")
        anim_path = bpy.data.objects[path_name]
    else:
        # If not, create it as an empty object 
        print("Creating new Animation Preview object")
        # Adding a sphere mesh to the data (but deleting the corresponding object in the blender scene)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(0.5, 0.5, 0.5))
        bpy.context.view_layer.objects.active = bpy.data.objects["Sphere"]
        bpy.ops.object.delete(use_global=False, confirm=False)
        # Assigning the sphere mesh to AnimPath (for later interaction with the TRACER framework)
        anim_path = bpy.data.objects.new(path_name, bpy.data.meshes["Sphere"])
        bpy.data.collections["TRACER_Collection"].objects.link(anim_path)  # Add anim_prev to the scene
        anim_path.parent = bpy.data.objects["TRACER Scene Root"]
        bpy.context.scene.tracer_properties.control_path_name = anim_path.name

    if len(anim_path.children) == 0:
        # Create default control point in the origin 
        point_zero = make_point()       # See line 568 - just down below:)
        point_zero.parent = anim_path
        if len(anim_path.users_collection) == 1 and anim_path.users_collection[0].name == "TRACER_Collection":
            anim_path.users_collection[0].objects.link(point_zero)
        else:
            report_type = {'ERROR'}
            report_string ="AnimPath has to be ONLY part of TRACER_Collection"

        anim_path["Control Points"] = [point_zero]                      # Add Control Points property and initialise it with the first "default" point. It will hold the list of all the Control Point Objects that make up the Animation Path
        anim_path["Auto Update"] = False                                # Add Auto Update property. It will hold the "mode status" for the Animation Path. It is used to enable/disable advanced editing features. 

        bpy.context.space_data.overlay.show_relationship_lines = False  # Disabling Relationship Lines to declutter scene view
        anim_path.lock_location[0] = True                                  # Locking rotation/translation of the Animation Path, as it's going to be done with its Control Points
        anim_path.lock_location[1] = True
        anim_path.lock_location[2] = True
        anim_path.lock_rotation[0] = True
        anim_path.lock_rotation[1] = True
        anim_path.lock_rotation[2] = True
        anim_path.lock_scale[0]    = True
        anim_path.lock_scale[1]    = True
        anim_path.lock_scale[2]    = True

    # Set the new path as "Editable" by default
    anim_path["TRACER-Editable"] = True
    # Select and set as active the first point of the Path
    anim_path["Control Points"][0].select_set(True)
    bpy.context.view_layer.objects.active = anim_path["Control Points"][0]
    # Hiding AnimPath mesh since we don't want to see it in blender 
    anim_path.hide_set(True)
    
    return (report_type, report_string)

### Function used to create a new Control Point. It creates the mesh geometry if it's not already present in the scene and adds and initialises the various properties
#   @param  spawn_location  Position in World Space, where the new point will be displayed
#   @returns   Reference of the created Control Point Object  
def make_point(spawn_location = (0, 0, 0), name = "Pointer"):
    # Generate new planar isosceles triangle mesh called ptr_mesh
    vertices = [(-0.0625, 0, -0.0625), (0.0625, 0, 0.0625), (0, -0.25, 0), (0.0625, 0, -0.0625), (-0.0625, 0, 0.0625)]
    edges = []
    faces = [[4, 1, 2], [0, 3, 2], [0, 4, 2], [1, 3, 2], [4, 0, 1], [1, 0, 3]]

    # Check whether a mesh called "Pointer" is already present in the blender data
    if "Pointer" in bpy.data.meshes:
        # If yes, retrieve such mesh and modify its vertices to create an isosceles triangle
        ptr_mesh = bpy.data.meshes["Pointer"]
    else:
        # If not, create a new mesh with the geometry data defined above
        ptr_mesh = bpy.data.meshes.new("Pointer")
        ptr_mesh.from_pydata(vertices, edges, faces)
        ptr_mesh.validate(verbose = True)
        ptr_mesh.uv_layers.new()

    # Create new object ptr_obj (with UI name "Pointer") that has ptr_mesh as a mesh
    ptr_obj = bpy.data.objects.new(name, ptr_mesh)
    ptr_obj.location = spawn_location                           # Placing ptr_obj at a specified location (when not specified, the default is origin)

    # Lock Z-axis location and XY-axes rotation
    ptr_obj.lock_location[2] = True
    ptr_obj.lock_rotation[0] = True
    ptr_obj.lock_rotation[1] = True
    
    # Adding custom property "Frame" and "Style Label"
    ptr_obj["Frame"] = 0
    ptr_obj["Ease In"] = 0
    ptr_obj["Ease Out"] = 0
    #! Style is not currently used by the framework
    # ptr_obj["Style"] = "Walking"
    ptr_obj["Left Handle Type"]  = "AUTO"
    ptr_obj["Right Handle Type"] = "AUTO"
    ptr_obj["Left Handle"]  = mathutils.Vector()
    ptr_obj["Right Handle"] = mathutils.Vector()

    # Customise shading option to highlight
    bpy.context.space_data.shading.wireframe_color_type = 'OBJECT'
    bpy.context.space_data.shading.color_type = 'OBJECT'
    ptr_obj.color = (0.9, 0.1, 0, 1)    # Setting object displaying colour (not material!)
    ptr_obj.show_wire = True
    
    return ptr_obj

### Function that adds a new point to the Animation Path
#   @param  anim_path   Reference to the Animation Path to which the point has to be added
#   @param  pos         Position in which to the new point should be inserted (default -1, i.e. at the endof the list) 
#   @param  after       Whether the point is being added before or after the selected point (only important to compute the correct offset)
def add_point(anim_path, pos=-1, after=True):
    report_type = {'INFO'}
    report_string = "New Control Point added to TRACER Scene"
    spawn_offset = mathutils.Vector((0, -bpy.context.scene.tracer_properties.new_control_point_pos_offset, 0))

    # Calculate offset proportionally to the dimensions of the mesh of the pointer (Control Point) object and in relation to the rotation of the PREVIOUS control point
    base_rotation = anim_path["Control Points"][pos].rotation_euler
    spawn_offset = spawn_offset if after else spawn_offset * -1  # flipping the offset so that the point gets spawned behind the selected one (if after == False)
    spawn_offset.rotate(base_rotation)
    # Create new point, place it next to the CURRENTLY SELECTED point, and select it
    new_point = make_point(anim_path["Control Points"][pos].location + spawn_offset)    # See line 568 - just here above :)
    new_point.rotation_euler = base_rotation    # Rotate the pointer so that it aligns with the previous one
    new_point.parent = anim_path                # Parent it to the selected (for now the only) path
    if len(anim_path.users_collection) == 1 and anim_path.users_collection[0].name == "TRACER_Collection":
        anim_path.users_collection[0].objects.link(new_point)
    else:
        report_type = {'ERROR'}
        report_string = "AnimPath has to ONLY be part of TRACER_Collection"

    if len(anim_path["Control Points"]) > 0:
        # If Control Path is already populated
        # Set Frame Value
        frame_offset = bpy.context.scene.tracer_properties.new_control_point_frame_offset
        if pos >= 0 and after:
            new_frame_value = anim_path["Control Points"][pos]['Frame'] + frame_offset
            new_point['Frame'] = new_frame_value
        elif pos >= 0 and not after:
            new_frame_value = anim_path["Control Points"][pos]['Frame'] - frame_offset
            new_point['Frame'] = new_frame_value if new_frame_value >= 0 else 0
        elif pos == -1 and after:
            cp = anim_path["Control Points"][-1]
            new_frame_value = anim_path["Control Points"][-1]['Frame'] + frame_offset
            new_point['Frame'] = new_frame_value
        else:
            new_point['Frame'] = 0

        # Append it to the list of Control Points of that path
        control_points = anim_path["Control Points"]
        control_points.append(new_point)
        anim_path["Control Points"] = control_points
            
        # If the position is not -1 (i.e. end of list), move the point to the correct position
        if pos >= 0:
            # If inserting AFTER the current point, move to the next position (pos+1), otherwise inserting at the position of the current point, which will be moved forward as a result  
            move_point(new_point, pos+1) if after else move_point(new_point, pos)   # See line 700 - just a bit below :)
    else:
        # If Control Points has no elements, delete the property and create it ex-novo
        del anim_path["Control Points"]
        anim_path["Control Points"] = [new_point]

    for area in bpy.context.screen.areas:
        if area.type == 'PROPERTIES':
            area.tag_redraw()

    # Deselect all selected objects
    for obj in bpy.context.selected_objects:
        obj.select_set(False)

    # Trigger Path Updating
    update_curve(anim_path)     # See line 740 - just a bit below :)

    # Select and set as active the new point
    new_point.select_set(True)
    bpy.context.view_layer.objects.active = new_point

    return (report_type, report_string)

### Function that builds the name of a Control Point object given the position that it should take up in the Control Path
def get_pos_name(pos):
    suffix = ""
    if pos < 0:
        return
    elif pos == 0:
        suffix = ""
    elif pos < 10:
        suffix = (".00" + str(pos))
    elif pos < 100:
        suffix = (".0" + str(pos))
    elif pos < 1000:
        suffix = ("." + str(pos))
    return "Pointer" + suffix

### Function to move a Control Point in the Control Path, given the point to move and the position it should take up
def move_point(point, new_pos):
    # Get the current position of the active object
    point_pos = point.parent["Control Points"].index(point)
    if new_pos == point_pos:
        # Just do a simple pass removing potential gaps in the numbering (useful after deletions)
        for i in range(len(point.parent["Control Points"])):
            point.parent["Control Points"][i].name = get_pos_name(i)    # See line 685 - just above :)
    if new_pos <  point_pos:
        # Move the elements after the new position forward by one and insert the active object at new_pos
        for i in range(new_pos, point_pos+1):
            if (i+1) < len(point.parent["Control Points"]):
                point.parent["Control Points"][i+1].name = "tmp"
            point.parent["Control Points"][i].name = get_pos_name(i+1)  # See line 685 - just above :)
        point.name = get_pos_name(new_pos)
    if new_pos  > point_pos:
        # Move the elements before the new position backward by one and insert the active object at new_pos
        point.name = "tmp"
        for i in range(point_pos+1, new_pos+1):
            point.parent["Control Points"][i].name = get_pos_name(i-1)  # See line 685 - just above :)
        point.name = get_pos_name(new_pos)
    # Evaluate the curve, given the new ordrering of the Control Points
    update_curve(point.parent)      # See line 740 - right below :)

### Update the list of Control Points given the current scene status, and remove the Control Path, which is going to be updated
def path_points_check(anim_path):
    # Check the children of the Animation Preview (or corresponding character)
    control_points = []
    cp_names = []   # Helper list containing the names of the control points left in the scene
    for child in anim_path.children:
        if re.search(r'Control Path', child.name):
            bpy.data.objects.remove(child, do_unlink=True)
        elif not child.name in bpy.context.view_layer.objects:
            bpy.data.objects.remove(child, do_unlink=True)
        else:
            control_points.append(child)
            cp_names.append(child.name)
    
    anim_path["Control Points"] = control_points

### Update Curve takes care of updating the AnimPath representation according to the modifications made by the user using the blender UI
def update_curve(anim_path: bpy.types.Object):
    # Deselect all selected objects
    for obj in bpy.context.selected_objects:
        obj.select_set(False)

    path_points_check(anim_path)        # See line 724 - right above this function :)

    # Create Control Path from control_points elements
    bezier_curve_obj = bpy.data.curves.new('Control Path', type='CURVE')                                    # Create new Curve Object with name Control Path
    bezier_curve_obj.dimensions = '2D'                                                                      # The Curve Object is a 2D curve

    bezier_spline = bezier_curve_obj.splines.new('BEZIER')                                                  # Create new Bezier Spline "Mesh"
    bezier_spline.bezier_points.add(len(anim_path.get("Control Points"))-1)                                 # Add points to the Spline to match the length of the control_points list
    for i, cp in enumerate(anim_path.get("Control Points")):
        cp: bpy.types.Object = cp
        bezier_point = bezier_spline.bezier_points[i] 
        bezier_point.co = cp.location                                                                       # Assign the poistion of the elements in the list of Control Points to the Bézier Points
        bezier_point.handle_left_type  = cp.get("Left Handle Type")                                         # Use the handle data from the list of Control Points for the Bézier Points,
        if cp.get("Left Handle Type") != "AUTO":
            bezier_point.handle_left = mathutils.Vector(cp.get("Left Handle").to_list()) + cp.location      # if the handle type is not 'AUTO', any user-made change is saved and applied
        bezier_point.handle_right_type = cp.get("Right Handle Type")
        if cp.get("Right Handle Type") != "AUTO":                                                           # do the same for both handles:)
            bezier_point.handle_right = mathutils.Vector(cp.get("Right Handle").to_list()) + cp.location

    # Deleting old Curve completely form Blender
    if anim_path.children[0].name == "Control Path":
        old_path: bpy.types.Object = anim_path.children[0]
        old_path.select_set(True)
        bpy.ops.object.delete()

    control_path = bpy.data.objects.new('Control Path', bezier_curve_obj)                                   # Create a new Control Path Object with the geometry data of the Bézier Curve
    if len(anim_path.users_collection) == 1 and anim_path.users_collection[0].name == "TRACER_Collection":
        anim_path.users_collection[0].objects.link(control_path)                                            # Add the Control Path Object in the scene
    control_path.parent = anim_path                                                                         # Make the Control Path a child of the Animation preview Object
    control_path.lock_location[2] = True                                                                    # Locking Z-component of the Control Path, as it's going to be done with its Control Points

    for area in bpy.context.screen.areas:
        if area.type == 'PROPERTIES':
            area.tag_redraw()

### Function for drawing number labels next to the control points
#   This callback is registered in the __init__.py script and will be called every frame (post pixel reder) 
def draw_pointer_numbers_callback(font_id, font_handler):
    # BLF drawing routine
    anchor_3d_pos = mathutils.Vector((0,0,0))
    if "AnimPath" in bpy.context.scene.objects:
        anim_path = bpy.context.scene.objects["AnimPath"]
        # for every control point of the animation path
        for i in range(len(anim_path["Control Points"])):
            cp = anim_path["Control Points"][i]
            # cp_props = anim_path["Control Points Properties"][i]
            # If the Control Point is not hidden in the viewport
            if not (cp == None or cp.hide_get()):
                # Getting 3D position of the control point (taking in account a 3D offset, so that the label can follow the mesh orientation)
                offset_3d = mathutils.Vector((-0.1, 0, 0.1))
                offset_3d.rotate(cp.rotation_euler)
                anchor_3d_pos = cp.location + offset_3d + anim_path.location
                # Getting the corresponding 2D viewport location of the 3D location of the control point
                txt_coords: mathutils.Vector = location_3d_to_region_2d(bpy.context.region,
                                                                        bpy.context.space_data.region_3d,
                                                                        anchor_3d_pos)

                if txt_coords != None:
                    # Setting text position, size, colour (white)
                    blf.position(font_id,
                                 txt_coords.x,
                                 txt_coords.y,
                                 0)
                    blf.size(font_id, 30.0)
                    blf.color(font_id, 1, 1, 1, 1)
                    # Writing text (the number relative to the position of the pointer in the list of control points in the path)
                    blf.draw(font_id, str(i))