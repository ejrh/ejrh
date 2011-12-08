/*
    othello_board.pov
    Edmund Horner, 13 December 1999
*/

#include "colors.inc"
#include "stones.inc"

camera
{
    location <0,1000000,0>
    look_at <0,0,0>
    right x
    angle 0.000458
}    

#declare Tex = texture
{
    checker
        texture { T_Stone13 finish { phong 0.0 } }
        texture { T_Stone35 finish { phong 0.0 } }

    rotate 90*x
}

#declare Board = union
{
    box { <-4,0,-4>, <4,0.25,4> } 
    texture { Tex }
    //pigment { White }
/*    
    cone { <-4,0,-4>, 0.25, <-4,0.25,-4>, 0 }
    cone { <-4,0,4>, 0.25, <-4,0.25,4>, 0 }
    cone { <4,0,-4>, 0.25, <4,0.25,-4>, 0 }
    cone { <4,0,4>, 0.25, <4,0.25,4>, 0 }
    
    difference
    {
        prism
        {
            conic_sweep
            linear_spline
    
            0, 1
            5,
    
            <-4.5,-4.5>, <-4.5,4.5>,
            <4.5,4.5>, <4.5,-4.5>,
            <-4.5,-4.5>
    
            scale <1,-4.5,1>
            translate <0,4.5,0>
        }
        union
        {
            box { <-4,-0.5,-4>, <4,5,4> }
            
            box { <-4.5,-0.5,-4.5>, <-4,0.5,-4> }
            box { <-4.5,-0.5,4.5>, <-4,0.5,4> }
            box { <4.5,-0.5,-4.5>, <4,0.5,-4> }
            box { <4.5,-0.5,4.5>, <4,0.5,4> }
        }
        
        translate <0,-0.5,0>
    }
    
    texture { T_Stone18 finish { phong 0.0 } }
*/    
}

/*
difference
{
    prism
    {
        conic_sweep
        linear_spline

        0, 1
        5,

        <-4.5,-4.5>, <-4.5,4.5>,
        <4.5,4.5>, <4.5,-4.5>,
        <-4.5,-4.5>

        scale <1,-4.5,1>
        translate <0,4.5,0>
    }
    box
    {
        <-4.5,0.5,-4.5>, <4.5,5,4.5>
    }
    
    translate <4,-0.5,4>

    texture { Tex }
}
*/    

light_source
{
    <0,1000000,0>
    color White*1.75
}

object { Board }

// +W64 +H64 +KFI0 +KFF15 +KI0 +KF0.5
