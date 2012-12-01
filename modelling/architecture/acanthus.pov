#version 3.7;


#macro AcanthusPart(w, h, r, b)
union {
    #local Pts = array[8] {
        <-0.1, -0.1, 1>,
        <0, 0, 1>,
        <0.1, 0.1, 1>,
        <0.5, 0.1, 1>,
        <0.933, 0.333, 1>,
        <1.05, 0.667, 0.75>,
        <0.833, 1.05, 0.25>,
        <0.733, 1.05, 0.25>,
    };

    sphere_sweep {
        b_spline
        dimension_size(Pts, 1)
        
        #for (i, 0, dimension_size(Pts, 1)-1)
            , <0, Pts[i].x*h, Pts[i].y*w>, Pts[i].z*r
        #end
        
        scale b*x
    }

#ifdef (DEBUG_ACANTHUS_PART)
    #for (i, 0, w)
        cylinder { <0,0,i>, <0,h,i>, 0.01 pigment { Blue } }
    #end
    #for (i, 0, h)
        cylinder { <0,i,0>, <0,i,w>, 0.01 pigment { Blue } }
    #end
    
    sphere_sweep {
        linear_spline
        dimension_size(Pts, 1)
        
        #for (i, 0, dimension_size(Pts, 1)-1)
            , <0, Pts[i].x*h, Pts[i].y*w>, r*0.1
        #end
        
        pigment { Yellow }
    }
#end
}
#end


#macro AcanthusLeaf(w, h, r, n, fitrad)
union {
    #local breadth_scale = 2;
    #local s = 1.25*breadth_scale*r;
    #for (i, 0,n-1)
        #local i2 = (i-(n-1)/2);
        
        #local h2 = h * (1 + 0.03*abs(i2));
        #local w2 = w * (1 - 0.03*abs(i2));
        
        object { AcanthusPart(w, h2, r, breadth_scale) rotate -i2*1*z translate fitrad*z rotate (360*s*i2/(2*fitrad*pi))*y translate -fitrad*z }
    #end
}
#end


#ifndef (INCLUDE)

global_settings{ assumed_gamma 1.0 }
#default{ finish{ ambient 0.1 diffuse 0.9 }} 
//--------------------------------------------------------------------------
#include "colors.inc"
#include "stones.inc"
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
#declare Camera_5 = camera {/*ultra_wide_angle*/ angle 90   // diagonal view
                            location  <5.0 , 3.0 ,1.5>
                            right     x*image_width/image_height
                            look_at   <0.0 , 3.0 , 1.5>}
camera{Camera_5}
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



union {
    AcanthusPart(3, 6, 0.15, 2) pigment { Green }
}

union {
    cylinder { <0,0,-2>, <0, 4,-2>, 2 pigment { Red } }
    object { AcanthusLeaf(2, 4, 0.1, 5, 2) pigment { Green } }
    
    rotate 90*y
    translate 4*z 
}

#end
