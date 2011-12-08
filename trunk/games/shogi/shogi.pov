// Persistence of Vision Ray Tracer Scene Description File
// File: ?.pov
// Vers: 3.6
// Desc: Basic Scene Example
// Date: mm/dd/yy
// Auth: ?
//

#version 3.6;

#include "colors.inc"
#include "shapes.inc"
#include "metals.inc"
#include "woods.inc"
#include "skies.inc"

#include "grass/mgrass.pov"
#include "trees/maketree.pov"
#include "trees/txttree.inc"


global_settings {
  assumed_gamma 1.0
}

// ----------------------------------------

#declare Eye = <5, 15, 5>;

camera {
  location Eye  
  right     x*image_width/image_height
  look_at   <5, 0.0, 5>
}

light_source {
  Eye            // light's position (translated below)
  color rgb 0.5*<1, 1, 1>  // light's color
}


light_source {
  1000*y
  color rgb 0.9*<1, 1, 1>
}
                        

sky_sphere {
    pigment {
      crackle
      scale 0.1
      color_map {
        [0.0 color Black ]
        [1.0 color Black ]
      }
    }
}


// ----------------------------------------   

#declare BoardTexture =
    texture { pigment { P_WoodGrain15A color_map { M_Wood10A }}}
    texture { pigment { P_WoodGrain15B color_map { M_Wood10B }}}

#declare RoundingRadius = 0.1;
union {
        box {<RoundingRadius,0,RoundingRadius>, <10-RoundingRadius,1,10-RoundingRadius>}
        box {<RoundingRadius,RoundingRadius,0>, <10-RoundingRadius,1-RoundingRadius,10>}                                               
        box {<0,RoundingRadius,RoundingRadius>, <10,1-RoundingRadius,10-RoundingRadius>}
        
        sphere {<RoundingRadius,RoundingRadius,RoundingRadius> RoundingRadius}                                               
        sphere {<RoundingRadius,1-RoundingRadius,RoundingRadius> RoundingRadius}
        sphere {<10-RoundingRadius,RoundingRadius,RoundingRadius> RoundingRadius}
        sphere {<10-RoundingRadius,1-RoundingRadius,RoundingRadius> RoundingRadius}
        sphere {<RoundingRadius,RoundingRadius,10-RoundingRadius> RoundingRadius}
        sphere {<RoundingRadius,1-RoundingRadius,10-RoundingRadius> RoundingRadius}
        sphere {<10-RoundingRadius,RoundingRadius,10-RoundingRadius> RoundingRadius}
        sphere {<10-RoundingRadius,1-RoundingRadius,10-RoundingRadius> RoundingRadius}  
        cylinder {<0,0,0>, <0,9.8,0> 0.1 rotate 90*x translate 0.9*y translate 0.1*z translate 0.1*x}
        cylinder {<0,0,0>, <0,9.8,0> 0.1 rotate 90*x translate 0.9*y translate 0.1*z translate 0.1*x rotate 90*y translate 10*z}
        cylinder {<0,0,0>, <0,9.8,0> 0.1 rotate 90*x translate 0.9*y translate 0.1*z translate 0.1*x translate 9.8*x}
        cylinder {<0,0,0>, <0,9.8,0> 0.1 rotate 90*x translate 0.9*y translate 0.1*z translate 0.1*x rotate 90*y translate 0.2*z}
        texture {BoardTexture}
        }                                       
#declare i = 0.5;
#while (i <= 9.5)
        cylinder {<0.5,1,i>, <9.5,1,i> 0.025 pigment {Black}} 
        #declare i = i + 1;
#end
    
#declare i = 0.5;
#while (i <= 9.5)
        cylinder {<i,1,0.5>, <i,1,9.5> 0.025 pigment {Black}} 
        #declare i = i + 1;
#end                            

sphere {<3.5,1,3.5>, 0.075 pigment {Black}}
sphere {<6.5,1,6.5>, 0.075 pigment {Black}}
sphere {<6.5,1,3.5>, 0.075 pigment {Black}}
sphere {<3.5,1,6.5>, 0.075 pigment {Black}}

