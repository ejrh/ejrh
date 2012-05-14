#include "fractal.h"

#define _USE_MATH_DEFINES
#include <math.h>


void mfunc_loop(ALLOCATE_SLOTS allocate_slots, PIXEL_SOURCE next_pixel, PIXEL_OUTPUT output_pixel, BATON *baton)
{
    int i = 0;
    double cx, cy;
    double zr, zi;
    double zr2 = 2.0, zi2 = 2.0;
    int done = 0;
    
    allocate_slots(1, baton);
    
    while (1)
    {
        double t;
        
        /* Check if it's time to output a pixel and/or start a new one. */
        if (i <= 0 || zr2 + zi2 > 2.0*2.0)
        {
            if (done != 0)
            {
                if (zr2 + zi2 <= 2.0*2.0)
                    output_pixel(0, 0, zr, zi, baton);
                else
                    output_pixel(0, i, zr, zi, baton);
            }
            
            if (!next_pixel(0, &i, &zr, &zi, &cx, &cy, baton))
                break;
            
            done += 1;
        }
    
        /* Do some work on the current pixel. */
        zr2 = zr*zr;
        zi2 = zi*zi;
        t = zr*zi;
        zr = zr2 - zi2 + cx;
        zi = t + t + cy;

        i--;
    }
}


void mfunc_loop_float(ALLOCATE_SLOTS allocate_slots, PIXEL_SOURCE next_pixel, PIXEL_OUTPUT output_pixel, BATON *baton)
{
    int i = 0;
    float cr, ci;
    float zr, zi;
    float zr2 = 2.0, zi2 = 2.0;
    int done = 0;
    
    allocate_slots(1, baton);
    
    while (1)
    {
        float t;
        
        /* Check if it's time to output a pixel and/or start a new one. */
        if (i <= 0 || zr2 + zi2 > 2.0*2.0)
        {
            double zx, zy, cx, cy;
            
            if (done != 0)
            {
                if (zr2 + zi2 <= 2.0*2.0)
                    output_pixel(0, 0, zr, zi, baton);
                else
                    output_pixel(0, i, zr, zi, baton);
            }
            
            if (!next_pixel(0, &i, &zx, &zy, &cx, &cy, baton))
                break;
            
            zr = zx;
            zi = zy;
            cr = cx;
            ci = cy;
            
            done += 1;
        }
    
        /* Do some work on the current pixel. */
        zr2 = zr*zr;
        zi2 = zi*zi;
        t = zr*zi;
        zr = zr2 - zi2 + cr;
        zi = t + t + ci;

        i--;
    }
}
