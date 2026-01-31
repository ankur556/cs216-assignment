#include <iostream>
#include <unordered_map>
#include <vector>
#include <string>
#include "transactions.h"

using namespace std;

class UTXOManager {
private:
    unordered_map<string, TransactionOutput> utxo_set;

    string make_key(const string & tx_id, int index) {
        return tx_id + ":" + to_string(index);
    }

public:
    void add_utxo(string tx_id, int index, double amount, string owner) {
        string key = make_key(tx_id, index);
        utxo_set[key] = {amount, owner};
    }

    void remove_utxo(const string & tx_id, int index) {
        utxo_set.erase(make_key(tx_id, index));
    }

    bool exists(string tx_id, int index) {
        return utxo_set.find(make_key(tx_id, index)) != utxo_set.end();
    }

    double get_balance(string owner) {
        double balance = 0.0;
        for (auto const& entry : utxo_set) {
            if (entry.second.address == owner) {
                balance += entry.second.amount;
            }
        }
        return balance;
    }

    vector<TransactionOutput> get_utxos_for_owner(string owner) {
        vector<TransactionOutput> results;
        for (auto const& entry : utxo_set) {
            if (entry.second.address == owner) {
                results.push_back(entry.second);
            }
        }
        return results;
    }
};

int main() {
    UTXOManager myManager;
    myManager.add_utxo("tx1", 0, 50.0, "Alice");
    cout << "Alice's Balance: " << myManager.get_balance("Alice") << endl;
    return 0;
}