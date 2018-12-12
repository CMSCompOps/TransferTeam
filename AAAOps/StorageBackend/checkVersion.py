import math, sys, time, subprocess
from subprocess import Popen, PIPE
from shlex import split


with open("cms_site_names.txt", 'r') as f:
	for site in f:
		runCommand = "./storage_backend.sh "+site
		p1 = Popen(runCommand, shell=True)
		p1.wait()
