import main

''' TEST CODE '''

class BankAccount:
    bank_name = "Python Bank"

    def __init__(self, owner, balance):
        self.owner = owner
        self.balance = balance
        self.transactions = []

    def deposit(self, amount):
        self.balance += amount
        self.transactions.append(amount)

    def withdraw(self, amount):
        if amount <= self.balance:
            self.balance -= amount
            self.transactions.append(-amount)
            return True
        return False


def total_transactions(account):
    total = 0

    for amount in account.transactions:
        total += amount

    return total


def summarize(account):
    history = {
        "owner": account.owner,
        "balance": account.balance,
        "transactions": account.transactions,
    }

    return history


def transfer(source, destination, amount):
    if source.withdraw(amount):
        destination.deposit(amount)
        return True

    return False


def create_accounts():
    alice = BankAccount("Alice", 100)
    bob = BankAccount("Bob", 50)

    alice.deposit(25)
    alice.deposit(10)

    bob.deposit(40)

    #main.update()

    return alice, bob


accounts = create_accounts()

alice = accounts[0]
bob = accounts[1]

shared_history = alice.transactions

transfer(alice, bob, 50)

alice_summary = summarize(alice)
bob_summary = summarize(bob)

alice_total = total_transactions(alice)
bob_total = total_transactions(bob)

funny_dict = { alice: alice_summary, bob: bob_summary }

print(alice_summary)
print(bob_summary)
print(alice_total)
print(bob_total)

main.update()