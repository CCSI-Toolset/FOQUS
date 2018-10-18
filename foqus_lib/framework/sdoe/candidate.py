import pandas as pd

def write_candidates(cfile, cand, col_names):
    # Write candidate file
    cand_panda = pd.DataFrame(cand, columns=col_names)  # cand = des_pt_bound
    cand_panda.to_csv(cfile, index=False)  # do not write row names
    return cand_panda
    
def load_candidates(cfile):
    # Load candidate file (or history file)
    cand_panda = pd.read_csv(cfile)
    cand = cand_panda.values
    header = list(cand_panda.columns.values)
    return cand, header

# TO DO: error checking    
