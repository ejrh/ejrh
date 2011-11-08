#include "fractal.h"

/** Type of fixed-point value. */
typedef long int FIXED;

/** Semi-scaling factor, which is applied to each multiplicand when
 * multiplying, so that the same precision is discarded on each, and the
 * product fits within range.
 *
 * 7723 was chosen to minimise artefacts around the boundary; otherwise one
 * occurs at position 2+0i.  A bit of calculation shows the sequence of
 * values:
 *   - b = 4; z = 0; c = 2
 *   - z = z^2 + c = 2
 *   - z = z^2 + c = 6 
 *   - z = z^2 + c = 38
 * where 6 > 4 of course, however the next z is already calculated at
 * that point.
 *
 * But z*FIXED_SCALE = 36*7724*7724 = 2147210244, which comes close to
 * overflowing the range of FIXED.  This value is used in the colour
 * interpolations.  If the value overflows, strange colours are used for that
 * pixel's calculation.  Depending on the excessiveness of FIXED_SEMI_SCALE,
 * the artefacts will be confined to small areas around the boundary or may
 * effectively overwhelm the whole fractal, giving an interesting "crop
 * circle" pattern.
 *
 * Part of the problem is the phase mismatch between z and z^2 in the cycle.
 * However this is a characteristic of all mfuncs and helps with smoothing
 * the interpolation.
 */
#define FIXED_SEMI_SCALE 7723

/** Scaling factor.  A fixed-point value X is represented by the integer X*FIXED_SCALE. */
#define FIXED_SCALE (FIXED_SEMI_SCALE*FIXED_SEMI_SCALE)

/** Convert a native value (e.g. a double) to a fixed-point one. */
#define TO_FIXED(x) ((long int) ((x) * FIXED_SCALE))

/** Multiply two fixed-point values.  Note that the same precision is discarded on each when multiplying. */
#define FIXED_TIMES(x, y) ((x) / FIXED_SEMI_SCALE) * ((y) / FIXED_SEMI_SCALE)

/** Convert a fixed-point value to a native one (e.g. a double). */
#define FROM_FIXED(x) ((x) / (double) FIXED_SCALE)


int mfunc_direct_int(double zx, double zy, double cx, double cy, int max_iterations, double *fx, double *fy)
{
    int i = 0;
    FIXED zr = TO_FIXED(zx), zi = TO_FIXED(zy);
    FIXED zr2 = 0, zi2 = 0;

    FIXED boundary = TO_FIXED(2.0*2.0);

    FIXED cx_fix = TO_FIXED(cx);
    FIXED cy_fix = TO_FIXED(cy);

    while (i < max_iterations && zr2 + zi2 < boundary)
    {
        FIXED t;

        zr2 = FIXED_TIMES(zr, zr);
        zi2 = FIXED_TIMES(zi, zi);
        t = FIXED_TIMES(zr, zi);
        zr = zr2 - zi2 + cx_fix;
        zi = t + t + cy_fix;

        i++;
    }
    *fx = FROM_FIXED(zr);
    *fy = FROM_FIXED(zi);

    if (zr2 + zi2 < boundary)
        return 0;

    return i;
}


void mfunc_loop_int(int max_iterations, ALLOCATE_SLOTS allocate_slots, PIXEL_SOURCE next_pixel, PIXEL_OUTPUT output_pixel, BATON *baton)
{
    allocate_slots(1, baton);

    while (1)
    {
        double zx, zy;
        double px, py;
        int k;
        double fx, fy;

        if (!next_pixel(0, &zx, &zy, &px, &py, baton))
            break;

        k = mfunc_direct_int(zx, zy, px, py, max_iterations, &fx, &fy);

        output_pixel(0, k, fx, fy, baton);
    }
}
