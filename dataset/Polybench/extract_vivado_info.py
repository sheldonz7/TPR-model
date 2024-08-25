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
    lines=list()
    with open(target_file) as f:
        lines=f.readlines()
    
    for line in lines:
        if line.find("Slack (MET)") != -1:
            Slack_MET_line = line
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
    for digit in Slack_MET_line:
        if digit.isdigit() and digit_pos_beg == 0:
            digit_pos_beg=digit_pos
        if digit.isdigit() == False:
            if digit == '.':
                pass
            else:
                digit_pos_end = digit_pos
                break
    Slack_MET_data = Slack_MET_line[digit_pos_beg:digit_pos_end]
    return target_line_max, target_data_max, Slack_MET_line, Slack_MET_data


###################################################################
def extract_post_route_util(target_file):
    #this is for extract CLB LUTs from pos_route_util file
    lines=list()
    pos = 0
    with open(target_file) as f:
        lines=f.readlines()
    for line in lines:
        if line.find("CLB LUTs") != -1:
            CLB_LUTS_target_line = line
            line1=lines[pos-3]
            line2=lines[pos-2]
            line3=lines[pos-1]
        if line.find("LUT as Logic") != -1:
            LUT_as_Logic_target_line = line
        if line.find("LUT as Memory") != -1:
            LUT_as_Memory_target_line = line
            break
        pos=pos+1
    return CLB_LUTS_target_line, LUT_as_Logic_target_line, LUT_as_Memory_target_line, line1, line2, line3
#####################################################################

def running_route():
    print("extracting vivado information beginning")
    path="./"
    if 'vivado_info' in os.listdir(path):
        pass
    else:
        os.mkdir('./vivado_info')
    targets=list()
    post_route_power_list = list()
    post_route_timing_summary_list = list()
    post_route_util_list = list()
    post_route_timing_summary_file = open("./vivado_info/"+"p_r_timing_summary"+".txt", 'a+')
    post_route_power_file = open('./vivado_info/'+'p_r_power'+'.txt', 'a+')
    post_route_util_file = open('./vivado_info/'+'p_r_util'+'.txt', 'a+')
    n=0
    #for i in os.listdir(path):
        #if os.path.isdir('./dataset/Polybench/{}'.format(i)) and (i != 'pragma_file'):
        #    targets.append(i)
    targets=['atax', 'bicg', 'gemm', 'gesummv', 'k2mm', 'k3mm', 'mvt', 'syr2k', 'syrk']
    for target in targets:
        target_file_1="./{}/hls/run/bambu_output/HLS_output/Synthesis/vivado_flow/post_route_power.rpt".format(target)
        target_line, target_data = extract_post_route_power(target_file_1)
        #target data is saved in target_data variable
        post_route_power_file.write("{}{}\n".format(target, target_line.replace(f'\n', '')))

        target_file_2="./{}/hls/run/bambu_output//HLS_output/Synthesis/vivado_flow/post_route_timing_summary.rpt".format(target)
        target_line, target_data, Slack_MET_line, Slack_MET_data = extract_post_route_timing_summary(target_file_2)
        #data path delay is saved in target_data
        post_route_timing_summary_file.write("{}:\n{}{}".format(target, Slack_MET_line, target_line))

        target_file_3="./{}/hls/run/bambu_output/HLS_output/Synthesis/vivado_flow/post_route_util.rpt".format(target)
        CLB_line, LUT_Logic_line, LUT_Memory_line, line1, line2, line3 = extract_post_route_util(target_file_3)
        file3=post_route_util_file.readlines()
        if n == 0:
            post_route_util_file.write("{}{}".format(line1, line2))
            n=n+1
        post_route_util_file.write("{}{}:\n{},\n{},\n{}\n".format(line3, target, CLB_line.replace(f'\n', ''), LUT_Logic_line.replace(f'\n', ''), LUT_Memory_line.replace(f'\n', '')))

    post_route_power_file.close()
    post_route_timing_summary_file.close()
    post_route_util_file.close()
    print("extracting vivado information ends")
if __name__ == "__main__":
    running_route()
