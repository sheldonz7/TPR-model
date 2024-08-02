import subprocess
import os

dataset_path = ""

# generate HLS strategy
print("Generating HLS strategy for all Polybench designs")







# run Bambu with the generated strategy
print("Running Bambu with the generated strategy")


for path in os.listdir(dataset_path):
    subprocess.run(
        "docker run --rm --user sqzhou -w workspace/binding-gnn/PandA-bambu/example    bambu-option    ",    
        shell=True, check=True, executable='/bin/bash')





# generate Vivado script(.tcl) for all HLS results
print("Generating Vivado script for all designs and solutions")






# run Vivado on host
print("Running Vivado on host")
subprocess.run(
    "vivado -mode batch -nojournal -nolog -notrace -source script_0.tcl",    
    shell=True, check=True, executable='/bin/bash')
