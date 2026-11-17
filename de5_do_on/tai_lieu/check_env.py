import os
import numpy
import scipy
import matplotlib
import glob

print("Python version:", __import__('sys').version)
print("numpy version:", numpy.__version__)
print("scipy version:", scipy.__version__)
print("matplotlib version:", matplotlib.__version__)

# Check workspace cwd
cwd = os.getcwd()
print("cwd:", cwd)
print("cwd ends with 'de5_do_on':", cwd.endswith('de5_do_on'))

# Check tai_lieu folder
tai_lieu_paths = glob.glob('**/tai_lieu', recursive=True, root_dir='E:\Đề tài 5')
print("tai_lieu paths found:", tai_lieu_paths)
print("Number of tai_lieu folders:", len(tai_lieu_paths))

# Check mo_phong folder
mo_phong_path = os.path.join('E:\Đề tài 5', 'mo_phong')
print("mo_phong exists:", os.path.exists(mo_phong_path))

# Check matrix.csv
matrix_paths = glob.glob('**/matrix.csv', recursive=True, root_dir='E:\Đề tài 5')
print("matrix.csv paths found:", matrix_paths)
print("Number of matrix.csv:", len(matrix_paths))