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

class DogBankAccount(BankAccount):

    def __init__(self, owner, balance):
        BankAccount.__init__(self, owner, balance)

    def bark(self):
        print(f"{self.owner} says woof")
        main.update()
        print()

class LinkedListNode():
    def __init__(self, value):
        self.value = value
        self.next = None

    def append(self, value):
        cur_node = self
        while cur_node.next is not None:
            cur_node = cur_node.next
            #main.update()
        cur_node.next = LinkedListNode(value)

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

transferCount = 0
def transfer(source, destination, amount):
    global transferCount
    transfer2 = transferCount

    def someOtherFunc():
        nonlocal transfer2
        transfer2 += 1
        #main.update()

    if source.withdraw(amount):
        destination.deposit(amount)
        transferCount += 1
        someOtherFunc()
        #main.update()
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


headNode = LinkedListNode(0)
headNode.append(10)
headNode.append(20)
headNode.append(30)
headNode.append(40)
headNode.append(50)

clifford = DogBankAccount("Clifford", 100)
clifford.bark()

accounts = create_accounts()

alice = accounts[0]
bob = accounts[1]

shared_history = alice.transactions

transfer(alice, bob, 50)

alice_summary = summarize(alice)
bob_summary = summarize(bob)

alice_total = total_transactions(alice)
bob_total = total_transactions(bob)

testList = [1,2,3,4,5,6,alice]
testList2 = ['abc','123','xyz']

# funny_dict = { alice: alice_summary, bob: bob_summary }

print(alice_summary)
print(bob_summary)
print(alice_total)
print(bob_total)

main.update(renderFrames=False)