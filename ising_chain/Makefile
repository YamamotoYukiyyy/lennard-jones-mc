# 一次元イジング鎖 DMRG のビルド
# ITensor は ../ITensor に配置されていることを想定

ITENSOR_DIR = ../ITensor
include $(ITENSOR_DIR)/this_dir.mk
include $(ITENSOR_DIR)/options.mk

TENSOR_HEADERS = $(PREFIX)/itensor/all.h
CCFLAGS = -I. $(ITENSOR_INCLUDEFLAGS) $(CPPFLAGS) $(OPTIMIZATIONS)
CCGFLAGS = -I. $(ITENSOR_INCLUDEFLAGS) $(DEBUGFLAGS)
LIBFLAGS = -L'$(ITENSOR_LIBDIR)' $(ITENSOR_LIBFLAGS)
LIBGFLAGS = -L'$(ITENSOR_LIBDIR)' $(ITENSOR_GLIBFLAGS)

APP = ising_dmrg

.PHONY: build clean

build: $(APP)

$(APP): $(APP).cc $(ITENSOR_LIBS) $(TENSOR_HEADERS)
	$(CCCOM) $(CCFLAGS) $(APP).cc -o $(APP) $(LIBFLAGS)

clean:
	rm -f $(APP) $(APP)-g *.o .debug_objs/*.o
