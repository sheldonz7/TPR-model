/* #####################################
  argv[1]: input_path
  argv[2]: node / edge
#####################################*/

#include <stdio.h>
#include <stdlib.h>
#include <iostream>
#include <string.h>
#include <math.h>
#include <memory>
#include <utility>
//#include "tracer.h"

using namespace std;

#define INV_NUM 8
#define INPUT_SCALE 1
#define M 64
#define N 64
#define DATA_TYPE float
#define SCALAR_VAL(x) x##f
#define SQRT_FUN(x) sqrtf(x)
#define EXP_FUN(x) expf(x)
#define POW_FUN(x,y) powf(x,y)

extern "C" void atax(DATA_TYPE A[M][N], DATA_TYPE x[N], DATA_TYPE y_out[N]);

void atax_verify(DATA_TYPE A[M][N], DATA_TYPE x[N], DATA_TYPE y_out[N]);

//########################################################
int main(int argc, char* argv[])
{
	if (argc < 2)
    {
        cout << "Arguements are not complete. (arg num = " << argc << " < 2)" << "\n";
        return 0;
    }

	//#################################
    srand(123); //hls test seed is 123
	int i, j, inv;
	char path[1024];
	float read_din;

	DATA_TYPE A[N][N];
	DATA_TYPE x[N];
	DATA_TYPE y_out[N];
	DATA_TYPE golden_A[N][N];
	DATA_TYPE golden_x[N];
    DATA_TYPE golden_y_out[N];
	
	sprintf(path, "%s/hd_%s.csv", argv[1], argv[2]);
//	rtlop_tracer::tracer_pt = std::move(build_tracer(path));
//	if(rtlop_tracer::tracer_pt == nullptr)
//	{
//		cout << "rtlop_tracer::tracer_pt = nullptr." << "\n";
//        return 0;
//	}

	cout << "checkpoint 1" << endl;
    //input stimulus generation, can only generate once
	FILE *wptr;
	sprintf(path, "%s/A_in.csv", argv[1]);
	wptr = fopen(path, "wb+");
    for(inv = 0; inv < INV_NUM; inv++){
        for (i = 0; i < N; i++){
		    for (j = 0; j < N; j++){
				golden_A[i][j] = ((float)rand() / (float)RAND_MAX) - 0.5 ;  //[-0.5,0.5], signed
				golden_A[i][j] *= INPUT_SCALE;
			    fprintf(wptr, "%.8f\n", golden_A[i][j]);
		    }
	    }
    }
	fclose(wptr);

	cout << "checkpoint 1" << endl;
	sprintf(path, "%s/x_in.csv", argv[1]);
	wptr = fopen(path, "wb+");
    for(inv = 0; inv < INV_NUM; inv++){
        for (i = 0; i < N; i++){
			golden_x[i] = ((float)rand() / (float)RAND_MAX) - 0.5 ;  //[-0.5,0.5], signed
			golden_x[i] *= INPUT_SCALE;
			fprintf(wptr, "%.8f\n", golden_x[i]);
	    }
    }
	fclose(wptr);

	FILE *fptr1, *fptr2, *wptr1;
	sprintf(path, "%s/A_in.csv", argv[1]);
	fptr1 = fopen(path, "r");
	sprintf(path, "%s/x_in.csv", argv[1]);
	fptr2 = fopen(path, "r");
	sprintf(path, "%s/golden_y_out.csv", argv[1]);
    wptr1 = fopen(path, "wb+");

    FILE *wptr2;
    sprintf(path, "%s/y_out.csv", argv[1]);
    wptr2 = fopen(path, "wb+");


	//#################################
    for(inv = 0; inv < INV_NUM; inv++){
        //==============================
		for(i = 0; i < N; i++){
		    for(j = 0; j < N; j++){
			    if(fscanf(fptr1, "%f", &read_din) > 0){
        	        golden_A[i][j] = read_din;
					A[i][j] = read_din;
				}
				else printf("A: error fscanf to the end!\n");
			}

			if(fscanf(fptr2, "%f", &read_din) > 0){
        	    golden_x[i] = read_din;
				x[i] = read_din;
			}
			else printf("x: error fscanf to the end!\n");
		}

		//==============================
		atax(A, x, y_out);
		atax_verify(golden_A, golden_x, golden_y_out);

		for (i = 0; i < N; i++){
			fprintf(wptr1, "%.4f\n", golden_y_out[i]);
			fprintf(wptr2, "%.4f\n", y_out[i]);
		}
	}

//	rtlop_tracer::tracer_pt->print();

	//#################################
    fclose(fptr1);
	fclose(fptr2);
    fclose(wptr1);
	return 0;
}

//###############################################
void atax_verify(DATA_TYPE A[M][N], DATA_TYPE x[N], DATA_TYPE y_out[N])
{
    int i, j;
    DATA_TYPE tmp[M];

    for (i = 0; i < N; i++)
        y_out[i] = 0;
    for (i = 0; i < M; i++)
    {
        tmp[i] = SCALAR_VAL(0.0);
        for (j = 0; j < N; j++)
	        tmp[i] = tmp[i] + A[i][j] * x[j];
        for (j = 0; j < N; j++)
	        y_out[j] = y_out[j] + A[i][j] * tmp[i];
    }
}

