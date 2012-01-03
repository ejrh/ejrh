__kernel void mfunc_kern( 
    uint n,
    uint w,
    __global float *gzx,
    __global float *gzy,
    __global float *gcx,
    __global float *gcy,
    __global unsigned short *vs,
    __global float *fx,
    __global float *fy
) 
{
    int i = get_global_id(0); 
    int j = i;
    while (j < w)
    {
        /* Do mfunc on the pixel at j. */
        float zr = gzx[j];
        float zi = gzy[j];
        float zr2 = 0.0f;
        float zi2 = 0.0f;
        float cr = gcx[j];
        float ci = gcy[j];
        int remaining = 1024;
        
        while (remaining && zr2 + zi2 < 4.0f)
        {
            float t;

            zr2 = zr*zr;
            zi2 = zi*zi;
            t = zr*zi;
            zr = zr2 - zi2 + cr;
            zi = 2.0f * t + ci;

            remaining--;
        }
        
        fx[j] = zr;
        fy[j] = zi;

        if (zr2 + zi2 < 4.0f)
            vs[j] = 0;
        else
            vs[j] = remaining;

        /* Next pixel. */
        j += n;
    }
}
