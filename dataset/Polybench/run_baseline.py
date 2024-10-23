import subprocess
import os
import extract_vivado_info as vivado_info
import shutil

# automatically obtain baseline results from Bambu built-in binding algorithms


bambu_coloring_algos = ["WEIGHTED_TS", "TS", "WEIGHTED_COLORING", "COLORING", "TTT_FAST", "BIPARTITE_MATCHING"]

dataset_path = "./raw"
pragma_file_path = "{}/pragma_file".format(dataset_path)

clock_period = 10
xilinx_part_number = "xcku060-3ffva1156-VVD"
channel_number = 4


def run_bambu_default():
    f = open("{}/bambu_default_bambu_run_status.csv".format(pragma_file_path), "w")
    f.write("Design Point,coloring algo,Bambu Success,error\n")
    f.close()
    
    for design_point_name in os.listdir(pragma_file_path):
        print("{}/{}".format(pragma_file_path, design_point_name))
        if not os.path.isdir("{}/{}".format(pragma_file_path, design_point_name)):
            continue
        design_name = design_point_name.split("_")[0]
        for coloring_algo in bambu_coloring_algos:
            bambu_run_path = "{}/{}/bambu_default_{}".format(pragma_file_path, design_point_name, coloring_algo)
            if os.path.exists(bambu_run_path):
                shutil.rmtree(bambu_run_path)
            print("made directory:", bambu_run_path)
            os.mkdir(bambu_run_path)
            
            docker_run_path = "/workspace/TPR-model/dataset/Polybench/raw/pragma_file/{}/bambu_default_{}".format(design_point_name, coloring_algo)
            result = subprocess.run("docker exec -w {} --user sqzhou bambu-option /opt/panda/bin/bambu ../{}.c --top-fname={} --print-dot --compiler=I386_CLANG13 -O2 --debug 4 --verbosity 4 > {}/stdout.txt 2> {}/stderr.txt --device={} --module-binding={}  --channels-number={} --clock-period={} --disable-function-proxy".format(docker_run_path, design_name, design_name, bambu_run_path, bambu_run_path, xilinx_part_number, coloring_algo, channel_number, clock_period), shell=True, capture_output=True, text=True)
            if result.returncode:
                print("################### Fail to run Bambu for design point {} #######################".format(design_point_name))
                print("Error: ", result.stderr)
                f = open("{}/bambu_default_bambu_run_status.csv".format(pragma_file_path), "a")
                f.write("{},{},{},{}\n".format(design_point_name, coloring_algo,"0", "Bambu exit with code {}".format(result.returncode)))
                f.close()
                return

def run_vivado_default():
    f = open("{}/bambu_default_vivado_run_status.csv".format(pragma_file_path), "w")
    f.write("Design Point, coloring_algo, CP_latency,dynamic_pwr,lut,success,error\n")
    f.close()


    for design_point_name in os.listdir(pragma_file_path):
        if not os.path.isdir("{}/{}".format(pragma_file_path, design_point_name)):
            continue
        design_name = design_point_name.split("_")[0]
        for coloring_algo in bambu_coloring_algos:
           
            bambu_run_path = "{}/{}/bambu_default_{}".format(pragma_file_path, design_point_name, coloring_algo)
            vivado_noop_tcl_path = "{}/{}".format(bambu_run_path, "HLS_output/Synthesis/vivado_flow/vivado_noop.tcl")
            vivado_tcl_path = "{}/{}".format(bambu_run_path, "HLS_output/Synthesis/vivado_flow/vivado.tcl")

            # remove optimization steps from the script
            lines = list()
            with open(vivado_tcl_path, "r") as f:
                lines = f.readlines()
            
            counter = 0
            with open(vivado_noop_tcl_path, "w+") as f:
                for line in lines:
                    if (counter > 0):
                        counter -= 1
                        continue
                    if line.find("# Optionally run optimization if there are timing violations after placement") != -1:
                        counter = 4
                        continue
                    elif line.find("# Optionally run optimization if there are timing violations after routing") != -1:
                        counter = 6
                        continue
                    else:
                        f.write(line)

            result = subprocess.run("vivado -mode batch -nojournal -nolog -notrace -source HLS_output/Synthesis/vivado_flow/vivado_noop.tcl", shell=True, cwd="{}".format(bambu_run_path), capture_output=True, text=True)
            if result.returncode:
                print("################### Fail to run vivado for design point {} #######################".format(design_point_name))
                print("Error: ", result.stderr)
                f = open("{}/bambu_default_vivado_run_status.csv".format(pragma_file_path), "a")
                f.write("{},{},{},{},{},{},{}\n".format(design_point_name, "N/A", "N/A", "N/A","0", "Vivado exit with code {}".format(result.returncode)))
                next

            # extract the performance information
            f = open("{}/bambu_default_vivado_run_status.csv".format(pragma_file_path), "a")
            f.write("{},{},".format(design_point_name, coloring_algo))
            error = vivado_info.extract_perf(clock_period, bambu_run_path, f)
            if error:
                if error == 1:
                    f.write("{},{},{},{},{}\n".format( "N/A", "N/A", "N/A","0", "Fail to extract performance information"))
                elif error == 2:
                    f.write("{},{},{},{},{}\n".format( "N/A", "N/A", "N/A","0", "Slack not met"))
                f.close()
                return

            f.write("\n")
            f.close()



# def run_vitis_hls():
    
#     for design_point_name in os.listdir(pragma_file_path):
#         # generate Vitis HLS script




#         vitis_run_path = 


run_bambu_default()
run_vivado_default()