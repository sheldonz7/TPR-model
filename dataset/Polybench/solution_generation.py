import pandas as pd
import sys
import os
import shutil
import itertools




CG_solutions_path = './raw/CG_solutions'

filtered_solutions_path = './raw/filtered_solutions_mem'
sampled_solutions_path = './raw/sampled_solutions_mem'
final_solutions_path = './raw/runtime_solutions_mem'

# # target number of data point for each kernel/design
# target_dataset_size = 




def merge_coloring_solutions(file_list, target_csv_path):
    # 初始化一个字典来记录每个位置的值，以及一个字典来处理不同索引下的唯一性
    merged_data = {}
    has_conflict = False
    unique_counter = {}

    # 遍历所有的 CSV 文件
    for file_path in file_list:
        # 读取当前文件的第三列（忽略第一行的标签）
        df = pd.read_csv(file_path)
        second_column = df.iloc[:, 1]  # 第二列数据（索引列）
        third_column = df.iloc[:, 2]  # 第三列数据

        # 遍历第三列的每一个元素
        for index, (second_value, third_value) in enumerate(zip(second_column, third_column)):
            if third_value != -1:
                # 初始化 unique_counter
                if second_value not in unique_counter:
                    unique_counter[second_value] = {}

                # 确保不同索引下的值唯一
                if third_value not in unique_counter[second_value]:
                    unique_counter[second_value][third_value] = len(unique_counter[second_value]) + 1

                new_third_value = unique_counter[second_value][third_value]

                if index not in merged_data:
                    merged_data[index] = new_third_value
                else:
                    # 如果当前位置已经有值且不相同，说明有冲突
                    if merged_data[index] != new_third_value:
                        has_conflict = True
                        break

    # 如果有冲突，输出警告信息
    if has_conflict:
        print("Conflict detected: More than one non--1 value at the same position.")
        sys.exit()

    # 生成新的第三列
    new_third_column = [-1] * len(third_column)
    for index, value in merged_data.items():
        new_third_column[index] = value

    # 构建新的 DataFrame 并保存到新的 CSV 文件
    new_df = df.copy()  # 使用第一个文件的前两列
    new_df.iloc[:, 2] = new_third_column


    unique_value = 1
    for idx, group in new_df.groupby(new_df.columns[1]):  # Group by the second column (index 1)
        value_map = {}
        for val in group.iloc[:, 2]:  # Iterate over the third column
            if val not in value_map:
                value_map[val] = unique_value
                unique_value += 1

        # Assign the mapped unique values back to the third column
        new_df.loc[group.index, new_df.columns[2]] = group.iloc[:, 2].map(value_map)



    # 检查新的第三列是否还含有 -1
    if -1 in new_third_column:
        print("New CSV still contains -1.")
        sys.exit()
    else:
        print("New CSV does not contain -1.")
  

    # Save the updated DataFrame back to a new CSV file
    new_df.to_csv(target_csv_path, index=False)






def filter_function_unit():
    
    # create filtered solutions dir
    if os.path.exists(filtered_solutions_path):
        shutil.rmtree(filtered_solutions_path)    
    os.mkdir(filtered_solutions_path)


    f = open("{}/CG_filtering_status.csv".format(filtered_solutions_path), "w")
    f.write("Design, function-unit, num-solutions\n")

    solution_number = dict()

    for design_point_name in os.listdir(CG_solutions_path):
        # remove the last segment of design_point_name 5 segments
        exact_design_point_name = "_".join(design_point_name.split('_')[0:-1]) 

        if exact_design_point_name not in solution_number:
            solution_number[exact_design_point_name] = dict()

        # look for resource contraint from CG data
        rc = dict()
        rc_data = pd.read_csv('./raw/CG/' + exact_design_point_name + '_RC.csv')

        # file not found
        if rc_data.empty:
            print('Resource constraint data not found for ' + exact_design_point_name)
            continue

        first_column = rc_data.iloc[:, 0]
        third_column = rc_data.iloc[:, 3]
        
        for index, (first_value, third_value) in enumerate(zip(first_column, third_column)):
            rc[int(first_value)] = int(third_value)
            print('Setting resource constraint for functional unit {} to be {}'.format(first_value, third_value))

        # create filtered solutions dir for current design point
        if not os.path.exists('{}/{}'.format(filtered_solutions_path, exact_design_point_name)):
            os.mkdir('{}/{}'.format(filtered_solutions_path, exact_design_point_name))

        fu_solution_num = dict()
        possible_coloring_solutions_num = 1


        # get the fu_name
        # fu_indices = []
        # for idx, fu_solution in enumerate(os.listdir('{}/{}'.format(CG_solutions_path, design_point_name))):
        #     fu_index = int(fu_solution.split('_')[2])
        #     fu_indices.append(fu_index)


        # iterate through all function unit solutions for the current design point, along with the index
        for idx, fu_solution in enumerate(sorted(os.listdir('{}/{}'.format(CG_solutions_path, design_point_name)), key=lambda x: int(x.split('_')[2]))):
            print("fu_solution: ", fu_solution)
            fu_index = int(fu_solution.split('_')[2])
            fu_name = ""

            if idx == len(os.listdir('{}/{}'.format(CG_solutions_path, design_point_name))) - 1:
                fu_name = 'fmult'
            elif idx == len(os.listdir('{}/{}'.format(CG_solutions_path, design_point_name))) - 2:
                fu_name = 'fadd'
            elif idx == len(os.listdir('{}/{}'.format(CG_solutions_path, design_point_name))) - 3:
                fu_name = 'bmem-ctrl'
            else:
                fu_name = 'bmem'

            fu_solution_name_full = fu_solution + "_" + fu_name

            if fu_solution_name_full not in solution_number[exact_design_point_name]:
                solution_number[exact_design_point_name][fu_solution_name_full] = dict()

            # for functional unit without resource constraint, set fu_rc as sys.maxsize            
            fu_rc = rc.get(fu_index, sys.maxsize)
            print('Resource constraint for functional unit {}: {}'.format(fu_index, fu_rc))

            # create filtered solutions dir for current function unit
            if not os.path.exists('{}/{}/{}'.format(filtered_solutions_path, exact_design_point_name, fu_solution_name_full)):
                os.mkdir('{}/{}/{}'.format(filtered_solutions_path, exact_design_point_name, fu_solution_name_full))

            num_filtered_solutions = 0

            # iterate over all coloring solutions and copy those solutions which uses no more colors than the resource contraint to filtered_solutions dir
            for coloring_solution in os.listdir('{}/{}/{}'.format(CG_solutions_path, design_point_name, fu_solution)):
            
                # if not coloring_solution.endswith('.csv'):
                #     continue
                # if not coloring_solution.endswith('.csv'):
                #     shutil.rmtree('{}/{}/{}/{}'.format(CG_solutions_path, design_point_name, fu_solution, coloring_solution))
                #     continue
                num_color = int(coloring_solution.split('_')[1])
                
                
                if num_color <= fu_rc:
                    if num_color not in solution_number[exact_design_point_name][fu_solution_name_full]:
                        solution_number[exact_design_point_name][fu_solution_name_full][num_color] = 1
                    else:
                        solution_number[exact_design_point_name][fu_solution_name_full][num_color] += 1

                    if not os.path.exists('{}/{}/{}/{}'.format(filtered_solutions_path, exact_design_point_name, fu_solution_name_full, num_color)):
                        os.mkdir('{}/{}/{}/{}'.format(filtered_solutions_path, exact_design_point_name, fu_solution_name_full, num_color))
                    shutil.copy('{}/{}/{}/{}'.format(CG_solutions_path, design_point_name, fu_solution, coloring_solution), '{}/{}/{}/{}'.format(filtered_solutions_path, exact_design_point_name, fu_solution_name_full, num_color))
                    #print('Copy {} to filtered_solutions for design point {}'.format(coloring_solution, exact_design_point_name))
                    #print('------------------')
                    num_filtered_solutions += 1
            
            

            f.write("{}, {}, {}\n".format(exact_design_point_name, fu_solution, num_filtered_solutions))
            fu_solution_num[fu_index] = num_filtered_solutions

        for fu_index, num_solution in fu_solution_num.items():
            possible_coloring_solutions_num *= num_solution

        f.write("{}, {}, {}\n".format(exact_design_point_name, 'overall', possible_coloring_solutions_num))

    f.close()

    return solution_number

def sample_coloring_result(solution_number):
    # sample the overall coloring result based on the number of different function units used
    # 


    dataset_limit_for_each_design = 300

    # for design with 7 functional unit, allow the first 3 design point to be multi mem for io4
    # for design with 8 or more functional unit

    if os.path.exists(sampled_solutions_path):
        shutil.rmtree(sampled_solutions_path)
    os.mkdir(sampled_solutions_path)
    # for fu in filtered_solutions_path:
    #     solution_count = dict()
        
    #     fu_name = fu.split('_')[-1]
    #     if (fu_name in mem_fu_list and mem_enable) or (fu_name in comp_fu_list and comp_enable):
    #         for fu_coloring_solution in filtered_solutions_path + '/' + fu:
    #             num_color = int(fu_coloring_solution.split('_')[1])
    #             if num_color not in solution_count:
    #                 solution_count[num_color] = 1
    #             else:
    #                 solution_count[num_color] += 1
    #     else:
            

    f = open("{}/coloring_solutions_sampling_summary.csv".format(sampled_solutions_path), "w")
    f.write("design_point_name, expected number of solution\n")

    

    design_point_limit = 3
    dataset_solution_count = 0
    for idx, (design_point_name, fu_solution_number) in enumerate(solution_number.items()):
        f.write(design_point_name + ',')
        
        
        if not os.path.exists('{}/{}'.format(sampled_solutions_path, design_point_name)):
            os.mkdir('{}/{}'.format(sampled_solutions_path, design_point_name))
        
        design_point_solution_count = 1
        num_fu = len(fu_solution_number.items())
        print("number of functional unit:", num_fu)
        

        fu_idx = idx%num_fu
      
        

        for idx, (fu_name_full, color_solution_number) in enumerate(fu_solution_number.items()):
            mem_enable = False
            mem_fu_list = ["bmem", "bmem-ctrl"]
            mem_solution_sample_ratio = 0.1
            mem_solution_sample_limit = 3

            comp_enable = True 
            comp_fu_list = ["fadd", "fmult"]
            comp_solution_sample_ratio = 0.4
            comp_solution_sample_limit = 3
            
            if (len(color_solution_number) > 5):
                mem_solution_sample_limit = 1
                comp_solution_sample_limit = 1
            elif (len(color_solution_number) > 4):
                mem_solution_sample_limit = 2
                comp_solution_sample_limit = 2

            
            if not os.path.exists('{}/{}/{}'.format(sampled_solutions_path, design_point_name, fu_name_full)):
                os.mkdir('{}/{}/{}'.format(sampled_solutions_path, design_point_name, fu_name_full))
            fu_name = fu_name_full.split('_')[-1]
            fu_solution_taken = 0

            if idx == fu_idx:
                mem_enable = True
               # comp_enable = True
            else:
                mem_enable = False
                # comp_enable = False

            if fu_name in mem_fu_list and mem_enable:
            
                

                for num_color, num_solution in color_solution_number.items():
                    # adjust the size
                    # if len(color_solution_number.items()) >
                    

                    num_solution_taken = round(num_solution * mem_solution_sample_ratio)
                    if num_solution_taken == 0:
                        num_solution_taken = 1
                    elif num_solution_taken > mem_solution_sample_limit:
                        num_solution_taken = mem_solution_sample_limit
                    
                    fu_solution_taken += num_solution_taken
                    
                    i = 0
                    for color_solution in os.listdir('{}/{}/{}/{}'.format(filtered_solutions_path, design_point_name, fu_name_full, num_color)):
                        if i == num_solution_taken:
                            break
                        shutil.copy('{}/{}/{}/{}/{}'.format(filtered_solutions_path, design_point_name, fu_name_full, num_color, color_solution), '{}/{}/{}/'.format(sampled_solutions_path, design_point_name, fu_name_full))
                        #print('Copy {} to sampled_solutions for design point {}'.format(color_solution, design_point_name))
                        #print('------------------')
                        i += 1
            elif fu_name in comp_fu_list and comp_enable:
                for num_color, num_solution in color_solution_number.items():
                    num_solution_taken = round(num_solution * comp_solution_sample_ratio)
                    if num_solution_taken == 0:
                        num_solution_taken = 1
                    elif num_solution_taken > comp_solution_sample_limit:
                        num_solution_taken = comp_solution_sample_limit
                    fu_solution_taken += num_solution_taken
                    i = 0
                    for color_solution in os.listdir('{}/{}/{}/{}'.format(filtered_solutions_path, design_point_name, fu_name_full, num_color)):               
                        if i == num_solution_taken:
                            break
                        shutil.copy('{}/{}/{}/{}/{}'.format(filtered_solutions_path, design_point_name, fu_name_full, num_color, color_solution), '{}/{}/{}/'.format(sampled_solutions_path, design_point_name, fu_name_full))
                        #print('Copy {} to sampled_solutions for design point {}'.format(color_solution, design_point_name))
                        #print('------------------')
                        i += 1
            else:
                # only pick one solution from the least number of colors
                num_color = min(color_solution_number.keys())
                fu_solution_taken += 1
                for color_solution in os.listdir('{}/{}/{}/{}'.format(filtered_solutions_path, design_point_name, fu_name_full, num_color)):
                    print("not applying ratio")
                    shutil.copy('{}/{}/{}/{}/{}'.format(filtered_solutions_path, design_point_name, fu_name_full, num_color, color_solution), '{}/{}/{}/'.format(sampled_solutions_path, design_point_name, fu_name_full))
                    #print('Copy {} to sampled_solutions for design point {}'.format(color_solution, design_point_name))
                    #print('------------------')
                    break
            
            print("fu_solution_taken: ", fu_solution_taken)
            design_point_solution_count *= fu_solution_taken


        f.write(str(design_point_solution_count) + "\n")
        dataset_solution_count += design_point_solution_count
    f.write("overall, " + str(dataset_solution_count) + "\n")
    f.close()        
    # simple way to check bram, mult and add numbers
    # last fu is alway fmult
    # second last fu is always fadd
    # third last fu is alway bmem control
    # all fus in the front are bmem

def sample_coloring_result_mem(solution_number):
    # sample the overall coloring result based on the number of different function units used
    # 


    dataset_limit_for_each_design = 300

    # for design with 7 functional unit, allow the first 3 design point to be multi mem for io4
    # for design with 8 or more functional unit

    if os.path.exists(sampled_solutions_path):
        shutil.rmtree(sampled_solutions_path)
    os.mkdir(sampled_solutions_path)
    # for fu in filtered_solutions_path:
    #     solution_count = dict()
        
    #     fu_name = fu.split('_')[-1]
    #     if (fu_name in mem_fu_list and mem_enable) or (fu_name in comp_fu_list and comp_enable):
    #         for fu_coloring_solution in filtered_solutions_path + '/' + fu:
    #             num_color = int(fu_coloring_solution.split('_')[1])
    #             if num_color not in solution_count:
    #                 solution_count[num_color] = 1
    #             else:
    #                 solution_count[num_color] += 1
    #     else:
            

    f = open("{}/coloring_solutions_sampling_summary.csv".format(sampled_solutions_path), "w")
    f.write("design_point_name, expected number of solution\n")

    

    design_point_limit = 3
    dataset_solution_count = 0
    for idx, (design_point_name, fu_solution_number) in enumerate(solution_number.items()):
        f.write(design_point_name + ',')
        
        
        if not os.path.exists('{}/{}'.format(sampled_solutions_path, design_point_name)):
            os.mkdir('{}/{}'.format(sampled_solutions_path, design_point_name))
        
        design_point_solution_count = 1
        num_fu = len(fu_solution_number.items())
        print("number of functional unit:", num_fu)
        

        fu_idx = idx%num_fu
      
        

        for idx, (fu_name_full, color_solution_number) in enumerate(fu_solution_number.items()):
            mem_enable = True
            mem_fu_list = ["bmem", "bmem-ctrl"]
            mem_solution_sample_ratio = 0.1
            mem_solution_sample_limit = 2

            comp_enable = False 
            comp_fu_list = ["fadd", "fmult"]
            comp_solution_sample_ratio = 0.4
            comp_solution_sample_limit = 3
            
            if (len(color_solution_number) > 5):
                mem_solution_sample_limit = 1
                comp_solution_sample_limit = 1 
            elif (len(color_solution_number) > 4):
                mem_solution_sample_limit = 1
                comp_solution_sample_limit = 2

            
            if not os.path.exists('{}/{}/{}'.format(sampled_solutions_path, design_point_name, fu_name_full)):
                os.mkdir('{}/{}/{}'.format(sampled_solutions_path, design_point_name, fu_name_full))
            fu_name = fu_name_full.split('_')[-1]
            fu_solution_taken = 0

            # if idx == fu_idx:
            #     mem_enable = True
            #    # comp_enable = True
            # else:
            #     mem_enable = False
            #     # comp_enable = False

            if fu_name in mem_fu_list and mem_enable:
            
                

                for num_color, num_solution in color_solution_number.items():
                    # adjust the size
                    # if len(color_solution_number.items()) >
                    

                    num_solution_taken = round(num_solution * mem_solution_sample_ratio)
                    if num_solution_taken == 0:
                        num_solution_taken = 1
                    elif num_solution_taken > mem_solution_sample_limit:
                        num_solution_taken = mem_solution_sample_limit
                    
                    fu_solution_taken += num_solution_taken
                    
                    i = 0
                    for color_solution in os.listdir('{}/{}/{}/{}'.format(filtered_solutions_path, design_point_name, fu_name_full, num_color)):
                        if i == num_solution_taken:
                            break
                        shutil.copy('{}/{}/{}/{}/{}'.format(filtered_solutions_path, design_point_name, fu_name_full, num_color, color_solution), '{}/{}/{}/'.format(sampled_solutions_path, design_point_name, fu_name_full))
                        #print('Copy {} to sampled_solutions for design point {}'.format(color_solution, design_point_name))
                        #print('------------------')
                        i += 1
            elif fu_name in comp_fu_list and comp_enable:
                for num_color, num_solution in color_solution_number.items():
                    num_solution_taken = round(num_solution * comp_solution_sample_ratio)
                    if num_solution_taken == 0:
                        num_solution_taken = 1
                    elif num_solution_taken > comp_solution_sample_limit:
                        num_solution_taken = comp_solution_sample_limit
                    fu_solution_taken += num_solution_taken
                    i = 0
                    for color_solution in os.listdir('{}/{}/{}/{}'.format(filtered_solutions_path, design_point_name, fu_name_full, num_color)):               
                        if i == num_solution_taken:
                            break
                        shutil.copy('{}/{}/{}/{}/{}'.format(filtered_solutions_path, design_point_name, fu_name_full, num_color, color_solution), '{}/{}/{}/'.format(sampled_solutions_path, design_point_name, fu_name_full))
                        #print('Copy {} to sampled_solutions for design point {}'.format(color_solution, design_point_name))
                        #print('------------------')
                        i += 1
            else:
                # only pick one solution from the least number of colors
                num_color = min(color_solution_number.keys())
                fu_solution_taken += 1
                for color_solution in os.listdir('{}/{}/{}/{}'.format(filtered_solutions_path, design_point_name, fu_name_full, num_color)):
                    print("not applying ratio")
                    shutil.copy('{}/{}/{}/{}/{}'.format(filtered_solutions_path, design_point_name, fu_name_full, num_color, color_solution), '{}/{}/{}/'.format(sampled_solutions_path, design_point_name, fu_name_full))
                    #print('Copy {} to sampled_solutions for design point {}'.format(color_solution, design_point_name))
                    #print('------------------')
                    break
            
            print("fu_solution_taken: ", fu_solution_taken)
            design_point_solution_count *= fu_solution_taken


        f.write(str(design_point_solution_count) + "\n")
        dataset_solution_count += design_point_solution_count
    f.write("overall, " + str(dataset_solution_count) + "\n")
    f.close()        


if __name__ == '__main__':
    filter_enabled = sys.argv[1]
    
    solution_number = filter_function_unit()

    print("solution_number:", solution_number)

    # sample coloring solutions for each design point
    # sample_coloring_result(["atax_io1_l1n1n1_l3n1n1"], [])


    # iterate over all sampled solutions
    # 
    if os.path.exists(final_solutions_path):
        shutil.rmtree(final_solutions_path)
    os.mkdir(final_solutions_path)

    sample_coloring_result_mem(solution_number)

    for design_point_name in os.listdir(sampled_solutions_path):
        design_point_coloring_solutions = []
        
        if os.path.isfile('{}/{}'.format(sampled_solutions_path, design_point_name)):
            continue

        design_point_fu_description = ",".join(sorted(os.listdir('{}/{}'.format(sampled_solutions_path, design_point_name)), key=lambda x: int(x.split('_')[2])))

        # iterate through all function units and combine the solutions
        for fu_solution in sorted(os.listdir('{}/{}'.format(sampled_solutions_path, design_point_name)), key=lambda x: int(x.split('_')[2])):
            fu_name = fu_solution.split('_')[-2]
            
            fu_coloring_solutions = []
            for coloring_solution in os.listdir('{}/{}/{}'.format(sampled_solutions_path, design_point_name, fu_solution)):
                # use the full path of the coloring result csv as the coloring solution name
                fu_coloring_solutions.append('{}/{}/{}/{}'.format(sampled_solutions_path, design_point_name, fu_solution, coloring_solution))
            
            design_point_coloring_solutions.append(fu_coloring_solutions)


        
        candidate_solutions = list(itertools.product(*design_point_coloring_solutions))
        
        design_point_final_solution_path = "{}/{}".format(final_solutions_path, design_point_name)
        
        if not os.path.exists(design_point_final_solution_path):
            os.mkdir(design_point_final_solution_path)

        # f = open("{}/coloring_solutions_info.csv".format(design_point_final_solution_path), "w")
        # f.write("coloring_solution_index,{}\n".format(design_point_fu_description))


        for index, candidate in enumerate(candidate_solutions):
            print("candidate solution: ", candidate)
            
            # get specific functional unit config
            fu_config_name = "fu"
            for fu_solution in candidate:
                fu_num = fu_solution.split('/')[-2].split('_')[-2]
                color_num = fu_solution.split('/')[-1].split('_')[1]
                fu_config_name = "_".join([fu_config_name, fu_num, color_num])
                print("fu_name: ", fu_name)
                print("color_num: ", color_num)
            print("fu_config_name: ", fu_config_name)
            target_csv_path = design_point_final_solution_path + "/"

            if not os.path.exists(target_csv_path):
                os.mkdir(target_csv_path)
            # f.write(str(index))

            # for coloring_solution in candidate:
            #     f.write(",{}".format(coloring_solution.split('/')[-1][:-4]))

            # f.write("\n")

            target_csv_path += 'coloring_{}_{}.csv'.format(str(index), fu_config_name)
            
            
            merge_coloring_solutions(candidate, target_csv_path)

            
                
                # file_list = ['./raw/CG_solutions/' + design_point_name + '/' + coloring_solution]
                # new_df = merge(file_list)
                # new_df.to_csv('./raw/CG_solutions/' + design_point_name + '/' + coloring_solution, index=False)
                # print('Finish merging ' + coloring_solution)
                # print(new_df)
                # print('------------------')