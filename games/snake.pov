#include "colors.inc"
#include "math.inc"
#include "transforms.inc"

#declare Camera_0 = camera {/*ultra_wide_angle*/ angle 75      // front view
                            location  <0.0 , 1.0 ,-3.0>
                            right     x*image_width/image_height
                            look_at   <0.0 , 1.0 , 0.0>}
#declare Camera_1 = camera {/*ultra_wide_angle*/ angle 90   // diagonal view
                            location  <2.0 , 2.5 ,-3.0>
                            right     x*image_width/image_height
                            look_at   <0.0 , 1.0 , 0.0>}
#declare Camera_2 = camera {/*ultra_wide_angle*/ angle 90 // right side view
                            location  <3.0 , 1.0 , 0.0>
                            right     x*image_width/image_height
                            look_at   <0.0 , 1.0 , 0.0>}
#declare Camera_3 = camera {/*ultra_wide_angle*/ angle 90        // top view
                            location  <0.0 , 3.0 ,-0.001>
                            right     x*image_width/image_height
                            look_at   <0.0 , 1.0 , 0.0>}
camera{Camera_1}

light_source{<1500,2500,-2500> color White}

#declare KERN_RAD = 0.0333;

#macro Slab(w, h)
union {
    #local p1 = <KERN_RAD,KERN_RAD,KERN_RAD>;
    #local p2 = <KERN_RAD,h-KERN_RAD,KERN_RAD>;
    #local p3 = <w-KERN_RAD,KERN_RAD,KERN_RAD>;
    #local p4 = <w-KERN_RAD,h-KERN_RAD,KERN_RAD>;
    
    cylinder { p1, p2, KERN_RAD }
    cylinder { p3, p4, KERN_RAD }
    cylinder { p1, p3, KERN_RAD }
    cylinder { p2, p4, KERN_RAD }
    
    sphere { p1, KERN_RAD }
    sphere { p2, KERN_RAD }
    sphere { p3, KERN_RAD }
    sphere { p4, KERN_RAD }
    
    box { <KERN_RAD,KERN_RAD,0>, <w-KERN_RAD,h-KERN_RAD,KERN_RAD*2> }
}
#end

#declare WIRE_RAD = 0.05;
#declare HOLE_RAD = 0.075;

#macro SegmentPanel()
difference {
    union {
        Slab(1-xprime-3*KERN_RAD, 1-KERN_RAD*4)
    }
    
    union {
        cylinder { <(1-KERN_RAD*4)/2, (1-KERN_RAD*4)/2, -0.1>, <(1-KERN_RAD*4)/2, (1-KERN_RAD*4)/2, KERN_RAD+0.1>, HOLE_RAD }
    }
        
    translate <KERN_RAD*2,KERN_RAD*2,0>
}
#end

#macro SegmentFace()
object {
    #local w = sqrt(2) - 2*xprime - 2*KERN_RAD;
    Slab(w, 1-KERN_RAD*4)
    translate <xprime+KERN_RAD,KERN_RAD*2,0>
}
#end

#macro Segment(Tex, Tex2)                                                          
union {
    #local xprime = KERN_RAD/tand(22.5);
    #local yprime = sqrt((xprime*xprime)/2);
    
    //prism { linear_spline 0, 1, 3, <0,0>, <1, 0>, <0, 1> texture { Tex } }
    
    union {
        #local p0a = <KERN_RAD, KERN_RAD, KERN_RAD>;
        #local p0b = <KERN_RAD, 1-KERN_RAD, KERN_RAD>;
        #local p1a = <1-xprime, KERN_RAD, KERN_RAD>;
        #local p1b = <1-xprime, 1-KERN_RAD, KERN_RAD>;
        #local p2a = <KERN_RAD, KERN_RAD, 1-xprime>;
        #local p2b = <KERN_RAD, 1-KERN_RAD, 1-xprime>;
    
        cylinder { p0a, p0b, KERN_RAD }
        cylinder { p1a, p1b, KERN_RAD }
        cylinder { p2a, p2b, KERN_RAD }
        
        cylinder { p0a, p1a, KERN_RAD }
        cylinder { p1a, p2a, KERN_RAD }
        cylinder { p2a, p0a, KERN_RAD }
            
        cylinder { p0b, p1b, KERN_RAD }
        cylinder { p1b, p2b, KERN_RAD }
        cylinder { p2b, p0b, KERN_RAD }
            
        sphere { p0a, KERN_RAD }
        sphere { p1a, KERN_RAD }
        sphere { p2a, KERN_RAD }
        
        sphere { p0b, KERN_RAD }
        sphere { p1b, KERN_RAD }
        sphere { p2b, KERN_RAD }
        
        //prism { linear_spline 0, KERN_RAD*2, 3 <KERN_RAD,KERN_RAD>, <1-xprime,KERN_RAD>, <KERN_RAD,1-xprime> }
        //prism { linear_spline 1-KERN_RAD*2, 1, 3 <KERN_RAD,KERN_RAD>, <1-xprime,KERN_RAD>, <KERN_RAD,1-xprime> }
        
        texture { Tex }
    }
    
    union {
        //SegmentPanel()
        //object { SegmentPanel() rotate 270*y scale -1*x }
        
        //object { SegmentFace() rotate 135*y scale <-1,0,0> translate <0,0,1> }
        
        texture { Tex2 }
    }
    
    /*union {
        prism {
            linear_spline KERN_RAD, 1-KERN_RAD, 9
            <0,KERN_RAD>, <KERN_RAD,KERN_RAD>, <KERN_RAD,0>, 
            <1-xprime,0>, <1-xprime,KERN_RAD>, <1-yprime,yprime>,
            <yprime,1-yprime>, <KERN_RAD,1-xprime>, <0, 1-xprime>
        }
        
        texture { Tex2 }
    }*/
    
    translate <-0.5, -0.5, 0>
}
#end


#macro Chain(Pieces, Transforms, Pos)
    #if (Pos < dimension_size(Pieces,1))
        #local piece = Pieces[Pos];
        #local xform = Transforms[Pos];
        object { piece }
        union {
            Chain(Pieces, Transforms, Pos+1)
            transform { xform }
        }
    #end
#end

#macro Sweep(Transforms, Rad)
    #local num_transforms = dimension_size(Transforms,1);
    
    sphere_sweep {
        cubic_spline
        num_transforms+3,
        
        #local xf = transform { translate <0,0,0> };
        #local p = <0,0,0>;
        p, Rad,
        p, Rad
        #for (i, 0, num_transforms-1)
            #local xf = transform { Transforms[i] xf }
            #local p = vtransform(<0,0,0>, xf);
            , p, Rad
        #end
        , p, Rad
    }
#end

#declare p1 = cylinder { <0,0,0>, <1,0,0>, 0.1 pigment { Red } }
#declare p2 = cylinder { <0,0,0>, <1,0,0>, 0.1 pigment { Green } }
#declare p3 = cylinder { <0,0,0>, <1,0,0>, 0.1 pigment { Blue } }

#declare t1 = transform { rotate 45*y translate <1,0,0> }
#declare t2 = transform { rotate 45*z translate <1,0,0> }
#declare t3 = transform { translate <1,0,0> }

//Chain(array[3] { p1, p2, p3 }, array[3] { t1, t2, t3 }, 0)


#macro Snake(Pieces, Turns)
    #local num_pieces = dimension_size(Pieces, 1);
    #local num_turns = dimension_size(Turns, 1);
    
    #local ActualPieces = array[num_turns];
    #local Transforms = array[num_turns];
    
    #for (i, 0, num_turns-1)
        #local ActualPieces[i] = Pieces[mod(i, num_pieces)];
        #local Transforms[i] = transform { rotate Turns[i]*z rotate 270*y translate <-0.5, 0, 0.5> }
    #end
    
    Chain(ActualPieces, Transforms, 0)
    
    object { Sweep(Transforms, WIRE_RAD) pigment { Green } }
#end

#macro InterpolateTurns(T1, T2)
    #local num = dimension_size(T1, 1);
    #local ts = array[num];
    
    #local p = int(clock*num);
    #local q = clock*num - int(clock*num);
    
    #debug "p = "
    #debug str(p, 0, 5)
    #debug ", q = "
    #debug str(q, 0, 5)
    #debug "\n"
    
    #for (i, 0, num-1)
        #if (i < p)
            #local ts[i] = T2[i];
        #elseif (i = p)
            #local ts[i] = T2[i]*q + T1[i]*(1 - q);
        #else
            #local ts[i] = T1[i];
        #end
    #end
    ts
#end

//#declare InitialTurns = array[24] { 180, 180, 180, 180, 180,  90, 180, 180, 180, 270, 180, 180, 180, 270, 180, 180, 180,  90, 180, 180, 180, 270,  90,   0 };
#declare InitialTurns = array[24] { 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180,   0 };
#declare SnakeTurns   = array[24] { 270, 270,  90, 270,  90,  90, 270,  90, 270, 270,  90,  90, 270, 270,  90, 270,  90,  90, 270 , 90, 270, 270,  90,   0 };

#declare Turns = InterpolateTurns(InitialTurns, SnakeTurns);

#declare p1 = Segment(pigment { White }, pigment { Blue });
#declare p2 = Segment(pigment { Blue }, pigment { White });

#declare SnakePieces = array[2] { p1, p2 };
Snake(SnakePieces, Turns)
