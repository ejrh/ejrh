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

/* Adapted from http://content.gpwiki.org/index.php/SDL:Tutorials:Drawing_and_Filling_Circles */
void FillCircle(SDL_Surface *surface, int cx, int cy, int radius, Uint8 R, Uint8 G, Uint8 B)
{
    static const int BPP = 4;

    double r = (double) radius;
    Uint32 pixel = SDL_MapRGB(surface->format, R, G, B);
    double dy;

    for (dy = 1; dy <= r; dy += 1.0)
    {
        double dx = floor(sqrt((2.0 * r * dy) - (dy * dy)));
        int x = cx - dx;
        int x2 = cx + dx;
        
        if (cy - r + dy < 0 || cy + r - dy >= surface->h)
            continue;
    
        if (x < 0)
            x = 0;
        if (x2 >= surface->w)
            x2 = surface->w-1;

        Uint8 *target_pixel_a = (Uint8 *)surface->pixels + ((int)(cy + r - dy)) * surface->pitch + x * BPP;
        Uint8 *target_pixel_b = (Uint8 *)surface->pixels + ((int)(cy - r + dy)) * surface->pitch + x * BPP;
           
        for (; x <= x2; x++)
        {
            *(Uint32 *)target_pixel_a = pixel;
            *(Uint32 *)target_pixel_b = pixel;
            target_pixel_a += BPP;
            target_pixel_b += BPP;
        }
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
    s0->rgb[1] = 64;
    s0->rgb[2] = 64;
    add_star(g, s0);
    
    for (i = 0; i < num; i++)
    {
        STAR *s = create_star();
        double a = rand_float(0.0, 2.0*M_PI);
        double t = rand_float(0.04, 1.0);
        double r = sqrt(t);
        s->mass = 1E15;
        s->pos[0] = radius * r * cos(a);
        s->pos[1] = radius * r * sin(a);
        s->pos[2] = 0.0;
        s->vel[0] = cos(a + M_PI/2)*sqrt((GRAVITY*s0->mass)/(radius*r));
        s->vel[1] = sin(a + M_PI/2)*sqrt((GRAVITY*s0->mass)/(radius*r));
        s->vel[2] = 0.0;
        s->radius = rand_float(1.5E8, 2.5E8);
        s->rgb[0] = 255*(1-(r-0.2)/0.8);
        s->rgb[1] = 255*(1-(r-0.2)/0.8);
        s->rgb[2] = 255*(r-0.2)/0.8;
        add_star(g, s);
    }
    
    s1 = create_star();
    s1->mass = 1E21;
    s1->pos[0] = 0.0; //-1*radius;
    s1->pos[1] = -1.1*radius;
    s1->pos[2] = 0.0;
    s1->vel[0] = sqrt((GRAVITY*s0->mass)/(1.1*radius));
    s1->vel[1] = 0.0;
    s1->vel[2] = 0.0;
    s1->radius = 2.5E9;
    s1->rgb[0] = 64;
    s1->rgb[1] = 255;
    s1->rgb[2] = 64;
    add_star(g, s1);
    
    g->radius = radius;
    
    return g;
}


typedef struct {
    char *name;
    double radius1, radius2;
    double density;
    unsigned char rgb[3];
} RING_DEF;


static void add_ring_def(GALAXY *g, STAR *host, RING_DEF *ring_def)
{
    int i;
    
    double rad1 = ring_def->radius1;
    double rad2 = ring_def->radius2;
    
    double area = M_PI * (rad2*rad2 - rad1*rad1);
    int num = area * ring_def->density;
    
    for (i = 0; i < num; i++)
    {
        STAR *s = create_star();
        double a = rand_float(0.0, 2.0*M_PI);
        double t = rand_float((rad1/rad2)*(rad1/rad2), 1.0);
        double r = sqrt(t);
        s->name = ring_def->name;
        s->mass = 1;
        s->pos[0] = rad2 * r * cos(a) + host->pos[0];
        s->pos[1] = rad2 * r * sin(a) + host->pos[1];
        s->pos[2] = 0.0 + host->pos[2];
        s->vel[0] = cos(a + M_PI/2)*sqrt((GRAVITY*host->mass)/(rad2*r));
        s->vel[1] = sin(a + M_PI/2)*sqrt((GRAVITY*host->mass)/(rad2*r));
        s->vel[2] = 0.0;
        s->radius = 1;
        s->rgb[0] = ring_def->rgb[0];
        s->rgb[1] = ring_def->rgb[1];
        s->rgb[2] = ring_def->rgb[2];
        add_star(g, s);
    }
}


static GALAXY *create_saturn_system()
{
    int i;
    
    STAR data[] = {
        { "Saturn", { -4.132357567925691546406596899032592773437500000000e+04, 2.624547659633674775250256061553955078125000000000e+05, -1.285231449172821157844737172126770019531250000000e+05 }, { -1.321738287756913043935469431744422763586044311523e+00, -1.416760763277918055980109102165442891418933868408e-01, 2.052598978944562002624252272653393447399139404297e-01 }, 5.683190000000000101774786560000000000000000000000e+26, 5.8232e+07, { 128, 128, 160 }},
        { "Mimas", { 1.409567324753654003143310546875000000000000000000e+08, 9.574750819348834455013275146484375000000000000000e+07, -6.476332548601751029491424560546875000000000000000e+07 }, { -9.090947870659949330729432404041290283203125000000e+03, 1.027173239543619092728476971387863159179687500000e+04, -4.947910852276939294824842363595962524414062500000e+03 }, 3.750000000000000000000000000000000000000000000000e+19, 1.988000000000000000000000000000000000000000000000e+05 },
        { "Enceladus", { -1.346646423684050142765045166015625000000000000000e+08, 1.796145972869812250137329101562500000000000000000e+08, -8.109942360257817804813385009765625000000000000000e+07 }, { -1.032324324210918894095811992883682250976562500000e+04, -5.961955427766158209124114364385604858398437500000e+03, 4.122600403365349848172627389430999755859375000000e+03 }, 1.080500000000000000000000000000000000000000000000e+20, 2.523000000000000000000000000000000000000000000000e+05 },
        { "Tethys", { -1.202809942193891108036041259765625000000000000000e+08, -2.355210807313123941421508789062500000000000000000e+08, 1.294422097910651117563247680664062500000000000000e+08 }, { 1.033042136592517090321052819490432739257812500000e+04, -4.469986358296642720233649015426635742187500000000e+03, 1.455732841394304841742268763482570648193359375000e+03 }, 6.176000000000000000000000000000000000000000000000e+20, 5.363000000000000000000000000000000000000000000000e+05 },
        { "Dione", { 3.752415533152946829795837402343750000000000000000e+08, -1.907725122715552151203155517578125000000000000000e+07, -2.658361976810793951153755187988281250000000000000e+07 }, { 1.399203536120398894126992672681808471679687500000e+02, 8.893435881080291437683627009391784667968750000000e+03, -4.671459857063751769601367413997650146484375000000e+03 }, 1.095720000000000000000000000000000000000000000000e+21, 5.625000000000000000000000000000000000000000000000e+05 },
        { "Rhea", { -5.090854258520848155021667480468750000000000000000e+08, 1.371752332241027057170867919921875000000000000000e+08, -2.097442392270272225141525268554687500000000000000e+07 }, { -2.103002919667294008831959217786788940429687500000e+03, -7.212144879378406585601624101400375366210937500000e+03, 3.927866256236482968233758583664894104003906250000e+03 }, 2.309000000000000000000000000000000000000000000000e+21, 7.645000000000000000000000000000000000000000000000e+05 },
        { "Titan", { 1.859434001346341967582702636718750000000000000000e+08, -1.064588874583194017410278320312500000000000000000e+09, 5.311216787451697587966918945312500000000000000000e+08 }, { 5.537858652959903338341973721981048583984375000000e+03, 6.786660947596921005242620594799518585205078125000e+02, -8.981951755912039061513496562838554382324218750000e+02 }, 1.345530000000000039321600000000000000000000000000e+23, 2.575500000000000000000000000000000000000000000000e+06 },
        { "Hyperion", { 6.785438374341639280319213867187500000000000000000e+08, -1.291317671920835971832275390625000000000000000000e+09, 5.796193702368202209472656250000000000000000000000e+08 }, { 4.393440271937975921900942921638488769531250000000e+03, 1.449020498642966003899346105754375457763671875000e+03, -1.165545193389325049793114885687828063964843750000e+03 }, 1.080000000000000000000000000000000000000000000000e+19, 1.330000000000000000000000000000000000000000000000e+05 },
        { "Iapetus", { -3.924461946250433325767517089843750000000000000000e+08, -3.455198435774922847747802734375000000000000000000e+09, 8.878241850633521080017089843750000000000000000000e+08 }, { 3.166737144333492324221879243850708007812500000000e+03, -4.061090169803360367950517684221267700195312500000e+02, -5.421294024479105928548960946500301361083984375000e+02 }, 1.805900000000000131072000000000000000000000000000e+21, 7.345000000000000000000000000000000000000000000000e+05 },
        { "Phoebe", { 2.780865461109186172485351562500000000000000000000e+09, 1.493880003168178939819335937500000000000000000000e+10, -2.454778540448060929775238037109375000000000000000e+08 }, { 1.390986447228290899147395975887775421142578125000e+03, -2.922135715724139117810409516096115112304687500000e+02, -1.730736812407085949416796211153268814086914062500e+02 }, 8.289000000000000000000000000000000000000000000000e+18, 1.066000000000000000000000000000000000000000000000e+05 },
        { "Janus", { -8.882741858761414885520935058593750000000000000000e+07, 1.129720113725817054510116577148437500000000000000e+08, -5.089124220484183728694915771484375000000000000000e+07 }, { -1.279473757595856113766785711050033569335937500000e+04, -7.635022181859696502215228974819183349609375000000e+03, 5.199443488147669995669275522232055664062500000000e+03 }, 1.980000000000000256000000000000000000000000000000e+18, 9.700000000000000000000000000000000000000000000000e+04 },
        { "Epimetheus", { -1.144094740904777050018310546875000000000000000000e+08, -8.417041555799186229705810546875000000000000000000e+07, 5.413648228789784014225006103515625000000000000000e+07 }, { 1.023102246512844067183323204517364501953125000000e+04, -1.101710760262067924486473202705383300781250000000e+04, 4.790151587009932882210705429315567016601562500000e+03 }, 5.500000000000000000000000000000000000000000000000e+17, 6.900000000000000000000000000000000000000000000000e+04 },
        { "Helene", { 2.190343989449981749057769775390625000000000000000e+08, 2.636936249384640753269195556640625000000000000000e+08, -1.578090366871612966060638427734375000000000000000e+08 }, { -8.080475036329729846329428255558013916015625000000e+03, 5.551190657924244078458286821842193603515625000000e+03, -2.133160450929045055090682581067085266113281250000e+03 }, 2.546999999999999600000000000000000000000000000000e+16, 1.600000000000000000000000000000000000000000000000e+04 },
        { "Telesto", { 1.739717238220119178295135498046875000000000000000e+08, -2.156840066120337843894958496093750000000000000000e+08, 9.947270346360719203948974609375000000000000000000e+07 }, { 9.131268180468428909080103039741516113281250000000e+03, 5.681452255716719264455605298280715942382812500000e+03, -3.629192192785497809381922706961631774902343750000e+03 }, 7.194000000000000000000000000000000000000000000000e+15, 1.500000000000000000000000000000000000000000000000e+04 },
        { "Calypso", { -2.929719976859532594680786132812500000000000000000e+08, -3.291448960296314209699630737304687500000000000000e+06, 2.999466980508165806531906127929687500000000000000e+07 }, { 6.312362027612933843556675128638744354248046875000e+02, -1.020389892853268065664451569318771362304687500000e+04, 4.948068373860418432741425931453704833984375000000e+03 }, 3.597000000000000000000000000000000000000000000000e+15, 1.500000000000000000000000000000000000000000000000e+04 },
        { "Atlas", { 1.391056293670377135276794433593750000000000000000e+07, 1.209508829335785955190658569335937500000000000000e+08, -6.472022818123295158147811889648437500000000000000e+07 }, { -1.649957884983301119063980877399444580078125000000e+04, 2.172627664406864823831710964441299438476562500000e+03, 4.588688375335610203364922199398279190063476562500e+02 }, 1.000000000000000000000000000000000000000000000000e+00, 1.850000000000000000000000000000000000000000000000e+04 },
        { "Prometheus", { 5.353496336651065200567245483398437500000000000000e+07, 1.120030236102474033832550048828125000000000000000e+08, -6.388402671387151628732681274414062500000000000000e+07 }, { -1.521588240917128860019147396087646484375000000000e+04, 6.228799761104840399639215320348739624023437500000e+03, -1.788210678313586868171114474534988403320312500000e+03 }, 1.400000000000000000000000000000000000000000000000e+17, 7.400000000000000000000000000000000000000000000000e+04 },
        { "Pandora", { -1.404407905464166998863220214843750000000000000000e+08, -8.017425164469866082072257995605468750000000000000e+06, 1.773353752788202092051506042480468750000000000000e+07 }, { 1.731366738497179994737962260842323303222656250000e+03, -1.449948364607551957305986434221267700195312500000e+04, 7.443358163609785151493269950151443481445312500000e+03 }, 1.300000000000000000000000000000000000000000000000e+17, 5.500000000000000000000000000000000000000000000000e+04 },
        { "Pan", { 1.206685956374875009059906005859375000000000000000e+08, -5.438901646032060682773590087890625000000000000000e+07, 1.681682699183699861168861389160156250000000000000e+07 }, { 7.089121339400583565293345600366592407226562500000e+03, 1.328871821561579963599797338247299194335937500000e+04, -7.649730140355948606156744062900543212890625000000e+03 }, 1.000000000000000000000000000000000000000000000000e+00, 1.000000000000000000000000000000000000000000000000e+04 },
        { "Ymir", { 1.342993003179216003417968750000000000000000000000e+10, -2.385115037917504882812500000000000000000000000000e+10, -3.260212723224080085754394531250000000000000000000e+09 }, { -9.877002033609976479056058451533317565917968750000e+02, -2.929979620771466670703375712037086486816406250000e+02, 6.135986057349362710056084324605762958526611328125e+01 }, 1.000000000000000000000000000000000000000000000000e+00, 1.000000000000000000000000000000000000000000000000e+00 },
        { "Paaliaq", { -6.153243437034428119659423828125000000000000000000e+08, 1.226394505416218948364257812500000000000000000000e+10, 1.217254859470880889892578125000000000000000000000e+10 }, { -1.136397738417278105771401897072792053222656250000e+03, -3.386275122946221927122678607702255249023437500000e+02, -6.572132212430821027737692929804325103759765625000e+02 }, 1.000000000000000000000000000000000000000000000000e+00, 1.000000000000000000000000000000000000000000000000e+00 },
    };
    
    GALAXY *g = create_galaxy();
    
    for (i = 0; i < sizeof(data)/sizeof(STAR); i++)
    {
        STAR *s = create_star();
        *s = data[i];
        if (s->rgb[0] == 0 && s->rgb[1] == 0 && s->rgb[2] == 0)
        {
            s->rgb[0] = 255;
            s->rgb[1] = 255;
            s->rgb[2] = 255;
        }
        add_star(g, s);
    }
    
    RING_DEF rings[] = {
        { "D Ring", 6.69E+7, 7.451E+7, 1E-13, { 216, 127, 127 } },
        { "C Ring", 7.4658E+7, 9.2E+7, 1E-13, { 216, 216, 127 } },
        { "B Ring", 9.2E+7, 1.1758E+8, 1E-13, { 127, 216, 127 } },
        //{ "Cassini Division", 1.1758E+8, 1.2217E+8, 0.0, { 0, 0, 0 } },
        { "A Ring", 1.2217E+8, 1.36775E+8, 1E-13, { 127, 216, 216 } },
        //{ "Roche Division", 1.36775E+8, 1.3938E+8, 0.0, { 0, 0, 0 } },
        { "F Ring", 1.4018E+8, 1.49E+8, 1E-13, { 127, 127, 216 } },
        { "Janus/Epimetheus Ring", 1.49E+8, 1.54E+8 , 1E-13, { 216, 127, 216 } },
        /*{ "G Ring", 1.66E+8, 1.75E+8 },
        { "Methone Ring Arc", 1.9423E+8 },
        { "Anthe Ring Arc", 1.97665E+8 },
        { "Pallene Ring", 2.11E+8, 2.135E+8 },
        { "E Ring", 1.8E+8, 4.8E+8 },
        { "Phoebe Ring", 4E+9, 1.3E+10 }, */
    };

    for (i = 0; i < sizeof(rings)/sizeof(RING_DEF); i++)
    {
        RING_DEF *ring = &rings[i];
        if (ring->radius2 == 0.0)
            continue;
        add_ring_def(g, g->stars[0], ring);
    }
    
    g->radius = 4E+9;
    
    g->gravity_well = g->stars[0];
    
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
    if (rad > 5.0)
    {
        FillCircle(display, px, py, (int) (rad/2), star->rgb[0], star->rgb[1], star->rgb[2]);
    }
    else if (rad >= 0.5)
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
    //g = create_square_galaxy(2.5E11, 1000);
    g = create_saturn_system();
    
    #define SECONDS_PER_YEAR 365.242199*24*3600
    
    num_frames = 10000;
    calcs_per_frame = 1;
    time_per_frame = SECONDS_PER_YEAR/1000000;
    frames_per_image = 1;
    
    scale = 1;
    
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
            SDL_SaveBMP(display, fn);
        }
        
        if (i > 50 && i <= 100) {
            g->stars[1]->mass *= 1.318256738556407;
            g->stars[1]->radius *= 1.06;
            //g->stars[1]->rgb[0];
            g->stars[1]->rgb[1] -= 5;
            g->stars[1]->rgb[2] -= 5;
        }
    }
    //fclose(f);
    
    destroy_galaxy(g);
    
    TTF_Quit();
        
    SDL_Quit();

    return 0;
}
