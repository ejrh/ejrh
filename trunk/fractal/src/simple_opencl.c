#include "fractal.h"

#include <stdlib.h>
#define _USE_MATH_DEFINES
#include <math.h>

#ifdef ENABLE_SIMPLE_OPENCL

#define typeof
#include <stdcl.h>


typedef struct DRAWING
{
    WINDOW *window;
    FRACTAL *fractal;
    GET_POINT *get_point;
    int width, height;
    int i;
} DRAWING;


DRAWING *simple_opencl_create(WINDOW *window, FRACTAL *fractal, GET_POINT get_point, MFUNC *mfunc)
{
    DRAWING *drawing = malloc(sizeof(DRAWING));
    if (!drawing)
    {
        fprintf(stderr, "%s:%d: Can't create drawing!", __FILE__, __LINE__);
        return NULL;
    }
    drawing->window = window;
    drawing->fractal = fractal;
    drawing->get_point = get_point;
    drawing->width = window->width;
    drawing->height = window->height;
    drawing->i = 0;
    return drawing;
}


static has_inited = 0;


static CLCONTEXT* cp;
static unsigned int devnum = 0;
static void *clh = NULL;
static cl_kernel krn = NULL;
static cl_float *zx, *zy, *cx, *cy;
static cl_ushort *vs;
static cl_float *fx, *fy;


static int opencl_setup(cl_uint workgroup_size, cl_uint work_size)
{
    if (!has_inited)
    {
        stdcl_init();
        has_inited = 1;
    }

    if (stdgpu)
    {
        cp = stdgpu;
    }
    else
    {
        cp = stdcpu;
    }

    if (!clh)
        clh = clopen(cp, "mfunc.cl", CLLD_NOW);
    if (!clh)
    {
        status = "OPENCL:NO FILE";
        return 0;
    }

    if (clh && krn)
    {
        return 1;
    }

    krn = clsym(cp, clh, "mfunc_kern", 0);
    if (!krn)
    {
        status = "OPENCL:NO KERNEL";
        return 0;
    }

    /* allocate OpenCL device-sharable memory */
    zx = clmalloc(cp, work_size*sizeof(cl_float), 0);
    zy = clmalloc(cp, work_size*sizeof(cl_float), 0);
    cx = clmalloc(cp, work_size*sizeof(cl_float), 0);
    cy = clmalloc(cp, work_size*sizeof(cl_float), 0);

    vs = clmalloc(cp, work_size*sizeof(cl_ushort), 0);
    fx = clmalloc(cp, work_size*sizeof(cl_float), 0);
    fy = clmalloc(cp, work_size*sizeof(cl_float), 0);

    return 1;
}


#define ROWS_PER_WORKLOAD 25


static void opencl_shutdown(void)
{
    clfree(zx);
    clfree(zy);
    clfree(cx);
    clfree(cy);

    clfree(vs);
    clfree(fx);
    clfree(fy);

    clclose(cp, clh);
}


void simple_opencl_update(DRAWING *drawing)
{
    cl_uint workgroup_size = 64;
    cl_uint work_size = drawing->width*ROWS_PER_WORKLOAD;

    int j;

    clndrange_t ndr = clndrange_init1d(0, workgroup_size, workgroup_size);

    if (drawing->i >= drawing->height)
    {
        status = "FINISHED";
        return;
    }

    if (drawing->i + work_size/drawing->width >= drawing->height)
        work_size = (drawing->height - drawing->i)*drawing->width;

    if (!opencl_setup(workgroup_size, work_size))
    {
        return;
    }

    for (j = 0; j < work_size; j++)
    {
        double temps[4];
        int px = j % drawing->width;
        int py = drawing->i + j / drawing->width;

        drawing->get_point(drawing->fractal, px, py, &temps[0], &temps[1], &temps[2], &temps[3]);
        zx[j] = temps[0];
        zy[j] = temps[1];
        cx[j] = temps[2];
        cy[j] = temps[3];
    }

    /* non-blocking sync vectors a and b to device memory (copy to GPU)*/
    clmsync(cp, devnum, zx, CL_MEM_DEVICE|CL_EVENT_NOWAIT);
    clmsync(cp, devnum, zy, CL_MEM_DEVICE|CL_EVENT_NOWAIT);
    clmsync(cp, devnum, cx, CL_MEM_DEVICE|CL_EVENT_NOWAIT);
    clmsync(cp, devnum, cy, CL_MEM_DEVICE|CL_EVENT_NOWAIT);

    /* non-blocking fork of the OpenCL kernel to execute on the GPU */
    clarg_set(cp, krn, 0, (cl_uint) workgroup_size);
    clarg_set(cp, krn, 1, (cl_uint) work_size);
    
    clarg_set_global(cp, krn, 2, (cl_float *)(intptr_t)(zx));
    clarg_set_global(cp, krn, 3, (cl_float *)(intptr_t)(zy));
    clarg_set_global(cp, krn, 4, (cl_float *)(intptr_t)(cx));
    clarg_set_global(cp, krn, 5, (cl_float *)(intptr_t)(cy));

    clarg_set_global(cp, krn, 6, (cl_ushort *)(intptr_t)(vs));
    clarg_set_global(cp, krn, 7, (cl_float *)(intptr_t)(fx));
    clarg_set_global(cp, krn, 8, (cl_float *)(intptr_t)(fy));

    clarg_set(cp, krn, 9, (cl_uint) drawing->window->depth);
    
    clfork(cp, devnum, krn, &ndr, CL_EVENT_NOWAIT);

    /* non-blocking sync vector c to host memory (copy back to host) */
    //N.B. devnum was hardcoded as 0 in the example, looks like a bug to report to brown deer!
    clmsync(cp, devnum, vs, CL_MEM_HOST|CL_EVENT_NOWAIT);
    clmsync(cp, devnum, fx, CL_MEM_HOST|CL_EVENT_NOWAIT);
    clmsync(cp, devnum, fy, CL_MEM_HOST|CL_EVENT_NOWAIT);

    /* force execution of operations in command queue (non-blocking call) */
    clflush(cp, devnum, 0);

    /* block on completion of operations in command queue */
    clwait(cp, devnum, CL_ALL_EVENT);

    for (j = 0; j < work_size; j++)
    {
        int px = j % drawing->width;
        int py = drawing->i + j / drawing->width;
        int k;

        if (vs[j] == 0)
        {
            k = 0;
        }
        else
        {
            k = drawing->window->depth - vs[j];
        }
    
        set_pixel(drawing->window, px, py, k, fx[j], fy[j]);
    }

    drawing->i += work_size/drawing->width;
    status = "OPENCL'ING";
}


void simple_opencl_destroy(DRAWING *drawing)
{
    free(drawing);
}

#endif
