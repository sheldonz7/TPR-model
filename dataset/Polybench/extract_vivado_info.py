import os
import shutil
import subprocess
import sys
import io

###################################################################
def extract_post_route_power(target_file):
    #this is for extracting Dynamic (W) from post_route_power file
    lines=list()
    with open(target_file) as f:
        lines=f.readlines()
    #locate the target line including target data
    for line in lines:
        if line.find("Dynamic (W)") != -1:
            target_line=line
            break
    locate_beg=target_line.find("|", 1)
    pos=locate_beg+2
    #locate the target data
    for i in target_line[locate_beg+2:]:
        if i.isdigit():
            pass
        else:
            if i == ' ':
                locate_end=pos
                break
            pass
        pos=pos + 1
    
    target_data=target_line[locate_beg+2:locate_end]
    return target_line, target_data

####################################################################

def extract_post_route_timing_summary(target_file):
    #this is for extracting data path delay from post_route_timing_summary file
    print("extracting post route timing summary")
    lines=list()
    slack_met = True
    with open(target_file) as f:
        lines=f.readlines()
    
    for line in lines:
        if line.find("Slack (MET)") != -1:
            Slack_line = line
        if line.find("Slack (VIOLATED)") != -1:
            Slack_line = line
            slack_met = False
            print("slack violated")
        if line.find("Data Path Delay:") != -1:
            target_line_max=line
            break
    locate_beg=target_line_max.find(":")
    #finding the beginning of the target data
    max_pos=locate_beg
    for i in target_line_max[locate_beg:]:
        if i != " ":
            locate_beg_max=max_pos
            break
        max_pos=max_pos+1
    #locating the end of the target data
    pos = 0
    for o in target_line_max[::-1]:
        if o != " ":
            locate_end_max = len(target_line_max) - pos
            break
        pos = pos + 1
    target_data_max=target_line_max[locate_beg_max:locate_end_max+1]
    digit_pos=0
    digit_pos_beg=0
    for digit in Slack_line:
        print("digit: ", digit)
        if not slack_met:
            if digit == "-" and (digit_pos_beg == 0):
                digit_pos_beg=digit_pos
        else:    
            if digit.isdigit() and (digit_pos_beg == 0):
                digit_pos_beg=digit_pos
        

        if digit_pos_beg != 0 and digit.isdigit() == False and digit != '-' and digit != '.':   
            digit_pos_end = digit_pos
            break
        digit_pos=digit_pos+1
    Slack_data = Slack_line[digit_pos_beg:digit_pos_end]
    print("Slack data: ", Slack_data)
    return target_line_max, target_data_max, Slack_line, Slack_data


###################################################################
def extract_post_route_util(target_file):
    #this is for extract CLB LUTs from pos_route_util file
    lines=list()
    pos = 0
    logic_name_pos = 0 
    logic_name_times=0
    logic_name=str()
    logic_name_pos1=0
    logic_name_pos2=0
    with open(target_file) as f:
        lines=f.readlines()
    for line in lines:
        '''
        # find the pos of the table and 1. {} logic
        if line.find("CLB LUTs") != -1:
            print(1233333333)
            logic_name=lines[pos+2]
            logic_name_pos1=pos+2 
        
        if logic_name in line:
            logic_name_times=logic_name_times+1
            if logic_name_times == 2:
                logic_name_pos2=pos
        CLB_LUTS_target_line=lines[logic_name_pos2+6]
        line1=lines[logic_name_pos2+3]
        line2=lines[logic_name_pos2+4]
        line3=lines[logic_name_pos2+5]
        '''
        if line.find("Table") != -1:
            logic_name=lines[pos+2]
            logic_name_pos1=pos+2
            #print(list(logic_name))
            '''
            CLB_LUTS_target_line = line
            line1=lines[pos-3]
            line2=lines[pos-2]
            line3=lines[pos-1]
            '''
        if logic_name == line:
            logic_name_times=logic_name_times+1
            if logic_name_times == 2:
                logic_name_pos2=pos
        CLB_LUTS_target_line=lines[logic_name_pos2+6]
        line1=lines[logic_name_pos2+3]
        line2=lines[logic_name_pos2+4]
        line3=lines[logic_name_pos2+5]

        if line.find("LUT as Logic") != -1:
            LUT_as_Logic_target_line = line
        if line.find("LUT as Memory") != -1:
            LUT_as_Memory_target_line = line
            break
        pos=pos+1
        logic_name_pos = logic_name_pos + 1

    lut_data_pos=CLB_LUTS_target_line.find('|', 2)
    lut_data_beg=lut_data_pos+2
    pos1 = lut_data_beg
    for digit in CLB_LUTS_target_line[lut_data_beg:]:
        if digit.isdigit() == False:
            lut_data_end=pos1
            break
        pos1=pos1+1
    lut = CLB_LUTS_target_line[lut_data_beg:lut_data_end]
    return CLB_LUTS_target_line, LUT_as_Logic_target_line, LUT_as_Memory_target_line, line1, line2, line3, lut
#####################################################################
def add_to_perf_measure(clock_period, Slack_data, dynamic_pwr, lut, prj_path, dest_csv_file):
    # if 'sample' in os.listdir('./{}/hls/'.format(target)):
    #     pass
    # else:
    #     os.mkdir('./{}/hls/sample'.format(target))
    perf_measure = open('{}/perf_measure.csv'.format(prj_path), 'w+')
    cp_latency=clock_period - float(Slack_data)
    l = perf_measure.readlines()
 
    perf_measure.write("cp_latency,dynamic_pwr,lut\n{},{},{}\n".format(cp_latency, dynamic_pwr, lut))
    dest_csv_file.write("{},{},{}".format(cp_latency, dynamic_pwr, lut))
    #perf_measure.write("{},{},{}\n".format(cp_latency, dynamic_pwr, lut))

#####################################################################

def extract_perf(clock_period, project_path, dest_csv_file):


    print("extracting vivado information beginning")
    path="./"
    if 'vivado_info' in os.listdir(path):
        pass
    else:
        os.mkdir('./vivado_info')
    targets=list()
    # post_route_timing_summary_file = open("./vivado_info/"+"p_r_timing_summary"+".txt", 'a+')
    # post_route_power_file = open('./vivado_info/'+'p_r_power'+'.txt', 'a+')
    # post_route_util_file = open('./vivado_info/'+'p_r_util'+'.txt', 'a+')

    n=0
    #for i in os.listdir(path):
        #if os.path.isdir('./dataset/Polybench/{}'.format(i)) and (i != 'pragma_file'):
        #    targets.append(i)
    # targets=['atax', 'bicg', 'gemm', 'gesummv', 'k2mm', 'k3mm', 'mvt', 'syr2k', 'syrk']

    target_file_1="{}/HLS_output/Synthesis/vivado_flow/post_route_power.rpt".format(project_path)
    if os.path.exists(target_file_1) == False:
        print("post_route_power.rpt does not exist")
        return 1
    target_line, dynamic_pwr_data = extract_post_route_power(target_file_1)
    #target data is saved in target_data variable
    #post_route_power_file.write("{}{}\n".format(target, target_line.replace(f'\n', '')))

    target_file_2="{}/HLS_output/Synthesis/vivado_flow/post_route_timing_summary.rpt".format(project_path)
    if os.path.exists(target_file_2) == False:
        print("post_route_timing_summary.rpt does not exist")
        return 1

    target_line, target_data, Slack_MET_line, Slack_data = extract_post_route_timing_summary(target_file_2)
    print("get slack data: ", Slack_data)
    if float(Slack_data) < 0.0:
        print("Slack is negative, skipping this project")
        return 2
    #data path delay is saved in target_data
    #post_route_timing_summary_file.write("{}:\n{}{}".format(target, Slack_MET_line, target_line))

    target_file_3="{}/HLS_output/Synthesis/vivado_flow/post_route_util.rpt".format(project_path)
    if os.path.exists(target_file_3) == False:
        print("post_route_util.rpt does not exist")
        return 1
    
    CLB_line, LUT_Logic_line, LUT_Memory_line, line1, line2, line3, lut = extract_post_route_util(target_file_3)
    # file3=post_route_util_file.readlines()
    # if n == 0:
    #     post_route_util_file.write("{}{}".format(line1, line2))
    #     n=n+1
    #post_route_util_file.write("{}{}:\n{},\n{},\n{}\n".format(line3, target, CLB_line.replace(f'\n', ''), LUT_Logic_line.replace(f'\n', ''), LUT_Memory_line.replace(f'\n', '')))
    add_to_perf_measure(clock_period, Slack_data, dynamic_pwr_data, lut, project_path, dest_csv_file)
    # post_route_power_file.close()
    # post_route_timing_summary_file.close()
    # post_route_util_file.close()
    print("extracting vivado information ends")


    return 0