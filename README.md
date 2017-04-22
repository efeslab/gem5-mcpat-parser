# gem5-mcpat-parser
A parser to convert the output of gem5 to a format for McPAT 1.3 (should work for older versions too) as of 2017 for the current version of gem5. This parser is partially incomplete it generates warnings that I do not know how to fix. When you run this parser, it will generate warnings like this:

	Warning: stat system.core0 'committed_fp_instructions' may have not been set!
	Warning: stat system.core0 'rename_writes' may have not been set!
	Warning: stat system.core0 'fp_rename_writes' may have not been set!
	Warning: stat system.core0.itlb 'total_accesses' may have not been set!
	Warning: stat system.core0.itlb 'total_misses' may have not been set!
	Warning: stat system.core0.dtlb 'total_accesses' may have not been set!
	Warning: stat system.core0.dtlb 'total_misses' may have not been set!
	Warning: stat system.core0.dcache 'write_accesses' may have not been set!
	Warning: stat system.core0.dcache 'write_misses' may have not been set!
	Warning: stat system.core0.BTB 'write_accesses' may have not been set!
	Warning: stat system.mc 'memory_writes' may have not been set!

Meaning that the aforementioned values are not set (i.e they are 0). 

To run the parser you can just do

	./gem5-mcpat-parser

In the current directory that contains the config.ini, stats.txt and template.xml file and it will generate a configuration.xml file with the values filled out. Use the -h option for more information.

However (to my understanding) the original creator of the parser made it such that this parser only works for single core simulations. If you try to use this parser with more than 1 CPU (--num-cpus=2 etc) then it will generate a lot more warnings.

This tool is based on a modified version of the 2015 version which can be found at this repository https://github.com/markoshorro/gem5McPATparse.

#Note:

The following modifications were made to this parser:

1) Removal of L3 cache from the template.xml file provided and removal of parsing of L3 cache information from the parser itself. Since gem5 no longer includes an L3 cache in the standard se.py (System call emulation configuration script) 

2) Renaming from gem5McPATparse to gem5-mcpat-parser.


