#
# Win64 barebone makefile for c++ examples.
#

MINGW    ?= $(shell dirname $(shell dirname $(shell which g++)))

CPP      = g++.exe
CC       = gcc.exe
LIBS     = -static-libgcc -static-libstdc++ -L. -lsnap7
INCS     = -I"../"
CXXINCS  = -I"../"
CXXFLAGS = $(CXXINCS)
CFLAGS   = $(INCS)
RM       = rm -f

.PHONY: all clean

all:
$(CPP) -o client.exe ../client.cpp ../snap7.cpp $(LIBS) $(CXXFLAGS)
$(CPP) -o server.exe ../server.cpp ../snap7.cpp $(LIBS) $(CXXFLAGS)
$(CPP) -o srv_resourceless.exe ../srv_resourceless.cpp ../snap7.cpp $(LIBS) $(CXXFLAGS)
$(CPP) -o apartner.exe ../apartner.cpp ../snap7.cpp $(LIBS) $(CXXFLAGS)
$(CPP) -o ppartner.exe ../ppartner.cpp ../snap7.cpp $(LIBS) $(CXXFLAGS)
$(CPP) -o loopback_test.exe ../loopback_test.cpp ../snap7.cpp $(LIBS) $(CXXFLAGS)

clean:
${RM} client.exe server.exe srv_resourceless.exe apartner.exe ppartner.exe loopback_test.exe
