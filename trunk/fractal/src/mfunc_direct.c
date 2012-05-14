#include "fractal.h"

typedef struct BATON
{
    int called;
    int max_iterations;
    double zx, zy;
    double cx, cy;
    double fx, fy;
    int remaining;
} BATON;


static void allocate_slots(int num_slots, BATON *baton)
{
}


static int next_pixel(int slot, int *max_iterations, double *zx, double *zy, double *cx, double *cy, BATON *baton)
{
    if (baton->called > 0)
        return 0;
    
    *max_iterations = baton->max_iterations;
    *zx = baton->zx;
    *zy = baton->zy;
    *cx = baton->cx;
    *cy = baton->cy;
    
    baton->called++;
}


static void output_pixel(int slot, int remaining, double fx, double fy, BATON *baton)
{
    baton->fx = fx;
    baton->fy = fy;
    baton->remaining = remaining;
}


int mfunc_direct(MFUNC mfunc, double zx, double zy, double cx, double cy, int max_iterations, double *fx, double *fy)
{
    BATON baton = {
        0,
        max_iterations,
        zx, zy,
        cx, cy,
    };
    mfunc(allocate_slots, next_pixel, output_pixel, &baton);
    *fx = baton.fx;
    *fy = baton.fy;
    
    return baton.remaining;
}
