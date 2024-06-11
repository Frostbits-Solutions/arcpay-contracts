from pyteal import *
from algosdk.v2client.algod import AlgodClient
from base64 import b64decode
from algosdk import transaction, mnemonic, account, encoding


def get_application_address(app_id):
    to_sign = b"appID" + app_id.to_bytes(8, "big")
    checksum = encoding.checksum(to_sign)
    return encoding.encode_address(checksum)


def clear_state_program():
    return Approve()


def compile_program(program):
    teal = compileTeal(program, mode=Mode.Application, version=10)
    response = client.compile(teal)
    return b64decode(response["result"])


def wait_for_confirmation(algod_client, tx_id):
    last_round = algod_client.status().get('last-round')
    tx_info = algod_client.pending_transaction_info(tx_id)
    while not (tx_info.get('confirmed-round') and tx_info.get('confirmed-round') > 0):
        last_round += 1
        algod_client.status_after_block(last_round)
        tx_info = algod_client.pending_transaction_info(tx_id)
    return tx_info


algod_token_tx = ""
headers_tx = {"X-Algo-API-Token": algod_token_tx}
client = AlgodClient(
    algod_token=algod_token_tx,
    algod_address="https://testnet-api.voi.nodly.io:443",
    headers=headers_tx,
)


def approval_program():

    on_create = Seq(
        App.globalPut(Concat(Bytes('m_'), Txn.sender()), Txn.sender()),
        App.globalPut(Bytes('total_client'), Int(0)),
        Approve()
    )

    add_master = Seq(
        If(
            App.globalGet(Concat(Bytes('m_'), Txn.sender())) == Txn.sender()
        ).Then(
            App.globalPut(Concat(Bytes('m_'), Txn.application_args[1]), Txn.application_args[1]),
            Approve()
        ),
        Reject()
    )

    del_master = Seq(
        If(
            App.globalGet(Concat(Bytes('m_'), Txn.sender())) == Txn.sender()
        ).Then(
            App.globalDel(Concat(Bytes('m_'), Txn.application_args[1])),
            Approve()
        ),
        Reject()
    )

    add_client = Seq(
        If(
            App.globalGet(Concat(Bytes('m_'), Txn.sender())) == Txn.sender()
        ).Then(
            App.globalPut(Concat(Bytes('c_'), Txn.application_args[1]), Txn.application_args[1]),
            App.globalPut(Concat(Bytes('network_'), Txn.application_args[1]), Int(1)),
            Approve()
        ),
        Reject()
    )

    del_client = Seq(
        If(
            App.globalGet(Concat(Bytes('m_'), Txn.sender())) == Txn.sender()
        ).Then(
            App.globalDel(Concat(Bytes('network_'), Txn.application_args[1])),
            App.globalDel(Concat(Bytes('c_'), Txn.application_args[1])),
            Approve()
        ),
        Reject()
    )

    add_network_fees = Seq(
        If(
            # Check client has more than 0 as fees
            App.globalGet(Concat(Bytes('network_'), Txn.application_args[1])) > Int(0)
        ).Then(
            # Double check client exist and the amount send in tx is greater than the fees to add
            Assert(
                And(
                    App.globalGet(Concat(Bytes('c_'), Txn.application_args[1])) == Txn.application_args[1],
                    Gtxn[Txn.group_index() - Int(1)].amount() >= Btoi(Txn.application_args[2])
                )
            ),
            # update the amount of fees of the client
            App.globalPut(
                Concat(Bytes('network_'), Txn.application_args[1]),
                Add(
                    Btoi(Txn.application_args[2]),
                    App.globalGet(Concat(Bytes('network_'), Txn.application_args[1]))
                )
            ),
            # update the amount of total client
            App.globalPut(
                Bytes('total_client'),
                Add(
                    Btoi(Txn.application_args[2]),
                    App.globalGet(Bytes('total_client'))
                )
            ),
            Approve()
        ),
        Approve()
    )

    claim_network_fees_client = Seq(
        # Check the client has some network to claim
        Assert(App.globalGet(Concat(Bytes('network_'), Txn.sender())) > Int(1)),
        # Double check client exist
        Assert(App.globalGet(Concat(Bytes('c_'), Txn.sender())) == Txn.sender()),
        Seq(
            # Send the network fees to the client
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.Payment,
                    TxnField.amount: Minus(App.globalGet(Concat(Bytes('network_'), Txn.sender())), Int(1)),
                    TxnField.sender: Global.current_application_address(),
                    TxnField.receiver: Txn.sender()
                }
            ),
            InnerTxnBuilder.Submit(),
            # Decrease the total amount for client from what was sent
            App.globalPut(
                Bytes('total_client'),
                Minus(
                    App.globalGet(Bytes('total_client')),
                    Minus(App.globalGet(Concat(Bytes('network_'), Txn.sender())), Int(1))
                )
            ),
            # Put fees to client to default value (1)
            App.globalPut(
                Concat(Bytes('network_'), Txn.sender()),
                Int(1)
            ),
        ),
        Approve()
    )

    claim_our_network_fees = Seq(
        Assert(
            And(
                # Check a master is claiming
                App.globalGet(Concat(Bytes('m_'), Txn.sender())) == Txn.sender(),
                # Check network to send is greater than 0
                Balance(Global.current_application_address())
                >
                Add(App.globalGet(Bytes('total_client')), Global.min_balance(), Int(100_000))
            )
        ),
        Seq(
            # Send the network fees to the client
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.Payment,
                    TxnField.amount: Minus(
                        # Remove the total amount reserved to client, the min balance and a security from the total
                        Balance(Global.current_application_address()),
                        Add(App.globalGet(Bytes('total_client')), Global.min_balance(), Int(100_000))
                    ),
                    TxnField.sender: Global.current_application_address(),
                    TxnField.receiver: Txn.sender()
                }
            ),
            InnerTxnBuilder.Submit(),
        ),
        Approve()
    )

    on_delete = Seq(
        Assert(Txn.sender() == Global.creator_address()),
        If(
            Balance(Global.current_application_address()) != Int(0)
        ).Then(
            Seq(
                InnerTxnBuilder.Begin(),
                InnerTxnBuilder.SetFields(
                    {
                        TxnField.type_enum: TxnType.Payment,
                        TxnField.close_remainder_to: Global.creator_address(),
                    }
                ),
                InnerTxnBuilder.Submit()
            )
        ),
        Approve()
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.on_completion() == OnComplete.DeleteApplication, on_delete],
        [Txn.application_args[0] == Bytes("add_master"), add_master],
        [Txn.application_args[0] == Bytes("del_master"), del_master],
        [Txn.application_args[0] == Bytes("add_client"), add_client],
        [Txn.application_args[0] == Bytes("del_client"), del_client],
        [Txn.application_args[0] == Bytes("add_network_fees"), add_network_fees],
        [Txn.application_args[0] == Bytes("claim_network_fees_client"), claim_network_fees_client],
        [Txn.application_args[0] == Bytes("claim_our_network_fees"), claim_our_network_fees],
    )

    return program


print("create app")
mnemonic_creator = "arrest pear require glad middle legend army stick bounce brush oyster police family version width endorse inquiry expand voice knee where foam search absent flush"
mnemonic_client = "fish report foil gate west poverty margin vibrant visual pet asset proud park insect define blur suffer kidney expand student usual sort true absent raccoon"
private_key_creator = mnemonic.to_private_key(mnemonic_creator)
private_key_client = mnemonic.to_private_key(mnemonic_client)
public_key_creator = account.address_from_private_key(private_key_creator)
public_key_client = account.address_from_private_key(private_key_client)
# txn = transaction.ApplicationCreateTxn(
#     sender=public_key_creator,
#     on_complete=transaction.OnComplete.NoOpOC,
#     approval_program=compile_program(approval_program()),
#     clear_program=compile_program(clear_state_program()),
#     global_schema=transaction.StateSchema(num_uints=7, num_byte_slices=7),
#     local_schema=transaction.StateSchema(num_uints=0, num_byte_slices=0),
#     sp=client.suggested_params(),
# )
# signedTxn = txn.sign(private_key_creator)
# data = client.send_transaction(signedTxn)
# print("Creation tx id:", data)
# test = wait_for_confirmation(client, data)
# print("Creation app id:", test['application-index'])
# app_address = get_application_address(test['application-index'])
# print("Application Address", app_address)
#
#
# input("wait")
#
#
# print("start add master")
# app_args = [b"add_master", encoding.decode_address("4QEDSOV3U67UBPX6LXBVKWOFB4UYN465AJBSCU7SJHBG7ET4RVEMUIHXBM")]
# txn = transaction.ApplicationCallTxn(
#     sender=public_key_creator,
#     index=test['application-index'],
#     on_complete=transaction.OnComplete.NoOpOC,
#     app_args=app_args,
#     sp=client.suggested_params(),
# )
# signedTxn = txn.sign(private_key_creator)
# client.send_transaction(signedTxn)
# print("end add master")
#
#
# input("wait")
#
#
# print("start add master")
# mnemonic_second = "bag breeze topic like hollow upgrade tissue guitar miss deny grocery easy record smoke inject casino great exhaust label rough coyote inflict future ability wave"
# private_key_second = mnemonic.to_private_key(mnemonic_second)
# public_key_second = account.address_from_private_key(private_key_second)
# app_args = [b"add_master", encoding.decode_address("6J4RO7U2WYQWOGWXQOZUTBBA46W4QSFL5HTHJWC5BZR53RSYRAOPAY7KPM")]
# txn = transaction.ApplicationCallTxn(
#     sender=public_key_second,
#     index=test['application-index'],
#     on_complete=transaction.OnComplete.NoOpOC,
#     app_args=app_args,
#     sp=client.suggested_params(),
# )
# signedTxn = txn.sign(private_key_second)
# client.send_transaction(signedTxn)
# print("end add master")
#
#
# input("wait")
#
#
# print("start del master")
# app_args = [b"del_master", encoding.decode_address("6J4RO7U2WYQWOGWXQOZUTBBA46W4QSFL5HTHJWC5BZR53RSYRAOPAY7KPM")]
# txn = transaction.ApplicationCallTxn(
#     sender=public_key_creator,
#     index=test['application-index'],
#     on_complete=transaction.OnComplete.NoOpOC,
#     app_args=app_args,
#     sp=client.suggested_params(),
# )
# signedTxn = txn.sign(private_key_creator)
# client.send_transaction(signedTxn)
# print("end del master")
#
# input("wait")
#
# print("start add client")
# app_args = [b"add_client", encoding.decode_address("6J4RO7U2WYQWOGWXQOZUTBBA46W4QSFL5HTHJWC5BZR53RSYRAOPAY7KPM")]
# txn = transaction.ApplicationCallTxn(
#     sender=public_key_creator,
#     index=test['application-index'],
#     on_complete=transaction.OnComplete.NoOpOC,
#     app_args=app_args,
#     sp=client.suggested_params(),
# )
# signedTxn = txn.sign(private_key_creator)
# client.send_transaction(signedTxn)
# print("end add client")
#
# input("wait")
#
# print("start del client")
# app_args = [b"del_client", encoding.decode_address("6J4RO7U2WYQWOGWXQOZUTBBA46W4QSFL5HTHJWC5BZR53RSYRAOPAY7KPM")]
# txn = transaction.ApplicationCallTxn(
#     sender=public_key_creator,
#     index=test['application-index'],
#     on_complete=transaction.OnComplete.NoOpOC,
#     app_args=app_args,
#     sp=client.suggested_params(),
# )
# signedTxn = txn.sign(private_key_creator)
# client.send_transaction(signedTxn)
# print("end del client")
#
# input("wait")
#
# print("start add client")
# app_args = [b"add_client", encoding.decode_address("6J4RO7U2WYQWOGWXQOZUTBBA46W4QSFL5HTHJWC5BZR53RSYRAOPAY7KPM")]
# txn = transaction.ApplicationCallTxn(
#     sender=public_key_creator,
#     index=test['application-index'],
#     on_complete=transaction.OnComplete.NoOpOC,
#     app_args=app_args,
#     sp=client.suggested_params(),
# )
# signedTxn = txn.sign(private_key_creator)
# client.send_transaction(signedTxn)
# print("end add client")
#
# input("wait")

# print("start add network client fake")
# app_args = [b"add_network_fees", encoding.decode_address("IWVHFOUARK3DWFUNITGC57UHNZ46YW7PWJQBGME5AD3IPEI6FAYUYYTDGI"), 4]
# txn = transaction.ApplicationCallTxn(
#     sender=public_key_creator,
#     index=test['application-index'],
#     on_complete=transaction.OnComplete.NoOpOC,
#     app_args=app_args,
#     sp=client.suggested_params(),
# )
# signedTxn = txn.sign(private_key_creator)
# client.send_transaction(signedTxn)
# print("end add client fake")
#
input("wait")
app_address='HYGWVRG7UKZWMGIGV2HCGDQDQ4Q5CDZZVTSB4L6BE4PZQX4QTHPPNTZU7A'
print("start add network client")
params = client.suggested_params()
txn_payment = transaction.PaymentTxn(public_key_creator, params, app_address, 30_000)
app_args = [b"add_network_fees", encoding.decode_address("6J4RO7U2WYQWOGWXQOZUTBBA46W4QSFL5HTHJWC5BZR53RSYRAOPAY7KPM"), 10_000]
txn = transaction.ApplicationCallTxn(
    sender=public_key_creator,
    index=49547082,#test['application-index'],
    on_complete=transaction.OnComplete.NoOpOC,
    app_args=app_args,
    sp=params,
)
transaction.assign_group_id([txn_payment, txn])
signed_txn_payment = txn_payment.sign(private_key_creator)
signed_txn = txn.sign(private_key_creator)
signed_group = [signed_txn_payment, signed_txn]
client.send_transactions(signed_group)
print("end add network client")
#
# input("wait")
#
# print("start claim our network fees")
# app_args = [b"claim_our_network_fees"]
# txn = transaction.ApplicationCallTxn(
#     sender=public_key_creator,
#     index=test['application-index'],
#     on_complete=transaction.OnComplete.NoOpOC,
#     app_args=app_args,
#     sp=client.suggested_params(),
# )
# signedTxn = txn.sign(private_key_creator)
# client.send_transaction(signedTxn)
# print("end claim our network fees")
#
# input("wait")
#
# print("start claim network client")
# app_args = [b"claim_network_fees_client"]
# txn = transaction.ApplicationCallTxn(
#     sender=public_key_client,
#     index=test['application-index'],
#     on_complete=transaction.OnComplete.NoOpOC,
#     app_args=app_args,
#     sp=client.suggested_params(),
# )
# signed_txn = txn.sign(private_key_client)
# client.send_transaction(signed_txn)
# print("end claim client")
#
# input("wait")
#
#
# try:
#     print("start claim network client")
#     app_args = [b"claim_network_fees_client"]
#     txn = transaction.ApplicationCallTxn(
#         sender=public_key_client,
#         index=test['application-index'],
#         on_complete=transaction.OnComplete.NoOpOC,
#         app_args=app_args,
#         sp=client.suggested_params(),
#     )
#     signed_txn = txn.sign(private_key_client)
#     client.send_transaction(signed_txn)
#     print("end claim client")
# except:
#     print("fail to claim network")
#
# input("wait")
#
# print("start del app")
# delete_txn = transaction.ApplicationDeleteTxn(
#     sender=public_key_creator,
#     index=test['application-index'],
#     # accounts=accounts,
#     sp=client.suggested_params(),
# )
# delete_txn = delete_txn.sign(private_key_creator)
# client.send_transaction(delete_txn)
# print("end del app")
#
# input("wait")
