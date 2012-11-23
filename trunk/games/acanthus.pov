// PoVRay 3.7 Scene File " ... .pov"
// author:  ...
// date:    ...
//--------------------------------------------------------------------------
#version 3.7;
global_settings{ assumed_gamma 1.0 }
#default{ finish{ ambient 0.1 diffuse 0.9 }} 
//--------------------------------------------------------------------------
#include "colors.inc"
#include "textures.inc"
#include "glass.inc"
#include "metals.inc"
#include "golds.inc"
#include "stones.inc"
#include "woods.inc"
#include "shapes.inc"
#include "shapes2.inc"
#include "functions.inc"
#include "math.inc"
#include "transforms.inc"
//--------------------------------------------------------------------------
// camera ------------------------------------------------------------------
#declare Camera_0 = camera {perspective angle 75               // front view
                            location  <0.0 , 1.0 ,-3.0>
                            right     x*image_width/image_height
                            look_at   <0.0 , 1.0 , 0.0>}
#declare Camera_1 = camera {/*ultra_wide_angle*/ angle 90   // diagonal view
                            location  <2.0 , 2.5 ,-3.0>
                            right     x*image_width/image_height
                            look_at   <0.0 , 1.0 , 0.0>}
#declare Camera_2 = camera {/*ultra_wide_angle*/ angle 90  //right side view
                            location  <3.0 , 1.0 , 0.0>
                            right     x*image_width/image_height
                            look_at   <0.0 , 1.0 , 0.0>}
#declare Camera_3 = camera {/*ultra_wide_angle*/ angle 90        // top view
                            location  <0.0 , 3.0 ,-0.001>
                            right     x*image_width/image_height
                            look_at   <0.0 , 1.0 , 0.0>}
#declare Camera_4 = camera {/*ultra_wide_angle*/ angle 90   // diagonal view
                            location  <4.0 , 3.5 ,-4.0>
                            right     x*image_width/image_height
                            look_at   <0.0 , 1.0 , 0.0>}
camera{Camera_4}
// sun ----------------------------------------------------------------------
light_source{< 3000,3000,-3000> color White}
// sky ----------------------------------------------------------------------
sky_sphere { pigment { gradient <0,1,0>
                       color_map { [0.00 rgb <0.6,0.7,1.0>]
                                   [0.35 rgb <0.1,0.0,0.8>]
                                   [0.65 rgb <0.1,0.0,0.8>]
                                   [1.00 rgb <0.6,0.7,1.0>] 
                                 } 
                       scale 2         
                     } // end of pigment
           } //end of skysphere
// ground -------------------------------------------------------------------
plane{ <0,1,0>, 0 texture{ T_Stone18 } }





#macro AcanthusPart(h, r, w)
union {
    #declare w = 1;
    #declare h = 1.618*w;
    #declare r = 0.1;
    
    /*cylinder { <0,0,0>, <0,h,0>, 0.01 pigment { Blue } }
    cylinder { <0,h,0>, <0,h,w>, 0.01 pigment { Blue } }
    cylinder { <0,h,w>, <0,0,w>, 0.01 pigment { Blue } }
    cylinder { <0,0,w>, <0,0,0>, 0.01 pigment { Blue } }*/


    sphere_sweep {
        b_spline
        6,
        
        <0,-1,0>, r,
        <0,0,0>, r,
        <0,1,0>, r*0.75,
        <0,h,h-1>, r*0.5,
        <0,h,w>, r*0.25
        <0,h-0.1,w+0.1>, 0
        
        scale 2*x
    }
}

/*#local a = 60;
union {
    cylinder { <0,0,0>, <0,h,0>, 1 }
    difference { 
        torus { r, 1 rotate 90*x }
        union {
            plane { <0,1,0>, 0 }
            plane { <0,1,0>, 0 rotate a*z }
        }
        translate <r,h,0>
    }
    difference {
        sphere { <r,0,0>, 1 scale 2*y }
        plane { <0,-1,0>, 0 }
        rotate a*z translate <r,h,0>
    }
    scale w*z
}*/
#end

#macro AcanthusLeaf(h, r, w, n)
union {
    #local s = 0.1;
    #for (i, 0,n-1)
        #local i2 = (i-(n-1)/2);
        #local h2 = h;
        #if (i = 0 | i = n-1)
             #local h2 = h - 8;
        #elseif (i = 1 | i = n-2)
             #local h2 = h - 4;
        #end
        object { AcanthusPart(h2, r, w) translate <s*i2,0,0> rotate -i2*5*z }
    #end
}
#end

union {                         
    cylinder { <0,0,0>, <0,3,0>, 2 pigment { Red } }
    #for (i, 0, 3)
        object { AcanthusLeaf(20, 3, 2, 1) pigment { Green } translate <0,0,2> rotate i*90*y }
    #end
    #for (i, 0, 7)
        object { AcanthusLeaf(20, 3, 2, 5) pigment { Green } scale 0.5 translate <0,2,2> rotate (i*45 + 22.5)*y }
    #end
}
