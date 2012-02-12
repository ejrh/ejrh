#include "colors.inc"
#include "skies.inc"
#include "woods.inc"



#declare CAMERA = <9.0, 6.0, 6.0>;

camera {
    location  CAMERA
    look_at   <0, 0, 0>   // point center of view at this point <X,Y,Z>
    right x
}

light_source {
    CAMERA, White
}

//sky_sphere { S_Cloud5 }



// radiosity (global illumination) settings
#default{ finish{ ambient 0 diffuse 1 }} 

global_settings {
  radiosity {
    pretrace_start 0.08           // start pretrace at this size
    pretrace_end   0.04           // end pretrace at this size
    count 35                      // higher -> higher quality (1..1600) [35]

    nearest_count 5               // higher -> higher quality (1..10) [5]
    error_bound 1.8               // higher -> smoother, less accurate [1.8]
    recursion_limit 3             // how much interreflections are calculated (1..5+) [3]

    low_error_factor .5           // reduce error_bound during last pretrace step
    gray_threshold 0.0            // increase for weakening colors (0..1) [0]
    minimum_reuse 0.015           // reuse of old radiosity samples [0.015]
    brightness 1                  // brightness of radiosity effects (0..1) [1]

    adc_bailout 0.01/2
    //normal on                   // take surface normals into account [off]
    //media on                    // take media into account [off]
    //save_file "file_name"       // save radiosity data
    //load_file "file_name"       // load saved radiosity data
    //always_sample off           // turn sampling in final trace off [on]
    //max_sample 1.0              // maximum brightness of samples
  }
}



#declare MARGIN = 0.001;

#declare KERN = 0.05;

#declare PEG_THICKNESS = 0.25;

#macro Block(len)
    box { <KERN,KERN,0>, <len-KERN,1-KERN,1> }
    box { <KERN,0,KERN>, <len-KERN,1,1-KERN> }
    box { <0,KERN,KERN>, <len,1-KERN,1-KERN> }

    cylinder { <KERN,KERN,KERN>, <len-KERN,KERN,KERN>, KERN }
    cylinder { <KERN,1-KERN,KERN>, <len-KERN,1-KERN,KERN>, KERN }
    cylinder { <KERN,KERN,1-KERN>, <len-KERN,KERN,1-KERN>, KERN }
    cylinder { <KERN,1-KERN,1-KERN>, <len-KERN,1-KERN,1-KERN>, KERN }
    
    cylinder { <KERN,KERN,KERN>, <KERN,1-KERN,KERN>, KERN }
    cylinder { <len-KERN,KERN,KERN>, <len-KERN,1-KERN,KERN>, KERN }
    cylinder { <KERN,KERN,1-KERN>, <KERN,1-KERN,1-KERN>, KERN }
    cylinder { <len-KERN,KERN,1-KERN>, <len-KERN,1-KERN,1-KERN>, KERN }
    
    cylinder { <KERN,KERN,KERN>, <KERN,KERN,1-KERN>, KERN }
    cylinder { <len-KERN,KERN,KERN>, <len-KERN,KERN,1-KERN>, KERN }
    cylinder { <KERN,1-KERN,KERN>, <KERN,1-KERN,1-KERN>, KERN }
    cylinder { <len-KERN,1-KERN,KERN>, <len-KERN,1-KERN,1-KERN>, KERN }
    
    sphere { <KERN,KERN,KERN>, KERN }    
    sphere { <len-KERN,KERN,KERN>, KERN }    
    sphere { <KERN,1-KERN,KERN>, KERN }    
    sphere { <len-KERN,1-KERN,KERN>, KERN }    
    sphere { <KERN,KERN,1-KERN>, KERN }    
    sphere { <len-KERN,KERN,1-KERN>, KERN }    
    sphere { <KERN,1-KERN,1-KERN>, KERN }    
    sphere { <len-KERN,1-KERN,1-KERN>, KERN }    
#end

#declare Block1 = union
{
    Block(1)
}

#declare Block3 = union
{
    Block(3)
}

#declare Peg = union
{
    cylinder { <KERN, 0.5, 0.5>, <3-KERN, 0.5, 0.5>, PEG_THICKNESS/2 }
    cylinder { <0, 0.5, 0.5>, <3, 0.5, 0.5>, PEG_THICKNESS/2 - KERN }
    torus { PEG_THICKNESS/2 - KERN, KERN rotate 90*z translate <KERN, 0.5, 0.5> }
    torus { PEG_THICKNESS/2 - KERN, KERN rotate 90*z translate <3-KERN, 0.5, 0.5> }
}

#declare Hole = difference
{
    union {
        cylinder { <0, 0.5, 0.5>, <1, 0.5, 0.5>, PEG_THICKNESS/2 }
        cylinder { <-MARGIN, 0.5, 0.5>, <KERN, 0.5, 0.5>, PEG_THICKNESS/2+KERN }
        cylinder { <1-KERN, 0.5, 0.5>, <1+MARGIN, 0.5, 0.5>, PEG_THICKNESS/2+KERN }
    }
    union {
        torus { PEG_THICKNESS/2 + KERN, KERN rotate 90*z translate <KERN, 0.5, 0.5> }
        torus { PEG_THICKNESS/2 + KERN, KERN rotate 90*z translate <1-KERN, 0.5, 0.5> }
    }
}

#macro Piece(blocks, holes, pegs)
union {
    difference {
        object { blocks }
        object { holes }
    }
    object { pegs }
}
#end

#declare Piece1 = union {
Piece(
    union {
        object { Block1 translate <0,2,0> }
        object { Block3 rotate 90*z translate <2,0,0> }
        object { Block1 translate <2,2,0> }
    },                                            
    union {
        object { Hole rotate 90*y translate <1,2,1> }
        object { Hole rotate 90*y translate <1,0,1> }
        object { Hole translate <1,1,0> }
    },
    object { Peg rotate 90*y translate <1,2,3> }
)
    texture { T_Wood6  rotate x*90 }
}

#declare Piece2 = union {
Piece(
    union {
        object { Block1 }
        object { Block3 rotate 90*y translate <0,1,3> }
    },                                            
    union {
        object { Hole rotate 90*z translate <1,1,1> }
        object { Hole translate <0,1,0> }
        object { Hole translate <0,1,2> }
    },
    object { Peg rotate 90*z translate <1,0,1> }
)
    texture { T_Wood2  rotate x*90 }
}

#declare Piece3 = union {
Piece(
    union {
        object { Block1 translate <0,2,2>}
        object { Block3 translate <0,2,1> }
    },                                            
    union {
        object { Hole rotate 90*z translate <3,2,1> }
        object { Hole rotate 90*z translate <1,2,1> }
        object { Hole rotate 90*y translate <1,2,2> }
    },
    object { Peg rotate 90*z translate <3,0,1> }
)
    texture { T_Wood11  rotate x*90 }
}

#declare Piece4 = union {
Piece(
    union {
        object { Block1 translate <0,0,2>}
        object { Block3 rotate 90*z translate <2,0,2> }
    },                                            
    union {
        object { Hole rotate 90*y translate <1,0,3> }
        object { Hole rotate 90*y translate <1,2,3> }
        object { Hole translate <1,1,2> }
    },
    object { Peg rotate 90*y translate <1,0,3> }
)
    texture { T_Wood3  rotate x*90 }
}

#declare Piece5 = union {
Piece(
    union {
        object { Block1 translate <2,0,2>}
        object { Block3 translate <0,0,1> }
    },                                            
    union {
        object { Hole rotate 90*z translate <1,0,1> }
        object { Hole rotate 90*z translate <3,0,1> }
        object { Hole rotate 90*y translate <1,0,2> }
    },
    union { }
)
    texture { T_Wood7  rotate x*90 }
}


#declare Piece6 = union {
Piece(
    union {
        object { Block1 translate <2,0,0> }
        object { Block3 rotate 90*y translate <2,1,3> }
        object { Block1 translate <2,2,2> }
    },                                            
    union {
        object { Hole translate <2,1,2> }
        object { Hole translate <2,1,0> }
        object { Hole rotate 90*z translate <3,1,1> }
    },
    object { Peg translate <0,1,2> }
)
    texture { T_Wood4  rotate x*90 }
}


#declare Piece7 = union {
Piece(
    union { },                                            
    union { },
    object { Peg translate <0,1,0> }
)
    texture { T_Wood10 rotate x*90 }
}

union {
    cylinder { <0,0,0>, <3,0,0>, 0.01 pigment { White } }
    cylinder { <0,0,0>, <0,3,0>, 0.01 pigment { White } }
    cylinder { <0,0,0>, <0,0,3>, 0.01 pigment { White } }
    cylinder { <3,0,0>, <3,3,0>, 0.01 pigment { White } }
    cylinder { <3,0,0>, <3,0,3>, 0.01 pigment { White } }
    cylinder { <0,3,0>, <3,3,0>, 0.01 pigment { White } }
    cylinder { <0,3,0>, <0,3,3>, 0.01 pigment { White } }
    cylinder { <0,0,3>, <3,0,3>, 0.01 pigment { White } }
    cylinder { <0,0,3>, <0,3,3>, 0.01 pigment { White } }
    
    object { Piece1 translate <0,0,-5> }
    object { Piece2 translate <0,5,0> }
    object { Piece3 translate <0,5,4> }
    object { Piece4 translate <0,0,5> }
    object { Piece5 }
    object { Piece6 translate <5,0,0> }
    object { Piece7 translate <5,0,4> }
    
    translate -<3,3,3>    
}