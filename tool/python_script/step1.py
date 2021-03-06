# This script is used for the geme mapping

import os
import sys
import multiprocessing
import ntpath

# variable definiton
tool_path = sys.argv[1]
data_path = ""
IGC_reference_database = ""
output_path_intermediate = ""
output_path_catalog = ""
user_provided_index = ""

# parsing arguments
count = 2
while count < len(sys.argv):
    if sys.argv[count] == '-s':
        data_path = sys.argv[count + 1]
    elif sys.argv[count] == '-ref':
        IGC_reference_database = sys.argv[count + 1]
    elif sys.argv[count] == '-ind':
        user_provided_index = sys.argv[count + 1]
    elif sys.argv[count] == '-o1':
        output_path_intermediate = sys.argv[count + 1]
    elif sys.argv[count] == '-o2':
        output_path_catalog = sys.argv[count + 1]
    count = count + 1
# check argument
if os.path.isdir(data_path) == False:
    print "ERROR - The path of data directory is invalid: " + data_path
    sys.exit()
if os.path.exists(IGC_reference_database) == False:
    print "ERROR - The path of IGC reference database is invalid: " + IGC_reference_database 
    sys.exit()
if os.path.isdir(IGC_reference_database) == True:
    print "ERROR - The path of IGC reference should be file instead of directory: " + IGC_reference_database 
    sys.exit()
if len(user_provided_index) != 0 and os.path.isdir(user_provided_index) == False:
    print "ERROR - The path of Index folder is invalid: " + user_provided_index 
    sys.exit()
if os.path.isdir(output_path_intermediate) == False:
    print "ERROR - The path of alignment result directory is invalid: " + output_path_intermediate
    sys.exit()
if os.path.isdir(output_path_catalog) == False:
    print "ERROR - The path of catalog directory is invalid: " + output_path_catalog
    sys.exit()

# print out arguments for user
print "The path of genome datasets is " + data_path
if len(IGC_reference_database) != 0:
    print "The path of reference database is " + IGC_reference_database
if len(user_provided_index) != 0:
    print "The path of index folder is " + user_provided_index
print "The alignment result directory is " + output_path_intermediate
print "The catalog output directory is " + output_path_catalog


#  set tool directory
DNA_outputName = ""
RNA_outputName = ""
Bowtie2_dir = tool_path + "/bowtie2"
if os.path.isdir(Bowtie2_dir) == False or os.path.exists(Bowtie2_dir + "/bowtie2-build") == False or os.path.exists(Bowtie2_dir + "/bowtie2") == False:
    print "ERROR - can't detect bowtie2" 
    sys.exit()
Bedtools_dir = tool_path + "/bedtools/bin"
if os.path.isdir(Bedtools_dir) == False or os.path.exists(Bedtools_dir + "/bedtools") == False:
    print "ERROR - can't detect Bedtools" 
    sys.exit()
Samtools_dir = tool_path + "/samtools"
if os.path.isdir(Samtools_dir) == False or os.path.exists(Samtools_dir + "/samtools") == False:
    print "ERROR - can't detect Samtools" 
    sys.exit()
if len(user_provided_index) == 0:
    build_index = os.path.dirname(IGC_reference_database) + "/build_index"
else:
    build_index = user_provided_index

# define build index pipeline
def buildIndex(build_index, provideDB_path):
    # build index for the reference database
    if os.path.isdir( build_index ) == True: # if build_index folder exists
        if len(os.listdir(build_index)) == 0: # if it is empty
            build_index = build_index + "/IGC_ref"
            os.system(Bowtie2_dir + "/bowtie2-build " + provideDB_path + " " + build_index) #  build index
        else: # if it is not empty, get the prefix
            index_files = sorted(os.listdir(build_index))
            prefix = index_files[0][:-7]
            build_index = build_index + "/" + prefix
    else:
        os.system("mkdir " + build_index)
        build_index = build_index + "/IGC_ref"
        os.system(Bowtie2_dir + "/bowtie2-build " + provideDB_path + " " + build_index) #  build index
    return build_index

# define gene mapping pipeline
def pipeline(build_index, provideDB_path, DNA_dir, RNA_dir, DNA_first, DNA_second, RNA_first, RNA_second, output_path, DNA_outputName, RNA_outputName):    
    # metagenome mapping
    # bowtie2
    if DNA_second == "false": # single end
        os.system(Bowtie2_dir + "/bowtie2 -x " + build_index + " -U " + DNA_dir + "/" + DNA_first + " -S " + output_path + "/" + DNA_outputName + ".sam")
    else: # pair end
        os.system(Bowtie2_dir + "/bowtie2 -x " + build_index + " -1 " + DNA_dir + "/" + DNA_first + " -2 " + DNA_dir + "/" + DNA_second + " -S " + output_path + "/" + DNA_outputName + ".sam")
    # samtools
    os.system(Samtools_dir + "/samtools view -bS " + output_path + "/" + DNA_outputName + ".sam > " + output_path + "/" + DNA_outputName + ".bam")
    if os.path.exists(provideDB_path + ".bed") == False:
        os.system("awk '/^>/ {if (seqlen){print \"0\t\"seqlen-1}; gsub(/^>/,\"\",$1);printf(\"%s\t\",$1) ;seqlen=0;next; } { seqlen += length($0)}END{print \"0\t\"seqlen-1}' " + provideDB_path + " > " + provideDB_path + ".bed")
    #bedtools
    os.system(Bedtools_dir + "/bedtools coverage -abam " + output_path + "/" + DNA_outputName + ".bam -b " + provideDB_path + ".bed > " + output_path + "/" + DNA_outputName + ".coverage")

    # metatranscriptome mapping
    #bowtie2
    if RNA_second == "false": # single end
        os.system(Bowtie2_dir + "/bowtie2 -x " + build_index + " -U " + RNA_dir + "/" + RNA_first + " -S " + output_path + "/" + RNA_outputName + ".sam")
    else:
        os.system(Bowtie2_dir + "/bowtie2 -x " + build_index + " -1 " + RNA_dir + "/" + RNA_first + " -2 " + RNA_dir + "/" + RNA_second + " -S " + output_path + "/" + RNA_outputName + ".sam")
    # samtools
    os.system(Samtools_dir + "/samtools view -bS " + output_path + "/" + RNA_outputName + ".sam > " + output_path + "/" + RNA_outputName + ".bam")
    #bedtools
    os.system(Bedtools_dir + "/bedtools coverage -abam " + output_path + "/" + RNA_outputName + ".bam -b " + provideDB_path + ".bed > " + output_path + "/" + RNA_outputName + ".coverage")

    # merging
    os.system("bash -c \" join -j 1 -o 1.1,1.2,1.3,1.4,1.5,1.7,2.4,2.5,2.7 <(sort -k1 " + output_path + "/" + DNA_outputName + ".coverage) <(sort -k1 " + output_path + "/" + RNA_outputName + ".coverage) > " + output_path + "/" + DNA_outputName + "_" + RNA_outputName + ".coverage \"")
    
    # 11 columns
    # os.system("awk '{if ($3 + 0 != 0 && $6 + 0 != 0 && $9 + 0 != 0) print $1 \"\t\" $2 \"\t\" $3 \"\t\" $4 \"\t\" $5 \"\t\" $6 \"\t\" $7 \"\t\" $8 \"\t\" $9 \"\t\" (($7 / $3) / ($4 / $3)) \"\t\" (($7 / $9) / ($4 / $6))}' " + output_path + "/" + DNA_outputName + "_" + RNA_outputName + ".coverage > " + output_path + "/" + DNA_outputName + "_" + RNA_outputName + ".integrative_coverage")
    # 10 columns
    os.system("awk '{if ($3 + 0 != 0 && $6 + 0 != 0 && $9 + 0 != 0) print $1 \"\t\" $2 \"\t\" $3 \"\t\" $4 \"\t\" $5 \"\t\" $6 \"\t\" $7 \"\t\" $8 \"\t\" $9 \"\t\" (($7 / $3) / ($4 / $3)) }' " + output_path + "/" + DNA_outputName + "_" + RNA_outputName + ".coverage > " + output_path + "/" + DNA_outputName + "_" + RNA_outputName + ".integrative_coverage")
    
    # delete useless file
    os.system("rm -rf " + output_path + "/" + DNA_outputName + "_" + RNA_outputName + ".coverage" )

    # put integrative coverage file to the cat folder
    os.system("mv " + output_path + "/" + DNA_outputName + "_" + RNA_outputName + ".integrative_coverage " + output_path_catalog + "/" + fileName + ".cat")


# build index first
build_index = buildIndex(build_index, IGC_reference_database)

# detecting datasets directory and processing them
fileNames = os.listdir(data_path)
processes = []
for fileName in fileNames:
    DNA_first = ""
    DNA_second = ""
    RNA_first = ""
    RNA_second = ""
    if os.path.isdir(data_path + "/" + fileName + "/DNA") == True and os.path.isdir(data_path + "/" + fileName + "/RNA") == True: # means both dna and rna dataset exist
        # check dna folder
        if len(os.listdir(data_path + "/" + fileName + "/DNA")) == 1:
            DNA_first = os.listdir(data_path + "/" + fileName + "/DNA")[0]
            DNA_second = "false"
        elif len(os.listdir(data_path + "/" + fileName + "/DNA")) == 2:
            DNA_first = os.listdir(data_path + "/" + fileName + "/DNA")[0]
            DNA_second = os.listdir(data_path + "/" + fileName + "/DNA")[1]
        else:
            print "ERROR - The dataset: " + fileName + " missing metagenome files"
        # check rna folder
        if len(os.listdir(data_path + "/" + fileName + "/RNA")) == 1:
            RNA_first = os.listdir(data_path + "/" + fileName + "/RNA")[0]
            RNA_second = "false"
        elif len(os.listdir(data_path + "/" + fileName + "/RNA")) == 2:
            RNA_first = os.listdir(data_path + "/" + fileName + "/RNA")[0]
            RNA_second = os.listdir(data_path + "/" + fileName + "/RNA")[1]
        else:
            print "ERROR - The dataset: " + fileName + " missing metatranscriptome files"
        # passing parameter

        # create output file
        if os.path.isdir(output_path_intermediate + "/" + fileName) == False:
            os.system("mkdir " + output_path_intermediate + "/" + fileName)
        
        DNA_outputName = fileName + "_DNA"
        RNA_outputName = fileName + "_RNA"
        print "Processing " + ntpath.basename(fileName)
        t = multiprocessing.Process(target=pipeline, args=(build_index, IGC_reference_database, data_path + "/" + fileName + "/DNA", data_path + "/" + fileName + "/RNA", DNA_first, DNA_second, RNA_first, RNA_second, output_path_intermediate + "/" + fileName, DNA_outputName, RNA_outputName,))
        processes.append(t)
        t.start()
        # pipeline(build_index, IGC_reference_database, data_path + "/" + fileName + "/DNA", data_path + "/" + fileName + "/RNA", DNA_first, DNA_second, RNA_first, RNA_second, alignment_results + "/" + fileName)
    else: # missing dna or rna dataset report error
        print "ERROR - The dataset: " + fileName + " missing metagenome or metatranscriptome datasets. Skip to processing next datasets"

for one_process in processes:
    one_process.join()
