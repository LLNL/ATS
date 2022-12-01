CXX=mpicxx

# Toss Build
#CXFLAGS=-g -qopenmp -pthread -O2

# Blueos Build and Toss4 Cray
CXFLAGS=-g -fopenmp -O2


#CXFLAGS=-openmp -pthread -O2 -axcore-avx2,mic-avx512
#CXFLAGS=-openmp -pthread -O2 -axmic-avx512

omp_test:omp_test.cc
	$(CXX) $(CXFLAGS) -o omp_test omp_test.cc

clean:
	rm omp_test 
