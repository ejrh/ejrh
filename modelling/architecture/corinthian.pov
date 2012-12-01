#version 3.7;
global_settings{ assumed_gamma 1.0 }
#default{ finish{ ambient 0.1 diffuse 0.9 }} 
//--------------------------------------------------------------------------
#include "colors.inc"
#include "stones.inc"

#declare INCLUDE = true;
#include "acanthus.pov"
#include "scroll.pov"
#undef INCLUDE



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
                            location  <15.0 , 5.5 , 10.5>
                            right     x*image_width/image_height
                            look_at   <0.0 , 5.5 , 10.5>}
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



#declare eps = 0.000001;

#macro ColumnCapital(r)
    #local h = 2*r;
    #local lh = h*0.35;
    union {                         
        cylinder { <0,0,0>, <0,r*0.2,0>, r*1.1 }
        torus { r*1.1, r*0.1 translate <0,r*0.1,0> }
        
        cylinder { <0,r*0.2,0>, <0,h,0>, r }
        #for (i, 0, 7)
            object { AcanthusLeaf(lh*0.3, lh, lh*0.05, 5, r) translate <0,r*0.2,r> rotate (i*45 + 22.5)*y }
        #end
        #for (i, 0, 7)
            object { AcanthusLeaf(lh*0.6, lh*1.8, lh*0.05, 5, r) translate <0,r*0.2,r> rotate (i*45)*y }
        #end
        
        #for (i, 0, 3)
            object { Scroll(lh*0.6, lh*0.6, lh*0.8, lh*0.05, 0.5) translate lh*0.4*x rotate 90*x translate <0,h,r> rotate (i*90 + 45)*y }
        #end
    }
#end
                                           
#macro ColumnSegment(r, h, jb, jt, kern)
    #local NUM_FLUTES = 24;
    #local fr = 2*pi*r/(NUM_FLUTES*4);
    #local h1 = fr*2 + kern;
    #local h2 = h - fr*2 - kern;
    
    #if (jb)
        #local h1 = 0;
        #local BottomCollar = difference {
            cylinder { <0,-eps,0>, <0,kern,0>, fr+kern }
            torus { fr+kern, kern translate <0,kern,0> } 
        };
    #end
    #if (jt)
        #local h2 = h;
        #local TopCollar = difference {
            cylinder { <0,-kern,0>, <0,eps,0>, fr+kern }
            torus { fr+kern, kern translate <0,-kern,0> } 
        };
    #end
    
    difference {
        union {
            cylinder { <0, kern, 0>, <0, h - kern, 0>, r }
            cylinder { <0, 0, 0>, <0, h, 0>, r - kern }
            torus { r - kern, kern translate kern*y }
            torus { r - kern, kern translate (h - kern)*y }
        }
        
        union {
            #for (i, 0, NUM_FLUTES-1)
                union {
                    cylinder { <r,h1,0>, <r,h2,0>, fr }
                    
                    #if (jb)
                        object { BottomCollar translate <r, h1, 0> }
                    #else
                        sphere { <r,h1,0>, fr }
                    #end

                    #if (jt)                    
                        object { TopCollar translate <r, h2, 0> }
                    #else
                        sphere { <r,h2,0>, fr }
                    #end
                    rotate i*360/NUM_FLUTES*y
                }
            #end
        }
    }
#end

#macro Box(dx, dy, dz, kern)
    #local dx2 = dx - 2*kern;
    #local dy2 = dy - 2*kern;
    #local dz2 = dz - 2*kern;
    
    union {
        #for (i, 0, 1)
            #for (j, 0, 1)
                #for (k, 0, 1)
                    sphere { <kern + i*dx2, kern + j*dy2, kern + k*dz2>, kern }
                #end
                cylinder { <kern + i*dx2, kern + j*dy2, kern>, <kern + i*dx2, kern + j*dy2, kern + dz2>, kern }
                cylinder { <kern + i*dx2, kern, kern + j*dz2>, <kern + i*dx2, kern + dy2, kern + j*dz2>, kern }
                cylinder { <kern, kern + i*dy2, kern + j*dz2>, <kern + dx2, kern + i*dy2, kern + j*dz2>, kern }
            #end
        #end
        box { <kern, kern, 0>, <kern + dx2, kern + dy2, dz> }
        box { <kern, 0, kern>, <kern + dx2, dy, kern + dz2> }
        box { <0, kern, kern>, <dx, kern + dy2, kern + dz2> }
    }
#end
                                        
#macro ColumnBase(r, h, r2, kern)
    union {
        cylinder { <0,0.6*h,0>, <0,h,0>, (r+r2)/2 }
        torus { (r+r2)/2, 0.2*h translate <0,0.8*h,0> }
        object { Box(r2*2, 0.6*h, r2*2, kern) translate <-r2,0,-r2> }
    }
#end

#macro Column(r, n)
    union {
        object { ColumnBase(r, r/2, r+0.1, 0.025) }
        #for (i, 0, n-1)
            object { ColumnSegment(r, 1, (i != 0), (i != n-1), 0.025) translate (i+r/2)*y }
        #end
        object { ColumnCapital(r) translate (n+r/2)*y }
    }
#end

union {
    #for (i, 0, 13)
        #if (mod(i, 4) = 0 | mod(i, 4) = 1)
            object { Column(0.5, 9) translate i*1.5*z }
        #end
    #end
    
    object { Box(1.5, 0.25, 14*1.5, 0.025) translate <-0.75,10.25,-0.75> }
    pigment { White }
}

union { 
    object { ColumnSegment(2, 2, false, false, 0.1) } 
    object { ColumnCapital(2) translate <0,2, 0> }
    
    translate <4,0,10.5> 
    
    pigment { Yellow } 
}
