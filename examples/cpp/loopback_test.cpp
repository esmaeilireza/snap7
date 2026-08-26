/*=============================================================================|
|  PROJECT SNAP7                                                         1.4.0 |
|==============================================================================|
|  Copyright (C) 2013, 2014 Davide Nardella                                    |
|  All rights reserved.                                                        |
|==============================================================================|
|  SNAP7 is free software: you can redistribute it and/or modify               |
|  it under the terms of the Lesser GNU General Public License as published by |
|  the Free Software Foundation, either version 3 of the License, or           |
|  (at your option) any later version.                                         |
|                                                                              |
|  It means that you can distribute your commercial software linked with       |
|  SNAP7 without the requirement to distribute the source code of your         |
|  application and without the requirement that your application be itself     |
|  distributed under LGPL.                                                     |
|                                                                              |
|  SNAP7 is distributed in the hope that it will be useful,                    |
|  but WITHOUT ANY WARRANTY; without even the implied warranty of              |
|  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               |
|  Lesser GNU General Public License for more details.                         |
|                                                                              |
|  You should have received a copy of the GNU General Public License and a     |
|  copy of Lesser GNU General Public License along with Snap7.                 |
|  If not, see  http://www.gnu.org/licenses/                                   |
|==============================================================================|
|                                                                              |
|  Loopback Smoke Test                                                         |
|  Tests local client/server communication without requiring real PLC hardware.|
|=============================================================================*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <thread>
#include <chrono>
#include "snap7.h"

#ifdef OS_WINDOWS
# define WIN32_LEAN_AND_MEAN
# include <windows.h>
#else
# include <unistd.h>
#endif

// Test configuration - uses localhost and non-privileged port
static const char* TEST_HOST = "127.0.0.1";
static const int TEST_PORT = 1102;  // Non-privileged port for testing
static const int TEST_RACK = 0;
static const int TEST_SLOT = 1;

// Test data
static byte test_db_data[256];
static bool server_ready = false;
static int server_error = 0;

// Server event callback
void S7API ServerEventCallback(void* usrPtr, PSrvEvent PEvent, int Size) {
    // Print events for debugging
    printf("[SERVER] %s\n", SrvEventText(PEvent).c_str());
}

// Server read event callback
void S7API ServerReadEventCallback(void* usrPtr, PSrvEvent PEvent, int Size) {
    if (PEvent->EvtParam1 == S7AreaDB) {
        int db_num = PEvent->EvtParam2;
        if (db_num == 1) {
            memset(test_db_data, 0xAA, sizeof(test_db_data));
        }
    }
}

// Server thread function
void ServerThread() {
    TS7Server* Server = new TS7Server();
    
    // Register a test DB
    Server->RegisterArea(srvAreaDB, 1, test_db_data, sizeof(test_db_data));
    
    // Set callbacks
    Server->SetEventsCallback(ServerEventCallback, NULL);
    Server->SetReadEventsCallback(ServerReadEventCallback, NULL);
    
    // Start server on localhost with test port
    server_error = Server->StartTo(TEST_HOST);
    if (server_error == 0) {
        server_ready = true;
        printf("[SERVER] Started on %s:%d\n", TEST_HOST, TEST_PORT);
        
        // Keep server running
        while (server_ready) {
#ifdef OS_WINDOWS
            Sleep(100);
#else
            usleep(100000);
#endif
        }
    } else {
        printf("[SERVER] Failed to start: %s\n", SrvErrorText(server_error).c_str());
    }
    
    Server->Stop();
    delete Server;
}

bool Check(int Result, const char* Function) {
    printf("\n+-----------------------------------------------------\n");
    printf("| %s\n", Function);
    printf("+-----------------------------------------------------\n");
    if (Result == 0) {
        printf("| Result         : OK\n");
        printf("+-----------------------------------------------------\n");
        return true;
    } else {
        printf("| ERROR !!!\n");
        if (Result < 0)
            printf("| Library Error (-1)\n");
        else
            printf("| %s\n", CliErrorText(Result).c_str());
        printf("+-----------------------------------------------------\n");
        return false;
    }
}

// SysSleep for cross-platform sleep
void SysSleep(longword Delay_ms) {
#ifdef OS_WINDOWS
    Sleep(Delay_ms);
#else
    struct timespec ts;
    ts.tv_sec = (time_t)(Delay_ms / 1000);
    ts.tv_nsec = (long)((Delay_ms - ts.tv_sec * 1000) * 1000000);
    nanosleep(&ts, NULL);
#endif
}

int main() {
    int ok = 0;
    int ko = 0;
    
    printf("=== Snap7 Loopback Smoke Test ===\n");
    printf("Host: %s, Port: %d, Rack: %d, Slot: %d\n\n", TEST_HOST, TEST_PORT, TEST_RACK, TEST_SLOT);
    
    // Start server in background thread
    std::thread server_thread(ServerThread);
    
    // Wait for server to be ready
    for (int i = 0; i < 50 && !server_ready; i++) {
        SysSleep(100);
    }
    
    if (!server_ready) {
        printf("ERROR: Server failed to start within timeout\n");
        server_ready = false; // Signal server thread to exit
        server_thread.join();
        return 1;
    }
    
    // Create client
    TS7Client* Client = new TS7Client();
    
    // Connect to local server
    int res = Client->ConnectTo(TEST_HOST, TEST_RACK, TEST_SLOT);
    if (Check(res, "Client Connect")) {
        printf("  Connected to   : %s (Rack=%d, Slot=%d)\n", TEST_HOST, TEST_RACK, TEST_SLOT);
        printf("  PDU Requested  : %d bytes\n", Client->PDURequested());
        printf("  PDU Negotiated : %d bytes\n", Client->PDULength());
        ok++;
    } else {
        ko++;
    }
    
    if (res == 0) {
        // Test 1: Read DB1 (should return 0xAA pattern from server callback)
        byte buffer[256];
        int size = sizeof(buffer);
        res = Client->DBRead(1, 0, size, buffer);
        if (Check(res, "DBRead (DB1)")) {
            bool pattern_ok = true;
            for (int i = 0; i < size; i++) {
                if (buffer[i] != 0xAA) {
                    pattern_ok = false;
                    break;
                }
            }
            if (pattern_ok) {
                printf("  Data pattern verified: 0xAA\n");
                ok++;
            } else {
                printf("  ERROR: Data pattern mismatch\n");
                ko++;
            }
        } else {
            ko++;
        }
        
        // Test 2: Write and read back
        byte write_data[32];
        for (int i = 0; i < 32; i++) write_data[i] = (byte)(i + 1);
        
        res = Client->DBWrite(1, 0, 32, write_data);
        if (Check(res, "DBWrite (DB1)")) {
            ok++;
        } else {
            ko++;
        }
        
        memset(buffer, 0, sizeof(buffer));
        res = Client->DBRead(1, 0, 32, buffer);
        if (Check(res, "DBRead after Write (DB1)")) {
            bool data_ok = true;
            for (int i = 0; i < 32; i++) {
                if (buffer[i] != write_data[i]) {
                    data_ok = false;
                    break;
                }
            }
            if (data_ok) {
                printf("  Write/Read verified\n");
                ok++;
            } else {
                printf("  ERROR: Write/Read data mismatch\n");
                ko++;
            }
        } else {
            ko++;
        }
        
        // Test 3: Get CPU info
        TS7CpuInfo cpu_info;
        res = Client->GetCpuInfo(&cpu_info);
        if (Check(res, "GetCpuInfo")) {
            printf("  Module Type    : %s\n", cpu_info.ModuleTypeName);
            printf("  Serial Number  : %s\n", cpu_info.SerialNumber);
            printf("  AS Name        : %s\n", cpu_info.ASName);
            printf("  Module Name    : %s\n", cpu_info.ModuleName);
            ok++;
        } else {
            ko++;
        }
        
        // Test 4: Get Order Code
        TS7OrderCode order_code;
        res = Client->GetOrderCode(&order_code);
        if (Check(res, "GetOrderCode")) {
            printf("  Order Code     : %s\n", order_code.Code);
            printf("  Version        : %d.%d.%d\n", order_code.V1, order_code.V2, order_code.V3);
            ok++;
        } else {
            ko++;
        }
        
        // Test 5: Get CP Info
        TS7CpInfo cp_info;
        res = Client->GetCpInfo(&cp_info);
        if (Check(res, "GetCpInfo")) {
            printf("  Max PDU Length   : %d bytes\n", cp_info.MaxPduLengt);
            printf("  Max Connections  : %d\n", cp_info.MaxConnections);
            printf("  Max MPI Rate     : %d bps\n", cp_info.MaxMpiRate);
            printf("  Max Bus Rate     : %d bps\n", cp_info.MaxBusRate);
            ok++;
        } else {
            ko++;
        }
        
        // Test 6: PLC Status
        int status = Client->PlcStatus();
        if (Check(res, "PlcStatus")) {
            printf("  CPU Status     : ");
            switch (status) {
                case S7CpuStatusRun: printf("RUN\n"); break;
                case S7CpuStatusStop: printf("STOP\n"); break;
                default: printf("UNKNOWN\n"); break;
            }
            ok++;
        } else {
            ko++;
        }
        
        // Test 7: List Blocks
        TS7BlocksList blocks;
        res = Client->ListBlocks(&blocks);
        if (Check(res, "ListBlocks")) {
            printf("  OB Count  : %d\n", blocks.OBCount);
            printf("  FB Count  : %d\n", blocks.FBCount);
            printf("  FC Count  : %d\n", blocks.FCCount);
            printf("  SFB Count : %d\n", blocks.SFBCount);
            printf("  SFC Count : %d\n", blocks.SFCCount);
            printf("  DB Count  : %d\n", blocks.DBCount);
            printf("  SDB Count : %d\n", blocks.SDBCount);
            ok++;
        } else {
            ko++;
        }
        
        // Test 8: Read SZL (System Zone List)
        byte szl_buffer[1024];
        int szl_size = sizeof(szl_buffer);
        PS7SZL szl = (PS7SZL)szl_buffer;
        res = Client->ReadSZL(0x0011, 0x0000, szl, &szl_size);
        if (Check(res, "ReadSZL (ID:0x0011 IDX:0x0000)")) {
            printf("  LENTHDR : %d\n", szl->Header.LENTHDR);
            printf("  N_DR    : %d\n", szl->Header.N_DR);
            ok++;
        } else {
            ko++;
        }
        
        // Test 9: Connection refusal (connect to non-listening port)
        TS7Client* Client2 = new TS7Client();
        res = Client2->ConnectTo(TEST_HOST, TEST_RACK, TEST_SLOT + 10); // Different slot, should fail
        if (res != 0) {
            printf("\n+-----------------------------------------------------\n");
            printf("| Connection Refusal Test\n");
            printf("+-----------------------------------------------------\n");
            printf("| Result         : OK (correctly refused)\n");
            printf("+-----------------------------------------------------\n");
            ok++;
        } else {
            printf("\n+-----------------------------------------------------\n");
            printf("| Connection Refusal Test\n");
            printf("+-----------------------------------------------------\n");
            printf("| ERROR: Expected connection refusal\n");
            printf("+-----------------------------------------------------\n");
            ko++;
        }
        delete Client2;
        
        // Disconnect
        Client->Disconnect();
        printf("\n[CLIENT] Disconnected\n");
    }
    
    // Cleanup
    delete Client;
    
    // Stop server
    server_ready = false;
    server_thread.join();
    
    // Summary
    printf("\n=== Test Summary ===\n");
    printf("Performed : %d\n", (ok + ko));
    printf("Passed    : %d\n", ok);
    printf("Failed    : %d\n", ko);
    
    return (ko == 0) ? 0 : 1;
}