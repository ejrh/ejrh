#include "fractal.h"

#include <stdio.h>
#include <stdlib.h>
#define _USE_MATH_DEFINES
#include <math.h>


#define PIXEL_COST 50
#define QUOTA_SIZE 500000

#define ITERATION_DEPTH_START 4
#define ITERATION_DEPTH_FACTOR M_SQRT2


typedef struct DRAWING
{
    WINDOW *window;
    FRACTAL *fractal;
    MFUNC *mfunc;
    GET_POINT *get_point;
    int *x_slots;
    int *y_slots;
    int *done;
    double *point_x;
    double *point_y;
    int width, height;
    int i, j;
    int quota;
    int iteration_depth;
    int last_depth;
} DRAWING;


DRAWING *iterative_create(WINDOW *window, FRACTAL *fractal, GET_POINT get_point, MFUNC *mfunc)
{
    int i;
    
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
    drawing->i = 0;
    drawing->j = 0;
    drawing->x_slots = NULL;
    drawing->y_slots = NULL;
    drawing->done = malloc(drawing->width * drawing->height * sizeof(int));
    if (!drawing->done)
    {
        fprintf(stderr, "Can't create done map!");
        free(drawing);
        return NULL;
    }
    drawing->point_x = malloc(drawing->width * drawing->height * sizeof(double));
    drawing->point_y = malloc(drawing->width * drawing->height * sizeof(double));
    if (!drawing->point_x || !drawing->point_y)
    {
        fprintf(stderr, "Can't create last point map!");
        free(drawing->point_x);
        free(drawing->point_y);
        free(drawing->done);
        free(drawing);
        return NULL;
    }
    drawing->iteration_depth = ITERATION_DEPTH_START;
    drawing->last_depth = 0;
    
    for (i = 0; i < drawing->width * drawing->height; i++)
    {
        drawing->point_x[i] = 0.0;
        drawing->point_y[i] = 0.0;
        drawing->done[i] = 0;
    }
    
    return drawing;
}


static void iterative_allocate_slots(int num_slots, BATON *baton)
{
    DRAWING *drawing = (DRAWING *) baton;
    
    drawing->x_slots = malloc(sizeof(int) * num_slots);
    drawing->y_slots = malloc(sizeof(int) * num_slots);
    if (!drawing->x_slots || !drawing->y_slots)
    {
        fprintf(stderr, "Can't create slots!");
        exit(1);
    }
}


static int iterative_next_pixel(int slot, int *max_iterations, double *zx, double *zy, double *cx, double *cy, BATON *baton)
{
    DRAWING *drawing = (DRAWING *) baton;
    
    if (drawing->quota <= 0)
        return 0;
    
restart:
    if (drawing->i >= drawing->height)
    {
        if (drawing->iteration_depth >= drawing->window->depth)
            return 0;
        
        drawing->i = 0;
        drawing->j = 0;
        drawing->last_depth = drawing->iteration_depth;
        drawing->iteration_depth = (drawing->iteration_depth * ITERATION_DEPTH_FACTOR) + 1;        
        if (drawing->iteration_depth > drawing->window->depth)
            drawing->iteration_depth = drawing->window->depth;
    }
    
    drawing->get_point(drawing->fractal, drawing->j, drawing->i, zx, zy, cx, cy);

    drawing->x_slots[slot] = drawing->j;
    drawing->y_slots[slot] = drawing->i;
    
    drawing->j++;

    if (drawing->j >= drawing->width)
    {
        drawing->j = 0;
        drawing->i++;
    }

    if (drawing->done[drawing->y_slots[slot]*drawing->width + drawing->x_slots[slot]])
    {
        goto restart;
    }
    
    *max_iterations = drawing->iteration_depth - drawing->last_depth;
    *zx = drawing->point_x[drawing->y_slots[slot]*drawing->width + drawing->x_slots[slot]];
    *zy = drawing->point_y[drawing->y_slots[slot]*drawing->width + drawing->x_slots[slot]];
    
    return 1;
}


static void iterative_output_pixel(int slot, int remaining, double fx, double fy, BATON *baton)
{
    DRAWING *drawing = (DRAWING *) baton;
    int k;
    
    if (remaining == 0)
    {
        k = 0;
    }
    else
    {
        k = drawing->iteration_depth - remaining;
    }
    
    if (k == 0 && drawing->iteration_depth < drawing->window->depth)
    {
        drawing->point_x[drawing->y_slots[slot] * drawing->width + drawing->x_slots[slot]] = fx;
        drawing->point_y[drawing->y_slots[slot] * drawing->width + drawing->x_slots[slot]] = fy;
    }
    else
    {
        drawing->done[drawing->y_slots[slot]*drawing->width + drawing->x_slots[slot]] = 1;
        set_pixel(drawing->window, drawing->x_slots[slot], drawing->y_slots[slot], k, fx, fy);
    }
    
    drawing->quota -= ((k == 0) ? drawing->iteration_depth : k) + PIXEL_COST;
}


void iterative_update(DRAWING *drawing)
{
    drawing->quota = QUOTA_SIZE;

    drawing->mfunc(iterative_allocate_slots, iterative_next_pixel, iterative_output_pixel, (BATON *) drawing);
    if (drawing->iteration_depth >= drawing->window->depth)
        status = "DONE";
    else
        status = "ITERATING";
}


void iterative_destroy(DRAWING *drawing)
{
    free(drawing->x_slots);
    free(drawing->y_slots);
    free(drawing->done);
    free(drawing->point_x);
    free(drawing->point_y);
    free(drawing);
}
