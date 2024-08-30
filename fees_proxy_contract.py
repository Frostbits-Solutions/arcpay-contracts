from pyteal import *
from subroutine import total_client


def approval_program():

    on_create = Seq(
        App.globalPut(Concat(Bytes('m_'), Txn.sender()), Txn.sender()),
        App.globalPut(total_client, Int(0)),
        Approve()
    )

    add_token = Seq(
        If(
            App.globalGet(Concat(Bytes('m_'), Txn.sender())) == Txn.sender()
        ).Then(
            If(
                Txn.application_args[1] == Bytes("asa")
            ).Then(
                InnerTxnBuilder.Begin(),
                InnerTxnBuilder.SetFields(
                    {
                        TxnField.type_enum: TxnType.AssetTransfer,
                        TxnField.xfer_asset: Btoi(Txn.application_args[2]),
                        TxnField.asset_receiver: Global.current_application_address(),
                    }
                ),
                InnerTxnBuilder.Submit()
            ),
            App.globalPut(Txn.application_args[2], Btoi(Txn.application_args[3])),
            Approve()
        ),
        Reject()
    )

    del_token = Seq(
        If(
            App.globalGet(Concat(Bytes('m_'), Txn.sender())) == Txn.sender()
        ).Then(
            If(
                Txn.application_args[1] == Bytes("asa")
            ).Then(
                InnerTxnBuilder.Begin(),
                InnerTxnBuilder.SetFields(
                    {
                        TxnField.type_enum: TxnType.AssetTransfer,
                        TxnField.xfer_asset: Btoi(Txn.application_args[2]),
                        TxnField.asset_close_to: Global.creator_address()
                    }
                ),
                InnerTxnBuilder.Submit()
            ),
            App.globalDel(Txn.application_args[2]),
            Approve()
        ),
        Reject()
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
        Assert(App.globalGet(Concat(Bytes('m_'), Txn.sender())) == Txn.sender()),
        App.globalPut(Txn.application_args[1], Int(1)),
        Approve()
    )

    del_client = Seq(
        Assert(App.globalGet(Concat(Bytes('m_'), Txn.sender())) == Txn.sender()),
        App.globalDel(Txn.application_args[1]),
        Approve(),
    )

    add_network_fees = Seq(
        If(
            # Check client has more than 0 as fees
            App.globalGet(Txn.application_args[1]) > Int(0)
        ).Then(
            # Check the amount send in tx is greater than the fees to add
            Assert(Gtxn[Txn.group_index() - Int(1)].amount() >= Btoi(Txn.application_args[2])),
            # update the amount of fees of the client
            App.globalPut(
                Txn.application_args[1],
                Add(
                    Btoi(Txn.application_args[2]),
                    App.globalGet(Txn.application_args[1])
                )
            ),
            # update the amount of total client
            App.globalPut(
                total_client,
                Add(
                    Btoi(Txn.application_args[2]),
                    App.globalGet(total_client)
                )
            )
        ),
        Approve()
    )

    add_arc200_fees = Seq(
        If(
            Gtxn[Txn.group_index() - Int(1)].type_enum() == TxnType.AssetTransfer
        ).Then(
            If(
                Gtxn[Txn.group_index() - Int(1)].asset_amount() <= Btoi(Txn.application_args[2])
            ).Then(
                Approve()
            )
        ).Else(
            If(
                Btoi(Substring(Gtxn[Txn.group_index() - Int(1)].application_args[2], Int(24), Int(32))) <= Btoi(Txn.application_args[2])
            ).Then(
                Approve()
            )
        ),
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.ApplicationCall,
                TxnField.application_id: App.globalGet(Txn.application_args[3]),
                TxnField.on_completion: OnComplete.NoOp,
                TxnField.application_args: [
                    Bytes('add_fees'),
                    Txn.application_args[1],
                    Txn.application_args[2]
                ],
                TxnField.applications: [App.globalGet(Txn.application_args[3])]
            }
        ),
        InnerTxnBuilder.Submit(),
        Approve()
    )

    claim_network_fees_client = Seq(
        # Check the client has some network to claim
        Assert(App.globalGet(Txn.sender()) > Int(1)),
        Seq(
            # Send the network fees to the client
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.Payment,
                    TxnField.amount: Minus(App.globalGet(Txn.sender()), Int(1)),
                    TxnField.sender: Global.current_application_address(),
                    TxnField.receiver: Txn.sender()
                }
            ),
            InnerTxnBuilder.Submit(),
            # Decrease the total amount for client from what was sent
            App.globalPut(
                total_client,
                Minus(
                    App.globalGet(total_client),
                    Minus(App.globalGet(Txn.sender()), Int(1))
                )
            ),
            # Put fees to client to default value (1)
            App.globalPut(Txn.sender(), Int(1))
        ),
        Approve()
    )

    claim_network_fees_team = Seq(
        Assert(
            And(
                # Check a master is claiming
                App.globalGet(Concat(Bytes('m_'), Txn.sender())) == Txn.sender(),
                # Check network to send is greater than 0
                Balance(Global.current_application_address())
                >
                Add(App.globalGet(total_client), Global.min_balance(), Int(100_000))
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
                        Add(App.globalGet(total_client), Global.min_balance(), Int(100_000))
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
        [Txn.application_args[0] == Bytes("test"), Approve()],
        [Txn.application_args[0] == Bytes("add_master"), add_master],
        [Txn.application_args[0] == Bytes("del_master"), del_master],
        [Txn.application_args[0] == Bytes("add_token"), add_token],
        [Txn.application_args[0] == Bytes("del_token"), del_token],
        [Txn.application_args[0] == Bytes("add_client"), add_client],
        [Txn.application_args[0] == Bytes("del_client"), del_client],
        [Txn.application_args[0] == Bytes("add_network_fees"), add_network_fees],
        [Txn.application_args[0] == Bytes("add_arc200_fees"), add_arc200_fees],
        [Txn.application_args[0] == Bytes("claim_network_fees_client"), claim_network_fees_client],
        [Txn.application_args[0] == Bytes("claim_network_fees_team"), claim_network_fees_team],
    )

    return program
