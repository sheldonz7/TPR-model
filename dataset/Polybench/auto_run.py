import subprocess
import os
import sys
import io
import shutil
from pathlib import Path
import extract_vivado_info as vivado_info
import time
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Lock, Process
import fcntl

#dataset_path = "/ugra/wlxing/workspace/TPR-model/dataset"
#############################  part1: generate HLS strategy  ###############################################


# Bambu parameter
# Device/part number
#xilinx_part_number = "xc7z020-1clg484-VVD"
xilinx_part_number = "xcku060-3ffva1156-VVD"

# memory
channel_number = 4

# clock
clock_period = 10

start_anew = True

dataset_path = "./raw"

graph_path = "./raw/graphs"

# path
runtime_solution_path = "{}/runtime_solutions".format(dataset_path)
pragma_file_path = "{}/pragma_file".format(dataset_path)



project_parallel_run = 8

# generate HLS strategy
print("Generating HLS strategy for all Polybench designs")

def split_i(list, pos, m):
    result = []

    line = list[pos]
    pla = line.find(':') + 1
    str1 = line[:pla]+'\n'
    str2 = line[pla+1:]
    blank_t = str1.count('\t') 
    blank_b = str1.count(' ')

    list[pos] = str1
    if str1.find('\t') != -1:
        for i in range(blank_t):
            str2 = '\t'+str2
    if str1.find(' ') != -1:
        for i in range(blank_b):
            str2 = ' '+str2
    list.insert(pos+1, str2)

    return list, blank_t, blank_b

###########
# creating pragma marked file 
def gen(anno, kernel_name, prj_name):
    dataset_gen_folder=Path('./pragma_file')
    if dataset_gen_folder.exists():
        pass
    else:  
        os.mkdir(dataset_gen_folder)

    dataset_gen_file_folder=Path('./pragma_file/{}_{}'.format(kernel_name, prj_name, 777))
    #creating the directory saving pragma file
    if dataset_gen_file_folder.exists():
        pass
    else:  
        os.mkdir(dataset_gen_file_folder)

    #creating the file with pragma
    data_file = open('./pragma_file/{}_{}/{}.c'.format(kernel_name, prj_name,kernel_name), 'w+')
    a_list = anno.keys()
    pos = 0
    
    with open("./{}/hls/src/{}.c".format(kernel_name, kernel_name), "r") as f:
        list = f.readlines()
    for i in list:
        i = str(str(i).replace('\n', ' '))
        i = str(i.replace(':', ''))
        i = i.strip()
        for m in a_list:
            i = str(i)
            if i.find(m) != -1:
                next_pos = pos+1
                list, blank_t, blank_b = split_i(list, pos, m)
                s = '#pragma unroll({})\n'.format(anno[m])
                if list[pos].find('\t') != -1:
                    for i in range(blank_t):
                        s = '\t'+s
                if list[pos].find(' ') != -1:
                    for i in range(blank_b):
                        s = ' '+s
                list.insert(next_pos, s)
                
                
        pos = pos+1        
    #writing pragma into data_file
    for i in list:
        data_file.write('{}'.format(i))

    data_file.close()

##############
#generating lp_d using the strategy
def gen_strategy(partition_factor, unroll_factor):
    lp_d = []

    for iob in partition_factor: # io/buffer partition

        lp1_d = []
        for i in unroll_factor:
            if i <= iob:
                lp1_d.append(['n', '1', 'n', str(i)])

        lp2_d = []
        for i in unroll_factor:
            if i <= iob:
                lp2_d.append(['n', '1', 'n', str(i)])

        for lp1 in lp1_d:
            for lp2 in lp2_d:
                lp_d.append([iob, lp1[0], lp1[1], lp1[2], lp1[3], lp2[0], lp2[1], lp2[2], lp2[3]])

    lp_d = sorted(lp_d, key = lambda x: x[0], reverse = False)
    
    return lp_d

##########

def run_routine(kernel_name, unroll_fac_loop_dic):

    total_cnt = 0
    partition_factor = [1, 2, 4, 8]
    unroll_factor = [1, 2, 4, 8]
    # anno stores the unroll factor for the loop which needs to be marked
    anno = {}
    mark = unroll_fac_loop_dic
    lp_d = gen_strategy(partition_factor, unroll_factor)
    
    dataset_gen_folder = Path("./pragma_file")
    if dataset_gen_folder.exists():
        pass
    else:  
        os.mkdir(dataset_gen_folder)
    ftotal = open('./pragma_file/prj_total_{}.txt'.format(kernel_name), 'w+')
    
    for lp in lp_d:
        iob = lp[0]
        lp1 = [lp[1], lp[2],  lp[3],  lp[4]]
        lp2 = [lp[5], lp[6],  lp[7],  lp[8]]
        
        match kernel_name:
            case "atax":
                prj_name = 'io{}_l1{}{}{}{}_l3{}{}{}{}'.format(lp[0], lp[1], lp[2], lp[3], lp[4], lp[5], lp[6], lp[7], lp[8])
            case "bicg":
                prj_name = 'io{}_l1{}{}{}{}_l3{}{}{}{}'.format(lp[0], lp[1], lp[2], lp[3], lp[4], lp[5], lp[6], lp[7], lp[8])
            case "gemm":
                prj_name = 'io{}_l2{}{}{}{}_l4{}{}{}{}'.format(lp[0], lp[1], lp[2], lp[3], lp[4], lp[5], lp[6], lp[7], lp[8])
            case "gesummv":
                prj_name = 'io{}_l1{}{}{}{}_l3{}{}{}{}_l5{}{}'.format(lp[0], lp[1], lp[2], lp[3], lp[4], lp[5], lp[6], lp[7], lp[8], lp[1], lp[2])
            case "k2mm":
                prj_name = 'io{}_l2{}{}{}{}_l5{}{}{}{}_l7{}{}{}{}'.format(lp[0], lp[1], lp[2], lp[3], lp[4], lp[1], lp[2], lp[3], lp[4], lp[5], lp[6], lp[7], lp[8])
            case "k3mm":
                prj_name = 'io{}_l2{}{}{}{}_l5{}{}{}{}_l8{}{}{}{}'.format(lp[0], lp[1], lp[2], lp[3], lp[4], lp[1], lp[2], lp[3], lp[4], lp[5], lp[6], lp[7], lp[8])
            case "mvt":
                prj_name = 'io{}_l1{}{}{}{}_l3{}{}{}{}'.format(lp[0], lp[1], lp[2], lp[3], lp[4], lp[5], lp[6], lp[7], lp[8])
            case "syr2k":
                prj_name = 'io{}_l2{}{}{}{}_l5{}{}{}{}_l7{}{}{}{}'.format(lp[0], lp[1], lp[2], lp[3], lp[4], lp[1], lp[2], lp[3], lp[4], lp[5], lp[6], lp[7], lp[8])
            case "syrk":
                prj_name = 'io{}_l2{}{}{}{}_l4{}{}{}{}'.format(lp[0], lp[1], lp[2], lp[3], lp[4], lp[5], lp[6], lp[7], lp[8])
        
        '''
        match kernel_name:
            case "atax":
                prj_name = 'l1{}{}{}{}_l3{}{}{}{}'.format(lp[1], lp[2], lp[3], lp[4], lp[5], lp[6], lp[7], lp[8])
            case "bicg":
                prj_name = 'l1{}{}{}{}_l3{}{}{}{}'.format(lp[1], lp[2], lp[3], lp[4], lp[5], lp[6], lp[7], lp[8])
            case "gemm":
                prj_name = 'l2{}{}{}{}_l4{}{}{}{}'.format(lp[1], lp[2], lp[3], lp[4], lp[5], lp[6], lp[7], lp[8])
            case "gesummv":
                prj_name = 'l1{}{}{}{}_l3{}{}{}{}_l5{}{}'.format(lp[1], lp[2], lp[3], lp[4], lp[5], lp[6], lp[7], lp[8], lp[1], lp[2])
            case "k2mm":
                prj_name = 'l2{}{}{}{}_l5{}{}{}{}_l7{}{}{}{}'.format(lp[1], lp[2], lp[3], lp[4], lp[1], lp[2], lp[3], lp[4], lp[5], lp[6], lp[7], lp[8])
            case "k3mm":
                prj_name = 'l2{}{}{}{}_l5{}{}{}{}_l8{}{}{}{}'.format(lp[1], lp[2], lp[3], lp[4], lp[1], lp[2], lp[3], lp[4], lp[5], lp[6], lp[7], lp[8])
            case "mvt":
                prj_name = 'l1{}{}{}{}_l3{}{}{}{}'.format(lp[1], lp[2], lp[3], lp[4], lp[5], lp[6], lp[7], lp[8])
            case "syr2k":
                prj_name = 'l2{}{}{}{}_l5{}{}{}{}_l7{}{}{}{}'.format(lp[1], lp[2], lp[3], lp[4], lp[1], lp[2], lp[3], lp[4], lp[5], lp[6], lp[7], lp[8])
            case "syrk":
                prj_name = 'l2{}{}{}{}_l4{}{}{}{}'.format(lp[1], lp[2], lp[3], lp[4], lp[5], lp[6], lp[7], lp[8])
        '''
        #output a stragy file   
        ftotal.write('{}\n'.format(prj_name))
        anno['prj_name'] = prj_name
        #e is loop which is needed to be marked
        for e in mark:
            if (e.count("wr") == 1 or e.count("rd") == 1):
                ftotal.write('set_directive_unroll -factor {} "{}/{}"\n'.format(iob, kernel_name, e))
                anno[e] = iob
            else:
                e_after_split=e.split("-")
                #print(e_after_split)
                #for example: lp2[3]// 2 is lp_num // 3 is index // lp is the loop need to be marked
                #lp stores which loop need the unroll factor
                lp=e_after_split[0]
                lp_num=int(e_after_split[1])
                #index stores the index of lp_1 and lp_2 in the gen_strategy function, for example lp==lp3, lp_num==1, index==3, it means 
                #lp3 should be marked lp1[3]
                index=int(e_after_split[2])
                #choose freom lp_1 or lp_2
                if lp_num == 1:
                    ftotal.write('set_directive_unroll -factor {} "{}/{}"\n'.format(lp1[index], kernel_name, lp))
                    anno[lp] = lp1[index]
                else:
                    ftotal.write('set_directive_unroll -factor {} "{}/{}"\n'.format(lp2[index], kernel_name, lp))
                    anno[lp] = lp2[index]
        ftotal.write('\n')
        print(anno)
        gen(anno, kernel_name, prj_name)
        shutil.copy('./{}/hls/src/{}.h'.format(kernel_name, kernel_name), './pragma_file/{}_{}/'.format(kernel_name, prj_name))
        total_cnt = total_cnt + 1
    ftotal.close()
    return total_cnt

##########

#main
def generating_HLS_strategy():
    kernel_name_list = ["atax", "bicg", "gemm", "gesummv", "k2mm", "k3mm", "mvt", "syr2k", "syrk"]
    #lp2-1-3 means that the unroll factor of lp2 comes from lp1[3] 
    unroll_fac_loop_dic = { "atax":["lprd_2", "lpwr_1", "lp2-1-3", "lp4-2-3"], 
                            "bicg":["lprd_2", "lpwr", "lp2-1-3", "lp4-2-3"], 
                            "gemm":["lprd_2", "lpwr_2", "lp3-1-3", "lp5-2-3"], 
                            "gesummv":["lprd_2", "lpwr", "lp2-1-3", "lp4-2-3", "lp5-1-1"], 
                            "k2mm":["lprd_2", "lpwr_2", "lp3-1-3", "lp6-1-3", "lp8-2-3"], 
                            "k3mm":["lprd_2", "lpwr_2", "lp3-1-3", "lp6-1-3", "lp9-2-3"], 
                            "mvt":["lprd_2", "lpwr", "lp2-1-3", "lp4-2-3"], 
                            "syr2k":["lprd_2", "lpwr_2", "lp3-1-3", "lp6-1-3", "lp8-2-3"], 
                            "syrk":["lprd_2", "lpwr_2", "lp3-1-3", "lp5-2-3"]}

    for kernel_name in kernel_name_list:
        #kernel_name_1 = os.path.basename(sys.argv[0])
        #kernel_name = kernel_name_1.removeprefix('test_').removesuffix('.py')
        total_cnt=run_routine(kernel_name, unroll_fac_loop_dic[kernel_name])
        #print(total_cnt)

#####################################  part2: run Bambu with the generated strategy  ######################################

def running_bambu():
    print("############################ Running Bambu with the generated strategy ####################################")
    paths = os.listdir('./')
    for path in paths:
        if os.path.isdir("./{}".format(path)) and (path != "pragma_file"):
            print("################# {} start #####################".format(path))
            folder_path = Path("./{}/hls/run/".format(path))
            bambu_output_folder = Path("{}/bambu_output".format(folder_path))
            
            if folder_path.exists():
                if bambu_output_folder.exists():
                    pass
                else:
                    os.mkdir(bambu_output_folder)
                pass
            else:  
                os.mkdir(folder_path)
                os.mkdir(bambu_output_folder)
                
            shutil.copy('./{}/hls/src/{}.c'.format(path, path), './{}/hls/run/'.format(path))
            shutil.copy('./{}/hls/src/{}.h'.format(path, path), './{}/hls/run/'.format(path))

            subprocess.run("docker container start bambu-dev", shell=True)
            print("{} is running".format(path))
            docker_running_path = "/workspace/TPR-model/dataset/Polybench/{}/hls/run/bambu_output/".format(path)
            subprocess.run("docker exec -w {} --user wlxing bambu-dev /opt/panda/bin/bambu ../{}.c --top-fname={} --print-dot --compiler=I386_CLANG13 -O2 --debug 4 --verbosity 4 > stdout.txt 2> stderr.txt --device={} --channels-number={} --clock-period={} --disable-function-proxy".format(docker_running_path, path, path, xilinx_part_number, channel_number, clock_period), shell=True)
            
            print("################### {} bambu running finished #######################".format(path))
            
    '''
    for path in os.listdir(dataset_path):
        subprocess.run(
            "docker run --rm --user sqzhou -w workspace/binding-gnn/PandA-bambu/example    bambu-option    ",    
            shell=True, check=True, executable='/bin/bash')
    '''
def divide_list_into_groups(lst, n):
    """Divide a list into groups of n elements."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def run_bambu_with_coloring_solution():
    # Bambu run status
    f = open("{}/custom_coloring_bambu_run_status.csv".format(pragma_file_path), "w")
    f.write("Design Point,Coloring solution,Bambu Success,error,time taken\n")
    f.close()

    # Vivado run status
    f = open("{}/custom_coloring_vivado_run_status.csv".format(pragma_file_path), "w")
    f.write("Design Point,Coloring solution,CP_latency,dynamic_pwr,lut,success,error,time taken\n")
    f.close()

    # read projects to run
    for design_point_name in os.listdir(runtime_solution_path):
        print("################# start running design point {} #####################".format(design_point_name))
        print("################# divide coloring solutions into group of {} #####################".format(project_parallel_run))
        coloring_solutions_list = os.listdir("{}/{}".format(runtime_solution_path, design_point_name))
        

        coloring_solution_groups = list(divide_list_into_groups(coloring_solutions_list[1:], project_parallel_run))
        previous_solution_group = []

        # make sure the graph directory for current design point is reset
        if os.path.exists("{}/{}".format(graph_path, design_point_name)):
            shutil.rmtree("{}/{}".format(graph_path, design_point_name))
        os.makedirs("{}/{}".format(graph_path, design_point_name))

        for coloring_solution_group in coloring_solution_groups:
            print("----Running coloring solutions ", end="")
            
            for coloring_solution in coloring_solution_group:
                print("{} ".format(coloring_solution), end="")
            print("-------")

            #f2 = open("{}/custom_coloring_bambu_run_status.csv".format(pragma_file_path), "a")
        
            bambu_procs = []
            vivado_proc = []

            lock = Lock()
            # run all the coloring solutions in parallel
            # with ProcessPoolExecutor(max_workers=project_parallel_run) as executor:
            #     futures = [executor.submit(run_bambu_for_coloring_solution, coloring_solution, design_point_name, f, lock) for coloring_solution in coloring_solutions]
            #     for future in futures:
            #         future.result()  # Wait for all processes to complete

            for coloring_solution in coloring_solution_group:
                p = Process(target=run_bambu_for_coloring_solution, args=(coloring_solution, design_point_name, lock))
                bambu_procs.append(p)
          
                p.start()

            # run Vivado for previous coloring group
            for coloring_solution in previous_solution_group:
                p = Process(target=run_vivado_for_coloring_solution, args=(coloring_solution, design_point_name, lock))
                vivado_proc.append(p)
                p.start()


            for p in bambu_procs + vivado_proc:
                p.join()

            previous_solution_group = coloring_solution_group

        procs = []

        # run Vivado for the last group
        for coloring_solution in previous_solution_group:
            p = Process(target=run_vivado_for_coloring_solution, args=(coloring_solution, design_point_name, lock))
            procs.append(p)
            p.start()
        
        for p in procs:
            p.join()

        

        print("################# Successfully ran design point {} #####################".format(design_point_name))


        # for coloring_solution in os.listdir("{}/{}".format(runtime_solution_path, design_point_name)):
        #     if(coloring_solution == "coloring_solutions_info.csv"):
        #         continue
            





def run_bambu_for_coloring_solution(coloring_solution, design_point_name, lock):
    
    
    design_name = design_point_name.split("_")[0]
    start = time.time()
            
    coloring_solution_name = coloring_solution[:-4]
    coloring_solution_file_path = "{}/{}/{}".format(runtime_solution_path, design_point_name, coloring_solution)
    coloring_index = coloring_solution_name.split("_")[-1]

    print("################# start running Bambu for design point {} {} #####################".format(design_point_name, coloring_solution_name))

    bambu_run_path = "{}/{}/{}".format(pragma_file_path, design_point_name, coloring_solution_name + "_bambu_run")
    docker_run_path = "/workspace/TPR-model/dataset/Polybench/raw/pragma_file/{}/{}".format(design_point_name, coloring_solution_name + "_bambu_run")
    

    if os.path.exists(bambu_run_path):
        shutil.rmtree(bambu_run_path)
    os.mkdir(bambu_run_path)

    # copy the coloring solution to the project folder
    shutil.copy(coloring_solution_file_path, bambu_run_path + "/coloring_result.csv")
    print("Coloring solution copied to the project folder")

    # make sure the container is up
    subprocess.run("docker container start bambu-option", shell=True)


    result = subprocess.run("docker exec -w {} --user sqzhou bambu-option /opt/panda/bin/bambu ../{}.c --top-fname={} --print-dot --compiler=I386_CLANG13 -O2 --debug 4 --verbosity 4 > {}/stdout.txt 2> {}/stderr.txt --device={} --channels-number={} --clock-period={} --disable-function-proxy".format(docker_run_path, design_name, design_name, bambu_run_path, bambu_run_path, xilinx_part_number, channel_number, clock_period), shell=True, capture_output=True, text=True)
    if result.returncode:
        print("################### Fail to run Bambu for design point {} {} #######################".format(design_point_name, coloring_solution_name))
        print("Error: ", result.stderr)
        lock.acquire()
        f = open("{}/custom_coloring_bambu_run_status.csv".format(pragma_file_path), "a")
        f.write("{},{},{},{},{}\n".format(design_point_name, coloring_solution_name, "0", "Bambu exit with code {}".format(result.returncode),time.time() - start))
        f.close()
        lock.release()
        return

    # check if coloring solution path exists
    if not os.path.exists("{}/{}/{}".format(graph_path, design_point_name, coloring_solution_name)):
        os.makedirs("{}/{}/{}".format(graph_path, design_point_name, coloring_solution_name))
    
    # extract CDFG
    #shutil.copy("{}/{}_CG_cdfg_partitions_only.dot".format(bambu_run_path,design_name), "{}/cg_{}_{}.dot".format(graph_path, design_point_name, coloring_solution_name))
    shutil.copy("{}/{}_cdfg_bulk_graph.dot".format(bambu_run_path,design_name), "{}/{}/{}/cdfg_raw.dot".format(graph_path, design_point_name, coloring_solution_name))
    
    # also copy the coloring solution to the graph path
    shutil.copy(coloring_solution_file_path, "{}/{}/{}/coloring.csv".format(graph_path, design_point_name, coloring_solution_name))




    print("################### Successfully ran Bambu for design point {} {} #######################".format(design_point_name, coloring_solution_name))
    print("Time taken: ", time.time() - start)
    lock.acquire()
    f = open("{}/custom_coloring_bambu_run_status.csv".format(pragma_file_path), "a")
    f.write("{},{},{},{},{}\n".format(design_point_name, coloring_solution_name, "1", "N/A", time.time() - start))
    f.close()
    lock.release()


            

    # for each project and each of its solutions, copy that solution to the project folder and run Bambu
    


def run_vivado_for_coloring_solution(coloring_solution, design_point_name, lock):
    design_name = design_point_name.split("_")[0]
    coloring_solution_name = coloring_solution[:-4]

    print("################# start running Vivado for design point {} {} #####################".format(design_point_name, coloring_solution_name))


        
    start = time.time()

    coloring_solution_name = coloring_solution[:-4]
    coloring_index = coloring_solution_name.split("_")[-1]

    bambu_run_path = "{}/{}/{}".format(pragma_file_path, design_point_name, coloring_solution_name + "_bambu_run")
    
   
    
    
    vivado_tcl_path = "{}/{}".format(bambu_run_path, "/HLS_output/Synthesis/vivado_flow/vivado.tcl")
    if not os.path.exists(vivado_tcl_path):
        print("################### Vivado tcl file does not exist for design point {} {} #######################".format(design_point_name, coloring_solution_name))
        lock.acquire()
        f = open("{}/custom_coloring_vivado_run_status.csv".format(pragma_file_path), "a")
        f.write("{},{},{},{},{},{},{},{}\n".format(design_point_name, coloring_solution_name, "N/A", "N/A", "N/A","0", "Vivado tcl file does not exist", time.time() - start))
        f.close()
        lock.release()
        return

    
    

    result = subprocess.run("vivado -mode batch -nojournal -nolog -notrace -source HLS_output/Synthesis/vivado_flow/vivado.tcl", shell=True, cwd="{}".format(bambu_run_path), capture_output=True, text=True)
    if result.returncode:
        print("################### Fail to run vivado for design point {} {} #######################".format(design_point_name, coloring_solution_name))
        print("Error: ", result.stderr)
        
        lock.acquire()
        f = open("{}/custom_coloring_vivado_run_status.csv".format(pragma_file_path), "a")
        f.write("{},{},{},{},{},{},{},{}\n".format(design_point_name, coloring_solution_name, "N/A", "N/A", "N/A","0", "Vivado exit with code {}".format(result.returncode), time.time() - start))
        os.remove("{}/{}/cdfg_{}.dot".format(graph_path, design_point_name, coloring_solution_name))
        os.remove("{}/{}/cdfg_{}".format(graph_path, design_point_name, coloring_solution))
        f.close()
        lock.release()
        return
    
    
    # extract the performance information
    lock.acquire()
    f = open("{}/custom_coloring_vivado_run_status.csv".format(pragma_file_path), "a")
    f.write("{},{},".format(design_point_name, coloring_solution_name))
    error = vivado_info.extract_perf(10, bambu_run_path, f)
    if error:
        f.write("{},{},{},{},{},{}\n".format( "N/A", "N/A", "N/A","0", "Fail to extract performance information", time.time() - start))
        f.close()
        lock.release()
        return
    

    # copy perf measure to the graph path
    shutil.copy("{}/perf_measure.csv".format(bambu_run_path), "{}/{}/{}/perf_measure.csv".format(graph_path, design_point_name, coloring_solution_name))

    print("################### Successfully ran Vivado for design point {} {} #######################".format(design_point_name, coloring_solution_name))
    print("Time taken: ", time.time() - start)
    f.write(",{},{},{}\n".format("1", "N/A", time.time() - start))
    f.close()
    lock.release()

    

    




######################################  part3: generate Vivado script(.tcl) for all HLS results   #############################################################
print("Generating Vivado script for all designs and solutions")





#generating_HLS_strategy()
run_bambu_with_coloring_solution()
#running_vivado()
#vivado_info.running_route(clock_period)
