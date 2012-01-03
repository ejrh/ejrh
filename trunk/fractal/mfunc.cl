__kernel void mfunc_kern( 
    /* Work size: number of threads and total number of pixels. */
    uint n,
    uint w,
    
    /* Input coordinates. */
    __global float *gzx,
    __global float *gzy,
    __global float *gcx,
    __global float *gcy,
    
    /* Outputs. */
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
        
        /* Move coordinates into local variables. */
        float zr = gzx[j];
        float zi = gzy[j];
        float zr2 = 0.0f;
        float zi2 = 0.0f;
        float cr = gcx[j];
        float ci = gcy[j];
        
        /* Remaining depth to search up to. */
        int remaining = 1024;
        
        /* Iterate until depth exhausted or point escapes set. */
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
        
        /* Store final point. */
        fx[j] = zr;
        fy[j] = zi;

        /* Store depth at point, depending on whether it has escaped. */
        if (zr2 + zi2 < 4.0f)
            vs[j] = 0;
        else
            vs[j] = remaining;

        /* Next pixel. */
        j += n;
    }
}
