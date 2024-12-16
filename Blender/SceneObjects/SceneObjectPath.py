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
from bpy.types import Object
import functools
import math
import struct
import copy
import mathutils
from mathutils import Vector, Quaternion

from .SceneObject import SceneObject, NodeTypes
from ..AbstractParameter import Parameter, Key, KeyList, KeyType
from ..serverAdapter import send_parameter_update


### Class defining the properties and exposed functionalities of any object in a TRACER scene
#   
class SceneObjectPath(SceneObject):
    
    def __init__(self, bl_obj: Object):
        super().__init__(bl_obj)

        # If the Blender Object has the property Control Points, add the respective Animated Parameters for path locations and path rotations
        # These parameters are associated with the root object of the Control Path in the scene
        control_path = bl_obj.get("Control Points", None)
        if control_path != None and len(control_path) > 0:
            first_point: Object = control_path[0]
            path_locations = Parameter(first_point.location, bl_obj.name+"-path_locations", self)
            path_locations.init_animation()
            self.parameter_list.append(path_locations)
            path_rotations = Parameter(first_point.rotation_quaternion, bl_obj.name+"-path_rotations", self)
            path_rotations.init_animation()
            self.parameter_list.append(path_rotations)

    ### It updates the TRACER parameters describing the Control Path using the data from the the Control Path and Control Points geometrical data
    def update_control_points(self):
        if self.blender_object.get("Control Points", None) != None:
            rotations = self.parameter_list[-1]
            locations = self.parameter_list[-2]

            cp_list: list[bpy.types.Object] = self.blender_object.get("Control Points")
            cp_curve: bpy.types.SplineBezierPoints = self.blender_object.children[0].data.splines[0].bezier_points
            for i, cp in enumerate(cp_list):
                locations.key_list.set_key(Key( time                = cp.get("Frame"),
                                                value               = cp_curve[i].co,
                                                type                = KeyType.BEZIER,
                                                right_tangent_time  = cp.get("Ease Out"),
                                                right_tangent_value = cp_curve[i].handle_right,
                                                left_tangent_time   = cp.get("Ease In"),
                                                left_tangent_value  = cp_curve[i].handle_left ),
                                            i)
                original_rot_mode = cp.rotation_mode
                if original_rot_mode != 'QUATERNION':
                    cp.rotation_mode = 'QUATERNION'

                rotations.key_list.set_key(Key( time                = cp.get("Frame"),
                                                value               = cp.rotation_quaternion,
                                                type                = KeyType.LINEAR ),
                                            i)
                
                cp.rotation_mode = original_rot_mode

            self.parameter_list[-2] = locations
            self.parameter_list[-1] = rotations

    def serialise(self) -> bytearray:
        path_byte_array = super().serialise()

        # Serialise Path Control Points

        return path_byte_array
    
    ## Given a Control Path in the scene, it evaluates it, it fills a new Curve Package object with the sampled data, and adds it to the list of curves to be shared with the other TRACER clients
    # @param control_point_list List of Control Points defining the Control Path
    # @param is_cyclic          Whether the Control Path is cyclic or not (acyclic by default)
    # @returns  None            It doesn't return anything, but 
    def sample_control_path(self):
        sampled_points  = [] # list of floats [pos0.x, pos0.y, pos0.z, pos1.x, pos1.y, pos1.z, ..., posN.x, posN.y, posN.z]
        sampled_look_at = [] # list of floats [rot0.x, rot0.y, rot0.z, rot1.x, rot1.y, rot1.z, ..., rotN.x, rotN.y, rotN.z]
        value_error_msg = "The frame value of any point MUST be greater than the previous one!"

        control_points: list[bpy.types.Object] = self.blender_object.get("Control Points", None)
        bezier_points: bpy.types.SplineBezierPoints = self.blender_object.children[0].data.splines[0].bezier_points
        
        #point: bpy.types.Object = None
        for i, point in enumerate(control_points):
            # Read the attribute of the first point of the segment
            coords_point_one    = bezier_points[i].co
            r_handle_point_one  = bezier_points[i].handle_right
            frame_point_one     = point.get("Frame")
            ease_out_point_one  = point.get("Ease Out")

            if self.blender_object.get("Is Cyclic", False):
                if i == 0:
                    # If cyclic, we assume that the frame of the first point is 0 at the beginning of the path and point.get("Frame") at the end 
                    frame_point_one = 0

                if i == len(control_points)-1:
                    # If the path is cyclic and we are at the end of the path,
                    # Evaluate segment between last and fist point of the path
                    next_point = control_points[0]
                    value_error_msg = "When cyclic, the frame value of the first point MUST be greater than the last one!"
            else:
                if i < len(control_points)-1:
                    next_point = control_points[i+1]
                else:
                    next_point = None

            if next_point != None:
                # Read the attribute of the second point of the segment
                coords_point_two    = bezier_points[i+1].co
                l_handle_point_two  = bezier_points[i+1].handle_left
                frame_point_two     = next_point.get("Frame")        
                ease_in_point_two   = next_point.get("Ease In")

                segment_frames = frame_point_two - frame_point_one + 1      # Compute number of samples in the segment 

                if segment_frames > 0:
                    # Sampling a cubic bezier spline between (0,0) and (1,1) given handles parallel to X and as strong as the passed influence values
                    # This gives us a list of percentages for sampling the Control Path between two Control Points, with the given resolution and timings
                    timings = SceneObjectPath.adaptive_timings_resampling(ease_out_point_one/100, ease_in_point_two/100, segment_frames)

                    evaluated_positions = SceneObjectPath.adaptive_sample_bezier(coords_point_one, r_handle_point_one, l_handle_point_two, coords_point_two, timings)
                    # Probably it is necessary to check whether Eulers or Quaternions are used by the user to define pointer rotations (more often than not Eulers are used though)
                    evaluated_rotations = SceneObjectPath.rotation_interpolation(point.rotation_euler.to_quaternion(), next_point.rotation_euler.to_quaternion(), timings)

                    # Removing the 3 elements (points coordinates and euler angle respectively) from the two lists for all the segments but not the last (to avoid duplicates)
                    if i < len(control_points)-2:
                        evaluated_positions = evaluated_positions[: len(evaluated_positions) - 3]
                        evaluated_rotations = evaluated_rotations[: len(evaluated_rotations) - 3]

                    sampled_points.extend(evaluated_positions)
                    sampled_look_at.extend(evaluated_rotations) 
                else:
                    bpy.context.window_manager.report({"ERROR"}, value_error_msg)

        #curve_package.pointsLen = int(len(curve_package.points) / 3)
        #return curve_package

    ##  Function that ADAPTIVELY samples a cubic Beziér between two points - only 2D curves supported
    #   It uses the timing information provided by the artist through the UI (frames, ease-in, ease-out) to sample a given segment of the control path
    #   @param  b0          The coordinates of first point of the beziér segment
    #   @param  b1          The right handle of the first point of the beziér segment
    #   @param  b2          The left handle of the second point of the beziér segment
    #   @param  b3          The coordinates of second point of the beziér segment
    #   @param  resolution  How many points should be sampled on the segment, aka the frame delta betwen first and second point
    #   @param  influence1  Speed rate for easing out of the first point, aka the ease-out value of the first point of the beziér segment
    #   @param  influence2  Speed rate for easing into the second point, aka the ease-in value of the second point of the beziér segment
    #   @returns            A list of points (of size equal to resolution) sampled along the beziér segment between b0 and b3 (with handles defined by b1 and b2)
    def adaptive_sample_bezier(knot1: Vector, handle1: Vector, handle2: Vector, knot2: Vector, timings: list[float]) -> list[float]:
        sample: Vector
        sampled_segment = []

        # Sample the bezier segment between b0 and b3 given the sapmling rate in timings 
        for t in timings:
            sample = SceneObjectPath.sample_bezier(knot1, handle1, handle2, knot2, t)
            sampled_segment.extend([sample.x, sample.y, sample.z])

        return sampled_segment

    def adaptive_timings_resampling(ease_from: float, ease_to: float, resolution: int) -> list [float]:
        timings = []
        # Good results with oversampling by a factor of 10 but no interpolation or with interpolation but no oversampling 
        pre_sampling = mathutils.geometry.interpolate_bezier(Vector((0,0)), Vector((ease_from,0)), Vector((1-ease_to,1)), Vector((1,1)), 10*resolution)

        for i in range(resolution):
            t = i / resolution
            j = 0

            while pre_sampling[j].x <= t:
                j += 1

            t1 = (t - pre_sampling[j-1].x) / (pre_sampling[j].x - pre_sampling[j-1].x)
            eased_t = t1 * pre_sampling[j].y + (1-t1) * pre_sampling[j-1].y
            #eased_t = pre_sampling[j].y

            timings.append(eased_t)
    
        return timings

    def sample_bezier(knot1: Vector, handle1: Vector, handle2: Vector, knot2: Vector, t: float) -> Vector:
        sample = (                      math.pow((1-t), 3)) * knot1   +\
                 (3 *          t      * math.pow((1-t), 2)) * handle1 +\
                 (3 * math.pow(t, 2)  *          (1-t)    ) * handle2 +\
                 (    math.pow(t, 3)                      ) * knot2
        return sample


    ## Implementation of a single slerp function, to limit dependencies from external librabries
    # @param quat_1     value of the first Quaternion
    # @param quat_2     value of the second Quaternion
    # @param n_samples  number of samples to take on the range of the interpolation
    # @returns          list of directional vectors derived from the spherical-linearly interpolated Quaternions 
    def rotation_interpolation(quat_1: Quaternion, quat_2: Quaternion, timings: list[float]) -> list[Vector]:
        samples = []

        for t in timings:
            # quat_slerp = (math.sin(angle * (1-t)) / math.sin(angle)) * quat_1 +\
            #              (math.sin(angle *    t ) / math.sin(angle)) * quat_2
            quat_slerp = quat_1.slerp(quat_2, t)
            fwd_vector = Vector((0, -1, 0))
            fwd_vector.rotate(quat_slerp)
            samples.extend([fwd_vector.x, fwd_vector.y, fwd_vector.z])

        return samples