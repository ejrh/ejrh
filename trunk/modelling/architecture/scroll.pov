#version 3.7;


#macro Scroll(w, h, d, r, b)
union {
    #local Pts = array[16];
    
    #for (i, 0, 15)
        #local Pts[i] = <0.75+i*sin(i*pi/4)/16,0.5+i*cos(i*pi/4)/16,1>;
    #end
    
    #local Pts[12] = Pts[12] + <0.125, 0.05, 0>;
    #local Pts[13] = Pts[12] + <-0.375, -0.05, 0>;
    #local Pts[14] = Pts[13] + <-0.5, 0.0, 0>;
    #local Pts[15] = Pts[14] + <-0.25, 0.0, 0>;

    #local Trim = union {
        sphere_sweep {
            cubic_spline
            dimension_size(Pts, 1)
            
            #for (i, 0, dimension_size(Pts, 1)-1)
                , <0, Pts[i].x*h, Pts[i].y*w>, Pts[i].z*r
            #end
        }
        
        cylinder { <0, (0.75 - 0.375)*h, 0.5*w>, <0, (0.75 - 0.75)*h, 0.5*w>, r }
        sphere { <0, (0.75 - 0.75)*h, 0.5*w>, r }
            
        scale b*x
    }
    
    object { Trim }
    object { Trim translate -d*x }

    union {
        difference {
            prism {
                cubic_spline
                0.0, d,
                
                dimension_size(Pts, 1)-4
                
                , <Pts[5].x*h, Pts[5].y*w>
                #for (i, 6, dimension_size(Pts, 1)-2)
                    , <Pts[i].x*h, Pts[i].y*w>
                #end
                , <Pts[6].x*h, Pts[6].y*w>
                , <Pts[15].x*h, Pts[15].y*w>
        
                rotate 90*z
            }
            
            plane { z, -0.25*w }
        }
        box { <0, (0.75 - 0.75)*h, (0.5 - 0.75)*w>, <-d, (0.75 - 0.375)*h, 0.5*w> }
    }

#ifdef (DEBUG_SCROLL)
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
            , <0.1, Pts[i].x*h, Pts[i].y*w>, r*0.1
        #end
        
        pigment { Yellow }
    }
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
//plane{ <0,1,0>, 0 texture{ T_Stone18 } }

#declare DEBUG_SCROLL = 1;

union {
    Scroll(4, 4, 1, 0.2, 0.5) pigment { White }
}

#end
