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

#declare Eye = <0, 300, 0>;

camera {
  location Eye  
  right     x*image_width/image_height
  look_at   <0, 0, 0>
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
        [0.0 color Blue ]
        [1.0 color Black ]
      }
    }
}


// ----------------------------------------   


    prism
    {
        0, 5, 5,
        <0,0>, <115,20>, <125,50>, <115,80>, <0,100>
        
      
    pigment {

                 
// texture pigment {} attribute
// create a texture that lays an image's colors onto a surface
// image maps into X-Y plane from <0,0,0> to <1,1,0>
image_map {
  png "Shogi_osho2.png" // the file to read (iff/tga/gif/png/jpeg/tiff/sys)
  map_type 0        // 0=planar, 1=spherical, 2=cylindrical, 5=torus
  interpolate 2     // 0=none, 1=linear, 2=bilinear, 4=normalized distance
  // once           // for no repetitive tiling
  // [filter N V]   // N=all or color index # (0...N), V= value (0.0...1.0)
  // [transmit N V] // N=all or color index # (0...N), V= value (0.0...1.0)
  // [use_color | use_index]
} // image_map
                      
         rotate 90*x
         scale 100
         rotate 90*y
         scale 1.3
         translate -5*x
         translate -15*z
        }                 
}                  
                  
            