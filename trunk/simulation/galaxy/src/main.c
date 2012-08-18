#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#define _USE_MATH_DEFINES
#include <math.h>

#include <SDL.h>
#include <SDL_ttf.h>

#include "galaxy.h"
#include "calculate.h"
#include "bh.h"


#ifdef WIN32
    #define snprintf sprintf_s
    #define FONT_PATH "c:/windows/fonts/arial.ttf"
#else
    #define FONT_PATH "/usr/share/fonts/truetype/msttcorefonts/arial.ttf"
#endif

#define WIDTH 512
#define HEIGHT 512

static SDL_Surface *display = NULL;

#define GRAVITY 6.67428E-11

void DrawPixel(SDL_Surface *screen, Uint8 R, Uint8 G, Uint8 B, int x, int y)
{
    Uint32 color = SDL_MapRGB(screen->format, R, G, B);

    switch (screen->format->BytesPerPixel) {
        case 1: { /* Assuming 8-bpp */
            Uint8 *bufp;

            bufp = (Uint8 *)screen->pixels + y*screen->pitch + x;
            *bufp = color;
        }
        break;

        case 2: { /* Probably 15-bpp or 16-bpp */
            Uint16 *bufp;

            bufp = (Uint16 *)screen->pixels + y*screen->pitch/2 + x;
            *bufp = color;
        }
        break;

        case 3: { /* Slow 24-bpp mode, usually not used */
            Uint8 *bufp;

            bufp = (Uint8 *)screen->pixels + y*screen->pitch + x;
            *(bufp+screen->format->Rshift/8) = R;
            *(bufp+screen->format->Gshift/8) = G;
            *(bufp+screen->format->Bshift/8) = B;
        }
        break;

        case 4: { /* Probably 32-bpp */
            Uint32 *bufp;

            bufp = (Uint32 *)screen->pixels + y*screen->pitch/4 + x;
            *bufp = color;
        }
        break;
    }
}

void ReadPixel(SDL_Surface *screen, Uint8 *R, Uint8 *G, Uint8 *B, int x, int y)
{
    Uint8 A;

    switch (screen->format->BytesPerPixel) {
        case 1: { /* Assuming 8-bpp */
            Uint8 *bufp;

            bufp = (Uint8 *)screen->pixels + y*screen->pitch + x;
            SDL_GetRGBA(*bufp, screen->format, R, G, B, &A);
        }
        break;

        case 2: { /* Probably 15-bpp or 16-bpp */
            Uint16 *bufp;

            bufp = (Uint16 *)screen->pixels + y*screen->pitch/2 + x;
            SDL_GetRGBA(*bufp, screen->format, R, G, B, &A);
        }
        break;

        case 3: { /* Slow 24-bpp mode, usually not used */
            Uint8 *bufp;

            bufp = (Uint8 *)screen->pixels + y*screen->pitch + x;
            *R = *(bufp+screen->format->Rshift/8);
            *G = *(bufp+screen->format->Gshift/8);
            *B = *(bufp+screen->format->Bshift/8);
        }
        break;

        case 4: { /* Probably 32-bpp */
            Uint32 *bufp;

            bufp = (Uint32 *)screen->pixels + y*screen->pitch/4 + x;
            SDL_GetRGBA(*bufp, screen->format, R, G, B, &A);
        }
        break;
    }
}

void calculate_frame(GALAXY *g, double timestep)
{
    VECTOR *forces;
    //CALCULATOR *c = calculate.naive_calculator();
    CALCULATOR *c = bh_calculator();
    c->gravity = GRAVITY;

    forces = malloc(sizeof(VECTOR) * g->num);
    
    memset(forces, 0, sizeof(VECTOR) * g->num);
    
    c->calculate(c, g, forces);
    
    calculate.apply_forces(g, forces, timestep);
    c->destroy(c);

    free(forces);
}

/*
5
2.50e11
0.000e00 0.000e00 0.000e00 0.000e00 1.989e30 sun.gif
5.790e10 0.000e00 0.000e00 4.790e04 3.302e23 mercury.gif
1.082e11 0.000e00 0.000e00 3.500e04 4.869e24 venus.gif
1.496e11 0.000e00 0.000e00 2.980e04 5.974e24 earth.gif
2.279e11 0.000e00 0.000e00 2.410e04 6.419e23 mars.gif
*/
static GALAXY *create_solar_system()
{
    int i;
    
    STAR data[] = {
        { "Sol", { 0.000e00, 0.000e00 }, { 0.000e00, 0.000e00 }, 1.989e30 },
        { "Mercury", { 5.790e10, 0.000e00 }, { 0.000e00, 4.790e04 }, 3.302e23 },
        { "Venus", { 1.082e11, 0.000e00 }, { 0.000e00, 3.500e04 }, 4.869e24 },
        { "Earth", { 1.496e11, 0.000e00 }, { 0.000e00, 2.980e04 }, 5.974e24 },
        { "Mars", { 2.279e11, 0.000e00 }, { 0.000e00, 2.410e04 }, 6.419e23 },
    };
    
    GALAXY *g = create_galaxy();
    
    for (i = 0; i < sizeof(data)/sizeof(STAR); i++)
    {
        STAR *s = create_star();
        *s = data[i];
        add_star(g, s);
    }
    
    g->radius = 2.5E11;
    
    g->gravity_well = g->stars[0];
    
    return g;
}


static GALAXY *create_solar_system_2()
{
    int i;
    
    STAR data[] = {
        { "Sol", { -6.185971372636502E+08,  7.053427694221177E+07,  2.338221077370279E+06 }, {  2.007312008802111E+00, -1.050997984989123E+01, -2.364368911319387E-02 },  1.98910E+30, 6.960E+08, { 255,255,0 } },
        { "Mercury", {  1.284273743509015E+10, -6.652395322379692E+10, -6.673910195541095E+09 }, {  3.798138838776709E+04,  1.213699750496125E+04, -2.492355276317566E+03 },  3.30200E+23, 1.0, { 255,255,255 } },
        { "Venus", { -1.007411018134462E+11, -3.996141895535587E+10,  5.232264116797000E+09 }, {  1.276627109059595E+04, -3.268876952904768E+04, -1.184370543035742E+03 },  4.86850E+24, 1.0, { 0,255,0 } },
        { "Earth", { -1.132094265214519E+11,  9.548289411980477E+10, -3.369847273975611E+05 }, { -1.973662621796277E+04, -2.285956152047924E+04,  1.083328102204462E+00 },  5.97360E+24, 1.0, { 0,0,255 } },
        { "Moon", { -1.128423333235537E+11,  9.564765604362176E+10,  3.290122818410397E+07 }, { -2.015398219667083E+04, -2.198526562956678E+04, -3.467219883073369E+01 }, 734.9E+20, 1.73753E+06, { 255,255,255 } },
        { "Mars", {  1.537029064731368E+11, -1.385220649320696E+11, -6.691185912844039E+09 }, {  1.710943707271193E+04,  2.009092334165851E+04,  1.110321260857638E+00 },  6.41850E+23, 1.0, { 255,64,64 } },
        { "Phobos", {  1.536959115224088E+11, -1.385277512615332E+11, -6.688139217549749E+09 }, {  1.821267511026613E+04,  1.840628710864996E+04, -6.153766657189825E+02 },  1.08E+20, 1.11E+04, { 255,0,255 } },
        { "Deimos", {  1.537228570552382E+11, -1.385137585369931E+11, -6.700297482944936E+09 }, {  1.672568339339906E+04,  2.134989237437802E+04,  3.082438185365639E+02, },  1.80E+20, 6.0E+03, { 128,128,128 } },
        { "Jupiter", {  7.256525012200071E+11,  1.426602644693087E+11, -1.684232596585476E+10 }, { -2.678138016678334E+03,  1.344328751121466E+04,  4.061932828932413E+00 },  1.89813E+27, 1.0, { 255,255,255 } },
        { "Io", { 7.260689038329406E+11,  1.425983883181777E+11, -1.683880033370411E+10 }, { -6.782917579410297E+01,  3.060258721665560E+04,  6.585420109319209E+02 }, 8.933E+22, 1.8213E+06, { 255,255,255 } },
        { "Europa", {  7.261610834953812E+11,  1.422150272943564E+11, -1.685660497491473E+10 }, {  6.257529127494619E+03,  2.373721511394373E+04,  5.010529147104954E+02 },  4.797E+22, 1.565E+06, { 255,255,255 } },
        { "Ganymede", {  7.247560266685690E+11,  1.420761913792518E+11, -1.687564494540769E+10 }, { 3.288648174409432E+03,  4.350553200754702E+03, -2.624165752182233E+02 }, 1.482E+20 ,2.634E+06, { 255,255,255 } },
        { "Callisto", {  7.252252733813124E+11,  1.444960450288815E+11, -1.678917403061590E+10 }, { -1.066810523255353E+04,  1.164941341168039E+04, -1.601159653020332E+02 }, 1.076E+20, 2.403E+06, { 255,255,255 } },
        { "Saturn", { -1.403963658870086E+12, -2.965957930218173E+11,  6.102786096438922E+10 }, {  1.476330028656222E+03, -9.471913636904839E+03,  1.061583054386461E+02 },  5.68319E+26, 1.0, { 255,255,255 } },
        { "Uranus", {  3.004292714643044E+12, -2.462729937283149E+09, -3.893155014788460E+10 }, { -4.413452596504940E-05,  6.492447331148721E+03,  2.473039486975681E+01 },  8.68103E+25, 1.0, { 255,255,255 } },
        { "Neptune", {  3.814204544285126E+12, -2.367252636733651E+12, -3.915194618599451E+10 }, {  2.829641479452969E+03,  4.650563551022861E+03, -1.602996079114389E+02 },  1.02410E+26, 1.0, { 255,255,255 } },
        { "Pluto", {  4.356646254808469E+11, -4.748243320024902E+12,  3.820704462138057E+11 }, {  5.520933631414783E+03, -5.703864314295275E+02, -1.555800005493817E+03 },  1.31400E+22, 1.0, { 255,255,255 } }
    };
    
    GALAXY *g = create_galaxy();
    
    for (i = 0; i < sizeof(data)/sizeof(STAR); i++)
    {
        STAR *s = create_star();
        *s = data[i];
        add_star(g, s);
    }
    
    //blow_up_star(g, g->stars[9], 10, 10.0);
    
    g->radius = 7E12;
    
    g->gravity_well = g->stars[0];
    
    return g;
}


static GALAXY *create_disc_galaxy(double radius, int num)
{
    int i;
    
    GALAXY *g = create_galaxy();
    STAR *s0, *s1;

    s0 = create_star();
    s0->mass = 1E24;
    s0->pos[0] = 0.0;
    s0->pos[1] = 0.0;
    s0->pos[2] = 0.0;
    s0->vel[0] = 0.0;
    s0->vel[1] = 0.0;
    s0->vel[2] = 0.0;
    s0->radius = 2.5E9;
    s0->rgb[0] = 255;
    s0->rgb[1] = 127;
    s0->rgb[2] = 0;
    add_star(g, s0);
    
    for (i = 0; i < num; i++)
    {
        STAR *s = create_star();
        double a = rand_float(0.0, 2.0*M_PI);
        double t = rand_float(0.0, 1.0);
        double r = sqrt(t);
        s->mass = 1; //1E24;
        s->pos[0] = radius * r * cos(a);
        s->pos[1] = radius * r * sin(a);
        s->pos[2] = 0.0;
        s->vel[0] = cos(a + M_PI/2)*sqrt((GRAVITY*s0->mass)/(radius*r));
        s->vel[1] = sin(a + M_PI/2)*sqrt((GRAVITY*s0->mass)/(radius*r));
        s->vel[2] = 0.0;
        s->radius = rand_float(1.5E8, 2.5E8);
        s->rgb[0] = 255*r;
        s->rgb[1] = 255*(1-r);
        s->rgb[2] = rand() % 256;
        add_star(g, s);
    }
    
    s1 = create_star();
    s1->mass = 1E24;
    s1->pos[0] = 0;
    s1->pos[1] = -1.2*radius;
    s1->pos[2] = 0.0;
    s1->vel[0] = sqrt((GRAVITY*s0->mass)/(1.2*radius));
    s1->vel[1] = 0.0;
    s1->vel[2] = 0.0;
    s1->radius = 2.5E9;
    s1->rgb[0] = 0;
    s1->rgb[1] = 127;
    s1->rgb[2] = 255;
    add_star(g, s1);
    
    g->radius = radius;
    
    return g;
}

static GALAXY *create_square_galaxy(double radius, int num)
{
    int i;
    
    GALAXY *g = create_galaxy();
    STAR *s0, *s1;

    for (i = 0; i < num; i++)
    {
        STAR *s = create_star();
        s->mass = 1E18;
        s->pos[0] = rand_float(-radius, radius);
        s->pos[1] = rand_float(-radius, radius);
        s->pos[2] = 0.0;
        s->vel[0] = 0.0;
        s->vel[1] = 0.0;
        s->vel[2] = 0.0;
        s->radius = rand_float(1.5E8, 2.5E8);
        s->rgb[0] = 128+127*(s->pos[0]/radius);
        s->rgb[1] = 128+127*(s->pos[1]/radius);
        s->rgb[2] = rand() % 256;
        add_star(g, s);
    }
    
    g->radius = radius;
    
    return g;
}

static void put_pixel(unsigned char *buffer, int px, int py, int width, int height, unsigned char *rgb)
{
    if (px >= 0 && px < width && py >= 0 && py < height)
    {
        /*buffer[3*(py*width + px)] = rgb[0];
        buffer[3*(py*width + px)+1] = rgb[1];
        buffer[3*(py*width + px)+2] = rgb[2];*/
        DrawPixel(display, rgb[0], rgb[1], rgb[2], px, py);
    }
}

static void draw_star(unsigned char *buffer, int px, int py, int width, int height, double zoom, STAR *star)
{
    double rad = star->radius * zoom * width;
    
    put_pixel(buffer, px, py, width, height, star->rgb);
    if (rad >= 0.5)
    {
        put_pixel(buffer, px, py-1, width, height, star->rgb);
        put_pixel(buffer, px-1, py, width, height, star->rgb);
        put_pixel(buffer, px+1, py, width, height, star->rgb);
        put_pixel(buffer, px, py+1, width, height, star->rgb);
    }
}

int draw_image(GALAXY *g, double scale)
{
    int i;
    int width = WIDTH;
    int height = HEIGHT;
    int num_drawn;
    
    double zoom = scale/g->radius;
    double focus_x = 0.0;
    double focus_y = 0.0;
    
    /*for (i = 0; i < 3*width*height; i++)
    {
        if (buffer[i] > 100)
            buffer[i]--;
    }*/
    for (i = 0; i < height; i++)
    {
        int j;
        for (j = 0; j < width; j++)
        {
            unsigned char rgb[3];
            ReadPixel(display, &rgb[0], &rgb[1], &rgb[2], j, i);
            rgb[0] *= 0.9;
            rgb[1] *= 0.9;
            rgb[2] *= 0.9;
            DrawPixel(display, rgb[0], rgb[1], rgb[2], j, i);
        }
    }
    
    num_drawn = 0;
    
    for (i = 0; i < g->num; i++)
    {
        STAR *s = g->stars[i];
        int px, py;

        if (s->radius == 0.0)
            continue;

        px = (s->pos[0] - focus_x) * zoom * width/2 + width/2;
        py = (s->pos[1] - focus_y) * zoom * height/2 + height/2;
        draw_star( /* buffer */ NULL, px, py, width, height, zoom, s);
        
        if (px >= 0 && px < width && py >= 0 && py < height)
            num_drawn++;
    }
    
    return num_drawn;
}

void error(void)
{
    fprintf(stderr, "SDL error: %s\n", SDL_GetError());
        exit(1);
}

int main(int argc, char *argv[])
{
    int i;
    FILE *f;
    TTF_Font *font;
    SDL_Event evt;

    GALAXY *g;
    int num_frames;
    int calcs_per_frame;
    double time_per_frame;
    int frames_per_image;
    
    double scale;
    
    if(SDL_Init(SDL_INIT_VIDEO) < 0) {
        error();
    }

    if (TTF_Init() < 0) {
        error();
    }

    font = TTF_OpenFont(FONT_PATH, 16);
    if (!font)
        error();

    display = SDL_SetVideoMode(WIDTH, HEIGHT, 32, SDL_HWSURFACE | SDL_DOUBLEBUF);
    if(display == NULL) {
        error();
    }
        
    //GALAXY *g = create_solar_system_2();
    //g = create_disc_galaxy(2.5E11, 5000);
    g = create_square_galaxy(2.5E11, 1000);
    
    #define SECONDS_PER_YEAR 365.242199*24*3600
    
    num_frames = 250000;
    calcs_per_frame = 1;
    time_per_frame = SECONDS_PER_YEAR*2;
    frames_per_image = 1;
    
    scale = 0.1;
    
    update_galaxy(g);
    recentre_galaxy(g);
    draw_image(g, scale);
    SDL_UpdateRect(display, 0, 0, WIDTH, HEIGHT);
    
    //f = fopen("stars.dat", "wb");
    for (i = 0; i < num_frames; i++)
    {
        int j;
        int num_drawn;
        
        while (SDL_PollEvent(&evt))
        {
            if (evt.type == SDL_QUIT)
                i = num_frames;
            else if (evt.type == SDL_KEYDOWN && evt.key.keysym.sym == SDLK_ESCAPE)
                i = num_frames;
            else if (evt.type == SDL_KEYDOWN && evt.key.keysym.sym == SDLK_z)
            {
                if (evt.key.keysym.mod & KMOD_SHIFT)
                    scale *= M_SQRT1_2;
                else
                    scale /= M_SQRT1_2;
            }
        }
        
        for (j = 0; j < calcs_per_frame; j++)
            calculate_frame(g, time_per_frame/calcs_per_frame);
        update_galaxy(g);
        //printf("%f %f %f\n", g->barycentre[0]/time_per_frame, g->barycentre[1]/time_per_frame, g->barycentre[2]/time_per_frame);
        recentre_galaxy(g);
        //fprintf(stderr, "Barycentre %f,%f,%f; mass %f; movement %f\n", g->barycentre[0], g->barycentre[1], g->barycentre[2], g->mass, (bcx - g->barycentre[1])/100/10000);
        
        //dump_galaxy(g, f);
        num_drawn = draw_image(g, scale);
        
        {
            SDL_Color white = { 255, 255, 255 };
            SDL_Color black = { 0, 0, 0 };
            char buffer[1000];
            SDL_Surface *txt;
            SDL_Rect dest = { 0, 0 };

            snprintf(buffer, sizeof(buffer), "frame %d, time %f, visible %d    ", i, g->time, num_drawn);
            txt = TTF_RenderText(font, buffer, white, black);
            dest.w = txt->w;
            dest.h = txt->h;

            SDL_BlitSurface(txt, NULL, display, &dest);
            SDL_FreeSurface(txt);
        }
        
        SDL_UpdateRect(display, 0, 0, WIDTH, HEIGHT);
        
        if (i % frames_per_image == 0)
        {
            char fn[1000];
            snprintf(fn, sizeof(fn), "img/out%05d.bmp", i / frames_per_image);
            //SDL_SaveBMP(display, fn);
        }
    }
    //fclose(f);
    
    destroy_galaxy(g);
    
    TTF_Quit();
        
    SDL_Quit();

    return 0;
}
