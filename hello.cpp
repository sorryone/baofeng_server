#include <Python.h>
using namespace std; 
#include <iostream>
#include "stdio.h"
#include   <stdlib.h>             
#include   <string.h>

int main() {
    cout  << "test\n";
    int data;  
    unsigned char buf[255] = {0x4F, 0x00, 0x00, 0x00, 01, 00, 00, 00, 11, 27, 00, 00};  
              
    //memcpy(buf, &data, sizeof(int)); 
    memcpy(&data, buf, 4); 
    char a [4];
    int s = 20;
    memcpy(a, &s, 4);
    printf ("%d,%d,%d,%d\n", a[0], a[1], a[2], a[3]);
    printf ("%d\n", data);
    return 0;
}

class TestFact{
public:
    TestFact(){};
    ~TestFact(){};
    int fact(int n);
};

int TestFact::fact(int n)
{
    if (n <= 1)
        return 1;
    else
        return n * (n - 1);
}

extern "C"
int fact(int n)
{
    TestFact t;
    return t.fact(n);
}
