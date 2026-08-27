##
## LINUX barebone makefile for c++ examples
##

Libs     := -L../../../bin/x86_64-linux -lsnap7 -lpthread -lrt
Wrapper  := snap7.cpp

CXX      := g++
CC       := gcc
CXXFLAGS := -O3 -std=c++11
CFLAGS   :=

.PHONY: all clean

all:
	$(CXX) $(CXXFLAGS) -o client ../client.cpp ../$(Wrapper) $(Libs)
	$(CXX) $(CXXFLAGS) -o server ../server.cpp ../$(Wrapper) $(Libs)
	$(CXX) $(CXXFLAGS) -o srv_resourceless ../srv_resourceless.cpp ../$(Wrapper) $(Libs)
	$(CXX) $(CXXFLAGS) -o apartner ../apartner.cpp ../$(Wrapper) $(Libs)
	$(CXX) $(CXXFLAGS) -o ppartner ../ppartner.cpp ../$(Wrapper) $(Libs)
	$(CXX) $(CXXFLAGS) -pthread -o loopback_test ../loopback_test.cpp ../$(Wrapper) $(Libs)

clean:
	$(RM) client server srv_resourceless apartner ppartner loopback_test
