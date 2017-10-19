import math
import re
from .xplane_object import XPlaneObject
from ..xplane_helpers import floatToStr, FLOAT_PRECISION, logger
from ..xplane_constants import *
from ..xplane_config import getDebug
import mathutils
from mathutils import Vector, Matrix, Euler

#### BEN NEEDS TO DOC THIS LATER

def vec_b_to_x(v):
    return Vector((v.x, v.z, -v.y))

def vec_x_to_b(v):
    return Vector((v.x, -v.z, v.y))

def basis_for_dir(neg_input_axis):
    m = Matrix.Identity(3)
    rotate_basis_x = -neg_input_axis
    rotate_basis_y = Vector((0,0,0))
    rotate_basis_z = Vector((0,0,0))
    
    #If 
    if abs(rotate_basis_x[0]) > max(abs(rotate_basis_x[1]),abs(rotate_basis_x[2])):
        rotate_basis_y[0] = 0.0
        rotate_basis_y[1] = 1.0 if rotate_basis_x[0] > 0.0 else -1.0
        rotate_basis_y[2] = 0.0
    elif abs(rotate_basis_x[1]) > abs(rotate_basis_x[2]):
        # User's axis is approximately Y - use Z for second axis.
        rotate_basis_y[0] = 0.0
        rotate_basis_y[1] = 0.0
        rotate_basis_y[2] = 1.0 if rotate_basis_x[1] > 0.0 else -1.0        
    else:
        #User's axis is approxiamtely Z - use X for second axis.
        rotate_basis_y[0] = 1.0 if rotate_basis_x[2] else -1.0
        rotate_basis_y[1] = 0.0
        rotate_basis_y[2] = 0.0

    #// Third axis is cross of first and second - chosen to not be degenerate.
    rotate_basis_z = rotate_basis_x.cross(rotate_basis_y).normalized()
    #// Recalculate second axis to truly be orthogonal to BOTH first and third.
    rotate_basis_y = rotate_basis_z.cross(rotate_basis_x)
    m[2] = rotate_basis_x
    m[0] = rotate_basis_y
    m[1] = rotate_basis_z
    
    def nearly_equal_number(number,max_diff):
        return abs(number) <= max_diff

    def nearly_equal_vec(vec_1, vec_2, max_diff=0.00001):
        return nearly_equal_number(vec_2.x - vec_1.x, max_diff) and\
               nearly_equal_number(vec_2.y - vec_1.y, max_diff) and\
               nearly_equal_number(vec_2.z - vec_1.z, max_diff)
    
    assert nearly_equal_vec(rotate_basis_x, -neg_input_axis)
    assert 0.98999999 <= rotate_basis_x.magnitude <= 1.00001  and\
           0.98999999 <= rotate_basis_y.magnitude <= 1.00001  and\
           0.98999999 <= rotate_basis_z.magnitude <= 1.00001
    assert nearly_equal_vec(rotate_basis_x.cross(rotate_basis_y),rotate_basis_z)
    assert nearly_equal_vec(rotate_basis_z.cross(rotate_basis_x),rotate_basis_y)
    return m

test_param_lights = {
    # NAMED LIGHTS
    # Spill version
    'taillight' : ((),('0.4','0.05','0','0.8','3','0','-0.5','0.86','0.0','0')),
    
    # PARAMETER LIGHTS
    'airplane_nav_left_size':(('SIZE','FOCUS'), 
        ('FOCUS','0','0','1','SIZE','1','7','7','0','0','0','1','sim/graphics/animation/lights/airplane_navigation_light_dir')),

    'airplane_nav_right_size':(('SIZE','FOCUS'), 
        ('FOCUS','0','0','1','SIZE','1','6','7','0','0','0','1','sim/graphics/animation/lights/airplane_navigation_light_dir')),

    'area_lt_param_sp': (('DX','DY','DZ','THROW'),
                         ('0.85', '0.75', '1.0', '0.6','THROW','DX', 'DY', 'DZ', '0.3', '0')),

    'full_custom_halo': (('R','G','B','A','S','X','Y','Z','F'),
                         ('R', 'G', 'B', 'A', 'S','X','Y','Z','F','1')),

    'helipad_flood_sp': (('BRIGHT', 'THROW', 'X', 'Y', 'Z', 'FOCUS'),
                         ('0.996', '0.945', '0.882', 'BRIGHT', 'THROW', 'X', 'Y', 'Z', 'FOCUS', '0')),

    'helipad_flood_bb': (('X', 'Y', 'Z', 'WIDTH'),
                         ('1', '1', '1', '0.5', '1', '2', '6', 'X', 'Y', 'Z', 'WIDTH', '0', '0', '0', '0')),

    'spot_params_sp':   (('R','G','B','BRIGHT','THROW','X','Y','Z','FOCUS'),
                         ('R','G','B','BRIGHT','THROW','X','Y','Z','FOCUS')),

    'spot_params_bb':   (('R','G','B','SIZE','X','Y','Z','WIDTH'),
                         ('R', 'G', 'B', '1.0', 'SIZE',  '2',  '5',  '2', 'X', 'Y', 'Z', 'WIDTH',  '0',  '0',  '0',  '0')),

    'radio_obs_flash':  (('X','Y','Z'),
                         ('1', '0.8', '0.8', '1', '1.5', '1', '4', '5', 'X', 'Y', 'Z', '0.5', '0.25', '0', '1.5', '1'))
}

####

# Class: XPlaneLight
# A Light
#
# Extends:
#   <XPlaneObject>
class XPlaneLight(XPlaneObject):
    # Property: indices
    # list - [start,end] Starting end ending indices for this light.

    # Property: color
    # list - [r,g,b] Color taken from the original Blender light. Can change depending on <lightType>.

    # Property: energy
    # float - Energy taken from Blender light.

    # Property: lightType
    # string - Type of the light taken from <XPlaneLampSettings>.

    # Property: size
    # float - Size of the light taken from <XPlaneLampSettings>.

    # Property: lightName
    # string - Name of the light taken from <XPlaneLampSettings>.

    # Property: params
    # string - Parameters taken from <XPlaneLampSettings>.

    # Property: dataref
    # string - Dataref path taken from <XPlaneLampSettings>.

    # Constructor: __init__
    #
    # Parameters:
    #   object - A Blender object
    def __init__(self, blenderObject):
        super(XPlaneLight, self).__init__(blenderObject)
        self.indices = [0,0]
        self.color = [blenderObject.data.color[0], blenderObject.data.color[1], blenderObject.data.color[2]]
        self.energy = blenderObject.data.energy
        self.type = XPLANE_OBJECT_TYPE_LIGHT
        self.lightType = blenderObject.data.xplane.type
        self.size = blenderObject.data.xplane.size
        self.lightName = blenderObject.data.xplane.name
        
        self.params = blenderObject.data.xplane.params
        self.parsed_params = {
                'R':None,
                'G':None,
                'B':None,
                'A':None,
                'INDEX':None,
                'SIZE':None,
                'BRIGHT':None,
                'THROW':None,
                'SPREAD':None,
                'X':None,
                'Y':None,
                'Z':None,
                'DX':None,
                'DY':None,
                'DZ':None,
                'W':None,
                'WIDTH':None,
                'FOCUS':None
            }

        self.is_omni = False
        
        self.uv = blenderObject.data.xplane.uv
        self.dataref = blenderObject.data.xplane.dataref

        # change color according to type
        if self.lightType == LIGHT_FLASHING:
            self.color[0] = -self.color[0]
        elif self.lightType == LIGHT_PULSING:
            self.color[0] = 9.9
            self.color[1] = 9.9
            self.color[2] = 9.9
        elif self.lightType == LIGHT_STROBE:
            self.color[0] = 9.8
            self.color[1] = 9.8
            self.color[2] = 9.8
        elif self.lightType == LIGHT_TRAFFIC:
            self.color[0] = 9.7
            self.color[1] = 9.7
            self.color[2] = 9.7

        self.getWeight(10000)

    # COPY PASTA WARNING!!!
    #
    # This is stolen from the bone code's bake matrix exporter.  I wanted this copied out
    # to 1. avoid re-test late in beta and 2. to have the option to optimize this later
    # for lights that can have direction vectors.

    def _writeStaticRotationForLight(self, bakeMatrix):
        debug = getDebug()
        indent = self.xplaneBone.getIndent()
        o = ''
        bakeMatrix = bakeMatrix
        rotation = bakeMatrix.to_euler('XYZ')
        rotation[0] = round(rotation[0],5)
        rotation[1] = round(rotation[1],5)
        rotation[2] = round(rotation[2],5)
        
        # ignore noop rotations
        if rotation[0] == 0 and rotation[1] == 0 and rotation[2] == 0:
            return o

        if debug:
            o += indent + '# static rotation\n'

		# Ben says: this is SLIGHTLY counter-intuitive...Blender axes are
		# globally applied in a Euler, so in our XYZ, X is affected -by- Y
		# and both are affected by Z.
		#
		# Since X-Plane works opposite this, we are going to apply the
		# animations exactly BACKWARD! ZYX.  The order here must
		# be opposite the decomposition order above.
		#
		# Note that since our axis naming is ALSO different this will
		# appear in the OBJ file as Y -Z X.
		#
		# see also: http://hacksoflife.blogspot.com/2015/11/blender-notepad-eulers.html

        axes = (2, 1, 0)
        eulerAxes = [(0.0,0.0,1.0),(0.0,1.0,0.0),(1.0,0.0,0.0)]
        i = 0

        for axis in eulerAxes:
            deg = math.degrees(rotation[axes[i]])

            # ignore zero rotation
            if not deg == 0:
                o += indent + 'ANIM_rotate\t%s\t%s\t%s\t%s\t%s\n' % (
                    floatToStr(axis[0]),
                    floatToStr(axis[2]),
                    floatToStr(-axis[1]),
                    floatToStr(deg), floatToStr(deg)
                )

            i += 1

        return o

    def collect(self):
        # We ask:
        # - Are do the length of the actual params match the length of the formal params
        # - Are the actual params all numbers
        # - Are there 'FOCUS' or 'WIDTH' parameters at play? If there are, is this light omni_directional?
        if self.lightType == LIGHT_PARAM:
            params_formal = test_param_lights[self.lightName][0]
            params_actual = self.params.split()
            if len(params_formal) != len(params_actual):
                logger.error("PARAM_DEF: %s and actual params: %s are different lengths (%d,%d)" % (
                                    len(' '.join(params_formal)),
                                    len(' '.join(params_actual))
                                )
                            )

            def is_number(number_str):
                try:
                    float(number_str)
                except:
                    return False
                else:
                    return True

            parsed_params_actual = [p for p in params_actual if not is_number(p)]
            if len(parsed_params_actual) != 0:
                logger.error("Invalid light params for %s:(%s) All light params must be a number" % (
                                    self.lightName,
                                    ','.join([str(p) for p in parsed_params_actual])
                                )
                            )

            if logger.hasErrors():
                return

            if "FOCUS" in params_formal:
                idx = params_formal.index("FOCUS")
            elif "WIDTH" in params_formal:
                idx = params_formal.index("WIDTH")
            else:
                idx = -1

            if idx != -1:
                self.is_omni = float(params_actual[idx]) >= 1.0

            #parse_them_all
            for i,p in enumerate(params_actual):
                self.parsed_params[params_formal[i]] = float(p)

    def clamp(self, num, minimum, maximum):
        if num < minimum:
            num = minimum
        elif num > maximum:
            num = maximum
        return num

    def write(self):
        debug = getDebug()
        indent = self.xplaneBone.getIndent()
        o = super(XPlaneLight, self).write()

        bakeMatrix = self.xplaneBone.getBakeMatrixForAttached()
        if self.blenderObject.data.type == 'POINT':
            translation = bakeMatrix.to_translation()
            has_anim = False
        elif self.blenderObject.data.type != 'POINT':
            def prettyprint(template_str, content):
                return "{:<40} %s".format(template_str) % content
            
            print("------------")
            # Vector P(arameters), in Blender Space
            dir_vec_p_x = Vector((self.parsed_params["X"],self.parsed_params["Y"],self.parsed_params["Z"]))
            print(prettyprint("Direction Vector P:", str(dir_vec_p_x)))
            
            dir_vec_p_norm_x = dir_vec_p_x.normalized()
            print(prettyprint("Direction Vector P (norm, XP Co-ords):",str(dir_vec_p_norm_x)))
            
            dir_vec_p_norm_b = vec_x_to_b(dir_vec_p_norm_x)
            print(prettyprint("Direction Vector P (norm, BL Co-ords):" , str(dir_vec_p_norm_b)))
            
            # Multiple bake matrix by Vector to get the direction of the Blender object
            dir_vec_b_norm = bakeMatrix.to_3x3() * Vector((0,0,-1))

            axis_angle_vec3 = dir_vec_p_norm.cross(dir_vec_b_normb)
            print(prettyprint("Cross Product (Dir Vecs B X P) (norm):" , (str(axis_angle_vec3))))

            axis_angle_theta = math.asin(self.clamp(axis_angle_vec3.magnitude,-1.0,1.0)) 
            print(prettyprint("AA Theta:", "%s (rad), %s (deg)" % (str(axis_angle_theta),str(axis_angle_theta * (180/math.pi)))))

            axis_angle = mathutils.Matrix.Rotation(axis_angle_theta,4,axis_angle_vec3)
            print(prettyprint("AA:\n", (str(axis_angle))))

            translation = bakeMatrix.to_translation()
            
            has_anim = False
        
            # Ben says: lights always have some kind of offset because the light itself
            # is "at" 0,0,0, so we treat the translation as the light position.
            # But if there is a ROTATION then in the light's bake matrix, the
            # translation is pre-rotation.  but we want to write a single static rotation
            # and then NOT write a translation every time.
            #
            # Soooo... we write a bake matrix and then we transform the translation by the
            # inverse to change our animation order (so we really have rot, trans when we
            # originally had trans, rot) and now we can use the translation in the lamp
            # itself.
            
            if round(axis_angle_theta,5) != 0.0 and self.is_omni is False:
                o += "%sANIM_begin\n" % indent
                
                if debug:
                    o += indent + '# static rotation\n'
                
                axis_angle_vec3_x = vec_b_to_x(axis_angle_vec3)
                anim_rotate_dir =  indent + 'ANIM_rotate\t%s\t%s\t%s\t%s\t%s\n' % (
                    floatToStr(axis_angle_vec3_x[0]),
                    floatToStr(axis_angle_vec3_x[1]),
                    floatToStr(axis_angle_vec3_x[2]),
                    floatToStr(axis_angle_theta), floatToStr(axis_angle_theta)
                )
                print(prettyprint("ANIM_rotate:",anim_rotate_dir))
                o += anim_rotate_dir
                print(prettyprint("rot_matrix",bakeMatrix.to_euler('XYZ')))
                rot_matrix = bakeMatrix.to_euler('XYZ').to_matrix().to_4x4()
                print(prettyprint("translation pre-transform:",translation))
                translation = rot_matrix.inverted() * translation
                print(prettyprint("translation post-transform:",translation))
                has_anim = True
        if self.lightType == LIGHT_NAMED:
            o += "%sLIGHT_NAMED\t%s %s %s %s\n" % (
                indent, self.lightName,
                floatToStr(translation[0]),
                floatToStr(translation[2]),
                floatToStr(-translation[1])
            )
        elif self.lightType == LIGHT_PARAM:
            o += "%sLIGHT_PARAM\t%s %s %s %s %s\n" % (
                indent, self.lightName,
                floatToStr(translation[0]),
                floatToStr(translation[2]),
                floatToStr(-translation[1]),
                self.params
            )
        elif self.lightType == LIGHT_CUSTOM:
            o += "%sLIGHT_CUSTOM\t%s %s %s %s %s %s %s %s %s %s %s %s %s\n" % (
                indent,
                floatToStr(translation[0]),
                floatToStr(translation[2]),
                floatToStr(-translation[1]),
                floatToStr(self.color[0]),
                floatToStr(self.color[1]),
                floatToStr(self.color[2]),
                floatToStr(self.energy),
                floatToStr(self.size),
                floatToStr(self.uv[0]),
                floatToStr(self.uv[1]),
                floatToStr(self.uv[2]),
                floatToStr(self.uv[3]),
                self.dataref
            )

        # do not render lights with no indices
        elif self.indices[1] > self.indices[0]:
            offset = self.indices[0]
            count = self.indices[1] - self.indices[0]
            o += "%sLIGHTS\t%d %d\n" % (indent, offset, count)

        if has_anim:
            o += "%sANIM_end\n" % indent

        return o
