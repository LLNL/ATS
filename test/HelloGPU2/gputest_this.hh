// ----------------------------------------------------------------------------------------
// Portable Wrappers for CUDA/NVCC
// ----------------------------------------------------------------------------------------

#if defined (HAVE_NVCC)

#define SADGPU_ASSERT(status) assert(status == cudaSuccess)

#define SADGPU_CHECK(status)                                                                                            \
    if (status != cudaSuccess)                                                                                         \
    {                                                                                                                  \
        printf("%s:%d CUDA ERROR: %d\n", __FILE__, __LINE__, status);                                                  \
        printf("%s:%d CUDA ERROR: %s\n", __FILE__, __LINE__, cudaGetErrorName(status));                                \
        printf("%s:%d CUDA ERROR: %s\n", __FILE__, __LINE__, cudaGetErrorString(status));                              \
        SADGPU_ASSERT(status);                                                                                          \
    }

#define SADGPU_DEVICE_PROP                   cudaDeviceProp
#define SADGPU_MEMCPY_HOST_TO_DEVICE         cudaMemcpyHostToDevice
#define SADGPU_MEMCPY_HOST_TO_HOST           cudaMemcpyHostToHost
#define SADGPU_MEMCPY_DEVICE_TO_HOST         cudaMemcpyDeviceToHost
#define SADGPU_VISIBLE_DEVICES               "CUDA_VISIBLE_DEVICES"
#define SADGPU_DEVICE_SYNCRHONIZE            cudaDeviceSynchronize
#define SADGPU_DEVICE_RESET()                SADGPU_CHECK(cudaDeviceReset())
#define SADGPU_DRIVER_GET_VERSION(x)         SADGPU_CHECK(cudaDriverGetVersion(x))
#define SADGPU_RUNTIME_GET_VERSION(x)        SADGPU_CHECK(cudaRuntimeGetVersion(x))
#define SADGPU_GET_DEVICE(x)                 SADGPU_CHECK(cudaGetDevice(x))
#define SADGPU_GET_DEVICE_COUNT(x)           SADGPU_CHECK(cudaGetDeviceCount(x))
#define SADGPU_GET_DEVICE_PROPERTIES(x, y)   SADGPU_CHECK(cudaGetDeviceProperties(x, y))
#define SADGPU_GET_DEVICE_PCI_BUS_ID(x,y,z)  SADGPU_CHECK(cudaDeviceGetPCIBusId(x, y, z))
#define SADGPU_MALLOC(x, y)                  SADGPU_CHECK(cudaMalloc(x, y))
#define SADGPU_MEMCPY(w, x, y, z)            SADGPU_CHECK(cudaMemcpy(w, x, y, z))
#define SADGPU_MEMCPY_NOCHECK(w, x, y, z)    cudaMemcpy(w, x, y, z)
#define SADGPU_PEEK_AT_LAST_ERROR()          SADGPU_CHECK(cudaPeekAtLastError())
#define SADGPU_FREE(x)                       SADGPU_CHECK(cudaFree(x))
#define SADGPU_SET_DEVICE(x)                 SADGPU_CHECK(cudaSetDevice(x))
#define SADGPU_SET_DEVICE_FLAGS(x)           SADGPU_CHECK(cudaSetDeviceFlags(x))
#define SADGPU_MALLOC_MANAGED(x, y)          SADGPU_CHECK(cudaMallocManaged(x, (y)))



// ----------------------------------------------------------------------------------------
// Portable Wrappers for HIP/ROCM
// ----------------------------------------------------------------------------------------

#elif defined (HAVE_HIP)

#include <hip/hip_version.h>
#include <hip/hip_runtime.h>
#include <hip/hip_runtime_api.h>
#include <hip/hip_common.h>

#define SADGPU_ASSERT(status) assert(status == hipSuccess)

#define SADGPU_CHECK(status)                                                            \
    if (status != hipSuccess)                                                           \
    {                                                                                   \
        printf("%s:%d HIP ERROR: %d\n", __FILE__, __LINE__, status);                    \
        printf("%s:%d HIP ERROR: %s\n", __FILE__, __LINE__, hipGetErrorName(status));   \
        printf("%s:%d HIP ERROR: %s\n", __FILE__, __LINE__, hipGetErrorString(status)); \
        SADGPU_ASSERT(status);                                                          \
    }

#define SADGPU_DEVICE_PROP                   hipDeviceProp_t
#define SADGPU_MEMCPY_HOST_TO_DEVICE         hipMemcpyHostToDevice
#define SADGPU_MEMCPY_HOST_TO_HOST           hipMemcpyHostToHost
#define SADGPU_MEMCPY_DEVICE_TO_HOST         hipMemcpyDeviceToHost
#define SADGPU_VISIBLE_DEVICES               "ROCR_VISIBLE_DEVICES"
#define SADGPU_VISIBLE_DEVICES_OLD           "HIP_VISIBLE_DEVICES"
#define SADGPU_DEVICE_SYNCRHONIZE            hipDeviceSynchronize

#define SADGPU_DEVICE_RESET()                SADGPU_CHECK(hipDeviceReset())
#define SADGPU_DRIVER_GET_VERSION(x)         SADGPU_CHECK(hipDriverGetVersion(x))
#define SADGPU_RUNTIME_GET_VERSION(x)        SADGPU_CHECK(hipRuntimeGetVersion(x))
#define SADGPU_GET_DEVICE(x)                 SADGPU_CHECK(hipGetDevice(x))
#define SADGPU_GET_DEVICE_COUNT(x)           SADGPU_CHECK(hipGetDeviceCount(x))
#define SADGPU_GET_DEVICE_PROPERTIES(x, y)   SADGPU_CHECK(hipGetDeviceProperties(x, y))
#define SADGPU_GET_DEVICE_PCI_BUS_ID(x,y,z)  SADGPU_CHECK(hipDeviceGetPCIBusId(x, y, z))
#define SADGPU_MALLOC(x, y)                  SADGPU_CHECK(hipMalloc(x, y))
#define SADGPU_MEMCPY(w, x, y, z)            SADGPU_CHECK(hipMemcpy(w, x, y, z))
#define SADGPU_PEEK_AT_LAST_ERROR()          SADGPU_CHECK(hipPeekAtLastError())
#define SADGPU_FREE(x)                       SADGPU_CHECK(hipFree(x))
#define SADGPU_SET_DEVICE(x)                 SADGPU_CHECK(hipSetDevice(x))
#define SADGPU_SET_DEVICE_FLAGS(x)           SADGPU_CHECK(hipSetDeviceFlags(x))
#define SADGPU_MALLOC_MANAGED(x, y)          SADGPU_CHECK(hipMallocManaged(x, (y)))

#endif

// ----------------------------------------------------------------------------------------
// Classes
// ----------------------------------------------------------------------------------------

#define ARRAY_SIZE 16


class Cuda_Hello_Class
{
public:
    int blocksize = ARRAY_SIZE;
    int csize = ARRAY_SIZE*sizeof(char);
    int isize = ARRAY_SIZE*sizeof(int);

    char a[ARRAY_SIZE] = "Hello \0\0\0\0\0\0";
    int  b[ARRAY_SIZE] = {15, 10, 6, 0, -11, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
    char c[ARRAY_SIZE] = "012345678901234";

    char  *am;
    int   *bm;

    Cuda_Hello_Class() : am(nullptr), bm(nullptr) {};
    void Hello_World_Works_With_NVCC(void);
    void Hello_World_Workaroud_Hip_Issue(void);

    void Reset(void)
    {
        blocksize = ARRAY_SIZE;
        csize = ARRAY_SIZE*sizeof(char);
        isize = ARRAY_SIZE*sizeof(int);
        strncpy(a,"Hello \0\0\0\0\0\0",16);
        b[0] = 15; b[1]=10; b[2]=6, b[3]=0; b[4]=-11; b[5]=1;
        b[6] = b[7] = b[8] = b[9] = b[10] = b[11] = b[12] = b[13] = b[14] = b[15] = 0;
        strncpy(c,"012345678901234",16);
        am = nullptr;
        bm = nullptr;
    }
};


