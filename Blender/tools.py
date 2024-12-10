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
import sys
import re
import mathutils
import blf
import bpy_extras.view3d_utils
import subprocess  # use Python executable (for pip usage)
from pathlib import Path  # Object-oriented filesystem paths since Python 3.4
from .SceneObjects import SceneCharacterObject

# Checking for ZMQ package installation
def check_ZMQ():
    try:
        import zmq
        return True
    except Exception as e:
        print(e)
        return False

#???  
def get_rna_ui():
    rna_ui = bpy.context.object.get('_RNA_UI')
    if rna_ui is None:
        bpy.context.object['_RNA_UI'] = {}
        rna_ui = bpy.context.object['_RNA_UI']
    return rna_ui
    
## Create Collections that will contain every TRACER object
def setup_tracer_collection():
    tracer_props = bpy.context.scene.tracer_properties

    current_mode = ''
    if bpy.context.active_object:
        # Get current mode
        current_mode = str(bpy.context.active_object.mode)
        if current_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode = 'OBJECT', toggle=True)    # Force OBJECT mode
    
    # Check if the collection exists. If not, create it and link it to the scene.
    tracer_collection = bpy.data.collections.get(tracer_props.tracer_collection)
    if tracer_collection is None:
        tracer_collection = bpy.data.collections.new(tracer_props.tracer_collection)
        bpy.context.scene.collection.children.link(tracer_collection)

    # Check if the "TRACER Scene Root" object already exists. If not, create it and link it to the collection.
    root = bpy.context.scene.objects.get('TRACER Scene Root')
    if root is None:
        bpy.ops.object.empty_add(type='PLAIN_AXES', rotation=(0,0,0), location=(0, 0, 0), scale=(1, 1, 1))
        bpy.context.active_object.name = 'TRACER Scene Root'
        root = bpy.context.active_object
        if root.name not in bpy.context.scene.collection.objects:
            bpy.context.scene.collection.objects.link(root)
        # Unlinking object from ALL collections
        for coll in bpy.data.collections:
            if root.name in coll.objects:
                coll.objects.unlink(root)
        
        tracer_collection.objects.link(root)
        if root.name in bpy.context.scene.collection.objects:
            bpy.context.scene.collection.objects.unlink(root)
    else:
        # Check if the "TRACER Scene Root" object is already linked to the collection. If not link it.
        if not root.name in tracer_collection.objects:
            tracer_collection.objects.link(root)
    
    if current_mode != '' and current_mode != 'OBJECT':
        bpy.ops.object.mode_set(mode = 'OBJECT', toggle=True)    # Revert mode to previous one

# Clearing all the data structures containg TRACER-Related data
def clean_up_tracer_data(level):
    tracer_data = bpy.context.window_manager.tracer_data
    if level > 0:
        tracer_data.objectsToTransfer = [] #list of all objects
        tracer_data.nodeList = [] #list of all nodes
        tracer_data.geoList = [] #list of geometry data
        tracer_data.materialList = [] # list of materials
        tracer_data.textureList = [] #list of textures

    if level > 1:
        tracer_data.editableList = []
        tracer_data.headerByteData = bytearray([]) # header data as bytes
        tracer_data.nodesByteData = bytearray([]) # nodes data as bytes
        tracer_data.geoByteData = bytearray([]) # geo data as bytes
        tracer_data.texturesByteData = bytearray([]) # texture data as bytes
        tracer_data.materialsByteData = bytearray([]) # materials data as bytes
        tracer_data.pingByteMSG = bytearray([]) # ping msg as bytes
        ParameterUpdateMSG = bytearray([])# Parameter update msg as bytes

        tracer_data.rootChildCount = 0

# Installing ZMQ package for python
def install_ZMQ():
    if check_ZMQ():
        return 'ZMQ is already installed'
    else:
        if bpy.app.version[0] == 2 and bpy.app.version[1] < 81:
            return 'This only works with Blender versions > 2.81'

        else:
            try:
                # will likely fail the first time, but works after `ensurepip.bootstrap()` has been called once
                import pip
            except ModuleNotFoundError as e:
                # only first attempt will reach here
                print("Pip import failed with: ", e)
                print("ERROR: Pip not activated, trying bootstrap()")
                try:
                    import ensurepip
                    ensurepip.bootstrap()
                except:  # catch *all* exceptions
                    e = sys.exc_info()[0]
                    print("ERROR: Pip not activated, trying bootstrap()")
                    print("bootstrap failed with: ", e)
            py_exec = sys.executable

        # pyzmq pip install
        try:
            print("Trying pyzmq install")
            output = subprocess.check_output([py_exec, '-m', 'pip', 'install', '--ignore-installed', 'pyzmq'])
            print(output)
            if (str(output).find('not writeable') > -1):
                return 'admin error'
            else:
                return 'success'
        except subprocess.CalledProcessError as e:
            print("ERROR: Couldn't install pyzmq.")
            return (e.output)

# Selecting the hierarchy of all the objects seen by TRACER  
def select_hierarchy(obj):
    # Deselect all objects first
    bpy.ops.object.select_all(action='DESELECT')

    # If obj is a single object
    if isinstance(obj, bpy.types.Object):
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        for child in obj.children_recursive:
            child.select_set(True)
            
    # If obj is a list of objects
    elif isinstance(obj, list[bpy.types.Object]):
        for o in obj:
            o.select_set(True)
            for child in o.children_recursive:
                child.select_set(True)
    else:
        print("Invalid object type provided.")

# Getting the names of the collections to which the passed obj belongs
def get_current_collections(obj: bpy.types.Object) -> list[str]:
    current_collections = []
    for coll in obj.users_collection:
        current_collections.append(coll.name)
    return current_collections
    
# Makes the TRACER Scene Root object the parent of every currently selected object
def parent_to_root(objs: list[bpy.types.Object]) -> tuple[set[str], str]:
    parent_object_name = "TRACER Scene Root"
    parent_object: bpy.types.Object = bpy.data.objects.get(parent_object_name)
    collection: bpy.types.Collection = bpy.data.collections.get(bpy.context.scene.tracer_properties.tracer_collection)

    if parent_object is None or collection is None:
        report_type = {'ERROR'}
        report_string = "Set up the TRACER Scene components first"
        return (report_type, report_string)

    for obj in objs:
        # Check if the object is not the parent object itself
        if obj != parent_object:
            # Set the parent of the selected object to the parent object
            obj.parent = parent_object
            obj.matrix_parent_inverse = parent_object.matrix_world.inverted()
            for coll in obj.users_collection:
                coll.objects.unlink(obj)
            # Link the object to the new collection
            collection.objects.link(obj)
            switch_collection(obj.children_recursive)

def switch_collection(objs: list[bpy.types.Object]) -> tuple[set[str], str]:
    collection_name = bpy.context.scene.tracer_properties.tracer_collection  # Specify the collection name
    collection = bpy.data.collections.get(collection_name)
    if collection is None:
        report_type = {'ERROR'}
        report_string = "Set up the TRACER Scene components first"
        return (report_type, report_string)
                    
    for obj in objs:
        for coll in obj.users_collection:
            coll.objects.unlink(obj)

        # Link the object to the new collection
        collection.objects.link(obj)

'''
----------------------BEGIN FUNCTIONS RELATED TO THE CONTROL PATH-------------------------------
'''
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
        point_zero = make_point()
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
    new_point = make_point(anim_path["Control Points"][pos].location + spawn_offset)
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
            move_point(new_point, pos+1) if after else move_point(new_point, pos)
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
    update_curve(anim_path)

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
            point.parent["Control Points"][i].name = get_pos_name(i)
    if new_pos <  point_pos:
        # Move the elements after the new position forward by one and insert the active object at new_pos
        for i in range(new_pos, point_pos+1):
            if (i+1) < len(point.parent["Control Points"]):
                point.parent["Control Points"][i+1].name = "tmp"
            point.parent["Control Points"][i].name = get_pos_name(i+1)
        point.name = get_pos_name(new_pos)
    if new_pos  > point_pos:
        # Move the elements before the new position backward by one and insert the active object at new_pos
        point.name = "tmp"
        for i in range(point_pos+1, new_pos+1):
            point.parent["Control Points"][i].name = get_pos_name(i-1)
        point.name = get_pos_name(new_pos)
    # Evaluate the curve, given the new ordrering of the Control Points
    update_curve(point.parent)

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

    path_points_check(anim_path)

    # Create Control Path from control_points elements
    bezier_curve_obj = bpy.data.curves.new('Control Path', type='CURVE')                                    # Create new Curve Object with name Control Path
    bezier_curve_obj.dimensions = '2D'                                                                      # The Curve Object is a 2D curve

    bezier_spline = bezier_curve_obj.splines.new('BEZIER')                                                  # Create new Bezier Spline "Mesh"
    bezier_spline.bezier_points.add(len(anim_path.get("Control Points"))-1)                                 # Add points to the Spline to match the length of the control_points list
    for i, cp in enumerate(anim_path.get("Control Points")):
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
                txt_coords: mathutils.Vector = bpy_extras.view3d_utils.location_3d_to_region_2d(
                    bpy.context.region,
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

'''
----------------------END FUNCTIONS RELATED TO THE CONTROL PATH-------------------------------
'''