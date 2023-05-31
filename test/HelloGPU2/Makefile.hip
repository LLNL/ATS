#
# 2023 May 23 Tested with the following modules loaded
#
# module load python/3.9.12
# module load rocmcc/5.5.0-cce-15.0.1g-magic
# export ROCR_VISIBLE_DEVICES=0,1,2,3
# export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/tce/packages/rocmcc/rocmcc-5.5.0-cce-15.0.1g-magic/llvm/lib
# export CXI_FORK_SAFE=1
# export CXI_FORK_SAFE_HP=1
# export MPICH_SMP_SINGLE_COPY_MODE=NONE

CXX      = 	mpihipcc
CXXFLAGS = 	-ffp-contract=off -ggdb -O2 -finline-functions -std=c++14 -DHAVE_HIP \
		   	-x hip -std=c++14 -fgpu-rdc --offload-arch=gfx90a \
			-Wno-gpu-maybe-wrong-side -Wno-unused-command-line-argument \
		 	-Wl,-Map,load.map.hip \
		    -I. -I/usr/tce/packages/rocmcc/rocmcc-5.5.0-cce-15.0.1g-magic/include 
LD       = 	mpihipcc
LDFLAGS  =	 		

a.out:gputest_this.cc
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o a.out gputest_this.cc

clean:
	rm -vf a.out
	rm -vf load.map*

# ----------------------------------------------------------------------------------------
# End of file
# ----------------------------------------------------------------------------------------
