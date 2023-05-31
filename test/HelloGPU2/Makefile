default:
	@echo Use one of these commands:
	@echo make hip
	@echo make nvcc

hip:
	make -f Makefile.hip

nvcc:
	make -j 4 -f Makefile.nvcc

clean:
	rm -vf a.out
	rm -vf load.map*
