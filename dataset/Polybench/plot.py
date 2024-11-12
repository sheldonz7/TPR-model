import pandas as pd
import matplotlib.pyplot as plt
import os
import matplotlib.patches as mpatches
import numpy as np
#output file postion: ./png/ranked/@ and ./png/non_ranked/@ ( @ is the name such as atax, bicg......)
#ranked folder contains the png file whose bar is ranked by the y axis value (non_ranked is on the opposite)

#the relative path of bambu_default_vivado_run_status.csv
bambu_default = './bambu_default_vivado_run_status.csv'
#the relative path of custom_coloring_vivado_run_status.csv
custom_coloring = './custom_coloring_vivado_run_status.csv'
#this is the design
design = ['atax', 'bicg', 'gemm', 'gesummv', 'k2mm', 'k3mm']
#design category you want to plot
Xs = ['CP_latency','dynamic_pwr', 'lut']

def plot_bar_func(name, design_point, df, x_index, mi, ma, type1, rows_b, CP_min, CP_max, bar):
    min = mi
    max = ma
    t = type1
    
    rows = df
    rb = rows_b
    text_val = list()
    #'WEIGHTED_TS': green
    #'TS': blue
    #'WEIGHTED_COLORING': purple
    #'COLORING': orange
    #'TTT_FAST': pink
    #'BIPARTITE_MATCHING': #6F4E37
    #normal : black

    #assign color for bar graph 
    def assign_color(sol):
        if sol == 'WEIGHTED_TS':
            return 'green'
        elif sol == 'TS':
            return 'blue'
        elif sol == 'WEIGHTED_COLORING':
            return 'purple'
        elif sol == 'COLORING':
            return 'orange'
        elif sol == 'TTT_FAST':
            return 'pink'
        elif sol == 'BIPARTITE_MATCHING':
            return '#6F4E37'
        else: 
            return 'black'
    # assign color for dot graph 
    def assign_color1(sol):
        if sol == 'WEIGHTED_TS':
            return 'green'
        elif sol == 'TS':
            return 'blue'
        elif sol == 'WEIGHTED_COLORING':
            return 'purple'
        elif sol == 'COLORING':
            return 'orange'
        elif sol == 'TTT_FAST':
            return 'pink'
        elif sol == 'BIPARTITE_MATCHING':
            return '#6F4E37'
        else: 
            return 'black'
    text_val=text_val+rb[x_index].tolist()
    rows['CP_latency_str'] = rows['CP_latency'].astype(str)
    #rows['color'] = rows[x_index].apply(lambda x: assign_color_c(x, min, max))
    rows['color'] = rows['Coloring solution'].apply(lambda x: assign_color(x))
    rows.loc[rows[x_index] == min, 'color'] = 'skyblue'
    rows.loc[rows[x_index] == max, 'color'] = 'red'
    text_val.append(max)
    text_val.append(min)
    y_labels = rows[x_index]
    x_values = rows['Coloring solution']
    print(x_values)
    plt.figure(figsize=(20, 7))

    #ploting the bar graph of CP_latency, dynamic_pwr and lut
    if bar == 'bar':
        bars = plt.bar(x_values, y_labels, color=rows['color'])

        tick = list()
        label = rows['Coloring solution'].tolist()
        num = 0
        for bar in bars:
            height = bar.get_height()
            if height in text_val:
                plt.text(
                    bar.get_x() + bar.get_width()/2,
                    height+height/600,
                    f'{height}',
                    ha='center',
                    va='bottom',
                    rotation=90, 
                    fontsize=5
                )
                tick.append(bar.get_x() + bar.get_width()/2)
            else:
                tick.append(bar.get_x() + bar.get_width()/2)
                label[num] = ''
            num = num +1

        plt.xticks(
            ticks=tick,
            labels=label,
            fontsize = 5,
            rotation = 90
        )

        plt.ylim(min-(max-min)/10, max+(max-min)/10)
        plt.xlim(-2)
        plt.title(t + ' ' + design_point, fontsize=25)
        plt.xlabel('Coloring solution/algo', fontsize=20)
        plt.ylabel(x_index, fontsize=20)

        #the patch is for documenting the relation between color and it's representation
        black_patch = mpatches.Patch(color='black', label='normal value')
        red_patch = mpatches.Patch(color='red', label='max value')
        skyblue_patch = mpatches.Patch(color='skyblue', label='min value')
        green_patch = mpatches.Patch(color='green', label='WEIGHTED_TS')
        blue_patch = mpatches.Patch(color='blue', label='TS')
        purple_patch = mpatches.Patch(color='purple', label='WEIGHTED_COLORING')
        orange_patch = mpatches.Patch(color='orange', label='COLORING')
        pink_patch = mpatches.Patch(color='pink', label='TTT_FAST')
        Coffee_patch = mpatches.Patch(color='#6F4E37', label='BIPARTITE_MATCHING')
        plt.legend(handles=[black_patch, red_patch, skyblue_patch, green_patch, blue_patch, 
                            purple_patch, orange_patch, pink_patch, Coffee_patch])

        plt.tight_layout()
        plt.savefig('./png/{}/{}/{}/{}'.format(t, x_index, name, design_point), dpi=300)
        plt.close()
        print("\nfdjklsfjkdsljfklsdjfkljdskljfklsdjfkldsjklfjdsklfjsdklfjdskljfklsdjl\n")

    #starting plot the dot figure including lut_vs_CPlatency and pwr_vs_CPlatency
    elif x_index in ['dynamic_pwr', 'lut'] and bar == ' ':
        print("\njfdklsjfkdlsjfkldsjlk\n")
        dot_text_val=text_val+rb[x_index].tolist()
        dot_text_label=rows['Coloring solution'].tolist()
        dot_text_tick = list()
        bambu_dot_list = list()
        def bambu_dot(dot):
            bambu_dot_list.append([dot[x_index], dot['CP_latency']])
        
        text_val=text_val+rb[x_index].tolist()
        plt.figure(figsize=(CP_max,CP_max))
        rows['color']=rows['Coloring solution'].apply(lambda x: assign_color1(x))

        dots = plt.scatter(rows[x_index], rows['CP_latency'], color=rows['color'], s=8)

        rb.apply(lambda x: bambu_dot(x), axis=1)
        for dot in bambu_dot_list:
            plt.text(
                dot[0],
                dot[1],
                f"({dot[0]}, {dot[1]})",
                ha = 'center',
                fontsize=10
            )
        offsets = dots.get_offsets()
        nm = 0
        for offset in offsets:
            if offset[0] not in dot_text_val:
                dot_text_label[nm] = ''
            dot_text_tick.append(offset[0])
            nm = nm + 1
        
        if x_index == 'lut':
            plt.ylim(CP_min-(CP_max-CP_min)/10, CP_max+(CP_max-CP_min)/10)
            plt.xlim(min-10, max+10)
            # modify the format for x ticks
            plt.xticks(
                #ticks=dot_text_tick,
                #labels=dot_text_label,
                np.arange(min, max, (max-min)/8),
                fontsize = 10,
                #rotation = 90
                )
            
            #modify the format for y ticks
            plt.yticks(
                np.arange(CP_min, CP_max, (CP_max-CP_min)/8),
                fontsize = 10,
                rotation = 90
            )
        else:
            plt.ylim(CP_min-(CP_max-CP_min)/10, CP_max+(CP_max-CP_min)/10)
            plt.xlim(min-0.005, max+0.005)
            
            #modify the format for x ticks
            plt.xticks(
                #cahnge x ticks
                #ticks=dot_text_tick,
                #labels=dot_text_label,
                np.arange(min, max, (max-min)/8),
                fontsize = 10,
                #rotation = 90
                )
            #modify the format for x ticks
            plt.yticks(
                #change the y ticks 
                np.arange(CP_min, CP_max, (CP_max-CP_min)/8),
                fontsize = 10,
                rotation = 90
            )
            
        plt.title(t + ' ' + x_index + ' ' + design_point, fontsize=25)
        plt.xlabel(x_index, fontsize=20)
        plt.ylabel('CP_latency value', fontsize=20)
        #plot grid in the graph
        #plt.grid(True)

        #the patch is for documenting the relation between color and it's representation
        black_patch = mpatches.Patch(color='black', label='normal value')
        green_patch = mpatches.Patch(color='green', label='WEIGHTED_TS')
        blue_patch = mpatches.Patch(color='blue', label='TS')
        purple_patch = mpatches.Patch(color='purple', label='WEIGHTED_COLORING')
        orange_patch = mpatches.Patch(color='orange', label='COLORING')
        pink_patch = mpatches.Patch(color='pink', label='TTT_FAST')
        Coffee_patch = mpatches.Patch(color='#6F4E37', label='BIPARTITE_MATCHING')
        plt.legend(handles=[black_patch, green_patch, blue_patch, purple_patch, orange_patch, 
                            pink_patch, Coffee_patch])
        plt.tight_layout()
        print("jfkdlsjfklsdjklfdsjkfjdskljflkdsjlkfj")
        if x_index == 'dynamic_pwr':
            plt.savefig('./png/{}/pwr_vs_CPlatency/{}/{}'.format(t, name, design_point), dpi=300)
        else:
            plt.savefig('./png/{}/lut_vs_CPlatency/{}/{}'.format(t, name, design_point), dpi=300)
        plt.close()
    
#ranking the number in each x_idx(the evaluation such as CP_latency)
def rank(df, x_idx, design_p):
    df_merged=df
    x_index1=x_idx
    design_point=design_p
    data_b = pd.read_csv(bambu_default)
    rows_b = data_b[data_b['Design Point'] == design_point]
    rows = df_merged[df_merged['Design Point'] == design_point]
    
    sorted_rows=rows.sort_values(by = x_index1, ascending = True, inplace = False)
    min = sorted_rows[x_index1].iloc[0]
    max = sorted_rows[x_index1].iloc[-1]
    
    print(rows)
    return rows, sorted_rows, min, max, rows_b

def running_routine(x_index):
    x_index1 = x_index
    df_b = pd.read_csv(bambu_default)
    df_b_c = df_b
    columns = df_b.columns.tolist()
    columns[1] = 'Coloring solution'
    df_b_c.columns = columns

    df_c = pd.read_csv(custom_coloring)
    df_merged = pd.concat([df_b_c, df_c], axis = 0, join='outer', ignore_index=True)
   
    existed_DP = list()
    new_DP = ''
    

    for design_point in df_b['Design Point']:
        if design_point not in existed_DP:
            existed_DP.append(design_point)
    #print(existed_DP)
    for point in existed_DP:
        for name in design:
            if name in point:
                if not os.path.exists('./png'):
                    os.mkdir('./png')
                if not os.path.exists('./png/ranked'):
                    os.mkdir('./png/ranked')
                if not os.path.exists('./png/non_ranked'):
                    os.mkdir('./png/non_ranked')
                for choice in ['non_ranked', 'ranked']:
                    if not os.path.exists("./png/{}/{}".format(choice, x_index)):
                        os.mkdir('./png/{}/{}'.format(choice, x_index))
                    if not os.path.exists('./png/{}/{}/{}'.format(choice, x_index, name)):
                        os.mkdir('./png/{}/{}/{}'.format(choice, x_index, name))
                    if not os.path.exists("./png/{}/{}".format(choice, 'pwr_vs_CPlatency')):
                        os.mkdir('./png/{}/{}'.format(choice, 'pwr_vs_CPlatency'))
                    if not os.path.exists("./png/{}/{}".format(choice, 'lut_vs_CPlatency')):
                        os.mkdir('./png/{}/{}'.format(choice, 'lut_vs_CPlatency'))
                    if not os.path.exists('./png/{}/{}/{}'.format(choice, 'lut_vs_CPlatency', name)):
                        os.mkdir('./png/{}/{}/{}'.format(choice, 'lut_vs_CPlatency', name))
                    if not os.path.exists('./png/{}/{}/{}'.format(choice, 'pwr_vs_CPlatency', name)):
                        os.mkdir('./png/{}/{}/{}'.format(choice, 'pwr_vs_CPlatency', name))

                    
                
            #if os.path.exists('./{}/{}'.format(name, design_point)):
            #    os.mkdir('./{}/{}'.format(name, design_point))
            #operate within the same design point
                rows, sorted_rows, min, max, rows_b = rank(df_merged, x_index1, point)
                rows1, s_r, CP_min, CP_max, r_b = rank(df_merged, 'CP_latency', point)
                #print("jdksljfksdljfklsdj", name, design_point)               
                print("\n####### The graph of non_ranked {} {} is graphing #######\n".format(x_index, point))
                plot_bar_func(name, point, rows, x_index1, min, max, 'non_ranked', rows_b, CP_min, CP_max, 'bar')
                print("\n####### The graph of ranked {} {} is graphing #######\n".format(x_index, point))
                plot_bar_func(name, point, sorted_rows, x_index1, min, max, 'ranked', rows_b, CP_min, CP_max, 'bar')

                print("\n####### The graph of non_ranked {} {} is graphing #######\n".format(x_index, point))
                plot_bar_func(name, point, rows, x_index1, min, max, 'non_ranked', rows_b, CP_min, CP_max, ' ')
                print("\n####### The graph of ranked {} {} is graphing #######\n".format(x_index, point))
                plot_bar_func(name, point, sorted_rows, x_index1, min, max, 'ranked', rows_b, CP_min, CP_max, ' ')

if __name__ == '__main__':
    for i in Xs:
        running_routine(i)
                

