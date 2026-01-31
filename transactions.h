#pragma once

#include <string>
#include <vector>

struct TransactionInput {
    std::string prev_tx;
    int index;
    std::string owner;
};

struct TransactionOutput {
    double amount;
    std::string address;
};

struct Transactions {
    std::string tx_id;
    std::vector<TransactionInput> inputs;
    std::vector<TransactionOutput> outputs;
};
