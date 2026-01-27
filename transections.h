#pragma once
#include <vector>
#include <iostream>
#include <string>

using namespace std;

struct TransactionInput {
    string prev_tx;
    int index;
    string owner;
};

struct TransectionOutput {
    double amount;
    string address;
};

struct Transections {
    string tx_id;
    vector<TransactionInput> inputs;
    vector<TransectionOutput> outputs;
};