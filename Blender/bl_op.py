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
import re

from bpy.types import Context
from .serverAdapter import set_up_thread, close_socket_d, close_socket_s, close_socket_c, close_socket_u
from .tools import cleanUp, installZmq, checkZMQ, setupCollections, parent_to_root, add_path, add_point, move_point, eval_curve, path_points_check
from .sceneDistribution import gatherSceneData, resendCurve
from .GenerateSkeletonObj import process_armature


## operator classes
#
class SetupScene(bpy.types.Operator):
    bl_idname = "object.setup_vpet"
    bl_label = "VPET Scene Setup"
    bl_description = 'Create Collections for static and editable objects'

    def execute(self, context):
        print('setup scene')
        setupCollections()
        return {'FINISHED'}


class DoDistribute(bpy.types.Operator):
    bl_idname = "object.zmq_distribute"
    bl_label = "VPET Do Distribute"
    bl_description = 'Distribute the scene to VPET clients'

    def execute(self, context):
        for obj in bpy.context.selected_objects:
            obj.select_set(False)
        print("do distribute")
        if checkZMQ():
            reset()
            objCount = gatherSceneData() # TODO: is it possible to move the scene initialization (gatherSceneData()) outside of the DoDistribute function? A good place could be in the SetupScene function
            bpy.ops.wm.real_time_updater('INVOKE_DEFAULT')
            bpy.ops.object.single_select('INVOKE_DEFAULT')
            cleanUp(level=1)
            if objCount > 0:
                set_up_thread()
                self.report({'INFO'}, f'Sending {str(objCount)} Objects to VPET')
            else:
                self.report({'ERROR'}, 'VPET collections not found or empty')
        else:
            self.report({'ERROR'}, 'Please Install Zero MQ before continuing')
        
        return {'FINISHED'}

class StopDistribute(bpy.types.Operator):
    bl_idname = "object.zmq_stopdistribute"
    bl_label = "VPET Stop Distribute"
    bl_description = 'Stop the distribution and free the sockets. Important!'

    def execute(self, context):
        print('stop distribute')
        print('stop subscription')
        self.report({'INFO'}, f'STOP SENDING Objects to VPET')
        reset()
        return {'FINISHED'}

class InstallZMQ(bpy.types.Operator):
    bl_idname = "object.zmq_install"
    bl_label = "Install ZMQ"
    bl_description = 'Install Zero MQ. You need admin rights for this to work!'

    def execute(self, context):
        print('Installing ZMQ')
        zmq_result = installZmq()
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
    bl_label = "VPET Character Setup"
    bl_description = 'generate obj for each Character bone'

    def execute(self, context):
        print('Setup Character')
        selected_objects = bpy.context.selected_objects
        for obj in selected_objects:
            if obj.type == 'ARMATURE':
                process_armature(obj)
                print 
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
            obj["VPET-Editable"] = True
        return{'FINISHED'}
    
class ParentToRoot(bpy.types.Operator):
    bl_idname = "object.parent_to_root"
    bl_label = "Parent obj to root obj"
    bl_description = 'Parent all the selectet object to the TRACER root obj'

    def execute(self, context):
        print('Parent obj')
        parent_to_root()
        return {'FINISHED'}
   
# Operator to add a new Animation Path
# The execution is triggered by a button in the VPET Panel or by an entry in the Add Menu
class AddPath(bpy.types.Operator):
    bl_idname = "object.add_path"
    bl_label = "Add Control Path"
    bl_description = 'Create an Object to act as a Control Path for a locomotion animation. The character will be animated by AnimHost to follow such path'
    bl_options = {'REGISTER', 'UNDO'}

    default_name = "AnimPath"

    def execute(self, context):
        self.total_frames = 180
        #TODO: eventually bind the path to a character in the scene
        # if(context.active_object == "ARMATURE"):
        #     print('Add Path START')
        #     add_path(context.active_object)
        #     #resendCurve()
        # else:
        #     print("Select a Character Object to execute this functionality")
        print('Add Path START')
        add_path(context.active_object, self.default_name)      # Call the function resposible of creating the animation path
        bpy.ops.path.interaction_listener('INVOKE_DEFAULT')     # Invoke Modal Operaton for automatically update the Animation Path in (almost) real-time
        return {'FINISHED'}

# Operator to add a new Animation Control Point
# The execution is triggered by a button in the VPET Panel or by an entry in the Add Menu
class AddPointAfter(bpy.types.Operator):
    bl_idname = "object.add_control_point_after"
    bl_label = "Create a new Control Point after the selected"
    bl_description = 'Add a new Control Point to the (selected) Animation Path after the one currently selected'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        #TODO: eventually make it contextual to the selection of a specific path
        # if(context.active_object == "ARMATURE"):
        #     print('Add Path START')
        #     add_path(context.active_object)
        #     #resendCurve()
        # else:
        #     print("Select a Character Object to execute this functionality")
        print('Add Point START')
        anim_path = bpy.data.objects[AddPath.default_name]
        new_point_index = anim_path["Control Points"].index(context.active_object)  if (context.active_object in anim_path["Control Points"] \
                                                                                        and anim_path["Control Points"].index(context.active_object) < len(anim_path["Control Points"])-1) \
                    else  -1

        add_point(anim_path, pos=new_point_index, after=True)
        return {'FINISHED'}
    
# Operator to add a new Animation Control Point
# The execution is triggered by a button in the VPET Panel or by an entry in the Add Menu
class AddPointBefore(bpy.types.Operator):
    bl_idname = "object.add_control_point_before"
    bl_label = "Create a new Control Point before the selected"
    bl_description = 'Add a new Control Point to the (selected) Animation Path before the one currently selected'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        #TODO: eventually make it contextual to the selection of a specific path
        # if(context.active_object == "ARMATURE"):
        #     print('Add Path START')
        #     add_path(context.active_object)
        #     #resendCurve()
        # else:
        #     print("Select a Character Object to execute this functionality")
        print('Add Point START')
        anim_path = bpy.data.objects[AddPath.default_name]
        new_point_index = anim_path["Control Points"].index(context.active_object) if (context.active_object in anim_path["Control Points"] \
                                                                                   and anim_path["Control Points"].index(context.active_object) < len(anim_path["Control Points"])) \
                    else  0

        add_point(anim_path, pos=new_point_index, after=False)
        return {'FINISHED'}
    
# Operator to manage the Properties of the Animation Control Points
class ControlPointProps(bpy.types.PropertyGroup):
    bl_idname = "path.control_point_props"
    bl_label = "Confirm Changes"
    #bl_options = {'REGISTER', 'UNDO'}

    def get_items():
        items = [("Walking", "Walking", "Walking Locomotion Style"),
                 ("Running", "Running", "Running Locomotion Style"),
                 ("Jumping", "Jumping", "Jumping Locomotion Style")]
        return items
    
    def update_property_ui(scene):
        if not bpy.context.active_object == None:
            active_obj = bpy.context.active_object
        else:
            return
        
        # If a Path has been created in the scene and the selected object is a Control Point
        if (not bpy.data.objects[AddPath.default_name] == None) and (re.search(r'Pointer', active_obj.name)):
            scene.control_point_settings.position = active_obj.parent["Control Points"].index(active_obj)
            scene.control_point_settings.frame = active_obj["Frame"]
            scene.control_point_settings.ease_in = active_obj["Ease In"]
            scene.control_point_settings.ease_out = active_obj["Ease Out"]
            scene.control_point_settings.style = active_obj["Style"]
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
        # TODO: update also following points keeping a constant delta to the previous ones
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

    position: bpy.props.IntProperty(name="Position", min=0, update=update_position)
    frame: bpy.props.IntProperty(name="Frame", min=0, max=6000, update=update_frame)
    ease_in: bpy.props.IntProperty(name="Ease In", min=0, max=100, update=update_in)
    ease_out: bpy.props.IntProperty(name="Ease Out", min=0, max=100, update=update_out)
    style: bpy.props.EnumProperty(items=get_items(), name="Style", description="Choose a Locomotion Style", default="Running", update=update_style)

    # def execute(self, context):
    #     print("Setting Control Point Properties")
    #     return {'FINISHED'}

# Operator to add a new Animation Path
# The execution is triggered by a button in the VPET Panel or by an entry in the Add Menu
class EvalCurve(bpy.types.Operator):
    bl_idname = "object.eval_curve"
    bl_label = "Re-evaluate the curve"
    bl_description = 'Recalculate the Control Path given the new configuration of the Control Points'

    def execute(self, context):
        print('Evaluate Curve START')
        anim_path = bpy.data.objects[AddPath.default_name]
        # Check for deleted control points and evtl. do some cleanup before updating the curve 
        for child in anim_path.children:
            if not bpy.context.scene in child.users_scene:
                print(child.name + " IS NOT in the scene")
                bpy.data.objects.remove(child, do_unlink=True)
        eval_curve(anim_path)
        
        for area in bpy.context.screen.areas:
            if area.type == 'PROPERTIES':
                area.tag_redraw()
        
        return {'FINISHED'}
    
    def on_delete_update_handler(scene):
        anim_path = bpy.data.objects[AddPath.default_name]
        if anim_path["Auto Update"]:
            # Check for deleted control points and evtl. do some cleanup before updating the curve  
            for i, child in enumerate(anim_path.children):
                if not bpy.context.scene in child.users_scene:
                    print(child.name + " IS NOT in the scene")
                    bpy.data.objects.remove(child, do_unlink=True)
                    eval_curve(anim_path)
                    if i < len(anim_path["Control Points"]) - 1:
                        # If the removed element was not the last point in the list
                        # Select the element that is now in that position
                        anim_path["Control Points"][i].select_set(True)
                    else:
                        # Select the new last element
                        anim_path["Control Points"][-1].select_set(True)
                    # Call move_point function to update the names of the points left in the list
                    move_point(anim_path["Control Points"][0], 0)
            
            for area in bpy.context.screen.areas:
                if area.type == 'PROPERTIES':
                    area.tag_redraw()
    
class ToggleAutoEval(bpy.types.Operator):
    bl_idname = "object.toggle_auto_eval"
    bl_label = "Enable Path Auto Update"
    bl_description = 'Enable/Disable the automatic re-calculation of the path'

    def execute(self, context):
        # If the toggling should happen only when the path is selected, add also the following condition -> and bpy.data.objects[AddPath.default_name].select_get()
        if (AddPath.default_name in bpy.data.objects):
            anim_path = bpy.data.objects[AddPath.default_name]
            anim_path["Auto Update"] = not anim_path["Auto Update"]
            bpy.context.tool_settings.use_proportional_edit_objects = not anim_path["Auto Update"]
            bpy.context.tool_settings.use_proportional_edit = not anim_path["Auto Update"]
            # Forcing update visualisation of Property Panel
            for area in bpy.context.screen.areas:
                if area.type == 'PROPERTIES':
                    area.tag_redraw()

            if (not anim_path["Auto Update"]) or bpy.context.tool_settings.use_proportional_edit_objects:
                ToggleAutoEval.bl_label = "Enable Path Auto Update"
            else:
                ToggleAutoEval.bl_label = "Disable Path Auto Update"

        return {'FINISHED'}
    
class ControlPointSelect(bpy.types.Operator):
    bl_idname = "object.control_point_select"
    bl_label = ""
    bl_description = 'Allows selecting a Control Point from a Panel in the VPET UI'

    cp_name: bpy.props.StringProperty()

    def execute(self, context):
        for obj in bpy.data.objects:
            obj.select_set(False)

        if not self.cp_name in context.view_layer.objects:
            bpy.data.objects.remove(bpy.data.objects[self.cp_name], do_unlink=True)
            path_points_check(bpy.data.objects["AnimPath"])
        else:
            bpy.data.objects[self.cp_name].select_set(True)
            #print("Click " + self.cp_name + " " + str(bpy.data.objects[self.cp_name].select_get()))
            bpy.context.view_layer.objects.active = bpy.data.objects[self.cp_name]

        return {'FINISHED'}
    
class InteractionListener(bpy.types.Operator):
    bl_idname = "path.interaction_listener"
    bl_label = "Interaction Listener"
    bl_description = "Listening to Interaction Events on the Animation Path Object and Sub-Objects"

    def __init__(self):
        print("Start")

    def __del__(self):
        print("End")

    def modal(self, context, event):
        if (event.type == 'DEL' or event.type == 'X') and event.value == 'RELEASE':
            if AddPath.default_name in bpy.data.objects:
                if self.anim_path["Auto Update"]:
                    eval_curve(self.anim_path)
                else:
                    path_points_check(self.anim_path)
            else:
                return {'FINISHED'}

        # If the Auto Update property is active, and Enter or the Left Mouse Button are clicked, update the animation curve
        if  (event.type == 'LEFTMOUSE' or event.type == 'RET' or event.type == 'NUMPAD_ENTER') and event.value == 'RELEASE' and \
            (not context.object == None and (context.object.name == AddPath.default_name or ((not context.object.parent == None) and  context.object.parent.name == AddPath.default_name))) and \
            (not self.anim_path == None) and self.anim_path["Auto Update"]:
            eval_curve(self.anim_path)
        
        # If the active object is one of the children of AnimPath, listen to 'Shift + =' or 'Ctrl + +' Release events,
        # this will trigger the addition of a new point to the animation path, right after the currently selected points
        if  (context.active_object in bpy.data.objects[AddPath.default_name].children) and \
            ((event.type == 'PLUS'and not event.ctrl and not event.shift) or (event.type == 'NUMPAD_PLUS' and event.ctrl and not event.shift) or (event.type == 'EQUAL' and event.shift and not event.ctrl)) and \
            event.value == 'RELEASE':
            # new_point_index = self.anim_path["Control Points"].index(context.active_object) + 1
            # print("Insert new point at: " + str(new_point_index))
            # add_point(self.anim_path, pos=new_point_index, after=True)
            bpy.ops.object.add_control_point_after()

        # If the active object is one of the children of AnimPath, listen to 'Ctrl + Shift + =' or 'Ctrl + Shift + +' Release events,
        # this will trigger the addition of a new point to the animation path, right before the currently selected points
        if  (context.active_object in bpy.data.objects[AddPath.default_name].children) and \
            ((event.type == 'PLUS' and event.ctrl and event.shift) or (event.type == 'NUMPAD_PLUS' and event.ctrl and event.shift) or (event.type == 'EQUAL' and event.shift and event.ctrl)) and \
            event.value == 'RELEASE':
            # new_point_index = self.anim_path["Control Points"].index(context.active_object) + 1
            # print("Insert new point at: " + str(new_point_index))
            # add_point(self.anim_path, pos=new_point_index, after=False)
            bpy.ops.object.add_control_point_before()

        # If the User is trying to get into edit mode while selecting a pointer object redirect them to EDIT_CURVE mode while selecting the corresponding Curve Point
        if context.mode == 'EDIT_OBJECT' and context.active_object.parent == self.anim_path:
            pointer_idx = self.anim_path["Control Points"].index(context.active_object)

        return {'PASS_THROUGH'}
    
    def invoke(self, context, event):
        # Add the modal listener to the list of called handlers and save the Animation Path object
        context.window_manager.modal_handler_add(self)
        self.anim_path = bpy.data.objects[AddPath.default_name]
        self.path_changed = False
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
       

def reset():
    close_socket_d()
    close_socket_s()
    close_socket_c()
    close_socket_u()
    cleanUp(level=2)