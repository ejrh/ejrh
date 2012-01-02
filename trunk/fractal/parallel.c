#include "fractal.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define _USE_MATH_DEFINES
#include <math.h>

#ifdef WIN32
    extern int omp_get_num_procs(void);
#else
    #include <omp.h>
#endif


typedef struct DRAWING
{
    WINDOW *window;
    FRACTAL *fractal;
    MFUNC *mfunc;
    GET_POINT *get_point;
    int num_slots;
    int width, height;
    
    int num_frames;
    int num_jobs;
    int num_pixels;
    int pixels_per_job;
    
    int frame;
    int frame_offset;
    int frame_step;
} DRAWING;


typedef struct BATON
{
    DRAWING *drawing;
    int i, j;
    int done;
    int *x_slots;
    int *y_slots;
} BATON;


/**
 * Find the greatest integer n where 2^n <= x.
 *
 * I'm sure there are cheaper ways of doing it (just find the position of
 * the highest bit) !  But it's not called very often.
 *
 * @param x A positive integer.
 * @return n Such that 2^n <= x.
 */
static int powerof2(int x)
{
    int n = 0;
    while (x > 1)
    {
        n += 1;
        x >>= 1;
    }
    return n;
}


/**
 * Permuate the elements of the set from [0, n) into a low-discrepancy sequence.
 * Algorithm courtesy of Per, see http://stackoverflow.com/questions/8176743/recursive-interlacing-permutation.
 *
 * @param n Size of the sequence.
 * @param i Index to get.
 * @return The element at position i.
 */
static int rev(int n, int i)
{
    int j = 0;
    while (n >= 2)
    {
        int m = i & 1;
        if (m != 0)
            j += (n + 1) >> 1;
        n = (n + 1 - m) >> 1;
        i >>= 1;
    }
    return j;
}

static void next_frame(DRAWING *drawing)
{
    drawing->frame = rev(drawing->num_frames, drawing->frame_step++);
}


DRAWING *parallel_create(WINDOW *window, FRACTAL *fractal, GET_POINT get_point, MFUNC *mfunc)
{
    DRAWING *drawing = malloc(sizeof(DRAWING));
    if (!drawing)
    {
        fprintf(stderr, "%s:%d: Can't create drawing!", __FILE__, __LINE__);
        return NULL;
    }
    
    drawing->window = window;
    drawing->fractal = fractal;
    drawing->mfunc = mfunc;
    drawing->get_point = get_point;
    drawing->width = window->width;
    drawing->height = window->height;
    
    drawing->num_jobs = omp_get_num_procs();
    drawing->num_pixels = drawing->width * drawing->height;
    drawing->num_frames = 43;
    drawing->pixels_per_job = (int) ceil((double) drawing->num_pixels / drawing->num_frames / drawing->num_jobs);
    
    drawing->frame_offset = 0;   //TODO use last frame?
    drawing->frame_step = 0;
    next_frame(drawing);
    
    return drawing;
}


static void parallel_allocate_slots(int num_slots, BATON *baton)
{
    baton->x_slots = malloc(sizeof(int) * num_slots);
    baton->y_slots = malloc(sizeof(int) * num_slots);
    if (!baton->x_slots || !baton->y_slots)
    {
        fprintf(stderr, "Can't create slots!");
        exit(1);
    }
}


int parallel_next_pixel(int slot, int *max_iterations, double *zx, double *zy, double *cx, double *cy, BATON *baton)
{
    int a;

    if (baton->i >= baton->drawing->pixels_per_job)
        return 0;

    a = (baton->i * baton->drawing->num_jobs + baton->j) * baton->drawing->num_frames + ((baton->drawing->frame + baton->drawing->frame_offset) % baton->drawing->num_frames);
    if (a >= baton->drawing->num_pixels)
        return 0;
    
    baton->x_slots[slot] = a % baton->drawing->width;
    baton->y_slots[slot] = a / baton->drawing->width;

    baton->drawing->get_point(baton->drawing->fractal, baton->x_slots[slot], baton->y_slots[slot], zx, zy, cx, cy);

    baton->i++;
    
    baton->done++;
    
    *max_iterations = baton->drawing->window->depth;

    return 1;
}


void parallel_output_pixel(int slot, int remaining, double fx, double fy, BATON *baton)
{
    DRAWING *drawing = baton->drawing;
    int k;
    
    if (remaining == 0)
    {
        k = 0;
    }
    else
    {
        k = drawing->window->depth - remaining;
    }
    
    set_pixel(drawing->window, baton->x_slots[slot], baton->y_slots[slot], k, fx, fy);
}


void parallel_update(DRAWING *drawing)
{
    int j;
    int old_pixels_done = pixels_done;
    int thread_done[16];
    
    memset(thread_done, 0, sizeof(thread_done));

    //fprintf(stderr, "num_frames %d, frame_step %d, frame %d\n", drawing->num_frames, drawing->frame_step, drawing->frame);
    if (drawing->frame_step > drawing->num_frames)
        return;

    #pragma omp parallel for
    for (j = 0; j < drawing->num_jobs; j++)
    {
        BATON baton;
        baton.drawing = drawing;
        baton.j = j;
        baton.done = 0;
        baton.i = 0;    
        drawing->mfunc(parallel_allocate_slots, parallel_next_pixel, parallel_output_pixel, &baton);
        thread_done[j] = baton.done;
    }
    pixels_done = old_pixels_done;
    for (j = 0; j < drawing->num_jobs; j++)
        pixels_done += thread_done[j];

    next_frame(drawing);
}


void parallel_destroy(DRAWING *drawing)
{
    free(drawing);
}
